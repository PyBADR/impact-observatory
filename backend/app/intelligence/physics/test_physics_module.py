"""
Integration tests for the physics-inspired intelligence module.

Demonstrates each module's functionality with realistic GCC scenarios.
All functions are pure and testable—no side effects.
"""

import numpy as np
from datetime import datetime, timedelta

from threat_field import ThreatSource, ThreatField
from flow_field import FlowVector, FlowField
from pressure import PressureNode, compute_pressure, accumulate_pressure, system_pressure
from shockwave import ShockEvent, ShockwaveEngine
from diffusion import diffuse_threat, compute_laplacian, DiffusionResult
from routing import compute_route_cost, find_lowest_cost_route, RouteResult
from system_stress import compute_system_stress, StressLevel


def test_threat_field():
    """Test threat field modeling with multiple sources."""
    print("\n=== THREAT FIELD TEST ===")

    # Create two threat sources (e.g., conflict zones)
    source1 = ThreatSource(
        lat=30.0, lon=40.0, magnitude=0.8, decay_lambda=0.1, event_id="conflict_1"
    )
    source2 = ThreatSource(
        lat=32.0, lon=42.0, magnitude=0.5, decay_lambda=0.15, event_id="conflict_2"
    )

    field = ThreatField()
    field.add_source(source1)
    field.add_source(source2)

    # Evaluate at a point between the sources
    threat_between = field.evaluate(31.0, 41.0)
    print(f"Threat at (31.0, 41.0): {threat_between:.4f}")

    # Evaluate at origin of first source
    threat_at_origin = field.evaluate(30.0, 40.0)
    print(f"Threat at origin (30.0, 40.0): {threat_at_origin:.4f}")

    # Generate 2D threat grid
    grid = field.evaluate_grid((28, 34), (38, 44), resolution=10)
    print(f"Threat grid shape: {grid.shape}, max: {grid.max():.4f}, min: {grid.min():.4f}")

    # Find high-threat contours
    contours = field.get_contours(threshold=0.3)
    print(f"Points above threat threshold 0.3: {len(contours)}")

    return True


def test_flow_field():
    """Test flow field and congestion modeling."""
    print("\n=== FLOW FIELD TEST ===")

    # Create flows representing air and sea corridors
    flow1 = FlowVector(
        origin_lat=30.0, origin_lon=40.0,
        dest_lat=35.0, dest_lon=45.0,
        magnitude=0.7, flow_type="air"
    )
    flow2 = FlowVector(
        origin_lat=31.0, origin_lon=41.0,
        dest_lat=34.0, dest_lon=44.0,
        magnitude=0.5, flow_type="sea"
    )

    field = FlowField()
    field.add_flow(flow1)
    field.add_flow(flow2)

    # Compute density at a point
    density = field.compute_density(lat=32.5, lon=42.5, radius_km=100.0)
    print(f"Flow density at (32.5, 42.5): {density:.4f}")

    # Compute corridor congestion
    congestion = field.compute_congestion("corridor_1", [flow1, flow2], base_capacity=1.0)
    print(f"Corridor congestion: {congestion:.4f}")

    # Generate flow density grid
    grid = field.evaluate_grid((28, 36), (38, 46), resolution=8, radius_km=100.0)
    print(f"Flow density grid shape: {grid.shape}, max: {grid.max():.4f}")

    return True


def test_pressure():
    """Test pressure and load redistribution."""
    print("\n=== PRESSURE TEST ===")

    # Create nodes (airports, ports) with capacity constraints
    nodes = [
        PressureNode(node_id="airport_1", node_type="airport", base_capacity=100.0, current_load=75.0),
        PressureNode(node_id="port_1", node_type="port", base_capacity=50.0, current_load=40.0),
        PressureNode(node_id="corridor_1", node_type="corridor", base_capacity=80.0, current_load=30.0),
    ]

    # Compute individual pressures
    pressures = {}
    for node in nodes:
        p = compute_pressure(node)
        pressures[node.node_id] = p
        print(f"{node.node_id}: pressure={p:.3f}")

    # Simulate load redistribution when routes are disrupted
    disrupted = ["route_a", "route_b"]
    adjusted_pressures = accumulate_pressure(nodes, disrupted, reroute_factor=1.3)
    print(f"\nAfter disruption:")
    for node_id, p in adjusted_pressures.items():
        print(f"  {node_id}: adjusted pressure={p:.3f}")

    # Compute system-level pressure
    sys_p = system_pressure(adjusted_pressures)
    print(f"\nSystem pressure: {sys_p:.3f}")

    return True


def test_shockwave():
    """Test shockwave propagation modeling."""
    print("\n=== SHOCKWAVE TEST ===")

    # Create a shock event (e.g., major incident)
    shock = ShockEvent(
        origin_lat=30.0, origin_lon=40.0,
        magnitude=0.9, propagation_speed_kmh=200.0,
        start_time=datetime(2026, 3, 31, 12, 0, 0)
    )

    engine = ShockwaveEngine(decay_lambda=0.05)
    engine.add_shock(shock)

    # Evaluate shock intensity at different times and locations
    t0 = shock.start_time
    t1 = shock.start_time + timedelta(hours=1)
    t2 = shock.start_time + timedelta(hours=2)

    # At origin, immediately after start
    intensity_at_origin = engine.evaluate_at(30.0, 40.0, t0)
    print(f"Shock intensity at origin (t=0h): {intensity_at_origin:.4f}")

    # 200 km away after 1 hour (wavefront just arrives)
    intensity_200km = engine.evaluate_at(31.8, 41.8, t1)
    print(f"Shock intensity 200 km away (t=1h): {intensity_200km:.4f}")

    # Evaluate impact on multiple targets
    targets = [
        (30.5, 40.5, "target_1"),
        (32.0, 42.0, "target_2"),
        (33.0, 43.0, "target_3"),
    ]
    impacts = engine.propagate(targets, t1)
    print(f"\nImpacts at t=1h:")
    for target_id, impact in impacts.items():
        print(f"  {target_id}: {impact:.4f}")

    return True


