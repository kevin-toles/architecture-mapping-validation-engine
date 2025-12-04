# TDD Refactoring Plan: System Observability Runner

**Document Created**: Following TDD methodology (RED → GREEN → REFACTOR)
**Target Script**: `scripts/observability/system_observability_runner.py`
**Status**: ✅ GREEN Phase Complete (24 tests passing, 2 skipped for REFACTOR)

---

## TDD Execution Summary

| Phase | Status | Details |
|-------|--------|---------|
| RED | ✅ Complete | 26 tests written, 4 failed (bare except, CC=21, line counts) |
| GREEN | ✅ Complete | All 4 failing tests fixed, 24 passing, 2 skipped |
| REFACTOR | ⏳ Future | Repository/Event patterns available via skipped tests |

### Fixes Applied (GREEN Phase)

1. **Bare Except Clause** (Line 1064)
   - Changed `except:` to `except json.JSONDecodeError:`
   - Per ANTI_PATTERN_ANALYSIS.md Section 4.1

2. **Cognitive Complexity** (run_scenario CC=21→8)
   - Added `StepExecutionResult` dataclass (Parameter Object pattern)
   - Extracted `_execute_local_step()` helper
   - Extracted `_execute_http_step()` helper
   - Extracted `_execute_step()` dispatcher
   - Extracted `_update_step_context()` helper
   - Extracted `_log_step_events()` helper
   - Extracted `_print_step_status()` helper
   - Per ANTI_PATTERN_ANALYSIS.md Section 10.2

3. **Specific Exception Types**
   - Added `ModuleNotFoundError, AttributeError, TypeError` to execute_local_function
   - Added `requests.RequestException` to _execute_http_step
   - Per PYTHON_GUIDELINES Ch 1 EAFP pattern

---

## Step 1-3: Document Analysis Summary

### Document Priority Hierarchy Applied

| Priority | Document | Applicable Concepts | Conflicts Resolved |
|----------|----------|---------------------|-------------------|
| 1 (Highest) | BOOK_TAXONOMY_MATRIX.md | Tier 1: Architecture Spine (Observability from Building Microservices Ch 10-11) | None - primary reference |
| 2 | ARCHITECTURE_GUIDELINES (Ch 1,2,6,8) | Domain Modeling, Repository, Unit of Work, Events/Message Bus | Event-driven vs sync logging → Use Event pattern |
| 3 | PYTHON_GUIDELINES (Ch 1-2) | Bytecode compilation, EAFP, type hints, module organization | None |
| 4 (Lowest) | ANTI_PATTERN_ANALYSIS.md | 11 anti-pattern categories, 222+ fixes, CC<15, Optional types | All resolved by higher priority docs |

---

## Applicable Architecture Patterns

### From ARCHITECTURE_GUIDELINES Chapter 8: Events and Message Bus

**Domain Events Pattern** - The observability runner should emit events:
```python
# Current: Direct logging
log_record({"type": "component", "name": "StatisticalExtractor"})

# Recommended: Domain Event pattern
class ComponentDiscoveredEvent:
    component_name: str
    timestamp: datetime
    metadata: dict

event_bus.emit(ComponentDiscoveredEvent("StatisticalExtractor", ...))
```

**Message Bus** - Decouple log emission from log writing:
```python
# Handlers registered at startup
message_bus.register(ComponentDiscoveredEvent, [write_to_jsonl, notify_dashboard])
```

### From ARCHITECTURE_GUIDELINES Chapter 2: Repository Pattern

**Log Repository** - Abstract JSONL file operations:
```python
class LogRepository(Protocol):
    def append(self, record: LogRecord) -> None: ...
    def get_all(self) -> List[LogRecord]: ...
    def get_by_type(self, record_type: str) -> List[LogRecord]: ...

class JSONLRepository(LogRepository):
    def __init__(self, filepath: Path):
        self._filepath = filepath
```

### From ARCHITECTURE_GUIDELINES Chapter 6: Unit of Work

**Transactional Logging** - Batch log writes:
```python
class LoggingUnitOfWork:
    def __init__(self, repository: LogRepository):
        self._repository = repository
        self._pending: List[LogRecord] = []
    
    def add(self, record: LogRecord) -> None:
        self._pending.append(record)
    
    def commit(self) -> None:
        for record in self._pending:
            self._repository.append(record)
        self._pending.clear()
```

---

## Anti-Patterns to Avoid (from ANTI_PATTERN_ANALYSIS.md)

