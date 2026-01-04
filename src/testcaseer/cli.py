"""Command-line interface for TestCaseer."""

import asyncio
import re
import sys
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from testcaseer import __version__


# Browser choices enum for validation
class BrowserType(str, Enum):
    chromium = "chromium"
    firefox = "firefox"
    webkit = "webkit"


app = typer.Typer(
    name="testcaseer",
    help="Record browser actions and generate test cases for QA engineers.",
    add_completion=False,
    rich_markup_mode="rich",
)
console = Console()


def validate_url(url: str) -> str:
    """Validate and normalize URL."""
    # Add https:// if no scheme provided
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    
    # Basic URL validation
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    
    if not url_pattern.match(url):
        console.print(f"[red]✗ Invalid URL:[/red] {url}")
        console.print("  URL should be like: https://example.com or example.com")
        raise typer.Exit(1)
    
    return url


def validate_output_dir(output: Path) -> Path:
    """Validate output directory path."""
    # Check if parent directory exists or can be created
    try:
        output = output.resolve()
        
        # If path exists, check if it's a directory
        if output.exists():
            if not output.is_dir():
                console.print(f"[red]✗ Output path is not a directory:[/red] {output}")
                raise typer.Exit(1)
        else:
            # Try to create the directory
            output.mkdir(parents=True, exist_ok=True)
            console.print(f"[dim]Created output directory: {output}[/dim]")
        
        # Create screenshots subdirectory
        screenshots_dir = output / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        
        return output
    except PermissionError:
        console.print(f"[red]✗ Permission denied:[/red] Cannot create {output}")
        raise typer.Exit(1) from None
    except OSError as e:
        console.print(f"[red]✗ Invalid path:[/red] {e}")
        raise typer.Exit(1) from None


def print_banner() -> None:
    """Print TestCaseer banner."""
    banner = Panel(
        "[bold green]TestCaseer[/bold green] — Browser Action Recorder\n"
        f"[dim]Version {__version__}[/dim]",
        border_style="green",
        padding=(0, 2),
    )
    console.print(banner)


