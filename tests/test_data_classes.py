#!/usr/bin/env python3
"""
Tests for Data Classes Module
==============================

TDD RED phase: These tests define the expected interface for the
data_classes module, which should contain ONLY dataclass definitions.

Reference: ARCHITECTURE_GUIDELINES - separation of concerns
Reference: ANTI_PATTERN_ANALYSIS - Single Responsibility Principle
"""

from dataclasses import fields, is_dataclass
from typing import Any, Dict, List, Optional

import pytest


class TestScenarioStepDataClass:
    """Test ScenarioStep dataclass definition."""

    def test_scenario_step_is_dataclass(self) -> None:
        """Verify ScenarioStep is a dataclass."""
        from observability_platform.src.data_classes import ScenarioStep
        assert is_dataclass(ScenarioStep)

    def test_scenario_step_has_required_fields(self) -> None:
        """Verify ScenarioStep has required fields."""
        from observability_platform.src.data_classes import ScenarioStep

        field_names = {f.name for f in fields(ScenarioStep)}
        required = {"step_id", "name", "order"}
        assert required.issubset(field_names)

    def test_scenario_step_has_optional_http_fields(self) -> None:
        """Verify ScenarioStep has optional HTTP fields."""
        from observability_platform.src.data_classes import ScenarioStep

        field_names = {f.name for f in fields(ScenarioStep)}
        http_fields = {"method", "url", "payload", "expected_status"}
        assert http_fields.issubset(field_names)

    def test_scenario_step_has_optional_local_fields(self) -> None:
        """Verify ScenarioStep has optional local execution fields."""
        from observability_platform.src.data_classes import ScenarioStep

        field_names = {f.name for f in fields(ScenarioStep)}
        local_fields = {"function", "module"}
        assert local_fields.issubset(field_names)

    def test_scenario_step_can_be_instantiated(self) -> None:
        """Verify ScenarioStep can be created with minimal args."""
        from observability_platform.src.data_classes import ScenarioStep

        step = ScenarioStep(step_id="step_1", name="Test Step", order=1)
        assert step.step_id == "step_1"
        assert step.name == "Test Step"
        assert step.order == 1


class TestScenarioDataClass:
    """Test Scenario dataclass definition."""

    def test_scenario_is_dataclass(self) -> None:
        """Verify Scenario is a dataclass."""
        from observability_platform.src.data_classes import Scenario
        assert is_dataclass(Scenario)

    def test_scenario_has_required_fields(self) -> None:
        """Verify Scenario has required fields."""
        from observability_platform.src.data_classes import Scenario

        field_names = {f.name for f in fields(Scenario)}
        required = {"scenario_id", "name", "description"}
        assert required.issubset(field_names)

    def test_scenario_has_steps_field(self) -> None:
        """Verify Scenario has steps list field."""
        from observability_platform.src.data_classes import Scenario

        field_names = {f.name for f in fields(Scenario)}
        assert "steps" in field_names

    def test_scenario_can_be_instantiated(self) -> None:
        """Verify Scenario can be created with minimal args."""
        from observability_platform.src.data_classes import Scenario

        scenario = Scenario(
            scenario_id="test_scenario",
            name="Test Scenario",
            description="A test scenario"
        )
        assert scenario.scenario_id == "test_scenario"
        assert scenario.steps == []  # Default empty list


class TestStepExecutionResultDataClass:
    """Test StepExecutionResult dataclass definition."""

    def test_step_execution_result_is_dataclass(self) -> None:
        """Verify StepExecutionResult is a dataclass."""
        from observability_platform.src.data_classes import StepExecutionResult
        assert is_dataclass(StepExecutionResult)

    def test_step_execution_result_has_status_field(self) -> None:
        """Verify StepExecutionResult has status field."""
        from observability_platform.src.data_classes import StepExecutionResult

        field_names = {f.name for f in fields(StepExecutionResult)}
        assert "status" in field_names

    def test_step_execution_result_has_result_field(self) -> None:
        """Verify StepExecutionResult has result field."""
        from observability_platform.src.data_classes import StepExecutionResult

        field_names = {f.name for f in fields(StepExecutionResult)}
        assert "result" in field_names

    def test_step_execution_result_has_error_field(self) -> None:
        """Verify StepExecutionResult has error field."""
        from observability_platform.src.data_classes import StepExecutionResult

        field_names = {f.name for f in fields(StepExecutionResult)}
        assert "error" in field_names

    def test_step_execution_result_has_latency_field(self) -> None:
        """Verify StepExecutionResult has latency_ms field."""
        from observability_platform.src.data_classes import StepExecutionResult

        field_names = {f.name for f in fields(StepExecutionResult)}
        assert "latency_ms" in field_names

    def test_step_execution_result_can_be_instantiated(self) -> None:
        """Verify StepExecutionResult can be created."""
        from observability_platform.src.data_classes import StepExecutionResult

        result = StepExecutionResult(status="success")
        assert result.status == "success"
        assert result.latency_ms == 0.0  # Default


