"""Tests for Pydantic models."""

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from testcaseer.models import (
    ConsoleLog,
    ElementInfo,
    NetworkRequest,
    PageError,
    Step,
    TestCase,
)


class TestElementInfo:
    """Tests for ElementInfo model."""

    def test_create_element_info(self, sample_element_info: ElementInfo) -> None:
        """Test creating ElementInfo with all fields."""
        assert sample_element_info.selector == "button#submit"
        assert sample_element_info.tag_name == "button"
        assert sample_element_info.text == "Submit"
        assert sample_element_info.bounding_box["width"] == 120

    def test_element_info_minimal(self) -> None:
        """Test creating ElementInfo with minimal required fields."""
        element = ElementInfo(
            selector="div.container",
            tag_name="div",
            bounding_box={"x": 0, "y": 0, "width": 100, "height": 100},
        )
        assert element.selector == "div.container"
        assert element.xpath is None
        assert element.text is None
        assert element.placeholder is None
        assert element.attributes == {}

    def test_element_info_with_attributes(self) -> None:
        """Test ElementInfo with custom attributes."""
        element = ElementInfo(
            selector="input#name",
            tag_name="input",
            attributes={"id": "name", "type": "text", "required": "true", "data-testid": "name-input"},
            bounding_box={"x": 10, "y": 20, "width": 200, "height": 30},
        )
        assert element.attributes["data-testid"] == "name-input"
        assert len(element.attributes) == 4

    def test_element_info_missing_required_field(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            ElementInfo(
                selector="div",
                # missing tag_name and bounding_box
            )  # type: ignore[call-arg]


class TestNetworkRequest:
    """Tests for NetworkRequest model."""

    def test_create_network_request(self, sample_network_request: NetworkRequest) -> None:
        """Test creating NetworkRequest with all fields."""
        assert sample_network_request.method == "POST"
        assert sample_network_request.status == 200
        assert sample_network_request.resource_type == "xhr"
        assert "application/json" in sample_network_request.request_headers.get("Content-Type", "")

    def test_network_request_minimal(self) -> None:
        """Test creating NetworkRequest with minimal fields."""
        request = NetworkRequest(
            method="GET",
            url="https://example.com/api/data",
            resource_type="fetch",
        )
        assert request.method == "GET"
        assert request.status is None
        assert request.timing is None
        assert request.request_body is None
        assert request.response_body is None
        assert request.error is None

    def test_network_request_with_error(self) -> None:
        """Test NetworkRequest with error."""
        request = NetworkRequest(
            method="POST",
            url="https://api.example.com/submit",
            resource_type="xhr",
            error="net::ERR_CONNECTION_REFUSED",
        )
        assert request.error == "net::ERR_CONNECTION_REFUSED"
        assert request.status is None

    def test_network_request_serialization(self, sample_network_request: NetworkRequest) -> None:
        """Test that NetworkRequest serializes correctly."""
        data = sample_network_request.model_dump()
        assert data["method"] == "POST"
        assert data["url"] == "https://api.example.com/login"
        assert "request_headers" in data
        assert "response_body" in data


class TestConsoleLog:
    """Tests for ConsoleLog model."""

    def test_create_console_log(self, sample_console_log: ConsoleLog) -> None:
        """Test creating ConsoleLog."""
        assert sample_console_log.level == "info"
        assert "initialized" in sample_console_log.message
        assert sample_console_log.source is not None

    def test_console_log_all_levels(self) -> None:
        """Test ConsoleLog with all valid levels."""
        levels = ["log", "info", "warn", "error", "debug", "trace"]
        for level in levels:
            log = ConsoleLog(
                level=level,  # type: ignore[arg-type]
                message=f"Test message with level {level}",
            )
            assert log.level == level

    def test_console_log_invalid_level(self) -> None:
        """Test that invalid level raises ValidationError."""
        with pytest.raises(ValidationError):
            ConsoleLog(
                level="invalid",  # type: ignore[arg-type]
                message="Test",
            )

    def test_console_log_with_args(self) -> None:
        """Test ConsoleLog with arguments."""
        log = ConsoleLog(
            level="log",
            message="User data:",
            args=["name=John", "age=30", "city=NYC"],
        )
        assert len(log.args) == 3
        assert "name=John" in log.args


class TestPageError:
    """Tests for PageError model."""

    def test_create_page_error(self, sample_page_error: PageError) -> None:
        """Test creating PageError."""
        assert "TypeError" in sample_page_error.message
        assert sample_page_error.stack is not None
        assert "app.js" in sample_page_error.stack

    def test_page_error_without_stack(self) -> None:
        """Test PageError without stack trace."""
        error = PageError(message="Script error.")
        assert error.message == "Script error."
        assert error.stack is None
        assert error.timestamp is not None


class TestStep:
    """Tests for Step model."""

    def test_create_step(self, sample_step: Step) -> None:
        """Test creating Step."""
        assert sample_step.number == 1
        assert sample_step.action_type == "click"
        assert sample_step.element is not None
        assert sample_step.element.tag_name == "button"

    def test_step_with_input(self, sample_step_with_input: Step) -> None:
        """Test Step with input action."""
        assert sample_step_with_input.action_type == "input"
        assert sample_step_with_input.input_value == "user@example.com"

    def test_step_action_types(self) -> None:
        """Test all valid action types."""
        action_types = [
            "click", "dblclick", "input", "select", "check",
            "uncheck", "navigate", "scroll", "hover", "keypress", "wait"
        ]
        for action_type in action_types:
            step = Step(
                number=1,
                timestamp=datetime.now(),
                action_type=action_type,  # type: ignore[arg-type]
                description_short=f"Test {action_type}",
                description_detailed=f"Testing {action_type} action",
            )
            assert step.action_type == action_type

    def test_step_invalid_action_type(self) -> None:
        """Test that invalid action type raises ValidationError."""
        with pytest.raises(ValidationError):
            Step(
                number=1,
                timestamp=datetime.now(),
                action_type="invalid_action",  # type: ignore[arg-type]
                description_short="Test",
                description_detailed="Test",
            )

    def test_step_with_network_requests(
        self,
        sample_step: Step,
        sample_network_request: NetworkRequest,
    ) -> None:
        """Test Step with network requests."""
        step = sample_step.model_copy(update={"network_requests": [sample_network_request]})
        assert len(step.network_requests) == 1
        assert step.network_requests[0].method == "POST"

    def test_step_with_console_logs(
        self,
        sample_step: Step,
        sample_console_log: ConsoleLog,
    ) -> None:
        """Test Step with console logs."""
        step = sample_step.model_copy(update={"console_logs": [sample_console_log]})
        assert len(step.console_logs) == 1
        assert step.console_logs[0].level == "info"


class TestTestCase:
    """Tests for TestCase model."""

    def test_create_testcase(self, sample_testcase: TestCase) -> None:
        """Test creating TestCase."""
        assert sample_testcase.id == "tc_001"
        assert sample_testcase.name == "Тест авторизации"
        assert sample_testcase.browser == "chromium"
        assert len(sample_testcase.steps) == 2
        assert sample_testcase.total_steps == 2

    def test_testcase_minimal(self, sample_testcase_minimal: TestCase) -> None:
        """Test minimal TestCase."""
        assert sample_testcase_minimal.id == "tc_minimal"
        assert len(sample_testcase_minimal.steps) == 0
        assert sample_testcase_minimal.total_steps == 0

    def test_testcase_viewport(self, sample_testcase: TestCase) -> None:
        """Test TestCase viewport."""
        assert sample_testcase.viewport["width"] == 1920
        assert sample_testcase.viewport["height"] == 1080

    def test_testcase_serialization(self, sample_testcase: TestCase) -> None:
        """Test TestCase JSON serialization."""
        data = sample_testcase.model_dump()
        assert data["id"] == "tc_001"
        assert "steps" in data
        assert len(data["steps"]) == 2
        assert "console_logs" in data
        assert "network_requests" in data
        assert "page_errors" in data

    def test_testcase_json_round_trip(self, sample_testcase: TestCase) -> None:
        """Test that TestCase can be serialized and deserialized."""
        json_str = sample_testcase.model_dump_json()
        restored = TestCase.model_validate_json(json_str)
        
        assert restored.id == sample_testcase.id
        assert restored.name == sample_testcase.name
        assert len(restored.steps) == len(sample_testcase.steps)
        assert restored.total_duration == sample_testcase.total_duration

    def test_testcase_with_logs_and_errors(self, sample_testcase: TestCase) -> None:
        """Test TestCase with console logs and page errors."""
        assert len(sample_testcase.console_logs) == 1
        assert len(sample_testcase.page_errors) == 1
        assert sample_testcase.console_logs[0].level == "info"
        assert "TypeError" in sample_testcase.page_errors[0].message

