"""Main recorder class for TestCaseer."""

import asyncio
import contextlib
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from playwright.async_api import ConsoleMessage, Request, Response
from rich.console import Console

from testcaseer.browser import BrowserManager
from testcaseer.control_panel import CONTROL_PANEL_JS, inject_control_panel, update_panel_ui
from testcaseer.events import EVENT_LISTENER_JS, parse_element_info, setup_event_listeners
from testcaseer.exporters import HTMLExporter, JSONExporter, MarkdownExporter
from testcaseer.models import (
    ActionType,
    ConsoleLog,
    ElementInfo,
    NetworkRequest,
    PageError,
    Step,
    TestCase,
)
from testcaseer.screenshot import generate_screenshot_filename, take_screenshot

console = Console()


class Recorder:
    """
    Main class for recording browser actions.

    Manages the recording session, captures user actions, takes screenshots,
    captures console logs and network requests, and exports the test case
    in multiple formats.

    Usage:
        recorder = Recorder(
            output_dir=Path("./output"),
            start_url="https://example.com",
            name="My Test Case"
        )
        await recorder.run()
    """

    def __init__(
        self,
        output_dir: Path,
        start_url: str,
        name: str = "Test Case",
        browser_type: str = "chromium",
        headless: bool = False,
        viewport: tuple[int, int] = (1280, 720),
        timeout: int = 30000,
    ) -> None:
        """
        Initialize the recorder.

        Args:
            output_dir: Directory to save output files
            start_url: URL to open when starting
            name: Name for the test case
            browser_type: Browser to use (chromium, firefox, webkit)
            headless: Run browser without GUI
            viewport: Browser window size (width, height)
            timeout: Default timeout for operations in ms
        """
        self.output_dir = Path(output_dir).resolve()
        self.start_url = start_url
        self.name = name
        self.browser_type = browser_type
        self.headless = headless
        self.viewport = viewport
        self.timeout = timeout

        # Recording state
        self.is_recording = False
        self.steps: list[Step] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

        # Logs and network requests
        self.console_logs: list[ConsoleLog] = []
        self.network_requests: list[NetworkRequest] = []
        self.page_errors: list[PageError] = []
        self._pending_requests: dict[str, tuple[NetworkRequest, Request]] = {}
        self._step_console_logs: list[ConsoleLog] = []  # Logs for current step
        self._step_network_requests: list[NetworkRequest] = []  # Requests for current step

        # Browser manager
        self._browser_manager: BrowserManager | None = None

        # Control flags
        self._stop_event = asyncio.Event()
        self._recording_complete = asyncio.Event()

    @property
    def screenshots_dir(self) -> Path:
        """Get the screenshots directory."""
        return self.output_dir / "screenshots"

    async def run(self) -> None:
        """
        Run the recording session.

        Opens the browser, injects the control panel, and waits for user
        to start/stop recording via the UI controls.
        """
        # Prepare output directory
        self._prepare_output_dir()

        # Create browser manager
        self._browser_manager = BrowserManager(
            browser_type=self.browser_type,  # type: ignore[arg-type]
            headless=self.headless,
            viewport=self.viewport,
            timeout=self.timeout,
        )

        try:
            # Start browser
            page = await self._browser_manager.start()
            console.print("[green]✓[/green] Browser launched")

            # Set up event handlers for page events
            page.on("load", self._on_page_load)
            page.on("domcontentloaded", self._on_dom_ready)

            # Set up console and network listeners
            page.on("console", self._on_console_message)
            page.on("pageerror", self._on_page_error)
            page.on("request", self._on_request)
            page.on("response", self._on_response)
            page.on("requestfailed", self._on_request_failed)

            console.print("[green]✓[/green] Console & network listeners attached")

            # Set up control panel and event listeners
            await inject_control_panel(page, self)
            await setup_event_listeners(page, self)
            console.print("[green]✓[/green] Control panel injected")

            # Navigate to start URL
            await self._browser_manager.navigate(self.start_url)
            console.print(f"[green]✓[/green] Navigated to {self.start_url}")

            page_title = await page.title()
            if page_title:
                console.print(f"[green]✓[/green] Page loaded: {page_title}")

            console.print("\n[bold]Ready to record![/bold]")
            console.print("[dim]Click '▶ Start' in the browser to begin recording.[/dim]")
            console.print("[dim]Press Ctrl+C to cancel.[/dim]\n")

            # Wait for recording to complete
            await self._recording_complete.wait()

        finally:
            # Cleanup
            if self._browser_manager:
                await self._browser_manager.close()
                console.print("[green]✓[/green] Browser closed")

    def _prepare_output_dir(self) -> None:
        """Create output directories."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    # -------------------------------------------------------------------------
    # Console and Network Event Handlers
    # -------------------------------------------------------------------------

    def _on_console_message(self, message: ConsoleMessage) -> None:
        """Handle console message event."""
        if not self.is_recording:
            return

        # Map playwright message types to our levels
        level_map = {
            "log": "log",
            "info": "info",
            "warning": "warn",
            "error": "error",
            "debug": "debug",
            "trace": "trace",
        }

        level = level_map.get(message.type, "log")

        log_entry = ConsoleLog(
            level=level,  # type: ignore[arg-type]
            message=message.text,
            timestamp=datetime.now(),
            source=message.location.get("url") if message.location else None,
            args=[str(arg) for arg in message.args[:5]],  # Limit args
        )

        self.console_logs.append(log_entry)
        self._step_console_logs.append(log_entry)

        # Log to terminal based on level
        if level == "error":
            console.print(f"    [red]Console Error:[/red] {message.text[:80]}")
        elif level == "warn":
            console.print(f"    [yellow]Console Warn:[/yellow] {message.text[:80]}")

    def _on_page_error(self, error: Exception) -> None:
        """Handle page JavaScript error."""
        if not self.is_recording:
            return

        page_error = PageError(
            message=str(error),
            stack=getattr(error, "stack", None),
            timestamp=datetime.now(),
        )

        self.page_errors.append(page_error)
        console.print(f"    [red]JS Error:[/red] {str(error)[:80]}")

    def _on_request(self, request: Request) -> None:
        """Handle network request start."""
        if not self.is_recording:
            return

        # Skip data URLs and internal requests
        url = request.url
        if url.startswith("data:") or "__testcaseer" in url:
            return

        # Get request body for POST/PUT/PATCH
        request_body: str | None = None
        if request.method in ("POST", "PUT", "PATCH"):
            with contextlib.suppress(Exception):
                request_body = request.post_data

        # Create network request entry
        net_request = NetworkRequest(
            method=request.method,
            url=url,
            resource_type=request.resource_type,
            timestamp=datetime.now(),
            request_headers=dict(request.headers),
            request_body=request_body,
        )

        # Store pending request to match with response
        self._pending_requests[url] = (net_request, request)

    def _on_response(self, response: Response) -> None:
        """Handle network response."""
        if not self.is_recording:
            return

        url = response.url

        # Find matching request
        if url in self._pending_requests:
            net_request, original_request = self._pending_requests.pop(url)

            # Update with response data
            net_request.status = response.status
            net_request.response_headers = dict(response.headers)

            # Calculate timing
            timing = response.request.timing
            if timing and timing.get("responseEnd"):
                net_request.timing = timing.get("responseEnd", 0)

            # For XHR/fetch requests, try to capture response body
            if net_request.resource_type in ("xhr", "fetch"):
                # Schedule async body capture
                asyncio.create_task(self._capture_response_body(response, net_request))
            else:
                # Add to lists immediately for non-XHR requests
                self.network_requests.append(net_request)
                self._step_network_requests.append(net_request)

            # Log significant requests
            if response.status >= 400:
                console.print(
                    f"    [red]HTTP {response.status}:[/red] {net_request.method} {url[:60]}"
                )
            elif net_request.resource_type in ("xhr", "fetch"):
                console.print(
                    f"    [dim]API {response.status}:[/dim] {net_request.method} {url[:60]}"
                )

    async def _capture_response_body(self, response: Response, net_request: NetworkRequest) -> None:
        """Capture response body for XHR/fetch requests asynchronously."""
        try:
            # Try to get response body (limit to 50KB to avoid huge responses)
            body_bytes = await response.body()
            if len(body_bytes) <= 50 * 1024:  # 50KB limit
                try:
                    # Try to decode as text
                    body_text = body_bytes.decode("utf-8")
                    # Truncate if too long
                    if len(body_text) > 10000:
                        body_text = body_text[:10000] + "\n... (truncated)"
                    net_request.response_body = body_text
                except UnicodeDecodeError:
                    net_request.response_body = f"[Binary data, {len(body_bytes)} bytes]"
            else:
                net_request.response_body = f"[Large response, {len(body_bytes)} bytes]"
        except Exception as e:
            net_request.response_body = f"[Error capturing body: {e}]"
        finally:
            # Add to lists after body capture
            self.network_requests.append(net_request)
            self._step_network_requests.append(net_request)

    def _on_request_failed(self, request: Request) -> None:
        """Handle failed network request."""
        if not self.is_recording:
            return

        url = request.url

        if url in self._pending_requests:
            net_request, _ = self._pending_requests.pop(url)
            net_request.error = request.failure or "Request failed"

            self.network_requests.append(net_request)
            self._step_network_requests.append(net_request)

            console.print(f"    [red]Request Failed:[/red] {net_request.method} {url[:60]}")

    # -------------------------------------------------------------------------
    # Page Navigation Handlers
    # -------------------------------------------------------------------------

    async def _on_page_load(self, _: Any) -> None:
        """Handle page load event."""
        if self._browser_manager and self._browser_manager._page:
            # Re-inject control panel and event listeners
            try:
                await self._browser_manager._page.evaluate(CONTROL_PANEL_JS)
                await self._browser_manager._page.evaluate(EVENT_LISTENER_JS)
                await update_panel_ui(
                    self._browser_manager._page,
                    self.is_recording,
                    len(self.steps),
                )
            except Exception:
                pass

    async def _on_dom_ready(self, _: Any) -> None:
        """Handle DOM content loaded event."""
        pass

    # -------------------------------------------------------------------------
    # Recording Control
    # -------------------------------------------------------------------------

    async def start_recording(self) -> None:
        """
        Start recording user actions.

        Called when user clicks the Start button in the control panel.
        """
        if self.is_recording:
            return

        self.is_recording = True
        self.start_time = datetime.now()
        self.steps = []
        self.console_logs = []
        self.network_requests = []
        self.page_errors = []

        console.print("\n[bold red]● Recording started[/bold red]")
        console.print("[dim]Perform your actions in the browser...[/dim]")
        console.print("[dim]Console logs and network requests are being captured.[/dim]\n")

        # Update UI
        if self._browser_manager and self._browser_manager._page:
            await update_panel_ui(
                self._browser_manager._page,
                is_recording=True,
                steps_count=0,
            )

    async def stop_recording(self) -> None:
        """
        Stop recording and save results.

        Called when user clicks the Stop button in the control panel.
        """
        if not self.is_recording:
            # If not recording, just close
            self._recording_complete.set()
            return

        self.is_recording = False
        self.end_time = datetime.now()

        console.print("\n[bold green]■ Recording stopped[/bold green]")
        console.print(f"[dim]Recorded {len(self.steps)} steps[/dim]")
        console.print(f"[dim]Captured {len(self.console_logs)} console logs[/dim]")
        console.print(f"[dim]Captured {len(self.network_requests)} network requests[/dim]")

        # Update UI
        if self._browser_manager and self._browser_manager._page:
            await update_panel_ui(
                self._browser_manager._page,
                is_recording=False,
                steps_count=len(self.steps),
                message="Saving...",
            )

        # Export test case
        await self._export_testcase()

        # Update UI with completion message
        if self._browser_manager and self._browser_manager._page:
            await update_panel_ui(
                self._browser_manager._page,
                is_recording=False,
                steps_count=len(self.steps),
                message="✓ Saved!",
            )

            # Wait a bit before closing
            await asyncio.sleep(2)

        # Signal completion
        self._recording_complete.set()

    # -------------------------------------------------------------------------
    # Action Handling
    # -------------------------------------------------------------------------

    async def on_action(self, data: dict[str, Any]) -> None:
        """
        Handle an action event from the browser.

        Called by the injected JavaScript when user performs an action.

        Args:
            data: Action data from JavaScript
        """
        if not self.is_recording:
            return

        event_type = data.get("eventType", "")

        # Map event types to action types
        action_map: dict[str, ActionType] = {
            "click": "click",
            "dblclick": "dblclick",
            "input": "input",
            "select": "select",
            "check": "check",
            "uncheck": "uncheck",
            "keypress": "keypress",
        }

        action_type = action_map.get(event_type)
        if not action_type:
            return

        # Parse element info
        element_data = parse_element_info(data)

        # Create ElementInfo
        try:
            element = ElementInfo(
                selector=element_data["selector"],
                xpath=element_data.get("xpath"),
                tag_name=element_data["tag_name"],
                text=element_data.get("text"),
                placeholder=element_data.get("placeholder"),
                attributes=element_data.get("attributes", {}),
                bounding_box=element_data.get(
                    "bounding_box", {"x": 0, "y": 0, "width": 0, "height": 0}
                ),
            )
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to parse element: {e}[/yellow]")
            return

        # Generate step number
        step_number = len(self.steps) + 1

        # Generate descriptions
        description_short = self._generate_short_description(action_type, element, data)
        description_detailed = self._generate_detailed_description(action_type, element, data)

        # Take screenshot
        screenshot_path: Path | None = None
        if self._browser_manager and self._browser_manager._page:
            try:
                filename = generate_screenshot_filename(
                    step_number,
                    action_type,
                    element.attributes.get("id") or element.tag_name,
                )
                full_path = self.screenshots_dir / filename
                await take_screenshot(
                    self._browser_manager._page,
                    full_path,
                    highlight_selector=element.selector,
                )
                screenshot_path = Path("screenshots") / filename
            except Exception as e:
                console.print(f"[yellow]Warning: Screenshot failed: {e}[/yellow]")

        # Collect console logs and network requests for this step
        step_logs = self._step_console_logs.copy()
        step_requests = self._step_network_requests.copy()
        self._step_console_logs.clear()
        self._step_network_requests.clear()

        # Create step
        step = Step(
            number=step_number,
            timestamp=datetime.now(),
            action_type=action_type,
            element=element,
            input_value=data.get("value"),
            key=data.get("key"),
            screenshot_path=screenshot_path,
            network_requests=step_requests,
            console_logs=step_logs,
            description_short=description_short,
            description_detailed=description_detailed,
        )

        self.steps.append(step)

        # Log the action
        console.print(f"  [dim]{step_number}.[/dim] {description_short}")

        # Update UI
        if self._browser_manager and self._browser_manager._page:
            await update_panel_ui(
                self._browser_manager._page,
                is_recording=True,
                steps_count=len(self.steps),
            )

    # -------------------------------------------------------------------------
    # Description Generation
    # -------------------------------------------------------------------------

    def _generate_short_description(
        self,
        action_type: ActionType,
        element: ElementInfo,
        data: dict[str, Any],
    ) -> str:
        """Generate a short description for the step."""
        tag = element.tag_name
        text = element.text[:30] if element.text else None
        el_id = element.attributes.get("id")
        placeholder = element.placeholder

        identifier = text or el_id or placeholder or tag

        if action_type == "click":
            return f"Click on '{identifier}'"
        elif action_type == "dblclick":
            return f"Double-click on '{identifier}'"
        elif action_type == "input":
            value = data.get("value", "")
            if len(value) > 20:
                return f"Type '{value[:20]}...' in {identifier}"
            return f"Type '{value}' in {identifier}"
        elif action_type == "select":
            selected = data.get("selectedText", data.get("value", ""))
            return f"Select '{selected}' in {identifier}"
        elif action_type == "check":
            return f"Check {identifier}"
        elif action_type == "uncheck":
            return f"Uncheck {identifier}"
        elif action_type == "keypress":
            key = data.get("key", "")
            return f"Press {key}"
        else:
            return f"{action_type} on {identifier}"

    def _generate_detailed_description(
        self,
        action_type: ActionType,
        element: ElementInfo,
        data: dict[str, Any],
    ) -> str:
        """Generate a detailed description for the step."""
        short = self._generate_short_description(action_type, element, data)
        selector = element.selector

        return f"{short}\nElement: {selector}"

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    async def _export_testcase(self) -> None:
        """Export the recorded test case to all formats."""
        if not self.steps:
            console.print("[yellow]No steps recorded. Nothing to export.[/yellow]")
            return

        # Calculate duration
        duration = 0.0
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()

        # Get user agent
        user_agent = "Unknown"
        if self._browser_manager:
            user_agent = self._browser_manager.browser_type

        # Create TestCase
        testcase = TestCase(
            id=f"tc_{uuid.uuid4().hex[:8]}",
            name=self.name,
            created_at=self.start_time or datetime.now(),
            start_url=self.start_url,
            browser=self.browser_type,
            viewport={"width": self.viewport[0], "height": self.viewport[1]},
            user_agent=user_agent,
            steps=self.steps,
            console_logs=self.console_logs,
            network_requests=self.network_requests,
            page_errors=self.page_errors,
            total_duration=duration,
            total_steps=len(self.steps),
        )

        # Export to all formats
        console.print("\n[bold]Exporting test case...[/bold]")

        # JSON
        json_exporter = JSONExporter()
        json_path = json_exporter.export(testcase, self.output_dir)
        console.print(f"  [green]✓[/green] JSON: {json_path}")

        # Markdown
        md_exporter = MarkdownExporter()
        md_path = md_exporter.export(testcase, self.output_dir)
        console.print(f"  [green]✓[/green] Markdown: {md_path}")

        # HTML
        html_exporter = HTMLExporter()
        html_path = html_exporter.export(testcase, self.output_dir)
        console.print(f"  [green]✓[/green] HTML: {html_path}")

        console.print(f"\n[bold green]✓ Test case saved to {self.output_dir}[/bold green]")