class TestComponentDataClass:
    """Test Component dataclass definition."""

    def test_component_is_dataclass(self) -> None:
        """Verify Component is a dataclass."""
        from observability_platform.src.data_classes import Component
        assert is_dataclass(Component)

    def test_component_has_required_fields(self) -> None:
        """Verify Component has required fields."""
        from observability_platform.src.data_classes import Component

        field_names = {f.name for f in fields(Component)}
        required = {"component_id", "component_kind", "name"}
        assert required.issubset(field_names)

    def test_component_can_be_instantiated(self) -> None:
        """Verify Component can be created."""
        from observability_platform.src.data_classes import Component

        comp = Component(
            component_id="svc_1",
            component_kind="Service",
            name="Test Service"
        )
        assert comp.component_id == "svc_1"
        assert comp.component_kind == "Service"


class TestRelationshipDataClass:
    """Test Relationship dataclass definition."""

    def test_relationship_is_dataclass(self) -> None:
        """Verify Relationship is a dataclass."""
        from observability_platform.src.data_classes import Relationship
        assert is_dataclass(Relationship)

    def test_relationship_has_required_fields(self) -> None:
        """Verify Relationship has required fields."""
        from observability_platform.src.data_classes import Relationship

        field_names = {f.name for f in fields(Relationship)}
        required = {"from_id", "to_id", "relationship_type"}
        assert required.issubset(field_names)


class TestEntityDefinitionDataClass:
    """Test EntityDefinition dataclass definition."""

    def test_entity_definition_is_dataclass(self) -> None:
        """Verify EntityDefinition is a dataclass."""
        from observability_platform.src.data_classes import EntityDefinition
        assert is_dataclass(EntityDefinition)

    def test_entity_definition_has_required_fields(self) -> None:
        """Verify EntityDefinition has required fields."""
        from observability_platform.src.data_classes import EntityDefinition

        field_names = {f.name for f in fields(EntityDefinition)}
        required = {"entity_id", "name"}
        assert required.issubset(field_names)


class TestProcessDefinitionDataClass:
    """Test ProcessDefinition dataclass definition."""

    def test_process_definition_is_dataclass(self) -> None:
        """Verify ProcessDefinition is a dataclass."""
        from observability_platform.src.data_classes import ProcessDefinition
        assert is_dataclass(ProcessDefinition)

    def test_process_definition_has_required_fields(self) -> None:
        """Verify ProcessDefinition has required fields."""
        from observability_platform.src.data_classes import ProcessDefinition

        field_names = {f.name for f in fields(ProcessDefinition)}
        required = {"process_id", "name", "description"}
        assert required.issubset(field_names)


class TestModuleDoesNotContainExecutionLogic:
    """Verify data_classes does NOT contain execution logic.
    
    Reference: ANTI_PATTERN_ANALYSIS - Single Responsibility Principle
    """

    def test_no_run_scenario_function(self) -> None:
        """Verify run_scenario function is NOT in data_classes."""
        import observability_platform.src.data_classes as dc_module

        assert not hasattr(dc_module, "run_scenario")

    def test_no_execute_step_function(self) -> None:
        """Verify execute_step function is NOT in data_classes."""
        import observability_platform.src.data_classes as dc_module

        assert not hasattr(dc_module, "execute_step")

    def test_no_log_record_function(self) -> None:
        """Verify log_record function is NOT in data_classes."""
        import observability_platform.src.data_classes as dc_module

        assert not hasattr(dc_module, "log_record")

    def test_no_get_architecture_context_function(self) -> None:
        """Verify get_architecture_context is NOT in data_classes."""
        import observability_platform.src.data_classes as dc_module

        assert not hasattr(dc_module, "get_architecture_context")
