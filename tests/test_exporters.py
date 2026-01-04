"""Tests for exporters."""

import json
from pathlib import Path

import pytest

from testcaseer.exporters import HTMLExporter, JSONExporter, MarkdownExporter
from testcaseer.models import TestCase


class TestJSONExporter:
    """Tests for JSON exporter."""

    def test_export_creates_file(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that export creates a JSON file."""
        exporter = JSONExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        assert output_path.exists()
        assert output_path.name == "testcase.json"

    def test_export_valid_json(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported file is valid JSON."""
        exporter = JSONExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        data = json.loads(content)
        
        assert isinstance(data, dict)
        assert data["id"] == "tc_001"
        assert data["name"] == "Тест авторизации"

    def test_export_contains_all_fields(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported JSON contains all required fields."""
        exporter = JSONExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        data = json.loads(content)
        
        required_fields = [
            "id", "name", "created_at", "start_url", "browser",
            "viewport", "user_agent", "steps", "console_logs",
            "network_requests", "page_errors", "total_duration", "total_steps"
        ]
        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_export_steps_structure(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that steps are properly structured in JSON."""
        exporter = JSONExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        data = json.loads(content)
        
        assert len(data["steps"]) == 2
        step = data["steps"][0]
        assert "number" in step
        assert "action_type" in step
        assert "description_short" in step
        assert "element" in step

    def test_export_minimal_testcase(self, sample_testcase_minimal: TestCase, temp_dir: Path) -> None:
        """Test exporting minimal TestCase."""
        exporter = JSONExporter()
        output_path = exporter.export(sample_testcase_minimal, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        data = json.loads(content)
        
        assert data["id"] == "tc_minimal"
        assert data["steps"] == []
        assert data["total_steps"] == 0


class TestMarkdownExporter:
    """Tests for Markdown exporter."""

    def test_export_creates_file(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that export creates a Markdown file."""
        exporter = MarkdownExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        assert output_path.exists()
        assert output_path.name == "testcase.md"

    def test_export_contains_title(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported Markdown contains title."""
        exporter = MarkdownExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "# Тест-кейс: Тест авторизации" in content

    def test_export_contains_metadata(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported Markdown contains metadata."""
        exporter = MarkdownExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "**ID:**" in content
        assert "tc_001" in content
        assert "**Браузер:**" in content
        assert "chromium" in content

    def test_export_contains_steps(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported Markdown contains steps."""
        exporter = MarkdownExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "## Шаги" in content
        assert "### Шаг 1:" in content
        assert "### Шаг 2:" in content

    def test_export_contains_summary(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported Markdown contains summary."""
        exporter = MarkdownExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "## Итоги" in content or "Итоги" in content

    def test_export_minimal_testcase(self, sample_testcase_minimal: TestCase, temp_dir: Path) -> None:
        """Test exporting minimal TestCase."""
        exporter = MarkdownExporter()
        output_path = exporter.export(sample_testcase_minimal, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "Minimal Test" in content


class TestHTMLExporter:
    """Tests for HTML exporter."""

    def test_export_creates_file(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that export creates an HTML file."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        assert output_path.exists()
        assert output_path.name == "testcase.html"

    def test_export_valid_html(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported file is valid HTML."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert content.startswith("<!DOCTYPE html>")
        assert "</html>" in content

    def test_export_contains_title(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported HTML contains title."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "<title>Тест авторизации — TestCaseer</title>" in content

    def test_export_contains_metadata(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported HTML contains metadata."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "tc_001" in content
        assert "chromium" in content
        assert "1920" in content  # viewport width

    def test_export_contains_steps(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported HTML contains steps."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "Шаги" in content or "step" in content.lower()

    def test_export_contains_styles(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported HTML contains CSS styles."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "<style>" in content
        assert "</style>" in content

    def test_export_contains_tabs(self, sample_testcase: TestCase, temp_dir: Path) -> None:
        """Test that exported HTML contains tabs for navigation."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "tab" in content.lower()

    def test_export_minimal_testcase(self, sample_testcase_minimal: TestCase, temp_dir: Path) -> None:
        """Test exporting minimal TestCase."""
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase_minimal, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        assert "Minimal Test" in content

    def test_embed_screenshots(self, sample_testcase: TestCase, temp_dir: Path, sample_screenshot_bytes: bytes) -> None:
        """Test that screenshots are embedded as base64."""
        # Create screenshots directory and file
        screenshots_dir = temp_dir / "screenshots"
        screenshots_dir.mkdir()
        screenshot_path = screenshots_dir / "001_click_button.png"
        screenshot_path.write_bytes(sample_screenshot_bytes)
        
        exporter = HTMLExporter()
        output_path = exporter.export(sample_testcase, temp_dir)
        
        content = output_path.read_text(encoding="utf-8")
        # Check for base64 image data
        assert "data:image/png;base64," in content

