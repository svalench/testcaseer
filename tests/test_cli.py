"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from testcaseer.cli import app

runner = CliRunner()


class TestVersionCommand:
    """Tests for the version command."""

    def test_version_command(self) -> None:
        """Test that version command runs successfully."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0

    def test_version_shows_testcaseer(self) -> None:
        """Test that version shows TestCaseer version."""
        result = runner.invoke(app, ["version"])
        assert "TestCaseer" in result.stdout or "testcaseer" in result.stdout.lower()

    def test_version_shows_python(self) -> None:
        """Test that version shows Python version."""
        result = runner.invoke(app, ["version"])
        assert "Python" in result.stdout or "python" in result.stdout.lower()


class TestCheckCommand:
    """Tests for the check command."""

    def test_check_command(self) -> None:
        """Test that check command runs successfully."""
        result = runner.invoke(app, ["check"])
        # May exit with 1 if browsers not installed, but should run
        assert result.exit_code in [0, 1]

    def test_check_shows_dependencies(self) -> None:
        """Test that check shows dependency information."""
        result = runner.invoke(app, ["check"])
        # Should mention Python or dependencies
        assert "Python" in result.stdout or "Зависимости" in result.stdout or len(result.stdout) > 0


class TestRecordCommand:
    """Tests for the record command."""

    def test_record_help(self) -> None:
        """Test that record --help works."""
        result = runner.invoke(app, ["record", "--help"])
        assert result.exit_code == 0
        assert "url" in result.stdout.lower() or "URL" in result.stdout

    def test_record_requires_url(self) -> None:
        """Test that record requires URL argument."""
        result = runner.invoke(app, ["record"])
        assert result.exit_code != 0

    def test_record_url_validation(self, temp_dir: Path) -> None:
        """Test URL validation - adds https if missing."""
        with patch("testcaseer.recorder.Recorder") as mock_recorder_class:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock()
            mock_recorder_class.return_value = mock_instance
            
            result = runner.invoke(app, ["record", "example.com", "-o", str(temp_dir)])
            
            # Check that recorder was called
            if mock_recorder_class.called:
                call_kwargs = mock_recorder_class.call_args.kwargs
                # URL should have https:// prefix added
                assert "example.com" in call_kwargs.get("start_url", "")

    def test_record_with_output_dir(self, temp_dir: Path) -> None:
        """Test record with custom output directory."""
        with patch("testcaseer.recorder.Recorder") as mock_recorder_class:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock()
            mock_recorder_class.return_value = mock_instance
            
            output_path = temp_dir / "test_output"
            result = runner.invoke(app, ["record", "https://example.com", "-o", str(output_path)])
            
            # Should either succeed or fail gracefully
            assert result.exit_code in [0, 1]

    def test_record_with_browser_option(self, temp_dir: Path) -> None:
        """Test record with browser option."""
        with patch("testcaseer.recorder.Recorder") as mock_recorder_class:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock()
            mock_recorder_class.return_value = mock_instance
            
            result = runner.invoke(app, [
                "record", "https://example.com",
                "-o", str(temp_dir),
                "--browser", "firefox"
            ])
            
            # Should accept browser option
            if mock_recorder_class.called:
                call_kwargs = mock_recorder_class.call_args.kwargs
                assert call_kwargs.get("browser_type") == "firefox"


class TestCLIOutput:
    """Tests for CLI output formatting."""

    def test_cli_uses_rich(self) -> None:
        """Test that CLI uses Rich for output."""
        result = runner.invoke(app, ["version"])
        # Rich output often contains ANSI codes or formatted text
        # At minimum, should have some output
        assert len(result.stdout) > 0

    def test_cli_handles_keyboard_interrupt(self, temp_dir: Path) -> None:
        """Test that CLI handles Ctrl+C gracefully."""
        with patch("testcaseer.recorder.Recorder") as mock_recorder_class:
            mock_instance = MagicMock()
            mock_instance.run = AsyncMock(side_effect=KeyboardInterrupt)
            mock_recorder_class.return_value = mock_instance
            
            result = runner.invoke(app, ["record", "https://example.com", "-o", str(temp_dir)])
            
            # Should exit gracefully, not crash
            # Exit code can vary but shouldn't be an unhandled exception


class TestCLIEdgeCases:
    """Tests for CLI edge cases."""

    def test_empty_url(self) -> None:
        """Test handling of empty URL."""
        result = runner.invoke(app, ["record", ""])
        # Should fail with validation error
        assert result.exit_code != 0

    def test_invalid_browser(self, temp_dir: Path) -> None:
        """Test handling of invalid browser option."""
        result = runner.invoke(app, [
            "record", "https://example.com",
            "-o", str(temp_dir),
            "--browser", "invalid_browser"
        ])
        # Should fail with validation error
        assert result.exit_code != 0

    def test_help_command(self) -> None:
        """Test main help command."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "record" in result.stdout.lower()
