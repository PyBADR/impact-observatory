"""AI Insights Agent — Graph-RAG Reasoning Engine.

Production-grade agent that answers natural language questions about
GCC macro intelligence by combining Knowledge Graph context with LLM reasoning.

Architecture Layer: Agents → APIs (Layer 4-5 of the 7-layer stack)
Owner: AI Insights Agent
Consumers: Insights API, Dashboard, Vercept (Vy)

Pipeline:
  User Query
    ↓ Entity Resolution (GraphStore label/type match)
    ↓ Subgraph Retrieval (BFS multi-hop from resolved entities)
    ↓ Path Discovery (impact/dependency traces)
    ↓ Context Assembly (structured text for LLM)
    ↓ Prompt Engineering (GCC-domain system prompt + scenario awareness)
    ↓ LLM Reasoning (Ollama/Mock via LLMBackend protocol)
    ↓ Structured Output Parsing (InsightResult with confidence + evidence)
    ↓ SHA-256 Audit Hash
  InsightResult

Design Principles:
  1. Uses existing LLMBackend protocol (same as AI Entity Extractor)
  2. Graph context from GraphRAGService (in-memory store, not raw Neo4j)
  3. Structured output: typed InsightResult, not raw LLM text
  4. GCC scenario-aware: system prompt knows the 15 scenarios
  5. Auditable: every result carries SHA-256 hash + provenance
  6. Fallback-safe: LLM failure → structured error, not crash
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.graph_brain.ai_entity_extractor import LLMBackend, MockLLMBackend, OllamaBackend
from src.graph_brain.graph_rag_service import GraphRAGService, RetrievedContext
from src.graph_brain.service import GraphBrainService, get_graph_brain_service
from src.graph_brain.types import GraphConfidence

logger = logging.getLogger("graph_brain.insights_agent")


# ═══════════════════════════════════════════════════════════════════════════════
# Insight Result — structured output contract
# ═══════════════════════════════════════════════════════════════════════════════

class InsightCategory(str, Enum):
    """Classification of insight type."""
    RISK_ASSESSMENT = "risk_assessment"
    IMPACT_ANALYSIS = "impact_analysis"
    DEPENDENCY_MAP = "dependency_map"
    ANOMALY_DETECTION = "anomaly_detection"
    SCENARIO_ANALYSIS = "scenario_analysis"
    TREND_INSIGHT = "trend_insight"
    COMPLIANCE_ALERT = "compliance_alert"
    GENERAL = "general"


class InsightEvidence(BaseModel):
    """A single piece of evidence supporting an insight."""
    node_id: str = ""
    label: str = ""
    relationship: str = ""
    weight: float = 0.0
    description: str = ""


class InsightItem(BaseModel):
    """A single insight extracted from LLM reasoning."""
    title: str = Field("", description="Short insight headline")
    description: str = Field("", description="Detailed explanation")
    category: str = Field("general")
    severity: str = Field("medium", description="low | medium | high | critical")
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    evidence: list[InsightEvidence] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class InsightResult(BaseModel):
    """Full structured output of the AI Insights Agent."""
    query: str = ""
    insights: list[InsightItem] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    summary: str = Field("", description="Executive summary of all insights")
    overall_confidence: float = Field(0.0, ge=0.0, le=1.0)
    graph_context_summary: dict = Field(default_factory=dict)
    reasoning_trace: str = Field("", description="LLM raw reasoning for audit")
    llm_model: str = ""
    duration_ms: float = 0.0
    audit_hash: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_audit_hash(self) -> str:
        canonical = json.dumps({
            "query": self.query,
            "insight_count": len(self.insights),
            "risk_count": len(self.risks),
            "confidence": self.overall_confidence,
            "created_at": self.created_at.isoformat(),
        }, sort_keys=True).encode()
        self.audit_hash = hashlib.sha256(canonical).hexdigest()
        return self.audit_hash


# ═══════════════════════════════════════════════════════════════════════════════
# System Prompt — GCC domain + scenario awareness
# ═══════════════════════════════════════════════════════════════════════════════

INSIGHTS_SYSTEM_PROMPT = """You are an expert GCC macro intelligence analyst for the Impact Observatory (مرصد الأثر).
You analyze Knowledge Graph context about GCC financial, insurance, and geopolitical risks.

