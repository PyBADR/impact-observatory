"""Graph annotator — writes impact + decision data to graph store.

Fail-safe: never raises, always returns status string.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def annotate_graph(
    impact_assessment: dict[str, Any],
    decision_output: dict[str, Any],
    graph_store: Optional[Any] = None,
) -> str:
    """Annotate graph store with impact and decision data.

    Returns status: "ANNOTATED" | "NOT_CONNECTED" | "SKIPPED"
    Never raises.
    """
    if graph_store is None:
        return "NOT_CONNECTED"

    try:
        run_id = impact_assessment.get("run_id", "")
        scenario_id = impact_assessment.get("scenario_id", "")
        composite_severity = impact_assessment.get("composite_severity", 0.0)
        primary_action_type = decision_output.get("primary_action_type", "MONITOR")
        overall_urgency = decision_output.get("overall_urgency", "MONITOR")

        # Write impact node to graph
        if hasattr(graph_store, "add_node"):
            graph_store.add_node(
                node_id=f"impact:{run_id}",
                node_type="impact_assessment",
                properties={
                    "run_id": run_id,
                    "scenario_id": scenario_id,
                    "composite_severity": composite_severity,
                    "primary_action_type": primary_action_type,
                    "overall_urgency": overall_urgency,
                },
            )

        # Write decision edges from impacted domains to actions
        for action in decision_output.get("recommended_actions", [])[:3]:
            if hasattr(graph_store, "add_edge"):
                graph_store.add_edge(
                    source=f"impact:{run_id}",
                    target=f"action:{action.get('action_id', '')}",
                    edge_type="recommends",
                    properties={
                        "rank": action.get("rank", 0),
                        "urgency": action.get("urgency", "MONITOR"),
                        "action_type": action.get("action_type", "MONITOR"),
                    },
                )

        logger.info("[GraphAnnotator] Annotated graph for run %s", run_id)
        return "ANNOTATED"

    except Exception as e:
        logger.warning("[GraphAnnotator] Annotation failed (non-fatal): %s", e)
        return "SKIPPED"
