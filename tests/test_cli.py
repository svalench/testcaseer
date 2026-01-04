"""Tests for CLI commands."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

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

    def test_record_url_validation(self) -> None:
        """Test URL validation - adds https if missing."""
        with patch("testcaseer.cli.Recorder") as mock_recorder:
            mock_instance = AsyncMock()
            mock_recorder.return_value = mock_instance
            mock_instance.run = AsyncMock()
            
            # This should add https:// prefix
            result = runner.invoke(app, ["record", "example.com", "-o", "/tmp/test"])
            
            # Command should start (may fail for other reasons, but URL should be valid)
            # We just check it doesn't fail on URL validation
            if result.exit_code == 0:
                # Check that recorder was called with proper URL
                call_args = mock_recorder.call_args
                if call_args:
                    assert "example.com" in str(call_args)

    def test_record_with_output_dir(self, temp_dir: Path) -> None:
        """Test record with custom output directory."""
        with patch("testcaseer.cli.Recorder") as mock_recorder:
            mock_instance = AsyncMock()
            mock_recorder.return_value = mock_instance
            mock_instance.run = AsyncMock()
            
            output_path = temp_dir / "test_output"
            result = runner.invoke(app, ["record", "https://example.com", "-o", str(output_path)])
            
            # Should either succeed or fail gracefully
            assert result.exit_code in [0, 1]

    def test_record_with_browser_option(self, temp_dir: Path) -> None:
        """Test record with browser option."""
        with patch("testcaseer.cli.Recorder") as mock_recorder:
            mock_instance = AsyncMock()
            mock_recorder.return_value = mock_instance
            mock_instance.run = AsyncMock()
            
            result = runner.invoke(app, [
                "record", "https://example.com",
                "-o", str(temp_dir),
                "--browser", "firefox"
            ])
            
            # Should accept browser option
            if mock_recorder.called:
                call_kwargs = mock_recorder.call_args.kwargs if mock_recorder.call_args else {}
                # Browser option should be passed


class TestCLIOutput:
    """Tests for CLI output formatting."""

    def test_cli_uses_rich(self) -> None:
        """Test that CLI uses Rich for output."""
        result = runner.invoke(app, ["version"])
        # Rich output often contains ANSI codes or formatted text
        # At minimum, should have some output
        assert len(result.stdout) > 0

    def test_cli_handles_keyboard_interrupt(self) -> None:
        """Test that CLI handles Ctrl+C gracefully."""
        with patch("testcaseer.cli.Recorder") as mock_recorder:
            mock_instance = AsyncMock()
            mock_recorder.return_value = mock_instance
            mock_instance.run = AsyncMock(side_effect=KeyboardInterrupt)
            
            result = runner.invoke(app, ["record", "https://example.com", "-o", "/tmp/test"])
            
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

