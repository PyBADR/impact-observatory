#!/usr/bin/env python3
"""
CLI script for running seeded GCC scenarios and generating reports.
Provides command-line interface for scenario execution, validation, and output export.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scenarios.runner import ScenarioRunner
from seeds.scenario_seeds import list_scenario_ids, get_scenario_seed_by_id

logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    """Configure logging output."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def list_scenarios(args):
    """List all available seeded scenarios."""
    scenario_ids = list_scenario_ids()
    
    print("\n" + "=" * 70)
    print("Available GCC Seeded Scenarios (15 total)")
    print("=" * 70)
    
    for i, scenario_id in enumerate(sorted(scenario_ids), 1):
        seed = get_scenario_seed_by_id(scenario_id)
        print(f"\n{i:2d}. {scenario_id}")
        print(f"    Title:       {seed.title}")
        print(f"    Severity:    {seed.severity:.2f}")
        print(f"    Duration:    {seed.time_horizon_hours} hours")
        print(f"    Events:      {len(seed.inject_events)}")
        print(f"    Nodes:       {len(seed.affected_node_ids)}")
    
    print("\n" + "=" * 70)
    print(f"Total: {len(scenario_ids)} scenarios")
    print("=" * 70 + "\n")


def run_single_scenario(args):
    """Run a single scenario and display results."""
    scenario_id = args.scenario_id
    
    # Validate scenario exists
    try:
        seed = get_scenario_seed_by_id(scenario_id)
    except ValueError:
        logger.error(f"Scenario '{scenario_id}' not found")
        print(f"\nError: Scenario '{scenario_id}' not found")
        print(f"Run 'python run_scenario.py --list' to see available scenarios\n")
        sys.exit(1)
    
    # Initialize runner
    expected_outputs_dir = Path(__file__).parent.parent / "seeds" / "expected_outputs"
    runner = ScenarioRunner(expected_outputs_dir=str(expected_outputs_dir))
    
    logger.info(f"Running scenario: {scenario_id}")
    print(f"\n{'=' * 70}")
    print(f"Running: {seed.title}")
    print(f"{'=' * 70}\n")
    
    # Execute scenario
    try:
        result = runner.run_seeded_scenario(scenario_id)
        logger.info(f"Scenario '{scenario_id}' executed successfully")
    except Exception as e:
        logger.error(f"Failed to execute scenario '{scenario_id}': {e}")
        print(f"Error: Failed to execute scenario: {e}\n")
        sys.exit(1)
    
    # Validate against expected outputs
    validation_passed, validation_errors = runner.validate_against_expected(scenario_id, result)
    
    # Display results
    print(f"Scenario ID:              {result.scenario_id}")
    print(f"Title:                    {seed.title}")
    print(f"Description:              {seed.description}\n")
    
    print("Risk Metrics:")
    print(f"  Risk Increase:          {result.risk_increase:.4f}")
    print(f"  Confidence Adjustment:  {result.confidence_adjustment:.4f}")
    print(f"  System Stress Level:    {result.system_stress_level:.4f}\n")
    
    print("Impact Metrics:")
    print(f"  Affected Ports:         {result.affected_ports}")
    print(f"  Affected Airports:      {result.affected_airports}")
    print(f"  Affected Corridors:     {result.affected_corridors}")
    print(f"  Total Nodes Affected:   {result.nodes_affected_total}")
    print(f"  Critical Nodes:         {result.critical_nodes_impacted}\n")
    
    print("Cascade Metrics:")
    print(f"  Cascade Depth:          {result.cascade_depth}")
    print(f"  Propagation Factor:     {result.propagation_factor:.4f}")
    print(f"  Cascade Events:         {len(result.cascade_events)}\n")
    
    print("Systemic Impacts:")
    print(f"  Insurance Surge:        {result.insurance_surge:.4f}")
    print(f"  Logistics Delay:        {result.logistics_delay_hours:.2f} hours")
    print(f"  Time Horizon:           {result.time_horizon_status} hours\n")
    
    print("Validation:")
    print(f"  Status:                 {'PASSED' if validation_passed else 'FAILED'}")
    if not validation_passed:
        print(f"  Errors:")
        for error in validation_errors:
            print(f"    - {error}")
    print()
    
    # Export to JSON if requested
    if args.json:
        output_file = args.json
        results = {scenario_id: result}
        runner.export_results_json(results, output_file)
        logger.info(f"Results exported to {output_file}")
        print(f"Results exported to: {output_file}\n")
    
    print("=" * 70 + "\n")
    
    # Return non-zero exit code if validation failed
    if not validation_passed:
        sys.exit(1)


