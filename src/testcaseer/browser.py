"""Browser management for TestCaseer."""

from typing import Literal

from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright

BrowserType = Literal["chromium", "firefox", "webkit"]


class BrowserManager:
    """
    Manages Playwright browser lifecycle.

    Handles browser launch, page creation, and cleanup.
    """

    def __init__(
        self,
        browser_type: BrowserType = "chromium",
        headless: bool = False,
        viewport: tuple[int, int] = (1280, 720),
        timeout: int = 30000,
    ) -> None:
        """
        Initialize browser manager.

        Args:
            browser_type: Browser to use (chromium, firefox, webkit)
            headless: Run browser without GUI
            viewport: Browser window size (width, height)
            timeout: Default timeout for operations in ms
        """
        self.browser_type = browser_type
        self.headless = headless
        self.viewport = {"width": viewport[0], "height": viewport[1]}
        self.timeout = timeout

        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        """Get the current page."""
        if self._page is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._page

    @property
    def browser(self) -> Browser:
        """Get the browser instance."""
        if self._browser is None:
            raise RuntimeError("Browser not started. Call start() first.")
        return self._browser

    async def start(self) -> Page:
        """
        Start browser and create a new page.

        Returns:
            The created Page object
        """
        self._playwright = await async_playwright().start()

        # Get browser launcher based on type
        launcher = getattr(self._playwright, self.browser_type)

        # Launch browser
        self._browser = await launcher.launch(
            headless=self.headless,
        )

        # Create context with viewport
        self._context = await self._browser.new_context(
            viewport=self.viewport,
        )

        # Set default timeout
        self._context.set_default_timeout(self.timeout)

        # Create page
        self._page = await self._context.new_page()

        return self._page

    async def navigate(self, url: str) -> None:
        """
        Navigate to a URL.

        Args:
            url: URL to navigate to
        """
        await self.page.goto(url, wait_until="domcontentloaded")

    async def close(self) -> None:
        """Close browser and cleanup resources."""
        if self._page:
            await self._page.close()
            self._page = None

        if self._context:
            await self._context.close()
            self._context = None

        if self._browser:
            await self._browser.close()
            self._browser = None

        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    def get_user_agent(self) -> str:
        """Get the browser's user agent string."""
        if self._page is None:
            return ""
        # This will be populated after page is created
        return self._page.context.browser.browser_type.name

    async def __aenter__(self) -> "BrowserManager":
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:  # type: ignore[no-untyped-def]
        """Async context manager exit."""
        await self.close()
