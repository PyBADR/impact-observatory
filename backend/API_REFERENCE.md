# Impact Observatory — API Reference
## Model v2.1.0 | April 2026

Base URL (production): `https://api.impactobservatory.deevo.ai`
Base URL (local):      `http://localhost:8000`

All endpoints are prefixed with `/api/v1`.
All responses are JSON. Errors follow the standard envelope:
```json
{ "error": "string", "detail": "string | null", "status_code": 400 }
```

---

## Authentication

Include your API key in the `X-API-Key` header:
```
X-API-Key: your_api_key_here
```

---

## Endpoints

### 1. POST /api/v1/simulate

Run a full decision simulation.

**Request Body**

```json
{
  "scenario_id": "hormuz_chokepoint_disruption",
  "severity": 0.75,
  "horizon_hours": 336,
  "label": "Q2 2026 stress test"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `scenario_id` | string | Yes | Scenario key from catalog |
| `severity` | float [0.01–1.0] | Yes | Base event severity |
| `horizon_hours` | int [24–2160] | No | Simulation horizon (default: 336) |
| `label` | string (max 128) | No | Optional run label |

**Response: 200 OK**

```json
{
  "run_id": "a3f8c2d1e4b7...",
  "scenario_id": "hormuz_chokepoint_disruption",
  "model_version": "2.1.0",
  "severity": 0.75,
  "horizon_hours": 336,
  "time_horizon_days": 14,
  "generated_at": "2026-04-03T10:30:00+00:00",
  "duration_ms": 312,
  "event_severity": 0.9135,
  "peak_day": 3,
  "confidence_score": 0.8625,
  "financial_impact": {
    "total_loss_usd": 2847000000.0,
    "total_loss_formatted": "$2.8B",
    "direct_loss_usd": 1708200000.0,
    "indirect_loss_usd": 797160000.0,
    "systemic_loss_usd": 341640000.0,
    "systemic_multiplier": 0.89,
    "affected_entities": 18,
    "critical_entities": 5,
    "top_entities": [ "..." ]
  },
  "sector_analysis": [
    { "sector": "energy", "exposure": 0.2556, "stress": 0.8234, "classification": "SEVERE", "risk_level": "SEVERE" },
    "..."
  ],
  "propagation_score": 0.9135,
  "propagation_chain": [ "..." ],
  "unified_risk_score": 0.7842,
  "risk_level": "HIGH",
  "physical_system_status": {
    "nodes_assessed": 42,
    "saturated_nodes": 7,
    "flow_balance_status": "BALANCED",
    "system_utilization": 0.7234
  },
  "bottlenecks": [ "..." ],
  "congestion_score": 0.4512,
  "recovery_score": 0.3210,
  "recovery_trajectory": [ "..." ],
  "banking_stress": { "aggregate_stress": 0.7123, "classification": "HIGH", "..." },
  "insurance_stress": { "severity_index": 0.6231, "classification": "HIGH", "..." },
  "fintech_stress": { "aggregate_stress": 0.5342, "classification": "ELEVATED", "..." },
  "flow_analysis": {
    "money": { "disruption_factor": 0.5512, "volume_loss_usd": 23100000000, "..." },
    "logistics": { "..." },
    "energy": { "..." },
    "payments": { "..." },
    "claims": { "..." },
    "aggregate_disruption_usd": 34500000000,
    "most_disrupted_flow": "energy",
    "flow_recovery_days": 38
  },
  "explainability": {
    "causal_chain": [ "..." ],
    "narrative_en": "A Very High severity event...",
    "narrative_ar": "ظهر حدث بمستوى خطورة مرتفع جداً...",
    "sensitivity": { "..." },
    "uncertainty_bands": { "lower_bound": 0.7542, "upper_bound": 0.8142, "..." },
    "model_equation": "R(t) = 0.20*G + 0.25*P + ..."
  },
  "decision_plan": {
    "business_severity": "HIGH",
    "time_to_first_failure_hours": 18.4,
    "actions": [ "..." ],
    "escalation_triggers": [ "..." ],
    "monitoring_priorities": [ "..." ],
    "five_questions": { "..." }
  },
  "headline": {
    "total_loss_usd": 2847000000.0,
    "total_loss_formatted": "$2.8B",
    "peak_day": 3,
    "affected_entities": 18,
    "critical_count": 5,
    "severity_code": "HIGH",
    "average_stress": 0.6677
  }
}
```

**Error: 400 Bad Request**
```json
{ "error": "Unknown scenario 'xyz'", "detail": "Available: [...]", "status_code": 400 }
```

**Error: 422 Unprocessable Entity** — validation failure (severity out of range, etc.)

---

### 2. GET /api/v1/scenarios

List all available scenarios in the catalog.

**Request:** No body.

**Response: 200 OK**

```json
{
  "count": 15,
  "scenarios": [
    {
      "id": "hormuz_chokepoint_disruption",
      "name": "Strait of Hormuz Disruption",
      "name_ar": "اضطراب مضيق هرمز",
      "shock_nodes": ["hormuz", "shipping_lanes"],
      "base_loss_usd": 3200000000,
      "sectors_affected": ["energy", "maritime", "banking", "insurance", "fintech"],
      "cross_sector": true
    },
    "..."
  ]
}
```

---

### 3. GET /api/v1/runs/{run_id}

Retrieve a past simulation run by its UUID.

**Path Parameter:** `run_id` — UUID hex string

**Response: 200 OK** — Full `SimulateResponse` object (see above).

**Error: 404 Not Found**
```json
{ "error": "Run not found", "detail": "run_id: abc123", "status_code": 404 }
```

---

### 4. GET /api/v1/health

System health check.

**Response: 200 OK**

```json
{
  "status": "ok",
  "model_version": "2.1.0",
  "scenarios_available": 15,
  "nodes_in_registry": 42,
  "timestamp": "2026-04-03T10:30:00+00:00"
}
```

---

### 5. GET /api/v1/graph

Return the GCC node topology as a graph object.

**Response: 200 OK**

```json
{
  "nodes": [
    {
      "id": "hormuz",
      "label": "Strait of Hormuz",
      "label_ar": "مضيق هرمز",
      "sector": "maritime",
      "capacity": 21000000,
      "criticality": 1.0,
      "redundancy": 0.05,
      "lat": 26.59,
      "lng": 56.26
    },
    "..."
  ],
  "edges": [
    { "source": "hormuz", "target": "shipping_lanes", "weight": 1.0 },
    "..."
  ],
  "node_count": 42,
  "edge_count": 108
}
```

---

### 6. POST /api/v1/decision

Generate a standalone decision plan without running the full simulation.

**Request Body**

```json
{
  "run_id": "a3f8c2d1e4b7..."
}
```

**Response: 200 OK**

```json
{
  "run_id": "a3f8c2d1e4b7...",
  "scenario_id": "hormuz_chokepoint_disruption",
  "risk_level": "HIGH",
  "decision_plan": {
    "business_severity": "HIGH",
    "time_to_first_failure_hours": 18.4,
    "actions": [
      {
        "action_id": "ACT-001",
        "rank": 1,
        "sector": "energy",
        "owner": "National Oil Company / شركة النفط الوطنية",
        "action": "Activate strategic petroleum reserve drawdown...",
        "action_ar": "تفعيل سحب الاحتياطي البترولي الاستراتيجي...",
        "priority_score": 0.8234,
        "urgency": 0.9500,
        "loss_avoided_usd": 855000000,
        "loss_avoided_formatted": "$855.0M",
        "cost_usd": 1200000000,
        "cost_formatted": "$1.2B",
        "regulatory_risk": 0.70,
        "feasibility": 0.85,
        "time_to_act_hours": 6,
        "status": "IMMEDIATE",
        "escalation_trigger": "Activate if HIGH risk persists >12h"
      },
      "..."
    ],
    "escalation_triggers": [
      "LCR below 100% — activate emergency liquidity facility immediately",
      "Risk level HIGH — convene emergency financial stability board session"
    ],
    "monitoring_priorities": [
      "Monitor Energy sector — current classification: SEVERE",
      "..."
    ],
    "five_questions": {
      "what_happened": { "..." },
      "what_is_the_impact": { "..." },
      "what_is_affected": { "..." },
      "how_big_is_the_risk": { "..." },
      "recommended_actions": { "..." }
    }
  }
}
```

---

## Five Questions Framework

The `five_questions` object in `decision_plan` answers the key operational questions:

| Question | Key | Description |
|----------|-----|-------------|
| What happened? | `what_happened` | Event description (EN+AR), shock nodes, severity label |
| What is the impact? | `what_is_the_impact` | Total loss (USD), system stress, disrupted nodes, sector impacts |
| What is affected? | `what_is_affected` | Entity list, counts, critical count, sectors |
| How big is the risk? | `how_big_is_the_risk` | Unified risk score, risk factors, classification |
| What should we do? | `recommended_actions` | Top 3 actions, monitoring priorities, escalation triggers |

---

## Risk Classification Scale

| Code | Score | Meaning |
|------|-------|---------|
| `NOMINAL` | 0.00–0.20 | No action required |
| `LOW` | 0.20–0.35 | Enhanced monitoring |
| `GUARDED` | 0.35–0.50 | Precautionary measures |
| `ELEVATED` | 0.50–0.65 | Contingency plans active |
| `HIGH` | 0.65–0.80 | Emergency protocols |
| `SEVERE` | 0.80–1.00 | Full crisis mobilisation |

---

## Rate Limits

| Tier | Requests/minute | Requests/day |
|------|-----------------|--------------|
| Standard | 30 | 5,000 |
| Professional | 120 | 50,000 |
| Enterprise | 500 | Unlimited |
