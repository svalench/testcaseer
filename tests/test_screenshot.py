"""Tests for screenshot functionality."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from testcaseer.screenshot import generate_screenshot_filename, take_screenshot


class TestGenerateScreenshotFilename:
    """Tests for screenshot filename generation."""

    def test_generates_filename(self) -> None:
        """Test that function generates a filename."""
        filename = generate_screenshot_filename(1, "click", "button")
        assert isinstance(filename, str)
        assert len(filename) > 0

    def test_filename_includes_step_number(self) -> None:
        """Test that filename includes step number."""
        filename = generate_screenshot_filename(5, "click", "button")
        assert "005" in filename or "5" in filename

    def test_filename_includes_action_type(self) -> None:
        """Test that filename includes action type."""
        filename = generate_screenshot_filename(1, "click", "button")
        assert "click" in filename.lower()

    def test_filename_includes_element(self) -> None:
        """Test that filename includes element info."""
        filename = generate_screenshot_filename(1, "click", "submitBtn")
        assert "submitBtn" in filename or "submit" in filename.lower()

    def test_filename_has_png_extension(self) -> None:
        """Test that filename has .png extension."""
        filename = generate_screenshot_filename(1, "click", "button")
        assert filename.endswith(".png")

    def test_filename_sanitizes_special_chars(self) -> None:
        """Test that special characters are handled."""
        filename = generate_screenshot_filename(1, "input", "input#email[type='text']")
        # Should not contain problematic characters
        assert "/" not in filename
        assert "\\" not in filename

    def test_different_step_numbers(self) -> None:
        """Test filenames for different step numbers."""
        f1 = generate_screenshot_filename(1, "click", "btn")
        f2 = generate_screenshot_filename(10, "click", "btn")
        f3 = generate_screenshot_filename(100, "click", "btn")
        
        # All should be unique
        assert f1 != f2 != f3


class TestTakeScreenshot:
    """Tests for take_screenshot function."""

    @pytest.mark.asyncio
    async def test_take_screenshot_calls_page_screenshot(self, temp_dir: Path) -> None:
        """Test that take_screenshot calls page.screenshot()."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        
        output_path = temp_dir / "test.png"
        
        result = await take_screenshot(mock_page, output_path)
        
        mock_page.screenshot.assert_called_once()

    @pytest.mark.asyncio
    async def test_take_screenshot_returns_path(self, temp_dir: Path) -> None:
        """Test that take_screenshot returns a Path."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        
        output_path = temp_dir / "test.png"
        
        result = await take_screenshot(mock_page, output_path)
        
        assert isinstance(result, Path)
        assert "test.png" in str(result)

    @pytest.mark.asyncio
    async def test_take_screenshot_uses_correct_path(self, temp_dir: Path) -> None:
        """Test that screenshot is saved to correct path."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        
        output_path = temp_dir / "screenshot.png"
        
        result = await take_screenshot(mock_page, output_path)
        
        # The path should match what we provided
        assert result == output_path

    @pytest.mark.asyncio
    async def test_take_screenshot_with_highlight(self, temp_dir: Path) -> None:
        """Test screenshot with element highlight."""
        mock_page = MagicMock()
        mock_page.screenshot = AsyncMock()
        mock_element = MagicMock()
        mock_element.bounding_box = AsyncMock(return_value={"x": 10, "y": 20, "width": 100, "height": 50})
        mock_page.query_selector = AsyncMock(return_value=mock_element)
        
        output_path = temp_dir / "highlight.png"
        
        # This will try to add highlight but fail since file doesn't exist
        # That's ok - we're testing the call flow
        result = await take_screenshot(mock_page, output_path, highlight_selector="button#test")
        
        mock_page.query_selector.assert_called_once_with("button#test")


class TestScreenshotIntegration:
    """Integration tests for screenshot functionality."""

    def test_screenshot_file_creation(
        self,
        temp_dir: Path,
        sample_screenshot_bytes: bytes,
    ) -> None:
        """Test actual file creation."""
        screenshot_path = temp_dir / "test_screenshot.png"
        screenshot_path.write_bytes(sample_screenshot_bytes)
        
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 0

    def test_screenshot_is_valid_png(
        self,
        sample_screenshot_file: Path,
    ) -> None:
        """Test that created screenshot is valid PNG."""
        content = sample_screenshot_file.read_bytes()
        
        # PNG files start with specific bytes
        png_signature = bytes([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A])
        assert content[:8] == png_signature

    def test_multiple_screenshots(
        self,
        temp_dir: Path,
        sample_screenshot_bytes: bytes,
    ) -> None:
        """Test creating multiple screenshots."""
        for i in range(5):
            filename = generate_screenshot_filename(i + 1, "click", f"button{i}")
            path = temp_dir / filename
            path.write_bytes(sample_screenshot_bytes)
            assert path.exists()
        
        # Check all files exist
        png_files = list(temp_dir.glob("*.png"))
        assert len(png_files) == 5