DOMAIN EXPERTISE:
- GCC member states: Saudi Arabia, UAE, Qatar, Bahrain, Kuwait, Oman
- Key chokepoints: Strait of Hormuz, Bab el-Mandeb, Suez Canal
- Sectors: Energy, Banking, Insurance, Maritime, Infrastructure
- Regulatory: SAMA, CBUAE, QCB, CBB, CBK, CBO; IFRS 17 compliance
- Risk domains: Oil price, sovereign debt, cyber, supply chain, geopolitical

SCENARIO AWARENESS (15 active scenarios):
- Hormuz chokepoint disruption / full closure
- Saudi oil production shock
- UAE banking crisis
- GCC-wide cyber attack
- Qatar LNG disruption
- Bahrain sovereign stress
- Kuwait fiscal shock
- Oman port closure
- Red Sea trade corridor instability
- Energy market volatility
- Regional liquidity stress
- Critical port throughput disruption
- Financial infrastructure cyber disruption
- Iran regional escalation

OUTPUT FORMAT (strict JSON):
{
  "insights": [
    {
      "title": "short headline",
      "description": "detailed explanation with evidence",
      "category": "risk_assessment|impact_analysis|dependency_map|anomaly_detection|scenario_analysis|trend_insight|compliance_alert|general",
      "severity": "low|medium|high|critical",
      "confidence": 0.0-1.0,
      "recommendations": ["actionable recommendation"]
    }
  ],
  "risks": ["identified risk statement"],
  "patterns": ["observed pattern"],
  "anomalies": ["detected anomaly"],
  "summary": "executive summary paragraph",
  "overall_confidence": 0.0-1.0
}

