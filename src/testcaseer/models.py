"""Pydantic models for TestCaseer data structures."""

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ElementInfo(BaseModel):
    """Information about a DOM element."""

    selector: str = Field(description="CSS selector of the element")
    xpath: str | None = Field(default=None, description="XPath selector")
    tag_name: str = Field(description="HTML tag name (button, input, a, etc)")
    text: str | None = Field(default=None, description="Text content of the element")
    placeholder: str | None = Field(default=None, description="Placeholder for input elements")
    attributes: dict[str, str] = Field(default_factory=dict, description="HTML attributes")
    bounding_box: dict[str, float] = Field(description="Coordinates: x, y, width, height")


class NetworkRequest(BaseModel):
    """Network request information."""

    method: str = Field(description="HTTP method (GET, POST, etc)")
    url: str = Field(description="Request URL")
    status: int | None = Field(default=None, description="HTTP response status code")
    resource_type: str = Field(description="Resource type: document, xhr, fetch, etc")
    timing: float | None = Field(default=None, description="Request duration in ms")
    timestamp: datetime = Field(default_factory=datetime.now, description="Request time")
    request_headers: dict[str, str] = Field(default_factory=dict, description="Req headers")
    response_headers: dict[str, str] = Field(default_factory=dict, description="Response headers")
    request_body: str | None = Field(default=None, description="Request body (for POST/PUT)")
    response_body: str | None = Field(default=None, description="Response body preview")
    error: str | None = Field(default=None, description="Error message if request failed")


ConsoleLogLevel = Literal["log", "info", "warn", "error", "debug", "trace"]


class ConsoleLog(BaseModel):
    """Browser console log entry."""

    level: ConsoleLogLevel = Field(description="Log level (log, info, warn, error, debug)")
    message: str = Field(description="Log message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Log time")
    source: str | None = Field(default=None, description="Source file and line")
    args: list[str] = Field(default_factory=list, description="Additional arguments")


class PageError(BaseModel):
    """JavaScript error on the page."""

    message: str = Field(description="Error message")
    stack: str | None = Field(default=None, description="Stack trace")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred")


ActionType = Literal[
    "click",
    "dblclick",
    "input",
    "select",
    "check",
    "uncheck",
    "navigate",
    "scroll",
    "hover",
    "keypress",
    "wait",
]


class Step(BaseModel):
    """Single step in a test case."""

    number: int = Field(description="Step number (1-based)")
    timestamp: datetime = Field(description="Timestamp when the action was performed")
    action_type: ActionType = Field(description="Type of action performed")

    # Target information
    element: ElementInfo | None = Field(default=None, description="Target DOM element")
    url: str | None = Field(default=None, description="URL for navigation actions")

    # Action data
    input_value: str | None = Field(default=None, description="Input value for input actions")
    key: str | None = Field(default=None, description="Key pressed for keypress actions")

    # Screenshots
    screenshot_path: Path | None = Field(default=None, description="Path to screenshot file")
    screenshot_with_highlight: Path | None = Field(
        default=None, description="Path to screenshot with highlighted element"
    )

    # Network requests triggered by this action
    network_requests: list[NetworkRequest] = Field(default_factory=list)

    # Console logs captured during this step
    console_logs: list[ConsoleLog] = Field(default_factory=list)

    # Descriptions
    description_short: str = Field(description="Short description for step list")
    description_detailed: str = Field(description="Detailed step description")


class TestCase(BaseModel):
    """Complete test case with all steps and metadata."""

    # Metadata
    id: str = Field(description="Unique test case ID")
    name: str = Field(description="Test case name")
    created_at: datetime = Field(description="Creation timestamp")

    # Environment
    start_url: str = Field(description="Starting URL")
    browser: str = Field(description="Browser used for recording")
    viewport: dict[str, int] = Field(description="Viewport size: width, height")
    user_agent: str = Field(description="User agent string")

    # Steps
    steps: list[Step] = Field(default_factory=list, description="List of recorded steps")

    # All logs and requests (full timeline)
    console_logs: list[ConsoleLog] = Field(default_factory=list, description="Console logs")
    network_requests: list[NetworkRequest] = Field(default_factory=list, description="Network")
    page_errors: list[PageError] = Field(default_factory=list, description="JS errors")

    # Summary
    total_duration: float = Field(description="Total recording duration in seconds")
    total_steps: int = Field(description="Total number of steps")
