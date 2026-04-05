"""
Impact Observatory | مرصد الأثر — PDF Export Service

Generates a structured, Unicode-safe PDF report from a UnifiedRunResult dict.
Supports both English (LTR) and Arabic (RTL) output.

Arabic rendering pipeline:
  1. arabic_reshaper  — joins Arabic chars into their correct contextual forms
  2. python-bidi      — reorders codepoints for visual LTR rendering in fpdf2
  3. fpdf2 + TTF      — renders shaped text with a Unicode-capable font

Font discovery (tried in order):
  1. fonts/NotoNaskhArabic-Regular.ttf  (bundled alongside this file)
  2. /usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf  (Debian/Ubuntu)
  3. /usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf
  4. /System/Library/Fonts/SFArabic.ttf  (macOS dev)
  5. Any *Arabic*.ttf found under /usr/share/fonts/
  6. Fallback: built-in Helvetica (ASCII only — Arabic chars replaced with '?')

Never raises on Arabic text — worst case produces legible ASCII report.
"""

from __future__ import annotations

import os
import glob
import logging
from pathlib import Path
from io import BytesIO
from typing import Optional

logger = logging.getLogger("observatory.pdf_export")

# ── Font discovery ─────────────────────────────────────────────────────────────

_FONT_SEARCH_PATHS: list[str] = [
    # Bundled alongside this service file
    str(Path(__file__).parent / "fonts" / "NotoNaskhArabic-Regular.ttf"),
    # Debian/Ubuntu: apt install fonts-noto fonts-noto-extra
    "/usr/share/fonts/opentype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansArabic-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
    # macOS dev
    "/System/Library/Fonts/SFArabic.ttf",
    "/Library/Fonts/GeezaPro.ttc",
]


def _find_arabic_font() -> Optional[str]:
    for path in _FONT_SEARCH_PATHS:
        if os.path.isfile(path):
            return path
    # Last resort: glob for any Arabic TTF on the system
    for hit in glob.glob("/usr/share/fonts/**/*[Aa]rabic*.ttf", recursive=True):
        if os.path.isfile(hit):
            return hit
    return None


_arabic_font_path: Optional[str] = _find_arabic_font()
if _arabic_font_path:
    logger.info("pdf_export: Arabic font found at %s", _arabic_font_path)
else:
    logger.warning("pdf_export: No Arabic font found — Arabic output will use ASCII fallback")


# ── Text shaping helpers ───────────────────────────────────────────────────────

def _shape_arabic(text: str) -> str:
    """
    Reshape + reorder Arabic text for visual rendering in a LTR PDF engine.

    Returns the original text unchanged if shaping libraries are unavailable —
    fpdf2 will still render whatever Unicode the font supports.
    """
    try:
        import arabic_reshaper  # type: ignore[import-untyped]
        from bidi.algorithm import get_display  # type: ignore[import-untyped]
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except ImportError:
        return text


def _t(text: str, lang: str) -> str:
    """Return display-ready text: shape Arabic when lang='ar', pass-through otherwise."""
    if not text:
        return ""
    if lang == "ar":
        return _shape_arabic(text)
    return text


def _safe(text: object) -> str:
    """Coerce anything to str; never crash."""
    if text is None:
        return ""
    return str(text)


def _usd(value: object) -> str:
    try:
        v = float(value)  # type: ignore[arg-type]
        if v >= 1_000_000_000:
            return f"${v / 1_000_000_000:.2f}B"
        if v >= 1_000_000:
            return f"${v / 1_000_000:.1f}M"
        return f"${v:,.0f}"
    except (TypeError, ValueError):
        return "—"


