#!/usr/bin/env python3
"""
Data Classes Module
===================

Pure dataclass definitions for the observability platform.
This module contains ONLY dataclass definitions with no behavior.

Reference: ARCHITECTURE_GUIDELINES - separation of concerns
Reference: ANTI_PATTERN_ANALYSIS - Single Responsibility Principle

This module intentionally does NOT contain:
- Execution logic
- Logging functions
- Scenario definitions (those are runtime data, not schema)
- Architecture context building functions

These dataclasses define the schema/structure for:
- Scenario execution
- Architecture components
- Process definitions
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# =============================================================================
# Scenario Execution Data Classes
# =============================================================================

@dataclass
class ScenarioStep:
    """
    Definition of a single step within a scenario.
    
    A step can be either HTTP-based (method, url, payload) or
    local execution-based (function, module).
    """
    step_id: str
    name: str
    order: int
    # For HTTP-based steps
    method: Optional[str] = None
    url: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    # For local execution steps
    function: Optional[str] = None
    module: Optional[str] = None
    # Entity mappings
    entity_inputs: Optional[List[Dict[str, str]]] = None
    entity_outputs_keys: Optional[List[str]] = None
    # Service mappings
    service_id: Optional[str] = None
    interface_id: Optional[str] = None


@dataclass
class Scenario:
    """
    Definition of a complete business scenario.
    
    A scenario represents a user journey or workflow with
    multiple ordered steps.
    """
    scenario_id: str
    name: str
    description: str
    steps: List[ScenarioStep] = field(default_factory=list)
    process_id: Optional[str] = None
    trigger_type: str = "user_action"
    trigger_source: str = "observability_runner"


@dataclass
class StepExecutionResult:
    """
    Result of executing a single scenario step.
    
    Captures status, result data, errors, and timing.
    """
    status: str  # "success", "failed", "skipped"
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0


# =============================================================================
# Architecture Component Data Classes
# =============================================================================

@dataclass
class Component:
    """
    Definition of a system component.
    
    Components can be: Service, Endpoint, Database, 
    ExternalSystem, InfraNode, Container.
    
    Different component kinds use different optional fields.
    """
    component_id: str
    component_kind: str  # Service, Endpoint, Database, ExternalSystem, InfraNode, Container
    name: str
    description: str = ""
    # For services
    owner_team: Optional[str] = None
    inputs: Optional[List[str]] = None
    outputs: Optional[List[str]] = None
    # For endpoints
    service_id: Optional[str] = None
    protocol: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    consumes: Optional[List[str]] = None
    produces: Optional[List[str]] = None
    # For databases
    engine: Optional[str] = None
    # For external systems
    contact_type: Optional[str] = None
    base_url: Optional[str] = None
    # For containers
    node_id: Optional[str] = None
    image: Optional[str] = None
    environment: Optional[str] = None
    # For infra nodes
    provider: Optional[str] = None
    region: Optional[str] = None
    zone: Optional[str] = None


@dataclass
class Relationship:
    """
    Definition of a relationship between components.
    """
    from_id: str
    to_id: str
    relationship_type: str  # EXPOSES, WRITES_TO, READS_FROM, INTEGRATES_WITH, RUNS_ON
    description: str = ""


@dataclass
class EntityDefinition:
    """
    Definition of a domain entity.
    
    Entities are the data objects that flow through the system.
    """
    entity_id: str
    name: str
    description: str = ""
    states: Optional[List[str]] = None
    primary_key: Optional[str] = None
    schema_ref: Optional[str] = None


@dataclass
class ProcessDefinition:
    """
    Definition of a business process.
    
    Processes represent high-level workflows that span
    multiple components.
    """
    process_id: str
    name: str
    description: str = ""
    trigger_type: str = "user_action"
    trigger_source: str = "frontend_app"
    success_criteria: str = ""
    failure_criteria: str = ""


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    "Component",
    "EntityDefinition",
    "ProcessDefinition",
    "Relationship",
    "Scenario",
    "ScenarioStep",
    "StepExecutionResult",
]
