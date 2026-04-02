"""Mesa agent-based simulation for GCC scenario modeling.

Provides a Mesa-based behavioral simulation layer that models GCC graph nodes
as autonomous agents. Each agent updates its risk based on neighbor pressure,
applies temporal decay, and detects congestion thresholds using the canonical
GCC coefficients from math_core/gcc_weights.py.

This module is the *behavior/scenario simulation engine*, NOT the foundational
data layer. It wraps the existing GraphState and produces time-series risk,
pressure, and disruption trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import mesa
import networkx as nx
import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    SHOCKWAVE,
    PRESSURE,
    AssetClass,
    RISK_WEIGHTS_BY_ASSET,
    LAMBDA_T_KINETIC,
)
from src.engines.scenario.engine import GraphState


# ---------------------------------------------------------------------------
# Constants derived from GCC weights
# ---------------------------------------------------------------------------
_ALPHA = SHOCKWAVE.alpha   # 0.58 — adjacency propagation coefficient
_BETA = SHOCKWAVE.beta     # 0.92 — shock sensitivity
_DELTA = SHOCKWAVE.delta   # 0.47 — external perturbation weight

_RHO = PRESSURE.rho        # 0.72 — pressure persistence
_KAPPA = PRESSURE.kappa    # 0.18 — pressure inflow coefficient
_OMEGA = PRESSURE.omega    # 0.14 — pressure outflow coefficient
_XI = PRESSURE.xi          # 0.30 — pressure shock coefficient

_CONGESTION_THRESHOLD = 0.70  # pressure above this => congested
_CONVERGENCE_EPSILON = 1e-4   # risk delta norm for convergence
_DECAY_RATE = LAMBDA_T_KINETIC  # 0.015 per step temporal decay


# ---------------------------------------------------------------------------
# Layer-to-AssetClass mapping (matches seed_data.py layer names)
# ---------------------------------------------------------------------------
_LAYER_TO_ASSET: dict[str, AssetClass] = {
    "geography": AssetClass.SOCIETY,
    "infrastructure": AssetClass.INFRASTRUCTURE,
    "economy": AssetClass.ECONOMY,
    "finance": AssetClass.FINANCE,
    "society": AssetClass.SOCIETY,
}


def _infer_asset_class(node: dict[str, Any]) -> AssetClass:
    """Infer AssetClass from node metadata."""
    layer = node.get("layer", "")
    node_id = node.get("id", "")

    # Specific overrides based on node id patterns
    if "_apt" in node_id or node_id == "airspace":
        return AssetClass.AIRPORT
    if node_id in ("jebel_ali", "ras_tanura", "shuwaikh", "hamad_port"):
        return AssetClass.SEAPORT
    if node_id == "hormuz":
        return AssetClass.MARITIME_CORRIDOR
    if node_id == "shipping":
        return AssetClass.MARITIME_CORRIDOR

    return _LAYER_TO_ASSET.get(layer, AssetClass.INFRASTRUCTURE)


# ---------------------------------------------------------------------------
# MesaSimulationResult dataclass
# ---------------------------------------------------------------------------
@dataclass
class MesaSimulationResult:
    """Complete result of a Mesa agent-based simulation run."""

    risk_history: list[NDArray[np.float64]]
    pressure_history: list[NDArray[np.float64]]
    system_energy_history: list[float]
    final_state: dict[str, NDArray[np.float64]]
    congestion_events: list[tuple[int, str, float]]
    converged: bool
    steps_run: int


# ---------------------------------------------------------------------------
# GCCNodeAgent
# ---------------------------------------------------------------------------
class GCCNodeAgent(mesa.Agent):
    """Agent representing a single node in the GCC intelligence graph.

    Each agent carries its own risk, disruption, pressure, and capacity
    state. On each step it:
      1. Gathers neighbor pressure via the adjacency graph.
      2. Updates risk using the shockwave equation:
             R_new = alpha * neighbor_risk_avg + beta * shock + delta * external
         then applies temporal decay.
      3. Accumulates pressure:
             P_new = rho * P_old + kappa * inflow - omega * outflow + xi * shock
      4. Checks whether pressure exceeds the congestion threshold.
    """

    def __init__(
        self,
        model: GCCIntelligenceModel,
        node_id: str,
        asset_class: AssetClass,
        initial_risk: float = 0.05,
        initial_pressure: float = 0.10,
        capacity: float = 1.0,
    ) -> None:
        super().__init__(model)
        self.node_id: str = node_id
        self.asset_class: AssetClass = asset_class

        self.risk: float = initial_risk
        self.disruption: float = 0.0
        self.pressure: float = initial_pressure
        self.capacity: float = capacity

        # External shock injected from outside (reset each step)
        self.shock: float = 0.0
        # External perturbation (persistent)
        self.external: float = 0.0

    @property
    def agent_type(self) -> str:
        return "node"

    # ---- helpers ---------------------------------------------------------

    def _neighbor_agents(self) -> list[GCCNodeAgent]:
        """Return agents connected to this node in the graph."""
        g: nx.Graph = self.model.G
        nid = self.node_id
        if nid not in g:
            return []
        neighbors = []
        for nbr_id in g.neighbors(nid):
            agent = self.model.agent_map.get(nbr_id)
            if agent is not None:
                neighbors.append(agent)
        return neighbors

    def _weighted_neighbor_risk(self) -> float:
        """Weighted average risk from neighbors using edge weights."""
        g: nx.Graph = self.model.G
        nid = self.node_id
        total_weight = 0.0
        weighted_risk = 0.0
        for nbr_id in g.neighbors(nid):
            agent = self.model.agent_map.get(nbr_id)
            if agent is None:
                continue
            edge_data = g.edges[nid, nbr_id]
            w = edge_data.get("weight", 1.0)
            weighted_risk += agent.risk * w
            total_weight += w
        if total_weight == 0.0:
            return 0.0
        return weighted_risk / total_weight

    # ---- step ------------------------------------------------------------

    def step(self) -> None:
        """Single simulation step for this agent."""
        # 1. Neighbor risk influence
        neighbor_risk = self._weighted_neighbor_risk()

        # 2. Risk update: shockwave equation
        new_risk = (
            _ALPHA * neighbor_risk
            + _BETA * self.shock
            + _DELTA * self.external
        )
        # Temporal decay on current risk
        decayed_current = self.risk * (1.0 - _DECAY_RATE)
        # Take the max of propagated risk and decayed existing risk
        self.risk = float(np.clip(max(new_risk, decayed_current), 0.0, 1.0))

        # 3. Pressure accumulation
        neighbors = self._neighbor_agents()
        inflow = sum(n.risk for n in neighbors) / max(len(neighbors), 1)
        outflow = self.risk * (1.0 - self.risk)  # higher risk => less outflow
        self.pressure = float(np.clip(
            _RHO * self.pressure
            + _KAPPA * inflow
            - _OMEGA * outflow
            + _XI * self.shock,
            0.0,
            1.0,
        ))

        # 4. Disruption derived from risk and pressure
        self.disruption = float(np.clip(
            0.6 * self.risk + 0.4 * self.pressure,
            0.0,
            1.0,
        ))

        # 5. Decay shock (shocks are impulses, not persistent)
        self.shock = 0.0


# ---------------------------------------------------------------------------
# GCCIntelligenceModel
# ---------------------------------------------------------------------------
class GCCIntelligenceModel(mesa.Model):
    """Mesa model representing the GCC intelligence graph.

    Builds a NetworkX graph from the node/edge lists and populates it
    with GCCNodeAgent instances. Provides methods to inject shocks,
    run steps, and extract system state.
    """

    def __init__(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        shock_config: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.shock_config = shock_config or {}
        self._congestion_events: list[tuple[int, str, float]] = []
        self._step_count: int = 0

        # Build NetworkX graph
        self.G: nx.Graph = nx.Graph()
        node_lookup: dict[str, dict[str, Any]] = {}
        for n in nodes:
            nid = n["id"]
            self.G.add_node(nid, **n)
            node_lookup[nid] = n

        for e in edges:
            src, tgt = e["source"], e["target"]
            if src in node_lookup and tgt in node_lookup:
                self.G.add_edge(
                    src, tgt,
                    weight=e.get("weight", 1.0),
                    polarity=e.get("polarity", 1),
                    category=e.get("category", ""),
                )

        # Create agents
        self.agent_map: dict[str, GCCNodeAgent] = {}
        self.node_ids: list[str] = []

        for nid, ndata in node_lookup.items():
            if nid not in self.G:
                continue
            asset_class = _infer_asset_class(ndata)
            # Select specialized agent type based on node role
            agent_cls = _NODE_TO_AGENT_TYPE.get(nid, GCCNodeAgent)
            agent = agent_cls(
                model=self,
                node_id=nid,
                asset_class=asset_class,
                initial_risk=0.05,
                initial_pressure=0.10,
                capacity=1.0,
            )
            self.agent_map[nid] = agent
            self.node_ids.append(nid)

    @property
    def n_nodes(self) -> int:
        return len(self.node_ids)

    # ---- shock injection -------------------------------------------------

    def inject_shock(
        self,
        node_ids: list[str],
        severity: float,
    ) -> None:
        """Inject an external shock into one or more nodes.

        The shock is applied as an impulse: it affects the next step()
        then decays to zero.
        """
        clamped = float(np.clip(severity, 0.0, 1.0))
        for nid in node_ids:
            agent = self.agent_map.get(nid)
            if agent is not None:
                agent.shock = clamped
                agent.external = clamped * 0.5  # persistent but weaker

    # ---- step ------------------------------------------------------------

    def step(self) -> None:
        """Advance the simulation by one step.

        All agents update in shuffled order (Mesa default). After stepping,
        congestion detection runs.
        """
        self._step_count += 1

        # Step all agents
        agents = list(self.agent_map.values())
        self.random.shuffle(agents)
        for agent in agents:
            agent.step()

        # Detect congestion
        for agent in self.agent_map.values():
            if agent.pressure > _CONGESTION_THRESHOLD:
                self._congestion_events.append(
                    (self._step_count, agent.node_id, agent.pressure)
                )

    # ---- state extraction ------------------------------------------------

    def get_system_state(self) -> dict[str, NDArray[np.float64]]:
        """Return current risk, disruption, and pressure as numpy vectors."""
        n = self.n_nodes
        risk = np.zeros(n, dtype=np.float64)
        disruption = np.zeros(n, dtype=np.float64)
        pressure = np.zeros(n, dtype=np.float64)

        for i, nid in enumerate(self.node_ids):
            agent = self.agent_map[nid]
            risk[i] = agent.risk
            disruption[i] = agent.disruption
            pressure[i] = agent.pressure

        return {
            "risk_vector": risk,
            "disruption_vector": disruption,
            "pressure_vector": pressure,
        }

    def get_metrics(self) -> dict[str, float]:
        """Return aggregate system metrics."""
        state = self.get_system_state()
        risk = state["risk_vector"]
        pressure = state["pressure_vector"]

        system_energy = float(np.sqrt(np.sum(risk ** 2)) / max(self.n_nodes, 1))
        max_risk = float(np.max(risk)) if self.n_nodes > 0 else 0.0
        mean_risk = float(np.mean(risk)) if self.n_nodes > 0 else 0.0
        congested_count = int(np.sum(pressure > _CONGESTION_THRESHOLD))
        mean_pressure = float(np.mean(pressure)) if self.n_nodes > 0 else 0.0

        return {
            "system_energy": system_energy,
            "max_risk": max_risk,
            "mean_risk": mean_risk,
            "congested_count": congested_count,
            "mean_pressure": mean_pressure,
            "step": self._step_count,
        }

    @property
    def congestion_events(self) -> list[tuple[int, str, float]]:
        return list(self._congestion_events)


# ---------------------------------------------------------------------------
# Specialized Agent Types
# ---------------------------------------------------------------------------

class ConflictAgent(GCCNodeAgent):
    """Agent for conflict/event nodes — amplifies risk propagation.

    Conflict zones act as risk emitters: they push risk outward more
    aggressively and decay more slowly than standard nodes.
    """

    def step(self) -> None:
        # Amplified propagation — conflict nodes spread 20% more risk
        neighbor_risk = self._weighted_neighbor_risk()
        new_risk = (
            _ALPHA * 1.2 * neighbor_risk
            + _BETA * self.shock
            + _DELTA * self.external
        )
        decayed_current = self.risk * (1.0 - _DECAY_RATE * 0.5)  # slower decay
        self.risk = float(np.clip(max(new_risk, decayed_current), 0.0, 1.0))

        # Standard pressure
        neighbors = self._neighbor_agents()
        inflow = sum(n.risk for n in neighbors) / max(len(neighbors), 1)
        outflow = self.risk * (1.0 - self.risk)
        self.pressure = float(np.clip(
            _RHO * self.pressure + _KAPPA * inflow - _OMEGA * outflow + _XI * self.shock,
            0.0, 1.0,
        ))
        self.disruption = float(np.clip(0.7 * self.risk + 0.3 * self.pressure, 0.0, 1.0))
        self.shock = 0.0

    @property
    def agent_type(self) -> str:
        return "conflict"


class FlightAgent(GCCNodeAgent):
    """Agent for aviation nodes — models rerouting and delay cascades.

    Flight agents have higher sensitivity to airspace shocks and
    propagate delays through connected airport nodes.
    """

    def step(self) -> None:
        neighbor_risk = self._weighted_neighbor_risk()
        # Aviation is highly sensitive to airspace disruption
        new_risk = (
            _ALPHA * neighbor_risk
            + _BETA * 1.1 * self.shock  # 10% amplified shock sensitivity
            + _DELTA * self.external
        )
        decayed_current = self.risk * (1.0 - _DECAY_RATE)
        self.risk = float(np.clip(max(new_risk, decayed_current), 0.0, 1.0))

        # Delay pressure accumulates faster for aviation
        neighbors = self._neighbor_agents()
        inflow = sum(n.risk for n in neighbors) / max(len(neighbors), 1)
        outflow = self.risk * (1.0 - self.risk)
        self.pressure = float(np.clip(
            _RHO * self.pressure + _KAPPA * 1.15 * inflow - _OMEGA * outflow + _XI * self.shock,
            0.0, 1.0,
        ))
        self.disruption = float(np.clip(0.55 * self.risk + 0.45 * self.pressure, 0.0, 1.0))
        self.shock = 0.0

    @property
    def agent_type(self) -> str:
        return "flight"


class VesselAgent(GCCNodeAgent):
    """Agent for maritime nodes — models chokepoint sensitivity and AIS behavior.

    Vessel agents have heightened sensitivity to chokepoint (Hormuz)
    and maritime corridor disruptions. Risk decays slower due to
    transit time.
    """

    def step(self) -> None:
        neighbor_risk = self._weighted_neighbor_risk()
        new_risk = (
            _ALPHA * neighbor_risk
            + _BETA * self.shock
            + _DELTA * 1.15 * self.external  # maritime corridor persistence
        )
        # Slower decay — vessels can't reroute as quickly as flights
        decayed_current = self.risk * (1.0 - _DECAY_RATE * 0.7)
        self.risk = float(np.clip(max(new_risk, decayed_current), 0.0, 1.0))

        neighbors = self._neighbor_agents()
        inflow = sum(n.risk for n in neighbors) / max(len(neighbors), 1)
        outflow = self.risk * (1.0 - self.risk)
        self.pressure = float(np.clip(
            _RHO * self.pressure + _KAPPA * inflow - _OMEGA * 0.8 * outflow + _XI * self.shock,
            0.0, 1.0,
        ))
        self.disruption = float(np.clip(0.5 * self.risk + 0.5 * self.pressure, 0.0, 1.0))
        self.shock = 0.0

    @property
    def agent_type(self) -> str:
        return "vessel"


class LogisticsAgent(GCCNodeAgent):
    """Agent for logistics/supply-chain nodes — models cascading delays.

    Logistics agents are downstream absorbers: they accumulate pressure
    from multiple sources and have high congestion sensitivity.
    """

    def step(self) -> None:
        neighbor_risk = self._weighted_neighbor_risk()
        new_risk = (
            _ALPHA * neighbor_risk
            + _BETA * self.shock
            + _DELTA * self.external
        )
        decayed_current = self.risk * (1.0 - _DECAY_RATE)
        self.risk = float(np.clip(max(new_risk, decayed_current), 0.0, 1.0))

        # Logistics accumulates congestion faster
        neighbors = self._neighbor_agents()
        inflow = sum(n.risk for n in neighbors) / max(len(neighbors), 1)
        outflow = self.risk * (1.0 - self.risk)
        self.pressure = float(np.clip(
            _RHO * 1.1 * self.pressure + _KAPPA * 1.2 * inflow - _OMEGA * outflow + _XI * self.shock,
            0.0, 1.0,
        ))
        self.disruption = float(np.clip(0.5 * self.risk + 0.5 * self.pressure, 0.0, 1.0))
        self.shock = 0.0

    @property
    def agent_type(self) -> str:
        return "logistics"


# ---------------------------------------------------------------------------
# Agent type inference
# ---------------------------------------------------------------------------

_NODE_TO_AGENT_TYPE: dict[str, type[GCCNodeAgent]] = {
    # Conflict/event nodes
    "stability": ConflictAgent,
    "sentiment": ConflictAgent,
    # Aviation nodes
    "airspace": FlightAgent,
    "riyadh_apt": FlightAgent,
    "dubai_apt": FlightAgent,
    "kuwait_apt": FlightAgent,
    "doha_apt": FlightAgent,
    "muscat_apt": FlightAgent,
    "bahrain_apt": FlightAgent,
    "aviation": FlightAgent,
    # Maritime nodes
    "hormuz": VesselAgent,
    "shipping": VesselAgent,
    "jebel_ali": VesselAgent,
    "ras_tanura": VesselAgent,
    "shuwaikh": VesselAgent,
    "hamad_port": VesselAgent,
    "shipping_sector": VesselAgent,
    # Logistics nodes
    "logistics": LogisticsAgent,
    "supply_chain": LogisticsAgent,
}


# ---------------------------------------------------------------------------
# Top-level simulation runner
# ---------------------------------------------------------------------------
def run_mesa_simulation(
    graph_state: GraphState,
    scenario: dict[str, Any],
    n_steps: int = 20,
) -> MesaSimulationResult:
    """Run a full Mesa agent-based simulation from a GraphState and scenario.

    Parameters
    ----------
    graph_state : GraphState
        The current intelligence graph state (nodes, edges, etc.).
    scenario : dict
        Scenario definition with at minimum:
          - "shocks": list of dicts with "target_node_ids" (list[str])
            and "severity" (float).
    n_steps : int
        Number of simulation steps to run. Default 20.

    Returns
    -------
    MesaSimulationResult
        Full simulation trajectory and final state.
    """
    # Build node dicts from GraphState
    nodes: list[dict[str, Any]] = []
    for nid in graph_state.node_ids:
        label = graph_state.node_labels.get(nid, nid)
        # Infer layer from sector list if available
        idx = graph_state.node_ids.index(nid)
        sector = (
            graph_state.node_sectors[idx]
            if graph_state.node_sectors and idx < len(graph_state.node_sectors)
            else "infrastructure"
        )
        nodes.append({
            "id": nid,
            "label": label,
            "layer": sector,
        })

    # Create model
    model = GCCIntelligenceModel(
        nodes=nodes,
        edges=graph_state.edges,
        shock_config=scenario,
    )

    # Set initial risk from graph_state baseline if available
    if graph_state.baseline_risk is not None:
        for i, nid in enumerate(graph_state.node_ids):
            agent = model.agent_map.get(nid)
            if agent is not None and i < len(graph_state.baseline_risk):
                agent.risk = float(graph_state.baseline_risk[i])

    # Inject scenario shocks
    shocks = scenario.get("shocks", [])
    for shock_def in shocks:
        target_ids = shock_def.get("target_node_ids", [])
        severity = shock_def.get("severity", 0.5)
        model.inject_shock(target_ids, severity)

    # Run simulation collecting history
    risk_history: list[NDArray[np.float64]] = []
    pressure_history: list[NDArray[np.float64]] = []
    energy_history: list[float] = []
    converged = False
    steps_run = 0

    # Capture initial state
    init_state = model.get_system_state()
    prev_risk = init_state["risk_vector"].copy()

    for step_i in range(n_steps):
        model.step()
        steps_run += 1

        state = model.get_system_state()
        risk_history.append(state["risk_vector"].copy())
        pressure_history.append(state["pressure_vector"].copy())

        metrics = model.get_metrics()
        energy_history.append(metrics["system_energy"])

        # Check convergence
        risk_delta_norm = float(np.linalg.norm(state["risk_vector"] - prev_risk))
        if risk_delta_norm < _CONVERGENCE_EPSILON and step_i > 0:
            converged = True
            break

        prev_risk = state["risk_vector"].copy()

    # Final state
    final = model.get_system_state()

    return MesaSimulationResult(
        risk_history=risk_history,
        pressure_history=pressure_history,
        system_energy_history=energy_history,
        final_state={
            "risk_vector": final["risk_vector"],
            "pressure_vector": final["pressure_vector"],
            "disruption_vector": final["disruption_vector"],
        },
        congestion_events=model.congestion_events,
        converged=converged,
        steps_run=steps_run,
    )
