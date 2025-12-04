# Observability Platform

**Status**: POC (Proof of Concept)  
**Future State**: Standalone Application  
**Created**: November 2025  

---

## Overview

The Observability Platform is a synthetic user runner + logger designed to provide comprehensive visibility into the LLM Document Enhancer system. It captures architecture context, business scenarios, and execution events in a structured JSONL format suitable for analysis, debugging, and compliance auditing.

### Purpose

1. **Architecture Documentation**: Automatically log all system components, relationships, and entities
2. **Scenario Execution**: Define and execute business scenarios with full traceability
3. **Event Logging**: Capture step-by-step execution with timing, status, and error details
4. **Future Extraction**: Designed for easy extraction into a standalone observability application

---

## Directory Structure

```
observability_platform/
├── README.md                    # This file
├── DESIGN_DOCUMENT.md           # Detailed architecture and design decisions
├── src/
│   └── system_observability_runner.py   # Main runner script
├── tests/
│   └── test_observability_runner.py     # TDD test suite (26 tests)
├── docs/
│   └── TDD_REFACTORING_PLAN.md          # TDD methodology documentation
├── logs/                        # JSONL output directory
│   └── .gitkeep
└── config/                      # Future: configuration files
    └── .gitkeep
```

---

## Quick Start

### List Available Scenarios
```bash
python observability_platform/src/system_observability_runner.py --list-scenarios
```

### Log Architecture Context
```bash
python observability_platform/src/system_observability_runner.py --log-architecture
```

### Run a Scenario
```bash
python observability_platform/src/system_observability_runner.py --run-scenario extraction_evaluation
```

### Validate Log Output
```bash
python observability_platform/src/system_observability_runner.py --validate-log
```

---

## Current Capabilities

### Predefined Scenarios

| Scenario | Description | Steps |
|----------|-------------|-------|
| `extraction_evaluation` | Run 4 extraction profiles with LLM evaluation | 9 |
| `single_extraction` | Extract metadata from a single book | 2 |
| `enrichment_pipeline` | Full enrichment from metadata to aggregate | 6 |

### Architecture Records

The platform logs 57 architecture records including:
- **22 Components**: Services, endpoints, databases, external systems
- **9 Entity Definitions**: PDF documents, metadata, guidelines, etc.
- **6 Process Definitions**: Business processes with success/failure criteria
- **19 Relationships**: EXPOSES, WRITES_TO, READS_FROM, INTEGRATES_WITH

### JSONL Record Types

| Record Type | Description |
|-------------|-------------|
| `meta` | Schema version and generator info |
| `component` | Service, endpoint, database, or external system |
| `entity_definition` | Domain entity with states and schema |
| `process_definition` | Business process with triggers and criteria |
| `relationship` | Connection between components |
| `scenario_definition` | Business scenario with steps |
| `scenario_run` | Execution instance of a scenario |
| `event` | Step started, completed, or error events |
| `state_transition` | Entity state changes |

---

## Test Suite

Run the TDD test suite:
```bash
python -m pytest observability_platform/tests/ -v
```

### Test Categories

| Category | Tests | Status |
|----------|-------|--------|
| Type Annotations | 3 | ✅ Pass |
| Cognitive Complexity | 4 | ✅ Pass |
| Exception Handling | 2 | ✅ Pass |
| JSONL Schema | 4 | ✅ Pass |
| Scenario Execution | 5 | ✅ Pass |
| Architecture Patterns | 3 | ⏭️ 2 Skipped |
| DataClasses | 3 | ✅ Pass |
| Validate Log | 2 | ✅ Pass |

**Total**: 24 passing, 2 skipped

---

## Future Extraction

This platform is designed for extraction into a standalone application. Key considerations:

1. **Self-Contained**: All related files in `observability_platform/`
2. **No External Dependencies**: Uses only standard library + optional `requests`
3. **Documented Patterns**: Skipped tests define future architecture patterns
4. **Configuration Ready**: `config/` directory for future settings

See [DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md) for detailed architecture and extraction guidance.

---

## References

- [DESIGN_DOCUMENT.md](DESIGN_DOCUMENT.md) - Full design specification
- [TDD_REFACTORING_PLAN.md](docs/TDD_REFACTORING_PLAN.md) - TDD methodology and document analysis