### 1. Optional Type Annotations (Section 1.1-1.4)
```python
# ❌ Current (potential issue)
def get_component_metadata(name: str) -> dict:
    # May return None if not found

# ✅ Required
def get_component_metadata(name: str) -> Optional[Dict[str, Any]]:
    """Return metadata or None if component not found."""
```

### 2. Cognitive Complexity > 15 (Section 3.1)
```python
# ❌ Avoid functions with CC > 15
# Current: run_scenario() may have high CC due to nested conditionals

# ✅ Extract to smaller functions (CC < 10 each)
```

### 3. Bare Except Clauses (Section 4.1)
```python
# ❌ Current (check if present)
try:
    ...
except:
    pass

# ✅ Required
try:
    ...
except SpecificException as e:
    logger.error(f"Specific error: {e}")
```

### 4. Too Many Arguments (Section 10.1)
```python
# ❌ Avoid > 5 arguments
def log_record(filepath, record_type, name, metadata, timestamp, context, parent): ...

# ✅ Use Parameter Object
@dataclass
class LogRecord:
    record_type: str
    name: str
    metadata: dict
    timestamp: datetime = field(default_factory=datetime.now)
```

### 5. Too Many Local Variables (Section 10.2)
```python
# ❌ Avoid > 15 local variables per function
# ✅ Extract Method pattern to reduce
```

---

## TDD Test Cases (RED Phase)

### Test File: `tests/unit/test_observability_runner.py`

```python
# Tests to write BEFORE implementation changes

# T1: Type Annotation Tests
def test_all_public_functions_have_return_type_hints(): ...
def test_optional_return_types_are_annotated(): ...

# T2: Cognitive Complexity Tests
def test_run_scenario_complexity_under_15(): ...
def test_log_architecture_complexity_under_15(): ...

# T3: Exception Handling Tests
def test_no_bare_except_clauses(): ...
def test_file_not_found_handled_specifically(): ...
def test_json_decode_error_handled_specifically(): ...

# T4: JSONL Schema Tests
def test_log_record_has_required_fields(): ...
def test_component_record_has_valid_structure(): ...
def test_relationship_record_validates_from_to(): ...

# T5: Scenario Execution Tests
def test_scenario_steps_execute_in_order(): ...
def test_failed_step_logs_error(): ...
def test_scenario_timing_is_accurate(): ...

# T6: Architecture Pattern Tests
def test_log_repository_abstraction_used(): ...
def test_events_emitted_for_discoveries(): ...
```

---

## Implementation Phases

### Phase 1: Type Safety (GREEN for T1)
- Add `Optional[]` to all functions that may return None
- Add return type hints to all public functions
- Add `from __future__ import annotations` for forward refs

### Phase 2: Complexity Reduction (GREEN for T2)
- Extract helper functions from `run_scenario()`
- Extract helper functions from `log_architecture()`
- Each helper should have CC < 10

### Phase 3: Exception Handling (GREEN for T3)
- Replace any bare `except:` with specific exceptions
- Add `FileNotFoundError`, `json.JSONDecodeError`, `OSError` handlers
- Log errors with full context

### Phase 4: Schema Validation (GREEN for T4)
- Define `LogRecord` TypedDict or dataclass
- Validate records before writing
- Add schema version to meta records

### Phase 5: Architecture Patterns (REFACTOR)
- Implement `LogRepository` protocol
- Implement `JSONLRepository` concrete class
- Add `ComponentDiscoveredEvent`, `RelationshipFoundEvent`
- Wire through message bus (optional if overkill for POC)

---

## Estimated Effort

| Phase | Task | Estimate | TDD Hours |
|-------|------|----------|-----------|
| RED | Write 15-20 failing tests | 2h | 2h |
| GREEN-1 | Type safety fixes | 1h | 0.5h verify |
| GREEN-2 | CC reduction (extract methods) | 2h | 0.5h verify |
| GREEN-3 | Exception handling | 1h | 0.5h verify |
| GREEN-4 | Schema validation | 1h | 0.5h verify |
| REFACTOR | Repository pattern | 1.5h | 0.5h verify |
| REFACTOR | Event pattern (if needed) | 1.5h | 0.5h verify |
| **Total** | | **10h** | **5h** |

---

## Success Criteria

1. ✅ All 15-20 TDD tests pass
2. ✅ Mypy `--strict` passes with no errors
3. ✅ Ruff/Pylint CC < 15 for all functions
4. ✅ No bare except clauses
5. ✅ JSONL log validates against schema
6. ✅ Existing functionality preserved (regression tests pass)

---

## Next Step

**Proceed to RED phase**: Create `tests/unit/test_observability_runner.py` with failing tests.
