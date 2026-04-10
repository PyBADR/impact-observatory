"""PDF Export Service — generates executive-grade PDF reports.

Produces a clean boardroom-style PDF for:
  - Executive summary (headline loss, top 3 actions, risk classification)
  - Financial impact table (top 10 entities by loss)
  - Sector stress dashboard (banking, insurance, fintech gauges)
  - Decision action cards (top 3 prioritized actions)
  - Causal chain narrative (bilingual EN/AR)

Uses fpdf2 for pure-Python PDF generation with no external dependencies.
"""

from __future__ import annotations

import io
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def _s(text: str, max_len: int = 200) -> str:
    """Sanitize text for latin-1 PDF output — strip non-latin characters."""
    safe = text.encode("latin-1", errors="replace").decode("latin-1")
    return safe[:max_len] if max_len else safe


def _format_loss(usd: float) -> str:
    if usd >= 1e9:
        return f"${usd/1e9:.2f}B"
    if usd >= 1e6:
        return f"${usd/1e6:.0f}M"
    return f"${usd:,.0f}"


def _stress_bar(score: float, width: int = 40) -> str:
    """ASCII progress bar for stress score using latin-1 safe chars."""
    filled = int(score * width)
    return "[" + "#" * filled + "-" * (width - filled) + f"] {score:.0%}"


