"""
Observability Platform - Source Module
======================================

This package provides observability infrastructure for the LLM Document Enhancer:

- jsonl_logger: JSONL logging utilities (log_record, validate_log, etc.)
- data_classes: Dataclass definitions (Scenario, ScenarioStep, Component, etc.)
- architecture_context: Static architecture definitions (services, entities, etc.)

Scenario execution logic is in /scripts/scenario_runner.py.
Scenario definitions are in /scripts/scenarios/.

Reference: DESIGN_DOCUMENT.md
"""

from .jsonl_logger import (
    LOG_FILE,
    SCHEMA_VERSION,
    GENERATOR_ID,
    log_record,
    log_records,
    validate_log,
    ensure_log_directory,
    new_id,
    now_iso,
)

from .data_classes import (
    ScenarioStep,
    Scenario,
    StepExecutionResult,
    Component,
    Relationship,
    EntityDefinition,
    ProcessDefinition,
)

from .architecture_context import (
    get_architecture_context,
    get_runtime_context,
    log_architecture_context,
)

__all__ = [
    # JSONL Logger
    "LOG_FILE",
    "SCHEMA_VERSION",
    "GENERATOR_ID",
    "log_record",
    "log_records",
    "validate_log",
    "ensure_log_directory",
    "new_id",
    "now_iso",
    # Data Classes
    "ScenarioStep",
    "Scenario",
    "StepExecutionResult",
    "Component",
    "Relationship",
    "EntityDefinition",
    "ProcessDefinition",
    # Architecture Context
    "get_architecture_context",
    "get_runtime_context",
    "log_architecture_context",
]
