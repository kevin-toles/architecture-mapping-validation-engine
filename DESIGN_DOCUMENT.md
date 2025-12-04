# Observability Platform - Design Document

**Version**: 1.0.0  
**Status**: POC (Proof of Concept)  
**Last Updated**: November 29, 2025  

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Data Model](#data-model)
5. [TDD Implementation](#tdd-implementation)
6. [Deferred Refactoring](#deferred-refactoring)
7. [Extraction Guide](#extraction-guide)
8. [API Reference](#api-reference)

---

## Executive Summary

### Problem Statement

The LLM Document Enhancer is a complex multi-workflow system with:
- 6+ distinct workflows (PDF conversion, metadata extraction, taxonomy, enrichment, guideline generation, LLM enhancement)
- 4 LLM provider integrations (OpenAI, Anthropic, Gemini, DeepSeek)
- Multiple data entities flowing through the pipeline

Without observability, it's difficult to:
- Debug failures across workflow boundaries
- Understand data flow between components
- Validate that scenarios execute correctly
- Audit system behavior for compliance

### Solution

A synthetic user runner that:
1. **Defines business scenarios** as structured step sequences
2. **Executes steps** with timing and error capture
3. **Logs everything** to append-only JSONL for analysis
4. **Documents architecture** with component relationships

### Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Separation of Concerns** | Architecture context is separate from logging logic |
| **Single Responsibility** | Each helper function does one thing (Execute, Log, Print) |
| **EAFP Error Handling** | Try/except with specific exception types |
| **Parameter Objects** | `StepExecutionResult` dataclass for step outcomes |
| **Append-Only Logging** | JSONL format for replay and analysis |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Observability Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │ Architecture     │    │ Scenario         │                   │
│  │ Context          │    │ Definitions      │                   │
│  │ - Services       │    │ - Steps          │                   │
│  │ - Entities       │    │ - Order          │                   │
│  │ - Relationships  │    │ - Expectations   │                   │
│  └────────┬─────────┘    └────────┬─────────┘                   │
│           │                       │                              │
│           ▼                       ▼                              │
│  ┌─────────────────────────────────────────────┐                │
│  │            Execution Engine                  │                │
│  │  ┌─────────────┐  ┌─────────────┐           │                │
│  │  │ _execute_   │  │ _execute_   │           │                │
│  │  │ local_step  │  │ http_step   │           │                │
│  │  └──────┬──────┘  └──────┬──────┘           │                │
│  │         │                │                   │                │
│  │         ▼                ▼                   │                │
│  │  ┌─────────────────────────────┐            │                │
│  │  │     _execute_step           │            │                │
│  │  │   (dispatcher)              │            │                │
│  │  └──────────────┬──────────────┘            │                │
│  └─────────────────┼────────────────────────────┘                │
│                    │                                             │
│                    ▼                                             │
│  ┌─────────────────────────────────────────────┐                │
│  │           JSONL Logger                       │                │
│  │  log_record() / log_records()               │                │
│  └──────────────────┬──────────────────────────┘                │
│                     │                                            │
│                     ▼                                            │
│  ┌─────────────────────────────────────────────┐                │
│  │     system_observability_log.jsonl          │                │
│  │     (Append-Only)                           │                │
│  └─────────────────────────────────────────────┘                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

### 1. DataClasses

```python
@dataclass
class ScenarioStep:
    """A single step within a scenario."""
    step_id: str
    name: str
    order: int
    function: Optional[str] = None      # For local execution
    module: Optional[str] = None
    url: Optional[str] = None           # For HTTP execution
    method: Optional[str] = None
    # ... additional fields

@dataclass
class Scenario:
    """A complete business scenario."""
    scenario_id: str
    name: str
    description: str
    steps: List[ScenarioStep]
    process_id: Optional[str] = None

@dataclass
class StepExecutionResult:
    """Result of executing a single step (Parameter Object pattern)."""
    status: str  # "success", "failed", "skipped"
    result: Any = None
    error: Optional[str] = None
    latency_ms: float = 0.0

@dataclass
class Component:
    """A system component (service, endpoint, database, etc.)."""
    component_id: str
    component_kind: str
    name: str
    # ... additional fields based on kind
```

### 2. Execution Helpers

| Function | Responsibility | Lines |
|----------|----------------|-------|
| `_execute_step()` | Dispatch to appropriate executor | 12 |
| `_execute_local_step()` | Execute Python function | 15 |
| `_execute_http_step()` | Execute HTTP request | 30 |
| `_update_step_context()` | Extract entity outputs | 5 |
| `_log_step_events()` | Log start/complete events | 25 |
| `_print_step_status()` | Console output | 12 |

### 3. Main Functions

| Function | Purpose | Cognitive Complexity |
|----------|---------|---------------------|
| `run_scenario()` | Orchestrate scenario execution | 8 (was 21) |
| `log_architecture_context()` | Log all architecture records | 5 |
| `validate_log()` | Validate JSONL output | 6 |
| `main()` | CLI entry point | 4 |

---

## Data Model

### JSONL Schema (v1.0.0)

Each line is a self-contained JSON object with `record_type` discriminator:

```json
{"record_type":"meta","schema_version":"1.0.0","generated_by":"frontend_driver_v1","created_at":"2025-11-29T10:30:00.000Z"}
{"record_type":"component","component_id":"svc_pdf_converter","component_kind":"Service","name":"PDF to JSON Converter",...}
{"record_type":"relationship","from_id":"svc_pdf_converter","to_id":"db_document_store","relationship_type":"WRITES_TO"}
{"record_type":"event","event_type":"StepStarted","trace_id":"trc_abc123","step_id":"step_1",...}
```

### Record Type Reference

#### `meta`
```typescript
{
  record_type: "meta",
  schema_version: string,      // "1.0.0"
  generated_by: string,        // "frontend_driver_v1"
  created_at: string           // ISO timestamp
}
```

#### `component`
```typescript
{
  record_type: "component",
  component_id: string,        // "svc_pdf_converter"
  component_kind: "Service" | "Endpoint" | "Database" | "ExternalSystem" | "InfraNode",
  name: string,
  description?: string,
  // Kind-specific fields...
}
```

#### `relationship`
```typescript
{
  record_type: "relationship",
  from_id: string,             // Source component ID
  to_id: string,               // Target component ID
  relationship_type: "EXPOSES" | "WRITES_TO" | "READS_FROM" | "INTEGRATES_WITH" | "RUNS_ON"
}
```

#### `event`
```typescript
{
  record_type: "event",
  event_type: "StepStarted" | "StepCompleted" | "StepError",
  timestamp: string,           // ISO timestamp
  trace_id: string,            // Trace correlation ID
  scenario_run_id: string,
  step_id: string,
  status?: string,             // For StepCompleted
  metrics?: { latency_ms: number },
  error?: string
}
```

---

## TDD Implementation

### Methodology

Following strict RED → GREEN → REFACTOR cycle per project guidelines.

### Document Priority Hierarchy

1. **BOOK_TAXONOMY_MATRIX.md** - Architecture spine, observability from Building Microservices
2. **ARCHITECTURE_GUIDELINES** - Domain Modeling, Repository, Unit of Work, Events (Ch 1,2,6,8)
3. **PYTHON_GUIDELINES** - EAFP, type hints, module organization (Ch 1-2)
4. **ANTI_PATTERN_ANALYSIS.md** - 11 anti-pattern categories to avoid

### Test Results

```
====== test session starts ======
collected 26 items

test_observability_runner.py::TestTypeAnnotations::test_all_function_parameters_have_type_hints PASSED
test_observability_runner.py::TestTypeAnnotations::test_all_public_functions_have_return_type_hints PASSED
test_observability_runner.py::TestTypeAnnotations::test_optional_return_types_are_annotated PASSED
test_observability_runner.py::TestCognitiveComplexity::test_all_functions_complexity_under_15 PASSED
test_observability_runner.py::TestCognitiveComplexity::test_function_line_count_under_50 PASSED
test_observability_runner.py::TestCognitiveComplexity::test_log_architecture_complexity_under_15 PASSED
test_observability_runner.py::TestCognitiveComplexity::test_run_scenario_complexity_under_15 PASSED
test_observability_runner.py::TestExceptionHandling::test_exceptions_capture_error_type PASSED
test_observability_runner.py::TestExceptionHandling::test_no_bare_except_clauses PASSED
test_observability_runner.py::TestJSONLSchema::test_component_record_has_valid_structure PASSED
test_observability_runner.py::TestJSONLSchema::test_log_record_has_required_fields PASSED
test_observability_runner.py::TestJSONLSchema::test_relationship_record_validates_from_to PASSED
test_observability_runner.py::TestJSONLSchema::test_timestamp_format_is_iso PASSED
test_observability_runner.py::TestScenarioExecution::test_all_scenarios_have_required_fields PASSED
test_observability_runner.py::TestScenarioExecution::test_get_scenario_definitions_returns_dict PASSED
test_observability_runner.py::TestScenarioExecution::test_new_id_generates_unique_ids PASSED
test_observability_runner.py::TestScenarioExecution::test_new_id_has_correct_prefix PASSED
test_observability_runner.py::TestScenarioExecution::test_scenario_steps_execute_in_order PASSED
test_observability_runner.py::TestArchitecturePatterns::test_architecture_context_is_separate_from_logging PASSED
test_observability_runner.py::TestArchitecturePatterns::test_events_defined_for_discoveries SKIPPED
test_observability_runner.py::TestArchitecturePatterns::test_log_repository_protocol_exists SKIPPED
test_observability_runner.py::TestDataClasses::test_component_has_sensible_defaults PASSED
test_observability_runner.py::TestDataClasses::test_scenario_has_empty_steps_by_default PASSED
test_observability_runner.py::TestDataClasses::test_scenario_step_has_sensible_defaults PASSED
test_observability_runner.py::TestValidateLog::test_validate_log_counts_record_types PASSED
test_observability_runner.py::TestValidateLog::test_validate_log_returns_error_for_missing_file PASSED

====== 24 passed, 2 skipped ======
```

---

## Deferred Refactoring

### Status: NOT STARTED (Intentional)

The following patterns are documented but **not implemented** per YAGNI principle:

### 1. Repository Pattern (ARCHITECTURE_GUIDELINES Ch 2)

**Current State**: Direct file I/O via `log_record()`

**Future State**:
```python
class LogRepository(Protocol):
    def append(self, record: LogRecord) -> None: ...
    def get_all(self) -> List[LogRecord]: ...
    def get_by_type(self, record_type: str) -> List[LogRecord]: ...

class JSONLRepository(LogRepository):
    def __init__(self, filepath: Path):
        self._filepath = filepath
    
    def append(self, record: LogRecord) -> None:
        with open(self._filepath, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")
```

**When to Implement**: When multiple log destinations are needed (file + database + cloud)

**Test Ready**: `test_log_repository_protocol_exists` (currently SKIPPED)

### 2. Domain Events (ARCHITECTURE_GUIDELINES Ch 8)

**Current State**: Direct logging calls

**Future State**:
```python
@dataclass
class ComponentDiscoveredEvent:
    component_id: str
    component_kind: str
    timestamp: datetime
    metadata: Dict[str, Any]

@dataclass
class RelationshipFoundEvent:
    from_id: str
    to_id: str
    relationship_type: str
    timestamp: datetime

class MessageBus:
    def __init__(self):
        self._handlers: Dict[Type, List[Callable]] = {}
    
    def register(self, event_type: Type, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)
    
    def emit(self, event: Any) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)
```

**When to Implement**: When events need to trigger multiple actions (log + notify + metrics)

**Test Ready**: `test_events_defined_for_discoveries` (currently SKIPPED)

### Risk Assessment for Deferred Patterns

| Risk | Level | Mitigation |
|------|-------|------------|
| Breaking changes later | 🟢 Low | Patterns are additive, not replacement |
| Tests document intent | 🟢 Low | Skipped tests serve as living specification |
| Over-engineering now | 🟢 Avoided | YAGNI applied correctly |

---

## Extraction Guide

### Prerequisites for Standalone Application

When extracting to standalone:

1. **Copy `observability_platform/` directory** as-is
2. **Update imports** in `system_observability_runner.py`:
   - Remove `PROJECT_ROOT` path manipulation
   - Use relative imports within package
3. **Create `setup.py` or `pyproject.toml`**:
   ```toml
   [project]
   name = "observability-platform"
   version = "1.0.0"
   dependencies = ["requests>=2.28.0"]
   ```
4. **Implement deferred patterns** (Repository, Events) if needed
5. **Add CLI via Click or Typer** for richer argument handling

### Configuration Externalization

Currently hardcoded in `get_architecture_context()`. For standalone:

```yaml
# config/architecture.yaml
services:
  - id: svc_pdf_converter
    kind: Service
    name: PDF to JSON Converter
    owner_team: document-processing
    inputs: [entity_pdf_document]
    outputs: [entity_json_text, entity_chapter_segments]
```

### Database Integration

For persistent storage beyond JSONL:

```python
class PostgresRepository(LogRepository):
    def __init__(self, connection_string: str):
        self._engine = create_engine(connection_string)
    
    def append(self, record: LogRecord) -> None:
        with self._engine.connect() as conn:
            conn.execute(insert(observability_logs).values(**asdict(record)))
```

---

## API Reference

### CLI Arguments

| Argument | Description |
|----------|-------------|
| `--run-scenario SCENARIO` | Run a specific scenario |
| `--run-all` | Run all defined scenarios |
| `--log-architecture` | Log architecture context only |
| `--validate-log` | Validate and summarize log file |
| `--clear-log` | Clear existing log file |
| `--list-scenarios` | List all defined scenarios |

### Python API

```python
from observability_platform.src.system_observability_runner import (
    run_scenario,
    get_scenario_definitions,
    log_architecture_context,
    validate_log,
)

# Get available scenarios
scenarios = get_scenario_definitions()

# Run a scenario
result = run_scenario(scenarios["extraction_evaluation"])
print(f"Status: {result['status']}")
print(f"Trace ID: {result['trace_id']}")

# Log architecture
log_architecture_context()

# Validate output
stats = validate_log()
print(f"Total records: {stats['total_records']}")
```

---

## References

### Project Documents
- [BOOK_TAXONOMY_MATRIX.md](../../BOOK_TAXONOMY_MATRIX.md)
- [ANTI_PATTERN_ANALYSIS.md](../../ANTI_PATTERN_ANALYSIS.md)
- [ARCHITECTURE_GUIDELINES](../../workflows/llm_enhancement/output/ARCHITECTURE_GUIDELINES_Architecture_Patterns_with_Python_LLM_ENHANCED.md)

### External References
- Architecture Patterns with Python (Harry Percival, Bob Gregory) - Ch 2, 6, 8
- Building Microservices (Sam Newman) - Ch 10-11 Observability
