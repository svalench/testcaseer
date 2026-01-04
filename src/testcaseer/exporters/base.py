"""Base exporter class."""

from abc import ABC, abstractmethod
from pathlib import Path

from testcaseer.models import TestCase


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    @abstractmethod
    def export(self, testcase: TestCase, output_dir: Path) -> Path:
        """
        Export a test case to a file.

        Args:
            testcase: TestCase object to export
            output_dir: Directory to save the output file

        Returns:
            Path to the created file
        """
        pass