def _pct(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return "—"


# ── PDF builder ────────────────────────────────────────────────────────────────

# Label sets
_LABELS: dict[str, dict[str, str]] = {
    "en": {
        "title":               "Impact Observatory — Simulation Report",
        "generated":           "Generated",
        "run_id":              "Run ID",
        "scenario":            "Scenario",
        "severity":            "Scenario Severity (%)",
        "horizon":             "Simulation Horizon",
        "headline_loss":       "Projected Financial Loss (USD)",
        "nodes_impacted":      "Entities Affected",
        "propagation_depth":   "Propagation Depth",
        "sector_stress":       "Sector Stress Summary",
        "banking":             "Banking Stress Index",
        "insurance":           "Insurance Stress Index",
        "fintech":             "Fintech Stress Index",
        "agg_stress":          "Aggregate Stress",
        "total_loss":          "Projected Loss (USD)",
        "classification":      "Status",
        "decisions":           "Recommended Response Actions",
        "action":              "Action",
        "owner":               "Owner",
        "priority":            "Priority",
        "loss_avoided":        "Estimated Mitigation Value (USD)",
        "cost":                "Estimated Cost (USD)",
        "assumptions":         "Model Assumptions",
        "model_confidence":    "Model Confidence",
        "warnings":            "Warnings",
        "trust":               "Audit",
        "model_version":       "Model Version",
        "dataset_version":     "Dataset Version",
        "audit_ref":           "Audit Reference",
    },
    "ar": {
        "title":               "مرصد الأثر — تقرير المحاكاة",
        "generated":           "تاريخ الإنشاء",
        "run_id":              "معرّف التشغيل",
        "scenario":            "السيناريو",
        "severity":            "شدة السيناريو (%)",
        "horizon":             "أفق المحاكاة",
        "headline_loss":       "الخسارة المالية المتوقعة (دولار)",
        "nodes_impacted":      "الكيانات المتأثرة",
        "propagation_depth":   "عمق الانتشار",
        "sector_stress":       "ملخص ضغط القطاعات",
        "banking":             "مؤشر ضغط البنوك",
        "insurance":           "مؤشر ضغط التأمين",
        "fintech":             "مؤشر ضغط الفنتك",
        "agg_stress":          "الضغط الإجمالي",
        "total_loss":          "الخسارة المتوقعة (دولار)",
        "classification":      "الحالة",
        "decisions":           "إجراءات الاستجابة الموصى بها",
        "action":              "الإجراء",
        "owner":               "المسؤول",
        "priority":            "الأولوية",
        "loss_avoided":        "قيمة التخفيف المقدّرة (دولار)",
        "cost":                "التكلفة التقديرية (دولار)",
        "assumptions":         "افتراضات النموذج",
        "model_confidence":    "ثقة النموذج",
        "warnings":            "تحذيرات",
        "trust":               "سجل المراجعة",
        "model_version":       "إصدار النموذج",
        "dataset_version":     "إصدار مجموعة البيانات",
        "audit_ref":           "مرجع التدقيق",
    },
}


def generate_pdf(result: dict, lang: str = "en") -> bytes:
    """
    Generate a PDF report from a UnifiedRunResult dict.

    Args:
        result: The full run result dict from the unified pipeline.
        lang:   "en" or "ar"

    Returns:
        PDF bytes. Never raises — errors produce a minimal error-report PDF.
    """
    try:
        return _build_pdf(result, lang)
    except Exception as exc:
        logger.error("pdf_export.generate_pdf failed: %s", exc, exc_info=True)
        return _error_pdf(str(exc))


def _build_pdf(result: dict, lang: str) -> bytes:
    from fpdf import FPDF  # type: ignore[import-untyped]

    L = _LABELS.get(lang, _LABELS["en"])
    is_ar = lang == "ar"

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ── Font setup ─────────────────────────────────────────────────────────────
    has_unicode = _arabic_font_path is not None
    font_family = "ArReport"

    if has_unicode:
        try:
            pdf.add_font(font_family, "", _arabic_font_path, uni=True)
            pdf.add_font(font_family, "B", _arabic_font_path, uni=True)  # bold = same TTF for now
        except Exception as e:
            logger.warning("pdf_export: failed to add font %s: %s", _arabic_font_path, e)
            has_unicode = False
            font_family = "Helvetica"
    else:
        font_family = "Helvetica"

    def _set(size: int, bold: bool = False) -> None:
        style = "B" if bold else ""
        pdf.set_font(font_family, style=style if not has_unicode else "", size=size)

    def _cell(w: float, h: float, txt: str, ln: bool = False, align: str = "L", bold: bool = False) -> None:
        _set(size=10 if not bold else 10, bold=bold)
        if has_unicode:
            display = _t(txt, lang)
        else:
            # Helvetica can't render Arabic — strip to ASCII safely
            display = txt.encode("ascii", errors="replace").decode("ascii")
        pdf.cell(w, h, display, ln=1 if ln else 0, align=align)

    def _section(title: str) -> None:
        pdf.ln(4)
        _set(size=11, bold=True)
        txt = _t(title, lang)
        if not has_unicode:
            txt = txt.encode("ascii", errors="replace").decode("ascii")
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 7, txt, ln=1, fill=True, align="R" if is_ar else "L")
        pdf.ln(1)
        _set(size=10)

    def _row(label: str, value: str) -> None:
        lbl = _t(label, lang)
        val = _t(value, lang)
        if not has_unicode:
            lbl = lbl.encode("ascii", errors="replace").decode("ascii")
            val = val.encode("ascii", errors="replace").decode("ascii")
        _set(size=9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(55, 6, lbl, align="R" if is_ar else "L")
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 6, val, ln=1, align="R" if is_ar else "L")

    # ── Header ─────────────────────────────────────────────────────────────────
    _set(size=16, bold=True)
    title_text = _t(L["title"], lang)
    if not has_unicode:
        title_text = title_text.encode("ascii", errors="replace").decode("ascii")
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 12, title_text, ln=1, align="R" if is_ar else "L")
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # ── Run metadata ───────────────────────────────────────────────────────────
    _section(L["scenario"])
    scenario = result.get("scenario", {})
    _row(L["run_id"],   _safe(result.get("run_id", "")))
    _row(L["scenario"], _safe(scenario.get("label", scenario.get("template_id", ""))))
    _row(L["severity"], _pct(scenario.get("severity")))
    _row(L["horizon"],  f"{scenario.get('horizon_hours', '')}h")

    # ── Headline metrics ───────────────────────────────────────────────────────
    headline = result.get("headline", {})
    _section(L["headline_loss"])
    _row(L["headline_loss"],     _usd(headline.get("total_loss_usd")))
    _row(L["nodes_impacted"],    _safe(headline.get("total_nodes_impacted")))
    _row(L["propagation_depth"], _safe(headline.get("propagation_depth")))

    # ── Sector stress ──────────────────────────────────────────────────────────
    _section(L["sector_stress"])
    sectors_data = result.get("sector_rollups", {})
    sector_map = [
        (L["banking"],   sectors_data.get("banking",   {})),
        (L["insurance"], sectors_data.get("insurance", {})),
        (L["fintech"],   sectors_data.get("fintech",   {})),
    ]
    for sector_name, sd in sector_map:
        agg = sd.get("aggregate_stress", sd.get("stress_index", sd.get("risk_score", "")))
        loss = sd.get("total_loss", sd.get("loss_usd", ""))
        clf  = sd.get("classification", sd.get("severity_label", ""))
        _row(f"{_t(sector_name, lang)} — {L['agg_stress']}", _safe(round(float(agg), 3) if agg != "" else "—"))
        if loss:
            _row(f"{_t(sector_name, lang)} — {L['total_loss']}", _usd(loss))
        if clf:
            _row(f"{_t(sector_name, lang)} — {L['classification']}", _safe(clf))

    # ── Decision actions ───────────────────────────────────────────────────────
    decision_inputs = result.get("decision_inputs", {})
    actions = decision_inputs.get("actions", [])
    if actions:
        _section(L["decisions"])
        for i, a in enumerate(actions[:10]):  # cap at 10
            label = _safe(a.get("label", a.get("action_type", f"Action {i+1}")))
            owner = _safe(a.get("owner", ""))
            urgency = _safe(a.get("urgency", ""))
            loss_avoided = _usd(a.get("loss_avoided_usd", "")) if a.get("loss_avoided_usd") else "—"
            cost = _usd(a.get("cost_usd", "")) if a.get("cost_usd") else "—"
            _row(f"{i+1}. {L['action']}", label)
            if owner:
                _row(f"   {L['owner']}", owner)
            if urgency:
                _row(f"   {L['priority']}", urgency)
            _row(f"   {L['loss_avoided']}", loss_avoided)
            _row(f"   {L['cost']}", cost)

    # ── Confidence + warnings ──────────────────────────────────────────────────
    confidence = result.get("confidence", {})
    if confidence:
        _section(L["model_confidence"])
        mc = confidence.get("model_confidence", confidence.get("overall", ""))
        if mc:
            _row(L["model_confidence"], f"{float(mc):.3f}" if mc != "" else "—")

    warnings = result.get("warnings", [])
    if warnings:
        _section(L["warnings"])
        for w in warnings[:8]:
            _row("•", _safe(w))

    # ── Assumptions ───────────────────────────────────────────────────────────
    assumptions = result.get("assumptions", [])
    if assumptions:
        _section(L["assumptions"])
        for a in assumptions:
            _row("•", _safe(a))

    # ── Trust footer ──────────────────────────────────────────────────────────
    trust = result.get("trust", {})
    if trust:
        _section(L["trust"])
        _row(L["model_version"],   _safe(trust.get("model_version", result.get("model_version", ""))))
        _row(L["dataset_version"], _safe(trust.get("dataset_version", result.get("dataset_version", ""))))
        audit_hash = trust.get("audit_hash", "")
        if audit_hash:
            _row(L.get("audit_ref", "Audit Reference"), _safe(audit_hash)[:64])

    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def _error_pdf(error_msg: str) -> bytes:
    """Minimal fallback PDF for unrecoverable errors."""
    try:
        from fpdf import FPDF  # type: ignore[import-untyped]
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", size=12)
        pdf.cell(0, 10, "Impact Observatory — Report Generation Error", ln=1)
        pdf.set_font("Helvetica", size=9)
        safe_msg = error_msg.encode("ascii", errors="replace").decode("ascii")[:200]
        pdf.cell(0, 8, safe_msg, ln=1)
        buf = BytesIO()
        pdf.output(buf)
        return buf.getvalue()
    except Exception:
        # Absolute last resort: return minimal valid PDF bytes
        return b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