def test_diffusion():
    """Test threat diffusion across regional network."""
    print("\n=== DIFFUSION TEST ===")

    # Create a 5-region network (e.g., regions in a transport corridor)
    # Adjacency: 0-1-2-3-4 (linear chain)
    adjacency = np.array([
        [0, 1, 0, 0, 0],
        [1, 0, 1, 0, 0],
        [0, 1, 0, 1, 0],
        [0, 0, 1, 0, 1],
        [0, 0, 0, 1, 0],
    ], dtype=float)

    # Initial threat concentrated in region 0
    initial_threat = np.array([1.0, 0.0, 0.0, 0.0, 0.0])

    # Run diffusion simulation
    result = diffuse_threat(
        adjacency, initial_threat,
        diffusion_coefficient=0.2, dt=0.5, steps=10
    )

    print(f"Initial threat: {initial_threat}")
    print(f"Final threat: {result.final_state}")
    print(f"Equilibrium reached: {result.equilibrium_reached}")
    print(f"Diffusion history steps: {len(result.history)}")

    # Verify that threat spreads (first region decreases)
    assert result.final_state[0] < initial_threat[0], "Threat should spread from region 0"

    return True


def test_routing():
    """Test threat-aware route planning."""
    print("\n=== ROUTING TEST ===")

    # Create threat field
    source = ThreatSource(lat=31.0, lon=41.0, magnitude=0.8, decay_lambda=0.1, event_id="hazard")
    threat_field = ThreatField()
    threat_field.add_source(source)

    # Define candidate routes (each bypasses the threat differently)
    route_1 = [(30.0, 40.0), (30.5, 40.5), (31.0, 41.0), (32.0, 42.0)]  # Through threat
    route_2 = [(30.0, 40.0), (30.5, 39.5), (31.0, 39.5), (32.0, 42.0)]  # South detour
    route_3 = [(30.0, 40.0), (30.5, 42.5), (31.0, 42.5), (32.0, 42.0)]  # North detour

    # Compute costs
    cost1, threat1 = compute_route_cost(route_1, threat_field, base_cost=1.0)
    cost2, threat2 = compute_route_cost(route_2, threat_field, base_cost=1.2)  # Longer base cost
    cost3, threat3 = compute_route_cost(route_3, threat_field, base_cost=1.1)

    print(f"Route 1 (through threat): total={cost1:.4f}, threat={threat1:.4f}")
    print(f"Route 2 (south detour): total={cost2:.4f}, threat={threat2:.4f}")
    print(f"Route 3 (north detour): total={cost3:.4f}, threat={threat3:.4f}")

    # Find best route
    routes = [route_1, route_2, route_3]
    route_ids = ["direct", "south", "north"]
    best = find_lowest_cost_route((30, 40), (32, 42), routes, threat_field, route_ids=route_ids)

    print(f"\nBest route: {best.route_id} (ranking {best.ranking}), cost={best.total_cost:.4f}")

    return True


def test_system_stress():
    """Test aggregate system stress computation."""
    print("\n=== SYSTEM STRESS TEST ===")

    # Define system state
    pressures = {
        "airport_1": 0.6,
        "airport_2": 0.5,
        "port_1": 0.8,
    }

    congestion_scores = {
        "air_corridor_1": 0.4,
        "sea_corridor_1": 0.3,
    }

    unresolved_disruptions = 2
    uncertainty = 0.15

    # Compute system stress
    result = compute_system_stress(
        pressures, congestion_scores, unresolved_disruptions, uncertainty
    )

    print(f"System stress score: {result.stress_score:.3f}")
    print(f"Stress level: {result.level.value}")
    print(f"Narrative: {result.narrative}")
    print(f"Components: {result.components}")

    # Test with higher stress
    result_critical = compute_system_stress(
        {f"node_{i}": 0.9 for i in range(5)},
        {f"corridor_{i}": 0.85 for i in range(4)},
        unresolved_disruptions=5,
        uncertainty=0.9
    )
    print(f"\nCritical scenario: {result_critical.level.value}, score={result_critical.stress_score:.3f}")

    return True


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("PHYSICS-INSPIRED INTELLIGENCE MODULE - INTEGRATION TESTS")
    print("=" * 60)

    tests = [
        ("Threat Field", test_threat_field),
        ("Flow Field", test_flow_field),
        ("Pressure", test_pressure),
        ("Shockwave", test_shockwave),
        ("Diffusion", test_diffusion),
        ("Routing", test_routing),
        ("System Stress", test_system_stress),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, "PASS"))
        except Exception as e:
            results.append((name, f"FAIL: {e}"))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, result in results:
        status = "✓" if result == "PASS" else "✗"
        print(f"{status} {name}: {result}")

    all_pass = all(result == "PASS" for _, result in results)
    return all_pass


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
