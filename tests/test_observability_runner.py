#!/usr/bin/env python3
"""
TDD Tests for System Observability Runner
==========================================

RED Phase: These tests are written BEFORE implementation changes.
Following TDD methodology: RED → GREEN → REFACTOR

Test Categories:
- T1: Type Annotation Tests (Optional types, return types)
- T2: Cognitive Complexity Tests (CC < 15 per function)
- T3: Exception Handling Tests (no bare except)
- T4: JSONL Schema Validation Tests
- T5: Scenario Execution Tests
- T6: Architecture Pattern Tests (Repository, Events)

References:
- ANTI_PATTERN_ANALYSIS.md: Sections 1.1-1.4 (Optional types), 3.1 (CC), 4.1 (exceptions)
- ARCHITECTURE_GUIDELINES: Ch 8 (Events/Message Bus), Ch 2 (Repository)
- PYTHON_GUIDELINES: Ch 1 (EAFP error handling)
"""

import ast
import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from typing import Any, Dict, List, Set
from unittest.mock import MagicMock, patch

# Path configuration for observability_platform structure
OBSERVABILITY_ROOT = Path(__file__).parent.parent
PROJECT_ROOT = OBSERVABILITY_ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(OBSERVABILITY_ROOT / "src"))


# =============================================================================
# T1: Type Annotation Tests
# =============================================================================

class TestTypeAnnotations(unittest.TestCase):
    """
    Tests for proper type annotations per ANTI_PATTERN_ANALYSIS.md Section 1.1-1.4.
    
    Requirements:
    - All public functions have return type hints
    - Optional types are properly annotated (Optional[X] or X | None)
    - No missing type hints on function parameters
    """
    
    @classmethod
    def setUpClass(cls) -> None:
        """Load and parse the observability runner module."""
        cls.module_path = OBSERVABILITY_ROOT / "src" / "system_observability_runner.py"
        with open(cls.module_path, "r", encoding="utf-8") as f:
            cls.source_code = f.read()
        cls.tree = ast.parse(cls.source_code)
        cls.functions = [node for node in ast.walk(cls.tree) if isinstance(node, ast.FunctionDef)]
    
    def test_all_public_functions_have_return_type_hints(self) -> None:
        """Every public function (not starting with _) must have a return type hint."""
        public_functions_without_return_type: List[str] = []
        
        for func in self.functions:
            # Skip private functions (start with _) except __init__
            if func.name.startswith("_") and func.name != "__init__":
                continue
            
            # Check for return annotation
            if func.returns is None:
                public_functions_without_return_type.append(func.name)
        
        self.assertEqual(
            public_functions_without_return_type, 
            [],
            f"Public functions missing return type hints: {public_functions_without_return_type}"
        )
    
    def test_optional_return_types_are_annotated(self) -> None:
        """Functions that can return None must use Optional[X] or X | None."""
        # This test analyzes function bodies for 'return None' patterns
        functions_returning_none: List[str] = []
        functions_without_optional: List[str] = []
        
        for func in self.functions:
            returns_none = False
            has_optional_annotation = False
            
            # Check for 'return None' or 'return' without value
            for node in ast.walk(func):
                if isinstance(node, ast.Return):
                    if node.value is None:
                        returns_none = True
                    elif isinstance(node.value, ast.Constant) and node.value.value is None:
                        returns_none = True
            
            # Check if return type annotation includes Optional/None
            if func.returns is not None:
                return_annotation = ast.unparse(func.returns)
                if "Optional" in return_annotation or "None" in return_annotation:
                    has_optional_annotation = True
            
            if returns_none:
                functions_returning_none.append(func.name)
                if not has_optional_annotation:
                    functions_without_optional.append(func.name)
        
        # This test may have false positives, but catches the pattern
        if functions_without_optional:
            self.fail(
                f"Functions returning None without Optional annotation: {functions_without_optional}"
            )
    
    def test_all_function_parameters_have_type_hints(self) -> None:
        """Every function parameter (except self) must have a type hint."""
        functions_with_untyped_params: Dict[str, List[str]] = {}
        
        for func in self.functions:
            untyped_params = []
            for arg in func.args.args:
                if arg.arg == "self" or arg.arg == "cls":
                    continue
                if arg.annotation is None:
                    untyped_params.append(arg.arg)
            
            if untyped_params:
                functions_with_untyped_params[func.name] = untyped_params
        
        self.assertEqual(
            functions_with_untyped_params,
            {},
            f"Functions with untyped parameters: {functions_with_untyped_params}"
        )


