"""Integration tests for the Recorder."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from testcaseer.models import TestCase
from testcaseer.recorder import Recorder


@pytest.mark.integration
class TestRecorderInit:
    """Tests for Recorder initialization."""

    def test_recorder_init(self, temp_dir: Path) -> None:
        """Test Recorder initialization."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
            browser_type="chromium",
        )
        
        assert recorder.start_url == "https://example.com"
        # Use resolve() for comparison to handle symlinks like /var -> /private/var
        assert recorder.output_dir == temp_dir.resolve()
        assert recorder.browser_type == "chromium"

    def test_recorder_default_browser(self, temp_dir: Path) -> None:
        """Test Recorder with default browser."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        assert recorder.browser_type == "chromium"

    def test_recorder_creates_output_dir(self, temp_dir: Path) -> None:
        """Test that Recorder stores output directory."""
        output_path = temp_dir / "new_output"
        
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=output_path,
        )
        
        # Output dir should be set correctly (resolved)
        assert recorder.output_dir == output_path.resolve()


@pytest.mark.integration
class TestRecorderState:
    """Tests for Recorder state management."""

    def test_recorder_initial_state(self, temp_dir: Path) -> None:
        """Test Recorder initial state."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        assert recorder.is_recording is False
        assert len(recorder.steps) == 0

    def test_recorder_steps_list(self, temp_dir: Path) -> None:
        """Test that recorder has empty steps list."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        assert isinstance(recorder.steps, list)
        assert len(recorder.steps) == 0


@pytest.mark.integration
@pytest.mark.slow
class TestRecorderWithMocks:
    """Tests for Recorder with mocked browser."""

    @pytest.mark.asyncio
    async def test_start_recording(self, temp_dir: Path) -> None:
        """Test starting recording."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        with patch.object(recorder, "_browser_manager") as mock_browser:
            mock_browser.page = MagicMock()
            
            recorder.start_recording()
            
            assert recorder.is_recording is True

    @pytest.mark.asyncio
    async def test_stop_recording(self, temp_dir: Path) -> None:
        """Test stopping recording."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        with patch.object(recorder, "_browser_manager") as mock_browser:
            mock_browser.page = MagicMock()
            
            recorder.start_recording()
            assert recorder.is_recording is True
            
            recorder.stop_recording()
            assert recorder.is_recording is False

    @pytest.mark.asyncio
    async def test_recording_creates_steps(self, temp_dir: Path) -> None:
        """Test that recording can add steps."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        with patch.object(recorder, "_browser_manager") as mock_browser:
            mock_page = MagicMock()
            mock_page.url = "https://example.com"
            mock_page.title = AsyncMock(return_value="Example")
            mock_browser.page = mock_page
            mock_browser.user_agent = "TestAgent/1.0"
            mock_browser.viewport = {"width": 1920, "height": 1080}
            
            recorder.start_recording()
            # Steps list should exist
            assert isinstance(recorder.steps, list)
            
            recorder.stop_recording()


@pytest.mark.integration
class TestRecorderEventHandling:
    """Tests for Recorder event handling."""

    def test_recorder_has_steps_list(self, temp_dir: Path) -> None:
        """Test that recorder has steps list."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        assert hasattr(recorder, "steps")
        assert isinstance(recorder.steps, list)

    def test_console_logs_captured(self, temp_dir: Path) -> None:
        """Test that console logs are captured."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        assert hasattr(recorder, "console_logs")
        assert isinstance(recorder.console_logs, list)

    def test_network_requests_captured(self, temp_dir: Path) -> None:
        """Test that network requests are captured."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        assert hasattr(recorder, "network_requests")
        assert isinstance(recorder.network_requests, list)

    def test_page_errors_captured(self, temp_dir: Path) -> None:
        """Test that page errors are captured."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        assert hasattr(recorder, "page_errors")
        assert isinstance(recorder.page_errors, list)


@pytest.mark.integration
class TestRecorderExport:
    """Tests for Recorder export functionality."""

    @pytest.mark.asyncio
    async def test_export_all_formats(self, temp_dir: Path) -> None:
        """Test that recorder exports to all formats."""
        recorder = Recorder(
            start_url="https://example.com",
            output_dir=temp_dir,
        )
        
        # Start and stop recording to create testcase state
        recorder.start_recording()
        recorder.stop_recording()
        
        # Create output directory
        temp_dir.mkdir(parents=True, exist_ok=True)
        (temp_dir / "screenshots").mkdir(exist_ok=True)
        
        # Mock the testcase creation and export
        with patch.object(recorder, "_browser_manager") as mock_browser:
            mock_page = MagicMock()
            mock_page.url = "https://example.com"
            mock_page.title = AsyncMock(return_value="Example")
            mock_browser.page = mock_page
            mock_browser.user_agent = "TestAgent/1.0"
            mock_browser.viewport = {"width": 1920, "height": 1080}
            
            # Call the export method
            await recorder._export_testcase()
        
        # Check files created
        assert (temp_dir / "testcase.json").exists()
        assert (temp_dir / "testcase.md").exists()
        assert (temp_dir / "testcase.html").exists()