def run_all_scenarios(args):
    """Run all 15 scenarios and generate comprehensive report."""
    # Initialize runner
    expected_outputs_dir = Path(__file__).parent.parent / "seeds" / "expected_outputs"
    runner = ScenarioRunner(expected_outputs_dir=str(expected_outputs_dir))
    
    logger.info("Running all 15 scenarios")
    print(f"\n{'=' * 70}")
    print("Running All GCC Seeded Scenarios (15 total)")
    print(f"{'=' * 70}\n")
    
    # Execute all scenarios
    try:
        results = runner.run_all_scenarios()
        logger.info("All scenarios executed successfully")
    except Exception as e:
        logger.error(f"Failed to execute scenarios: {e}")
        print(f"Error: Failed to execute scenarios: {e}\n")
        sys.exit(1)
    
    # Validation summary
    validation_summary = {}
    all_passed = True
    
    for scenario_id, result in results.items():
        validation_passed, _ = runner.validate_against_expected(scenario_id, result)
        validation_summary[scenario_id] = validation_passed
        if not validation_passed:
            all_passed = False
    
    # Display summary
    print("\nScenario Execution Summary:")
    print(f"{'Scenario ID':<30} {'Risk Increase':<15} {'Cascade Depth':<15} {'Valid':<10}")
    print("-" * 70)
    
    for scenario_id, result in sorted(results.items()):
        valid_str = "PASS" if validation_summary[scenario_id] else "FAIL"
        print(f"{scenario_id:<30} {result.risk_increase:<15.4f} {result.cascade_depth:<15d} {valid_str:<10}")
    
    print("-" * 70)
    
    # Aggregate statistics
    all_risks = [r.risk_increase for r in results.values()]
    all_cascades = [r.cascade_depth for r in results.values()]
    
    print(f"\nAggregate Statistics:")
    print(f"  Total Scenarios:        {len(results)}")
    print(f"  Passed Validation:      {sum(validation_summary.values())}/{len(results)}")
    print(f"  Risk Increase - Min:    {min(all_risks):.4f}")
    print(f"  Risk Increase - Max:    {max(all_risks):.4f}")
    print(f"  Risk Increase - Avg:    {sum(all_risks)/len(all_risks):.4f}")
    print(f"  Cascade Depth - Min:    {min(all_cascades)}")
    print(f"  Cascade Depth - Max:    {max(all_cascades)}")
    print(f"  Cascade Depth - Avg:    {sum(all_cascades)/len(all_cascades):.2f}\n")
    
    # Export to JSON if requested
    if args.json:
        output_file = args.json
        runner.export_results_json(results, output_file)
        logger.info(f"Results exported to {output_file}")
        print(f"Results exported to: {output_file}\n")
    
    print("=" * 70 + "\n")
    
    # Return non-zero exit code if any validation failed
    if not all_passed:
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run seeded GCC infrastructure disruption scenarios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available scenarios
  python run_scenario.py --list
  
  # Run a single scenario
  python run_scenario.py --scenario hormuz_closure
  
  # Run a scenario and export results to JSON
  python run_scenario.py --scenario combined_disruption --json results.json
  
  # Run all scenarios
  python run_scenario.py --all
  
  # Run all scenarios with JSON export and verbose logging
  python run_scenario.py --all --json all_results.json --verbose
        """
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available seeded scenarios"
    )
    
    parser.add_argument(
        "--scenario",
        type=str,
        metavar="SCENARIO_ID",
        help="Run a specific scenario by ID"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 15 scenarios"
    )
    
    parser.add_argument(
        "--json",
        type=str,
        metavar="FILE",
        help="Export results to JSON file"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging output"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Route to appropriate command
    if args.list:
        list_scenarios(args)
    elif args.scenario:
        run_single_scenario(args)
    elif args.all:
        run_all_scenarios(args)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