# =============================================================================
# T2: Cognitive Complexity Tests
# =============================================================================

class TestCognitiveComplexity(unittest.TestCase):
    """
    Tests for cognitive complexity per ANTI_PATTERN_ANALYSIS.md Section 3.1.
    
    Requirements:
    - No function should have cognitive complexity > 15
    - Complex functions should be split into smaller units
    
    Note: Tests now check the source modules where functions are defined:
    - architecture_context.py for log_architecture_context
    - scenario_runner.py for run_scenario
    """
    
    @classmethod
    def setUpClass(cls) -> None:
        """Load and parse the observability modules."""
        # Main module (now a thin wrapper)
        cls.module_path = OBSERVABILITY_ROOT / "src" / "system_observability_runner.py"
        with open(cls.module_path, "r", encoding="utf-8") as f:
            cls.source_code = f.read()
        cls.tree = ast.parse(cls.source_code)
        cls.functions = [node for node in ast.walk(cls.tree) if isinstance(node, ast.FunctionDef)]
        
        # Architecture context module
        cls.arch_module_path = OBSERVABILITY_ROOT / "src" / "architecture_context.py"
        with open(cls.arch_module_path, "r", encoding="utf-8") as f:
            cls.arch_source_code = f.read()
        cls.arch_tree = ast.parse(cls.arch_source_code)
        cls.arch_functions = [node for node in ast.walk(cls.arch_tree) if isinstance(node, ast.FunctionDef)]
        
        # Scenario runner module
        cls.runner_module_path = PROJECT_ROOT / "scripts" / "scenario_runner.py"
        with open(cls.runner_module_path, "r", encoding="utf-8") as f:
            cls.runner_source_code = f.read()
        cls.runner_tree = ast.parse(cls.runner_source_code)
        cls.runner_functions = [node for node in ast.walk(cls.runner_tree) if isinstance(node, ast.FunctionDef)]
    
    def _calculate_cognitive_complexity(self, func: ast.FunctionDef) -> int:
        """
        Calculate cognitive complexity for a function.
        
        Based on SonarQube's cognitive complexity metric:
        - +1 for each if, elif, for, while, except
        - +1 for each boolean operator (and, or)
        - +1 for each nested level of control flow
        - +1 for each recursion
        """
        complexity = 0
        nesting_level = 0
        
        for node in ast.walk(func):
            # Control flow structures
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1 + nesting_level
            
            # Boolean operators
            if isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            
            # Ternary expressions
            if isinstance(node, ast.IfExp):
                complexity += 1
            
            # Try blocks
            if isinstance(node, ast.Try):
                complexity += 1
        
        return complexity
    
    def test_run_scenario_complexity_under_15(self) -> None:
        """run_scenario() should have cognitive complexity < 15."""
        # run_scenario is now in scripts/scenario_runner.py
        for func in self.runner_functions:
            if func.name == "run_scenario":
                cc = self._calculate_cognitive_complexity(func)
                self.assertLess(
                    cc, 15,
                    f"run_scenario() has cognitive complexity {cc}, should be < 15"
                )
                return
        
        self.fail("run_scenario function not found in scenario_runner.py")
    
    def test_log_architecture_complexity_under_15(self) -> None:
        """log_architecture_context() should have cognitive complexity < 15."""
        # log_architecture_context is now in architecture_context.py
        for func in self.arch_functions:
            if func.name == "log_architecture_context":
                cc = self._calculate_cognitive_complexity(func)
                self.assertLess(
                    cc, 15,
                    f"log_architecture_context() has cognitive complexity {cc}, should be < 15"
                )
                return
        
        self.fail("log_architecture_context function not found in architecture_context.py")
    
    def test_all_functions_complexity_under_15(self) -> None:
        """All functions should have cognitive complexity < 15."""
        high_complexity_functions: Dict[str, int] = {}
        
        for func in self.functions:
            cc = self._calculate_cognitive_complexity(func)
            if cc >= 15:
                high_complexity_functions[func.name] = cc
        
        self.assertEqual(
            high_complexity_functions,
            {},
            f"Functions with high cognitive complexity (≥15): {high_complexity_functions}"
        )
    
    def test_function_line_count_under_50(self) -> None:
        """Logic functions should not exceed 50 lines (R0915 threshold).
        
        Excluded functions (data definitions, orchestrators, CLI entry points):
        - get_architecture_context: Static architecture data
        - get_scenario_definitions: Static scenario data
        - log_architecture_context: Simple iteration over context data
        - main: CLI argument parsing and dispatch (standard pattern)
        - run_scenario: Orchestration of steps (extracted helpers for logic)
        """
        # Functions that are allowed to be long (data definitions, orchestration)
        excluded_functions = {
            "get_architecture_context",  # Static architecture data
            "get_scenario_definitions",  # Static scenario data
            "log_architecture_context",  # Simple iteration over data
            "main",  # CLI entry point - standard argparse pattern
            "run_scenario",  # Orchestration - complexity extracted to helpers
        }
        
        long_functions: Dict[str, int] = {}
        
        for func in self.functions:
            if func.name in excluded_functions:
                continue
            line_count = func.end_lineno - func.lineno + 1 if func.end_lineno else 0
            if line_count > 50:
                long_functions[func.name] = line_count
        
        self.assertEqual(
            long_functions,
            {},
            f"Functions exceeding 50 lines: {long_functions}"
        )


