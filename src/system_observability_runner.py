#!/usr/bin/env python3
"""
System Observability Runner
===========================

DEPRECATED: This file is maintained for backward compatibility.

The functionality has been refactored to:
- observability_platform/src/jsonl_logger.py - JSONL logging utilities
- observability_platform/src/data_classes.py - Dataclass definitions
- observability_platform/src/architecture_context.py - Architecture definitions
- scripts/scenario_runner.py - Scenario execution engine
- scripts/scenarios/ - Scenario definitions

Usage:
    # Preferred: use the new scenario_runner.py directly
    python scripts/scenario_runner.py --run extraction_evaluation
    python scripts/scenario_runner.py --list
    python scripts/scenario_runner.py --log-architecture
    python scripts/scenario_runner.py --validate

    # Legacy: this file still works for backward compatibility
    python observability_platform/src/system_observability_runner.py --run-scenario extraction_evaluation

Reference: observability_platform/DESIGN_DOCUMENT.md
"""

import argparse
import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Re-export from new modules for backward compatibility
from observability_platform.src.jsonl_logger import (
    LOG_FILE,
    SCHEMA_VERSION,
    GENERATOR_ID,
    ensure_log_directory,
    log_record,
    log_records,
    new_id,
    now_iso,
    validate_log,
)

from observability_platform.src.data_classes import (
    Component,
    EntityDefinition,
    ProcessDefinition,
    Relationship,
    Scenario,
    ScenarioStep,
    StepExecutionResult,
)

from observability_platform.src.architecture_context import (
    get_architecture_context,
    get_runtime_context,
    log_architecture_context,
)

# Import scenario runner functionality
from scripts.scenario_runner import (
    get_scenario_definitions,
    run_scenario,
    log_state_transition,
    print_log_summary,
)


def main() -> None:
    """
    Legacy CLI entry point.
    
    Maps old CLI arguments to new scenario_runner.py functionality.
    """
    parser = argparse.ArgumentParser(
        description="System Observability Runner - DEPRECATED, use scripts/scenario_runner.py"
    )
    
    parser.add_argument(
        "--run-scenario",
        choices=["extraction_evaluation", "single_extraction", "enrichment_pipeline"],
        help="Run a specific scenario"
    )
    
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run all defined scenarios"
    )
    
    parser.add_argument(
        "--log-architecture",
        action="store_true",
        help="Log architecture context only (services, entities, etc.)"
    )
    
    parser.add_argument(
        "--validate-log",
        action="store_true",
        help="Validate and summarize the log file"
    )
    
    parser.add_argument(
        "--clear-log",
        action="store_true",
        help="Clear the existing log file"
    )
    
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List all defined scenarios"
    )
    
    args = parser.parse_args()
    
    # Show deprecation warning
    print("⚠️  DEPRECATED: This CLI is deprecated. Use: python scripts/scenario_runner.py instead\n")
    
    if args.clear_log:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
            print(f"✅ Cleared log file: {LOG_FILE}")
        else:
            print(f"ℹ️  Log file does not exist: {LOG_FILE}")
        return
    
    if args.validate_log:
        print_log_summary()
        return
    
    if args.list_scenarios:
        scenarios = get_scenario_definitions()
        print("\n📋 Available Scenarios:")
        print("=" * 60)
        for name, scenario in scenarios.items():
            print(f"\n  {name}:")
            print(f"    Name: {scenario.name}")
            print(f"    Description: {scenario.description}")
            print(f"    Steps: {len(scenario.steps)}")
        return
    
    if args.log_architecture:
        log_architecture_context()
        print(f"\n✅ Architecture context logged to: {LOG_FILE}")
        return
    
    if args.run_scenario:
        log_architecture_context()
        scenarios = get_scenario_definitions()
        scenario = scenarios.get(args.run_scenario)
        
        if not scenario:
            print(f"❌ Unknown scenario: {args.run_scenario}")
            return
        
        run_scenario(scenario)
        print(f"\n✅ Scenario logged to: {LOG_FILE}")
        return
    
    if args.run_all:
        log_architecture_context()
        scenarios = get_scenario_definitions()
        
        for name, scenario in scenarios.items():
            print(f"\n{'='*60}")
            run_scenario(scenario)
        
        print(f"\n✅ All scenarios logged to: {LOG_FILE}")
        print_log_summary()
        return
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()