def generate_executive_pdf(run_result: dict, lang: str = "en") -> bytes:
    """Generate executive PDF report from a run result dict.

    Returns raw PDF bytes ready for streaming.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        raise RuntimeError("fpdf2 not installed. Run: pip install fpdf2")

    is_ar = lang == "ar"

    # Extract data
    headline = run_result.get("headline", {})
    total_loss = headline.get("total_loss_usd", 0)
    peak_day = headline.get("peak_day", 0)
    affected = headline.get("affected_entities", 0)
    critical_count = headline.get("critical_count", 0)

    financial = run_result.get("financial_impacts", run_result.get("financial", []))
    banking = run_result.get("banking_stress", run_result.get("banking", {}))
    insurance = run_result.get("insurance_stress", run_result.get("insurance", {}))
    fintech = run_result.get("fintech_stress", run_result.get("fintech", {}))
    decisions = run_result.get("decisions", {})
    actions = decisions.get("actions", [])
    explanation = run_result.get("explanation", {})
    narrative = explanation.get("narrative_en" if not is_ar else "narrative_ar", "")
    causal_chain = explanation.get("causal_chain", [])

    template_id = run_result.get("scenario_id", run_result.get("template_id", "unknown"))
    run_id = run_result.get("run_id", "unknown")
    severity = run_result.get("severity", 0.5)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── Build PDF ────────────────────────────────────────────────────────────
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ── Cover Header ──────────────────────────────────────────────────────────
    # Dark header bar
    pdf.set_fill_color(15, 23, 42)  # slate-900
    pdf.rect(0, 0, 210, 35, "F")
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_xy(10, 8)
    pdf.cell(0, 10, "IMPACT OBSERVATORY  |  Executive Report", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(10, 22)
    pdf.cell(0, 6, f"Classification: CONFIDENTIAL   |   Generated: {generated_at}   |   Run: {run_id}", ln=True)

    # Reset text color
    pdf.set_text_color(15, 23, 42)
    pdf.ln(8)

    # ── Scenario Banner ───────────────────────────────────────────────────────
    pdf.set_fill_color(239, 246, 255)  # light blue
    pdf.set_draw_color(37, 99, 235)
    pdf.rect(10, pdf.get_y(), 190, 18, "FD")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_xy(14, pdf.get_y() + 3)
    pdf.set_text_color(37, 99, 235)
    pdf.cell(0, 7, f"Scenario: {template_id.replace('_', ' ').upper()}   |   Severity: {severity:.0%}", ln=True)
    pdf.set_text_color(15, 23, 42)
    pdf.ln(6)

    # ── KPI Row ───────────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "KEY PERFORMANCE INDICATORS", ln=True)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    kpis = [
        ("HEADLINE LOSS", _format_loss(total_loss), (185, 28, 28)),
        ("PEAK IMPACT DAY", f"Day {peak_day}", (180, 83, 9)),
        ("ENTITIES IMPACTED", str(affected), (29, 78, 216)),
        ("CRITICAL ENTITIES", str(critical_count), (185, 28, 28)),
    ]

    x_start = 10
    box_w = 45
    box_h = 22
    for i, (label, value, color) in enumerate(kpis):
        x = x_start + i * (box_w + 2)
        y = pdf.get_y()
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(*color)
        pdf.rect(x, y, box_w, box_h, "FD")
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(100, 116, 139)
        pdf.set_xy(x + 2, y + 2)
        pdf.cell(box_w - 4, 4, label, ln=True)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*color)
        pdf.set_xy(x + 2, y + 8)
        pdf.cell(box_w - 4, 10, value)

    pdf.set_text_color(15, 23, 42)
    pdf.ln(box_h + 5)

    # ── Sector Stress ─────────────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "SECTOR STRESS LEVELS", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    sectors = [
        ("Banking", banking.get("aggregate_stress", 0), banking.get("liquidity_stress", 0)),
        ("Insurance", insurance.get("severity_index", 0), insurance.get("claims_surge_multiplier", 1) / 3),
        ("Fintech", fintech.get("payment_disruption_score", 0), fintech.get("cross_border_disruption", 0)),
    ]

    for sector_name, stress1, stress2 in sectors:
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(40, 5, sector_name + ":", ln=False)
        pdf.set_font("Courier", "", 8)
        bar = _stress_bar(stress1, 30)
        color = (185, 28, 28) if stress1 > 0.7 else (180, 83, 9) if stress1 > 0.4 else (21, 128, 61)
        pdf.set_text_color(*color)
        pdf.cell(0, 5, bar, ln=True)
        pdf.set_text_color(15, 23, 42)

    pdf.ln(4)

    # ── Financial Impact Table ────────────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "TOP FINANCIAL IMPACTS", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    # Table header
    pdf.set_fill_color(15, 23, 42)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 8)
    cols = [("Entity", 65), ("Loss (USD)", 35), ("Stress", 30), ("Classification", 40), ("Peak Day", 25)]
    for col_name, col_w in cols:
        pdf.cell(col_w, 7, col_name, border=0, fill=True)
    pdf.ln(7)

    pdf.set_text_color(15, 23, 42)
    pdf.set_font("Helvetica", "", 8)
    top_impacts = sorted(financial, key=lambda x: x.get("loss_usd", 0), reverse=True)[:10]
    for i, fi in enumerate(top_impacts):
        fill = i % 2 == 0
        pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
        cls = fi.get("classification", "MODERATE")
        cls_color = {
            "CRITICAL": (185, 28, 28), "SEVERE": (194, 65, 12),
            "HIGH": (180, 83, 9), "ELEVATED": (180, 83, 9),
        }.get(cls, (21, 128, 61))

        pdf.cell(65, 6, _s(fi.get("entity_label", fi.get("entity_id", "?")), 30), fill=fill)
        pdf.cell(35, 6, _format_loss(fi.get("loss_usd", 0)), fill=fill)
        pdf.cell(30, 6, f"{fi.get('stress_score', 0):.2%}", fill=fill)
        pdf.set_text_color(*cls_color)
        pdf.cell(40, 6, cls, fill=fill)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(25, 6, f"Day {fi.get('peak_day', 0)}", fill=fill)
        pdf.ln(6)

    pdf.ln(4)

    # ── Decision Actions ──────────────────────────────────────────────────────
    if actions:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "PRIORITY DECISION ACTIONS", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

        for i, action in enumerate(actions[:3]):
            priority = action.get("priority", 0)
            urgency = action.get("urgency", 0)
            sector = action.get("sector", "").upper()
            owner = action.get("owner", "")
            loss_avoided = action.get("loss_avoided_usd", 0)
            status = action.get("status", "PENDING_REVIEW")

            # Action box
            y_before = pdf.get_y()
            pdf.set_fill_color(240, 249, 255)
            pdf.set_draw_color(37, 99, 235)
            pdf.rect(10, y_before, 190, 24, "FD")

            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(37, 99, 235)
            pdf.set_xy(13, y_before + 2)
            pdf.cell(0, 5, f"#{i+1}  [{sector}]  Owner: {owner}  |  Priority: {priority:.2f}  |  Urgency: {urgency:.0%}  |  Avoids: {_format_loss(loss_avoided)}", ln=True)

            pdf.set_font("Helvetica", "", 8)
            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(13, y_before + 9)
            action_text = _s(action.get("action", ""))
            pdf.multi_cell(180, 5, action_text)

            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(100, 116, 139)
            pdf.set_xy(13, y_before + 19)
            pdf.cell(0, 4, f"Status: {status}  |  Time to act: {action.get('time_to_act_hours', 0)}h  |  Cost: {_format_loss(action.get('cost_usd', 0))}")

            pdf.set_text_color(15, 23, 42)
            pdf.set_xy(10, y_before + 26)
            pdf.ln(2)

    # ── Narrative ─────────────────────────────────────────────────────────────
    if narrative:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "EXECUTIVE NARRATIVE", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)
        pdf.set_font("Helvetica", "", 9)
        # Strip non-latin chars for basic fpdf (Arabic needs font embedding)
        safe_narrative = narrative.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 5, safe_narrative)
        pdf.ln(4)

    # ── Causal Chain ─────────────────────────────────────────────────────────
    if causal_chain:
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "CAUSAL PROPAGATION CHAIN (TOP 10 STEPS)", ln=True)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        pdf.set_fill_color(15, 23, 42)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(12, 6, "Step", fill=True)
        pdf.cell(55, 6, "Entity", fill=True)
        pdf.cell(35, 6, "Impact (USD)", fill=True)
        pdf.cell(25, 6, "Stress Delta", fill=True)
        pdf.cell(73, 6, "Mechanism", fill=True)
        pdf.ln(6)

        pdf.set_text_color(15, 23, 42)
        pdf.set_font("Helvetica", "", 8)
        for i, step in enumerate(causal_chain[:10]):
            fill = i % 2 == 0
            pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(12, 5, str(step.get("step", i + 1)), fill=fill)
            pdf.cell(55, 5, _s(step.get("entity_label", "?"), 28), fill=fill)
            pdf.cell(35, 5, _format_loss(step.get("impact_usd", 0)), fill=fill)
            pdf.cell(25, 5, f"{step.get('stress_delta', 0):.3f}", fill=fill)
            mechanism = _s(step.get("mechanism", ""), 38)
            pdf.cell(73, 5, mechanism, fill=fill)
            pdf.ln(5)

    # ── Footer ────────────────────────────────────────────────────────────────
    pdf.set_y(-20)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(100, 116, 139)
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    pdf.cell(0, 5, f"Impact Observatory | Marsad Al-Athar  |  CONFIDENTIAL  |  {generated_at}  |  Methodology: deterministic_propagation", ln=True, align="C")

    return bytes(pdf.output())