def print_session_info(
    url: str,
    output: Path,
    name: str,
    browser: str,
    headless: bool,
    timeout: int,
) -> None:
    """Print recording session information."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim")
    table.add_column("Value")
    
    table.add_row("URL", f"[blue]{url}[/blue]")
    table.add_row("Output", f"[yellow]{output}[/yellow]")
    table.add_row("Test Name", f"[cyan]{name}[/cyan]")
    table.add_row("Browser", browser)
    table.add_row("Headless", "Yes" if headless else "No")
    table.add_row("Timeout", f"{timeout}ms")
    
    console.print("\n[bold]Session Configuration:[/bold]")
    console.print(table)


def generate_testcase_name(url: str) -> str:
    """Generate a default test case name from URL."""
    from urllib.parse import urlparse
    
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    path = parsed.path.strip("/").replace("/", "_")
    
    if path:
        return f"{domain}_{path}"
    return domain


@app.command()
def record(
    url: Annotated[
        str,
        typer.Argument(
            help="URL to open in the browser (e.g., https://example.com)",
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output directory for test case files",
        ),
    ],
    name: Annotated[
        str | None,
        typer.Option(
            "--name",
            "-n",
            help="Test case name (auto-generated from URL if not provided)",
        ),
    ] = None,
    browser: Annotated[
        BrowserType,
        typer.Option(
            "--browser",
            "-b",
            help="Browser to use",
            case_sensitive=False,
        ),
    ] = BrowserType.chromium,
    headless: Annotated[
        bool,
        typer.Option(
            "--headless",
            help="Run browser in headless mode (no GUI)",
        ),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option(
            "--timeout",
            "-t",
            help="Action timeout in milliseconds",
            min=1000,
            max=300000,
        ),
    ] = 30000,
) -> None:
    """
    Record browser actions and generate a test case.

    Opens a browser window with a control panel. Use the panel buttons to:

    • [green]▶ Start[/green] — Begin recording actions
    • [red]⏹ Stop[/red] — Stop recording and save results

    Output files (JSON, Markdown, HTML) are saved to the specified directory.
    """
    # Print banner
    print_banner()
    
    # Validate URL
    url = validate_url(url)
    
    # Validate output directory
    output = validate_output_dir(output)
    
    # Generate name if not provided
    if name is None:
        name = generate_testcase_name(url)
    
    # Print session info
    print_session_info(url, output, name, browser.value, headless, timeout)
    
    # Check if playwright is installed
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        console.print("\n[red]✗ Playwright not installed![/red]")
        console.print("  Run: [cyan]playwright install chromium[/cyan]")
        raise typer.Exit(1) from None
    
    console.print("\n[bold green]Starting browser...[/bold green]")
    console.print("[dim]Use the control panel in the browser to start/stop recording.[/dim]")
    console.print("[dim]Press Ctrl+C to cancel.[/dim]\n")
    
    # Run the recorder
    try:
        asyncio.run(
            run_recorder(
                url=url,
                output_dir=output,
                name=name,
                browser_type=browser.value,
                headless=headless,
                timeout=timeout,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Recording cancelled by user.[/yellow]")
        raise typer.Exit(0) from None


async def run_recorder(
    url: str,
    output_dir: Path,
    name: str,
    browser_type: str,
    headless: bool,
    timeout: int,
) -> None:
    """
    Run the browser recorder.

    Args:
        url: URL to record
        output_dir: Directory to save output files
        name: Test case name
        browser_type: Browser to use
        headless: Run browser without GUI
        timeout: Action timeout in ms
    """
    from testcaseer.recorder import Recorder

    recorder = Recorder(
        output_dir=output_dir,
        start_url=url,
        name=name,
        browser_type=browser_type,
        headless=headless,
        viewport=(1280, 720),
        timeout=timeout,
    )

    await recorder.run()


@app.command()
def version() -> None:
    """Show version and system information."""
    print_banner()
    
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Component", style="dim")
    table.add_column("Version")
    
    table.add_row("TestCaseer", __version__)
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    table.add_row("Python", py_ver)
    
    # Check playwright
    try:
        from playwright._repo_version import version as pw_version
        table.add_row("Playwright", pw_version)
    except ImportError:
        table.add_row("Playwright", "[red]Not installed[/red]")
    
    # Check pydantic
    try:
        import pydantic
        table.add_row("Pydantic", pydantic.__version__)
    except ImportError:
        table.add_row("Pydantic", "[red]Not installed[/red]")
    
    console.print("\n[bold]System Information:[/bold]")
    console.print(table)


@app.command()
def check() -> None:
    """Check if all dependencies are properly installed."""
    print_banner()
    console.print("\n[bold]Checking dependencies...[/bold]\n")
    
    all_ok = True
    
    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    console.print(f"[green]✓[/green] Python {py_version}")
    
    # Check required packages
    packages = [
        ("playwright", "playwright"),
        ("pydantic", "pydantic"),
        ("typer", "typer"),
        ("rich", "rich"),
        ("jinja2", "jinja2"),
        ("PIL", "pillow"),
    ]
    
    for import_name, package_name in packages:
        try:
            __import__(import_name)
            console.print(f"[green]✓[/green] {package_name}")
        except ImportError:
            console.print(f"[red]✗[/red] {package_name} — [dim]pip install {package_name}[/dim]")
            all_ok = False
    
    # Check playwright browsers
    console.print("\n[bold]Checking browsers...[/bold]\n")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            for browser_name in ["chromium", "firefox", "webkit"]:
                try:
                    browser_launcher = getattr(p, browser_name)
                    browser = browser_launcher.launch(headless=True)
                    browser.close()
                    console.print(f"[green]✓[/green] {browser_name}")
                except Exception:
                    install_cmd = f"playwright install {browser_name}"
                    console.print(f"[yellow]○[/yellow] {browser_name} — [dim]{install_cmd}[/dim]")
    except Exception as e:
        console.print(f"[red]✗[/red] Could not check browsers: {e}")
        console.print("[dim]Run: playwright install[/dim]")
        all_ok = False
    
    # Summary
    console.print()
    if all_ok:
        console.print("[bold green]✓ All checks passed![/bold green]")
    else:
        console.print("[bold yellow]⚠ Some checks failed. See above for details.[/bold yellow]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