RULES:
1. Ground ALL insights in the provided graph context — cite specific entities and relationships
2. Distinguish between observed facts (from graph) and inferred patterns (your analysis)
3. Always consider cross-sector contagion effects (e.g., oil→banking→insurance)
4. Flag compliance-relevant findings (IFRS 17, PDPL, regulatory exposure)
5. Rate severity considering GCC enterprise impact scale
6. Do NOT invent entities or relationships not present in the context"""


# ═══════════════════════════════════════════════════════════════════════════════
# Mock Insights Backend — for testing
# ═══════════════════════════════════════════════════════════════════════════════

class MockInsightsBackend(LLMBackend):
    """Mock backend that returns domain-aware structured insights."""

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        prompt_lower = prompt.lower()

        insights = []
        risks = []
        patterns = []

        if "hormuz" in prompt_lower or "oil" in prompt_lower or "energy" in prompt_lower:
            insights = [
                {
                    "title": "Hormuz Chokepoint Risk Elevated",
                    "description": "The Strait of Hormuz handles ~21% of global oil transit. "
                                   "Graph context shows direct exposure paths from Hormuz to "
                                   "Saudi Aramco and ADNOC operations, with downstream "
                                   "propagation to energy sector and maritime insurance.",
                    "category": "risk_assessment",
                    "severity": "high",
                    "confidence": 0.85,
                    "recommendations": [
                        "Activate Hormuz scenario contingency pricing models",
                        "Review marine cargo insurance exposure across affected LOBs",
                    ],
                },
            ]
            risks = [
                "Oil price surge above $100/bbl would trigger reinsurance treaty thresholds",
                "Maritime supply chain disruption cascades to port throughput within 48 hours",
            ]
            patterns = ["Historical pattern: Hormuz tensions correlate with 15-25% CDS spread widening in GCC sovereigns"]

        elif "insurance" in prompt_lower or "claims" in prompt_lower:
            insights = [
                {
                    "title": "Claims Surge Correlation Detected",
                    "description": "Graph analysis shows claims surge events propagate "
                                   "from marine cargo LOB to reinsurance market within "
                                   "2 reporting cycles. Current graph shows active "
                                   "signal-to-event links in the insurance domain.",
                    "category": "impact_analysis",
                    "severity": "medium",
                    "confidence": 0.75,
                    "recommendations": [
                        "Monitor marine cargo loss ratios for threshold breach",
                        "Pre-position reinsurance capacity for Q3 renewals",
                    ],
                },
            ]
            risks = ["Reinsurance capacity tightening if combined ratio exceeds 105%"]
            patterns = ["Insurance claims follow maritime disruption events with 30-45 day lag"]

        elif "cyber" in prompt_lower:
            insights = [
                {
                    "title": "Financial Infrastructure Cyber Risk",
                    "description": "Graph shows interconnected dependencies between "
                                   "banking sector payment systems and critical infrastructure. "
                                   "A cyber event would propagate across multiple GCC states "
                                   "through shared SWIFT/payment corridors.",
                    "category": "scenario_analysis",
                    "severity": "critical",
                    "confidence": 0.70,
                    "recommendations": [
                        "Review cyber insurance sublimits for systemic risk exclusions",
                        "Map payment system dependencies across tenant portfolios",
                    ],
                },
            ]
            risks = ["Systemic cyber event could trigger multiple scenario activations simultaneously"]
            patterns = ["Cyber risk nodes have highest degree centrality in the graph"]

        else:
            insights = [
                {
                    "title": "General GCC Risk Landscape",
                    "description": "Based on the current graph context, GCC risk posture "
                                   "shows moderate interconnectedness across energy, banking, "
                                   "and infrastructure sectors.",
                    "category": "general",
                    "severity": "medium",
                    "confidence": 0.60,
                    "recommendations": ["Continue monitoring active scenarios"],
                },
            ]
            risks = ["Cross-sector contagion channels remain active"]

        return json.dumps({
            "insights": insights,
            "risks": risks,
            "patterns": patterns,
            "anomalies": [],
            "summary": f"Analysis of query: {prompt[:100]}... "
                       f"Identified {len(insights)} insight(s) and {len(risks)} risk(s).",
            "overall_confidence": 0.75 if insights else 0.30,
        })

    def is_available(self) -> bool:
        return True


# ═══════════════════════════════════════════════════════════════════════════════
# AI Insights Agent — main class
# ═══════════════════════════════════════════════════════════════════════════════

class InsightsAgent:
    """AI-powered insights agent that reasons over Knowledge Graph context.

    Usage:
        agent = InsightsAgent()
        result = agent.query("What is the impact of Hormuz closure on Saudi insurance?")
        # result is a typed InsightResult with structured insights, risks, patterns

    Args:
        graph_brain: GraphBrainService (in-memory store)
        backend: LLM backend (Ollama/Mock)
        max_context_chars: Maximum graph context for LLM prompt
        max_depth: BFS depth for subgraph retrieval
    """

    def __init__(
        self,
        graph_brain: Optional[GraphBrainService] = None,
        backend: Optional[LLMBackend] = None,
        max_context_chars: int = 8000,
        max_depth: int = 3,
    ) -> None:
        self._graph_brain = graph_brain or get_graph_brain_service()
        self._backend = backend or MockInsightsBackend()
        self._rag = GraphRAGService(
            graph_brain=self._graph_brain,
            max_depth=max_depth,
            max_context_chars=max_context_chars,
        )
        self._model_name = getattr(self._backend, "model", "mock")

    @property
    def is_available(self) -> bool:
        return self._backend.is_available()

    def query(
        self,
        query: str,
        context_limit: int = 10,
        include_paths: bool = True,
    ) -> InsightResult:
        """Run the full insights pipeline.

        Steps:
          1. Retrieve graph context (entity resolution + subgraph + paths)
          2. Build LLM prompt with context
          3. Call LLM for reasoning
          4. Parse structured output
          5. Compute audit hash

        Args:
            query: Natural language question about GCC risks/impacts
            context_limit: Max entities to resolve from query
            include_paths: Whether to trace impact paths (richer context, slower)

        Returns:
            InsightResult with structured insights, risks, patterns, and audit trail
        """
        t0 = time.monotonic()
        result = InsightResult(query=query, llm_model=self._model_name)

        try:
            # Step 1: Graph-RAG context retrieval
            context: RetrievedContext = self._rag.retrieve(
                query, context_limit=context_limit, include_paths=include_paths,
            )
            result.graph_context_summary = context.summary()

            # Step 2: Build prompt
            prompt = self._build_prompt(query, context)

            # Step 3: LLM reasoning
            raw_response = self._backend.generate(prompt, INSIGHTS_SYSTEM_PROMPT)
            result.reasoning_trace = raw_response

            # Step 4: Parse structured output
            self._parse_response(raw_response, result)

        except Exception as exc:
            logger.error("Insights agent failed for query '%s': %s", query[:100], exc)
            result.insights.append(InsightItem(
                title="Analysis Error",
                description=f"The insights agent encountered an error: {exc}",
                category="general",
                severity="low",
                confidence=0.0,
            ))

        result.duration_ms = (time.monotonic() - t0) * 1000
        result.compute_audit_hash()

        logger.info(
            "Insights query '%.50s': %d insights, %d risks, conf=%.2f (%.1fms)",
            query, len(result.insights), len(result.risks),
            result.overall_confidence, result.duration_ms,
        )
        return result

    # ── Prompt Construction ───────────────────────────────────────────────

    def _build_prompt(self, query: str, context: RetrievedContext) -> str:
        """Build the full LLM prompt with graph context."""
        parts = [
            "=== USER QUERY ===",
            query,
            "",
            "=== KNOWLEDGE GRAPH CONTEXT ===",
            context.context_text if context.context_text else "No graph context available.",
            "",
            "=== GRAPH STATISTICS ===",
            f"Entities resolved: {len(context.resolved_entities)}",
            f"Nodes in context: {context.node_count}",
            f"Edges in context: {context.edge_count}",
            f"Impact paths found: {context.path_count}",
            "",
            "Based on the graph context above, provide your analysis in the required JSON format.",
        ]
        return "\n".join(parts)

    # ── Response Parsing ──────────────────────────────────────────────────

    def _parse_response(self, raw: str, result: InsightResult) -> None:
        """Parse LLM JSON response into InsightResult fields."""
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Try markdown fence extraction
            import re
            match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group(1))
                except json.JSONDecodeError:
                    result.summary = raw[:500]
                    result.overall_confidence = 0.2
                    return
            else:
                result.summary = raw[:500]
                result.overall_confidence = 0.2
                return

        # Parse insights
        for raw_insight in data.get("insights", []):
            try:
                evidence = []
                for ev in raw_insight.get("evidence", []):
                    evidence.append(InsightEvidence(**ev))

                item = InsightItem(
                    title=raw_insight.get("title", "Untitled"),
                    description=raw_insight.get("description", ""),
                    category=raw_insight.get("category", "general"),
                    severity=raw_insight.get("severity", "medium"),
                    confidence=float(raw_insight.get("confidence", 0.5)),
                    evidence=evidence,
                    recommendations=raw_insight.get("recommendations", []),
                )
                result.insights.append(item)
            except Exception as exc:
                logger.warning("Failed to parse insight: %s — %s", raw_insight, exc)

        result.risks = data.get("risks", [])
        result.patterns = data.get("patterns", [])
        result.anomalies = data.get("anomalies", [])
        result.summary = data.get("summary", "")
        result.overall_confidence = float(data.get("overall_confidence", 0.0))


# ═══════════════════════════════════════════════════════════════════════════════
# Singleton factory
# ═══════════════════════════════════════════════════════════════════════════════

_instance: Optional[InsightsAgent] = None


def get_insights_agent() -> InsightsAgent:
    """Get or create the global InsightsAgent singleton.

    Reads config to determine LLM backend and parameters.
    """
    global _instance
    if _instance is None:
        try:
            from src.core.config import settings

            if settings.ai_use_mock_backend or not settings.ai_extraction_enabled:
                backend = MockInsightsBackend()
            else:
                backend = OllamaBackend(
                    base_url=settings.ollama_base_url,
                    model=settings.ollama_model,
                    timeout_seconds=settings.ollama_timeout_seconds,
                    temperature=0.3,  # slightly higher for reasoning vs extraction
                )

            _instance = InsightsAgent(backend=backend)
        except Exception:
            _instance = InsightsAgent()

    return _instance
