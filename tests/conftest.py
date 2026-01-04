"""Pytest configuration and fixtures for TestCaseer tests."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest

from testcaseer.models import (
    ConsoleLog,
    ElementInfo,
    NetworkRequest,
    PageError,
    Step,
    TestCase,
)


# -----------------------------------------------------------------------------
# Pytest markers configuration
# -----------------------------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")


# -----------------------------------------------------------------------------
# Path fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def screenshots_dir(temp_dir: Path) -> Path:
    """Create screenshots subdirectory."""
    screenshots = temp_dir / "screenshots"
    screenshots.mkdir()
    return screenshots


# -----------------------------------------------------------------------------
# Model fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_element_info() -> ElementInfo:
    """Create a sample ElementInfo object."""
    return ElementInfo(
        selector="button#submit",
        xpath="//button[@id='submit']",
        tag_name="button",
        text="Submit",
        placeholder=None,
        attributes={"id": "submit", "class": "btn btn-primary", "type": "submit"},
        bounding_box={"x": 100, "y": 200, "width": 120, "height": 40},
    )


@pytest.fixture
def sample_network_request() -> NetworkRequest:
    """Create a sample NetworkRequest object."""
    return NetworkRequest(
        method="POST",
        url="https://api.example.com/login",
        status=200,
        resource_type="xhr",
        timing=150.5,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        request_headers={"Content-Type": "application/json", "Authorization": "Bearer token123"},
        response_headers={"Content-Type": "application/json", "X-Request-Id": "abc123"},
        request_body='{"username": "test", "password": "***"}',
        response_body='{"success": true, "token": "jwt..."}',
        error=None,
    )


@pytest.fixture
def sample_console_log() -> ConsoleLog:
    """Create a sample ConsoleLog object."""
    return ConsoleLog(
        level="info",
        message="Application initialized successfully",
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        source="https://example.com/app.js:42",
        args=["App version:", "1.0.0"],
    )


@pytest.fixture
def sample_page_error() -> PageError:
    """Create a sample PageError object."""
    return PageError(
        message="TypeError: Cannot read property 'foo' of undefined",
        stack="TypeError: Cannot read property 'foo' of undefined\n    at bar (app.js:10)\n    at foo (app.js:5)",
        timestamp=datetime(2025, 1, 1, 12, 0, 5),
    )


@pytest.fixture
def sample_step(sample_element_info: ElementInfo) -> Step:
    """Create a sample Step object."""
    return Step(
        number=1,
        timestamp=datetime(2025, 1, 1, 12, 0, 0),
        action_type="click",
        element=sample_element_info,
        url=None,
        input_value=None,
        key=None,
        screenshot_path=Path("screenshots/001_click_button.png"),
        screenshot_with_highlight=None,
        network_requests=[],
        console_logs=[],
        description_short="Клик по кнопке Submit",
        description_detailed="Пользователь кликнул по кнопке Submit для отправки формы.",
    )


@pytest.fixture
def sample_step_with_input(sample_element_info: ElementInfo) -> Step:
    """Create a sample Step with input action."""
    element = ElementInfo(
        selector="input#email",
        xpath="//input[@id='email']",
        tag_name="input",
        text=None,
        placeholder="Enter your email",
        attributes={"id": "email", "type": "email", "name": "email"},
        bounding_box={"x": 100, "y": 100, "width": 300, "height": 40},
    )
    return Step(
        number=2,
        timestamp=datetime(2025, 1, 1, 12, 0, 5),
        action_type="input",
        element=element,
        url=None,
        input_value="user@example.com",
        key=None,
        screenshot_path=Path("screenshots/002_input_email.png"),
        screenshot_with_highlight=None,
        network_requests=[],
        console_logs=[],
        description_short="Ввод email",
        description_detailed="Пользователь ввёл 'user@example.com' в поле email.",
    )


@pytest.fixture
def sample_testcase(
    sample_step: Step,
    sample_step_with_input: Step,
    sample_console_log: ConsoleLog,
    sample_network_request: NetworkRequest,
    sample_page_error: PageError,
) -> TestCase:
    """Create a sample TestCase object."""
    return TestCase(
        id="tc_001",
        name="Тест авторизации",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        start_url="https://example.com/login",
        browser="chromium",
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        steps=[sample_step, sample_step_with_input],
        console_logs=[sample_console_log],
        network_requests=[sample_network_request],
        page_errors=[sample_page_error],
        total_duration=10.5,
        total_steps=2,
    )


@pytest.fixture
def sample_testcase_minimal() -> TestCase:
    """Create a minimal TestCase for basic tests."""
    return TestCase(
        id="tc_minimal",
        name="Minimal Test",
        created_at=datetime(2025, 1, 1, 12, 0, 0),
        start_url="https://example.com",
        browser="chromium",
        viewport={"width": 1280, "height": 720},
        user_agent="TestAgent/1.0",
        steps=[],
        console_logs=[],
        network_requests=[],
        page_errors=[],
        total_duration=0.0,
        total_steps=0,
    )


# -----------------------------------------------------------------------------
# Screenshot fixtures
# -----------------------------------------------------------------------------


@pytest.fixture
def sample_screenshot_bytes() -> bytes:
    """Create minimal valid PNG bytes for testing."""
    # Minimal 1x1 red PNG image
    return bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # 1x1 pixels
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,  # RGB, etc
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,  # Compressed data
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
        0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ])


@pytest.fixture
def sample_screenshot_file(temp_dir: Path, sample_screenshot_bytes: bytes) -> Path:
    """Create a sample screenshot file."""
    screenshot_path = temp_dir / "test_screenshot.png"
    screenshot_path.write_bytes(sample_screenshot_bytes)
    return screenshot_path

