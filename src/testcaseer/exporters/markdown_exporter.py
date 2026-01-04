"""Markdown exporter for test cases."""

from pathlib import Path

from jinja2 import Environment, PackageLoader

from testcaseer.exporters.base import BaseExporter
from testcaseer.models import TestCase


class MarkdownExporter(BaseExporter):
    """Export test cases to Markdown format."""

    def __init__(self) -> None:
        """Initialize the Markdown exporter with Jinja2 environment."""
        self.env = Environment(loader=PackageLoader("testcaseer", "templates"))

    def export(self, testcase: TestCase, output_dir: Path) -> Path:
        """
        Export test case to Markdown file.

        Args:
            testcase: TestCase object to export
            output_dir: Directory to save the output file

        Returns:
            Path to the created Markdown file
        """
        output_path = output_dir / "testcase.md"

        template = self.env.get_template("report.md.j2")
        content = template.render(testcase=testcase)

        output_path.write_text(content, encoding="utf-8")
        return output_path