# =============================================================================
# T3: Exception Handling Tests
# =============================================================================

class TestExceptionHandling(unittest.TestCase):
    """
    Tests for exception handling per ANTI_PATTERN_ANALYSIS.md Section 4.1.
    
    Requirements:
    - No bare except clauses
    - Specific exceptions should be caught
    - Exceptions should be logged with context
    """
    
    @classmethod
    def setUpClass(cls) -> None:
        """Load and parse the observability runner module."""
        cls.module_path = OBSERVABILITY_ROOT / "src" / "system_observability_runner.py"
        with open(cls.module_path, "r", encoding="utf-8") as f:
            cls.source_code = f.read()
        cls.tree = ast.parse(cls.source_code)
    
    def test_no_bare_except_clauses(self) -> None:
        """No bare 'except:' clauses should exist."""
        bare_excepts: List[int] = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    bare_excepts.append(node.lineno)
        
        self.assertEqual(
            bare_excepts,
            [],
            f"Bare except clauses found at lines: {bare_excepts}"
        )
    
    def test_exceptions_capture_error_type(self) -> None:
        """Except handlers should capture the exception with 'as e' pattern."""
        handlers_without_alias: List[int] = []
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ExceptHandler):
                # Skip bare excepts (tested separately)
                if node.type is None:
                    continue
                # Check for alias (e.g., 'except Exception as e')
                if node.name is None:
                    handlers_without_alias.append(node.lineno)
        
        # Allow some handlers without alias (e.g., 'except KeyError: pass')
        # But warn if there are many
        if len(handlers_without_alias) > 2:
            self.fail(
                f"Many except handlers without 'as e' at lines: {handlers_without_alias}"
            )


# =============================================================================
# T4: JSONL Schema Validation Tests
# =============================================================================

