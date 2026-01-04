"""JSON exporter for test cases."""

import json
from pathlib import Path

from testcaseer.exporters.base import BaseExporter
from testcaseer.models import TestCase


class JSONExporter(BaseExporter):
    """Export test cases to JSON format."""

    def export(self, testcase: TestCase, output_dir: Path) -> Path:
        """
        Export test case to JSON file.

        Args:
            testcase: TestCase object to export
            output_dir: Directory to save the output file

        Returns:
            Path to the created JSON file
        """
        output_path = output_dir / "testcase.json"

        # Pydantic v2: model_dump with JSON serialization mode
        data = testcase.model_dump(mode="json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return output_path

