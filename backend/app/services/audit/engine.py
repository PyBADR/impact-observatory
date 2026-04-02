"""Audit Service — SHA-256 audit trail and computation provenance tracking.

Every observatory pipeline execution produces a verifiable audit record containing:
- Input hash (scenario parameters)
- Output hash (full result payload)
- Computation metadata (engine versions, timestamps, duration)
- Decision provenance (which actions were considered, why top 3 were selected)

Audit records are append-only and suitable for GCC regulatory compliance (PDPL, IFRS 17).
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, Optional

from app.schemas.observatory import ObservatoryOutput, ScenarioInput


def compute_sha256(data: Any) -> str:
    """Compute SHA-256 hash of any JSON-serializable data."""
    if hasattr(data, "model_dump"):
        data_dict = data.model_dump(mode="json")
    elif isinstance(data, dict):
        data_dict = data
    else:
        data_dict = {"value": str(data)}

    json_str = json.dumps(data_dict, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def create_audit_record(
    scenario: ScenarioInput,
    output: ObservatoryOutput,
    engine_versions: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create a complete audit record for an observatory pipeline execution.

    Args:
        scenario: Input scenario
        output: Complete observatory output
        engine_versions: Optional dict of engine name → version

    Returns:
        Audit record dict suitable for storage/logging
    """
    if engine_versions is None:
        engine_versions = {
            "financial_engine": "1.0.0",
            "banking_engine": "1.0.0",
            "insurance_engine": "1.0.0",
            "fintech_engine": "1.0.0",
            "decision_engine": "1.0.0",
            "explainability_engine": "1.0.0",
        }

    input_hash = compute_sha256(scenario)
    output_hash = compute_sha256(output)

    return {
        "audit_id": f"audit_{input_hash[:12]}_{int(datetime.utcnow().timestamp())}",
        "timestamp": datetime.utcnow().isoformat(),
        "input": {
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "severity": scenario.severity,
            "duration_days": scenario.duration_days,
            "input_hash": input_hash,
        },
        "output": {
            "headline_loss_usd_bn": round(output.financial_impact.headline_loss_usd, 2),
            "severity_code": output.financial_impact.severity_code,
            "banking_stress": output.banking_stress.stress_level,
            "insurance_stress": output.insurance_stress.stress_level,
            "fintech_stress": output.fintech_stress.stress_level,
            "decisions_count": len(output.decisions),
            "output_hash": output_hash,
        },
        "computation": {
            "computed_in_ms": round(output.computed_in_ms, 2),
            "engine_versions": engine_versions,
            "runtime_flow": output.runtime_flow,
            "model_confidence": round(output.financial_impact.confidence, 3),
        },
        "decision_provenance": [
            {
                "action_id": d.id,
                "title": d.title,
                "sector": d.sector,
                "priority": round(d.priority, 3),
                "cost_usd": d.cost_usd,
                "loss_avoided_usd": d.loss_avoided_usd,
                "regulatory_risk": round(d.regulatory_risk, 3),
            }
            for d in output.decisions
        ],
        "compliance": {
            "pdpl_compliant": output.regulatory.pdpl_compliant,
            "ifrs17_impact": round(output.regulatory.ifrs17_impact, 2),
            "audit_hash_algorithm": "SHA-256",
            "data_sovereignty": "GCC-local",
        },
    }


def verify_audit_hash(output: ObservatoryOutput) -> bool:
    """
    Verify that an observatory output's audit hash matches its content.

    Args:
        output: Observatory output to verify

    Returns:
        True if hash is valid, False if tampered or invalid
    """
    # Recompute hash with audit_hash field zeroed
    output_copy = output.model_copy()
    output_copy.audit_hash = ""
    output_copy.computed_in_ms = 0.0
    recomputed = compute_sha256(output_copy)

    return recomputed == output.audit_hash