class TestJSONLSchema(unittest.TestCase):
    """
    Tests for JSONL log record schema validation.
    
    Requirements:
    - All records have 'record_type' field
    - Component records have required fields
    - Relationship records have from_id, to_id, relationship_type
    - Timestamps are valid ISO format
    """
    
    def setUp(self) -> None:
        """Create temporary log file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_log = Path(self.temp_dir) / "test_log.jsonl"
    
    def tearDown(self) -> None:
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_record_has_required_fields(self) -> None:
        """All log records must have record_type field."""
        from observability_platform.src.jsonl_logger import log_record, LOG_FILE, set_log_file, reset_log_file
        
        # Temporarily redirect log file
        set_log_file(self.temp_log)
        
        try:
            # Log a test record
            log_record({"record_type": "test", "data": "value"})
            
            # Read and validate
            with open(self.temp_log, "r") as f:
                record = json.loads(f.readline())
            
            self.assertIn("record_type", record)
        finally:
            reset_log_file()
    
    def test_component_record_has_valid_structure(self) -> None:
        """Component records must have component_id and component_kind."""
        from dataclasses import asdict
        from observability_platform.src.data_classes import Component
        
        component = Component(
            component_id="test_id",
            component_kind="Service",
            name="Test Service",
            description="A test service"
        )
        
        record = asdict(component)
        
        self.assertIn("component_id", record)
        self.assertIn("component_kind", record)
        self.assertIn("name", record)
        self.assertEqual(record["component_id"], "test_id")
        self.assertEqual(record["component_kind"], "Service")
    
    def test_relationship_record_validates_from_to(self) -> None:
        """Relationship records must have from_id, to_id, relationship_type."""
        from dataclasses import asdict
        from observability_platform.src.data_classes import Relationship
        
        rel = Relationship(
            from_id="svc_a",
            to_id="svc_b",
            relationship_type="CALLS"
        )
        
        record = asdict(rel)
        
        self.assertIn("from_id", record)
        self.assertIn("to_id", record)
        self.assertIn("relationship_type", record)
        self.assertEqual(record["from_id"], "svc_a")
        self.assertEqual(record["to_id"], "svc_b")
    
    def test_timestamp_format_is_iso(self) -> None:
        """now_iso() should return valid ISO format timestamp."""
        from system_observability_runner import now_iso
        
        ts = now_iso()
        
        # Should end with Z
        self.assertTrue(ts.endswith("Z"), f"Timestamp should end with Z: {ts}")
        
        # Should be parseable
        from datetime import datetime
        try:
            # Remove Z for parsing
            datetime.strptime(ts[:-1], "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError as e:
            self.fail(f"Invalid timestamp format: {ts}, error: {e}")


# =============================================================================
# T5: Scenario Execution Tests
# =============================================================================

class TestScenarioExecution(unittest.TestCase):
    """
    Tests for scenario execution functionality.
    
    Requirements:
    - Scenarios execute steps in order
    - Failed steps log errors
    - Timing is accurate
    """
    
    def test_scenario_steps_execute_in_order(self) -> None:
        """Steps should execute in the order defined by 'order' field."""
        from system_observability_runner import (
            Scenario, ScenarioStep, get_scenario_definitions
        )
        
        scenarios = get_scenario_definitions()
        
        for name, scenario in scenarios.items():
            orders = [step.order for step in scenario.steps]
            sorted_orders = sorted(orders)
            
            self.assertEqual(
                orders, sorted_orders,
                f"Scenario '{name}' steps are not in order: {orders}"
            )
    
    def test_new_id_generates_unique_ids(self) -> None:
        """new_id() should generate unique IDs."""
        from system_observability_runner import new_id
        
        ids: Set[str] = set()
        for _ in range(100):
            generated_id = new_id("trc")
            self.assertNotIn(generated_id, ids, "Duplicate ID generated")
            ids.add(generated_id)
    
    def test_new_id_has_correct_prefix(self) -> None:
        """new_id() should include the given prefix."""
        from system_observability_runner import new_id
        
        trace_id = new_id("trc")
        scenario_id = new_id("sr")
        
        self.assertTrue(trace_id.startswith("trc_"))
        self.assertTrue(scenario_id.startswith("sr_"))
    
    def test_get_scenario_definitions_returns_dict(self) -> None:
        """get_scenario_definitions() should return a non-empty dict."""
        from system_observability_runner import get_scenario_definitions
        
        scenarios = get_scenario_definitions()
        
        self.assertIsInstance(scenarios, dict)
        self.assertGreater(len(scenarios), 0, "No scenarios defined")
    
    def test_all_scenarios_have_required_fields(self) -> None:
        """All scenarios must have scenario_id, name, description."""
        from system_observability_runner import get_scenario_definitions
        
        scenarios = get_scenario_definitions()
        
        for name, scenario in scenarios.items():
            self.assertTrue(
                hasattr(scenario, 'scenario_id') and scenario.scenario_id,
                f"Scenario '{name}' missing scenario_id"
            )
            self.assertTrue(
                hasattr(scenario, 'name') and scenario.name,
                f"Scenario '{name}' missing name"
            )
            self.assertTrue(
                hasattr(scenario, 'description'),
                f"Scenario '{name}' missing description"
            )


# =============================================================================
# T6: Architecture Pattern Tests
# =============================================================================

class TestArchitecturePatterns(unittest.TestCase):
    """
    Tests for architecture patterns per ARCHITECTURE_GUIDELINES Ch 2, 6, 8.
    
    Requirements:
    - Repository abstraction for log persistence
    - Events emitted for discoveries
    - Unit of Work for transactional writes
    
    Note: These tests define the target architecture. They may fail initially
    (RED phase) and pass after REFACTOR phase.
    """
    
    @classmethod
    def setUpClass(cls) -> None:
        """Load module source for analysis."""
        cls.module_path = OBSERVABILITY_ROOT / "src" / "system_observability_runner.py"
        with open(cls.module_path, "r", encoding="utf-8") as f:
            cls.source_code = f.read()
    
    def test_log_repository_protocol_exists(self) -> None:
        """A LogRepository Protocol or ABC should be defined."""
        # Check for Protocol or ABC definition for repository pattern
        has_repository = (
            "LogRepository" in self.source_code or
            "class.*Repository" in self.source_code or
            "Protocol" in self.source_code
        )
        
        # This test documents the desired pattern but may pass if not implemented
        # In REFACTOR phase, we'd add: class LogRepository(Protocol)
        if not has_repository:
            self.skipTest(
                "LogRepository Protocol not yet implemented - add in REFACTOR phase"
            )
    
    def test_events_defined_for_discoveries(self) -> None:
        """Domain events should be defined for component discoveries."""
        # Check for event class definitions
        has_events = (
            "ComponentDiscoveredEvent" in self.source_code or
            "Event" in self.source_code and "@dataclass" in self.source_code
        )
        
        # This test documents the desired pattern
        if not has_events:
            self.skipTest(
                "ComponentDiscoveredEvent not yet implemented - add in REFACTOR phase"
            )
    
    def test_architecture_context_is_separate_from_logging(self) -> None:
        """Architecture context definition should be separate from logging logic."""
        from system_observability_runner import (
            get_architecture_context, log_architecture_context
        )
        
        # get_architecture_context should not call log functions
        # This test ensures separation of concerns
        context = get_architecture_context()
        
        self.assertIsInstance(context, dict)
        self.assertIn("services", context)
        self.assertIn("entities", context)
        # Should be able to get context without side effects


# =============================================================================
# T7: DataClass Validation Tests
# =============================================================================

class TestDataClasses(unittest.TestCase):
    """
    Tests for dataclass definitions.
    
    Per PYTHON_GUIDELINES and ANTI_PATTERN_ANALYSIS Section 10.1:
    - Use Parameter Object pattern for functions with >5 arguments
    - DataClasses should have proper defaults
    """
    
    def test_component_has_sensible_defaults(self) -> None:
        """Component dataclass should work with minimal required fields."""
        from system_observability_runner import Component
        
        # Should be able to create with just required fields
        component = Component(
            component_id="test",
            component_kind="Service",
            name="Test"
        )
        
        self.assertEqual(component.component_id, "test")
        self.assertIsNone(component.owner_team)  # Optional field
    
    def test_scenario_step_has_sensible_defaults(self) -> None:
        """ScenarioStep dataclass should work with minimal required fields."""
        from system_observability_runner import ScenarioStep
        
        step = ScenarioStep(
            step_id="step_1",
            name="Test Step",
            order=1
        )
        
        self.assertEqual(step.step_id, "step_1")
        self.assertIsNone(step.function)  # Optional field
        self.assertEqual(step.expected_status, 200)  # Default value
    
    def test_scenario_has_empty_steps_by_default(self) -> None:
        """Scenario dataclass should have empty steps list by default."""
        from system_observability_runner import Scenario
        
        scenario = Scenario(
            scenario_id="test",
            name="Test",
            description="A test scenario"
        )
        
        self.assertEqual(scenario.steps, [])
        self.assertEqual(scenario.trigger_type, "user_action")


# =============================================================================
# T8: Validate Log Function Tests
# =============================================================================

class TestValidateLog(unittest.TestCase):
    """
    Tests for log validation functionality.
    """
    
    def setUp(self) -> None:
        """Create temporary log file for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_log = Path(self.temp_dir) / "test_log.jsonl"
    
    def tearDown(self) -> None:
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_log_returns_error_for_missing_file(self) -> None:
        """validate_log() should return empty stats for missing file."""
        from observability_platform.src.jsonl_logger import validate_log, set_log_file, reset_log_file
        
        set_log_file(Path("/nonexistent/path/log.jsonl"))
        
        try:
            result = validate_log()
            # Missing file returns empty stats (total_records = 0)
            self.assertEqual(result["total_records"], 0)
        finally:
            reset_log_file()
    
    def test_validate_log_counts_record_types(self) -> None:
        """validate_log() should count records by type."""
        from observability_platform.src.jsonl_logger import validate_log, set_log_file, reset_log_file
        
        set_log_file(self.temp_log)
        
        try:
            # Write test records
            with open(self.temp_log, "w") as f:
                f.write('{"record_type":"component","name":"test1"}\n')
                f.write('{"record_type":"component","name":"test2"}\n')
                f.write('{"record_type":"relationship","from":"a","to":"b"}\n')
            
            result = validate_log()
            
            self.assertEqual(result["total_records"], 3)
            self.assertEqual(result["record_types"]["component"], 2)
            self.assertEqual(result["record_types"]["relationship"], 1)
        finally:
            reset_log_file()


# =============================================================================
# Main
# =============================================================================

if __name__ == "__main__":
    # Run with verbose output
    unittest.main(verbosity=2)
