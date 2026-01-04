"""HTML exporter for test cases."""

import base64
from pathlib import Path
from typing import Any

from jinja2 import Environment, PackageLoader

from testcaseer.exporters.base import BaseExporter
from testcaseer.models import Step, TestCase


class HTMLExporter(BaseExporter):
    """Export test cases to HTML format with embedded screenshots."""

    def __init__(self) -> None:
        """Initialize the HTML exporter with Jinja2 environment."""
        self.env = Environment(loader=PackageLoader("testcaseer", "templates"))

    def export(self, testcase: TestCase, output_dir: Path) -> Path:
        """
        Export test case to HTML file with embedded screenshots.

        Args:
            testcase: TestCase object to export
            output_dir: Directory to save the output file

        Returns:
            Path to the created HTML file
        """
        output_path = output_dir / "testcase.html"

        template = self.env.get_template("report.html.j2")

        # Convert screenshots to base64 for embedding
        steps_with_images = self._embed_screenshots(testcase.steps, output_dir)

        content = template.render(testcase=testcase, steps=steps_with_images)

        output_path.write_text(content, encoding="utf-8")
        return output_path

    def _embed_screenshots(
        self, steps: list[Step], output_dir: Path
    ) -> list[dict[str, Any]]:
        """
        Convert screenshot paths to base64 data URLs.

        Args:
            steps: List of Step objects
            output_dir: Base directory for screenshot paths

        Returns:
            List of step dictionaries with embedded screenshot data
        """
        result: list[dict[str, Any]] = []

        for step in steps:
            step_dict = step.model_dump()

            if step.screenshot_path:
                full_path = output_dir / step.screenshot_path
                if full_path.exists():
                    with open(full_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode()
                        step_dict["screenshot_base64"] = f"data:image/png;base64,{b64}"

            result.append(step_dict)

        return result

