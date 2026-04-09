"""
Impact Observatory | مرصد الأثر
Error Translation Layer — converts technical errors into executive-readable
bilingual messages with actionable guidance.

Architecture Layer: Narrative → Error Handling
No raw tracebacks reach the client. Every error becomes a structured brief.
"""
from __future__ import annotations

from typing import Any


# ─────────────────────────────────────────────────────────────────────────────
# Error class registry — maps HTTP status + error type to human-readable briefs
# ─────────────────────────────────────────────────────────────────────────────

_ERROR_CATALOG: dict[str, dict[str, str]] = {
    # ── Validation errors (422) ─────────────────────────────────────────
    "validation_error": {
        "title": "Invalid Configuration",
        "title_ar": "إعداد غير صالح",
        "message": "The scenario could not be executed because one or more input parameters are outside accepted bounds.",
        "message_ar": "تعذّر تنفيذ السيناريو لأن واحداً أو أكثر من المعاملات المدخلة خارج النطاق المقبول.",
        "guidance": "Review the scenario parameters: severity must be 0.0–1.0, horizon_hours must be 1–8760, and scenario_id must match the catalog.",
        "guidance_ar": "راجع معاملات السيناريو: الشدة يجب أن تكون بين 0.0–1.0، ساعات الأفق بين 1–8760، ومعرّف السيناريو يجب أن يتطابق مع الكتالوج.",
    },
    "invalid_scenario": {
        "title": "Unknown Scenario",
        "title_ar": "سيناريو غير معروف",
        "message": "The requested scenario identifier does not exist in the Impact Observatory catalog.",
        "message_ar": "معرّف السيناريو المطلوب غير موجود في كتالوج مرصد الأثر.",
        "guidance": "Use GET /api/v1/scenarios to retrieve the full list of available scenarios.",
        "guidance_ar": "استخدم GET /api/v1/scenarios للحصول على القائمة الكاملة للسيناريوهات المتاحة.",
    },
    "severity_out_of_range": {
        "title": "Severity Out of Range",
        "title_ar": "شدة خارج النطاق",
        "message": "Event severity must be between 0.0 (nominal) and 1.0 (catastrophic).",
        "message_ar": "يجب أن تكون شدة الحدث بين 0.0 (طبيعي) و1.0 (كارثي).",
        "guidance": "Adjust severity to a value within [0.0, 1.0]. Typical ranges: Low (0.2–0.4), Moderate (0.4–0.6), High (0.6–0.8), Extreme (0.8–1.0).",
        "guidance_ar": "عدّل الشدة إلى قيمة ضمن [0.0, 1.0]. النطاقات النموذجية: منخفض (0.2–0.4)، متوسط (0.4–0.6)، مرتفع (0.6–0.8)، شديد (0.8–1.0).",
    },

    # ── Authentication errors (401/403) ─────────────────────────────────
    "unauthorized": {
        "title": "Authentication Required",
        "title_ar": "المصادقة مطلوبة",
        "message": "This endpoint requires a valid API key or bearer token.",
        "message_ar": "تتطلب نقطة النهاية هذه مفتاح API أو رمز حامل صالح.",
        "guidance": "Include 'X-API-Key: <your-key>' header or 'Authorization: Bearer <token>' in the request.",
        "guidance_ar": "أضف ترويسة 'X-API-Key: <مفتاحك>' أو 'Authorization: Bearer <الرمز>' في الطلب.",
    },
    "forbidden": {
        "title": "Insufficient Permissions",
        "title_ar": "صلاحيات غير كافية",
        "message": "Your role does not have permission to execute this operation.",
        "message_ar": "دورك لا يمتلك صلاحية تنفيذ هذه العملية.",
        "guidance": "Contact your organization administrator to request the required permission level.",
        "guidance_ar": "تواصل مع مسؤول مؤسستك لطلب مستوى الصلاحية المطلوب.",
    },

    # ── Not found (404) ─────────────────────────────────────────────────
    "run_not_found": {
        "title": "Run Not Found",
        "title_ar": "التشغيل غير موجود",
        "message": "The specified run ID does not exist or has expired from the session store.",
        "message_ar": "معرّف التشغيل المحدد غير موجود أو انتهت صلاحيته من مخزن الجلسة.",
        "guidance": "Use POST /api/v1/runs to execute a new scenario run, or GET /api/v1/runs to list recent runs.",
        "guidance_ar": "استخدم POST /api/v1/runs لتنفيذ تشغيل سيناريو جديد، أو GET /api/v1/runs لعرض التشغيلات الأخيرة.",
    },
    "resource_not_found": {
        "title": "Resource Not Found",
        "title_ar": "المورد غير موجود",
        "message": "The requested resource could not be located.",
        "message_ar": "تعذّر العثور على المورد المطلوب.",
        "guidance": "Verify the resource identifier and endpoint path. Refer to /docs for the API reference.",
        "guidance_ar": "تحقق من معرّف المورد ومسار نقطة النهاية. ارجع إلى /docs لمرجع الواجهة البرمجية.",
    },

    # ── Engine errors (500) ──────────────────────────────────────────────
    "engine_error": {
        "title": "Simulation Engine Failure",
        "title_ar": "فشل محرك المحاكاة",
        "message": "The simulation engine encountered an internal error during pipeline execution.",
        "message_ar": "واجه محرك المحاكاة خطأً داخلياً أثناء تنفيذ خط الأنابيب.",
        "guidance": "This is typically transient. Retry the request. If the error persists, it may indicate a scenario configuration issue — try reducing severity or horizon_hours.",
        "guidance_ar": "هذا عابر عادةً. أعد المحاولة. إذا استمر الخطأ، فقد يشير إلى مشكلة في إعداد السيناريو — حاول تقليل الشدة أو ساعات الأفق.",
    },
    "timeout": {
        "title": "Simulation Timeout",
        "title_ar": "انتهاء مهلة المحاكاة",
        "message": "The simulation exceeded the maximum execution time. Complex scenarios with extreme horizons may require more time.",
        "message_ar": "تجاوزت المحاكاة الحد الأقصى لوقت التنفيذ. قد تتطلب السيناريوهات المعقدة ذات الآفاق القصوى وقتاً أطول.",
        "guidance": "Reduce horizon_hours (try 168 or 336 instead of 8760) or lower severity to reduce computational load.",
        "guidance_ar": "قلّل ساعات الأفق (جرّب 168 أو 336 بدلاً من 8760) أو خفّض الشدة لتقليل الحمل الحسابي.",
    },

    # ── Data feed errors ─────────────────────────────────────────────────
    "feed_unavailable": {
        "title": "External Data Feed Unavailable",
        "title_ar": "مصدر بيانات خارجي غير متاح",
        "message": "One or more real-time data feeds (ACLED, AIS, OpenSky) are temporarily unreachable. The simulation will use cached/seed data.",
        "message_ar": "واحد أو أكثر من مصادر البيانات الحية (ACLED، AIS، OpenSky) غير متاح مؤقتاً. ستستخدم المحاكاة بيانات مخزنة/أولية.",
        "guidance": "No action required. The simulation proceeds with fallback data. Results may be slightly less current but remain structurally valid.",
        "guidance_ar": "لا يلزم اتخاذ إجراء. تستمر المحاكاة ببيانات احتياطية. قد تكون النتائج أقل حداثة قليلاً لكنها تظل صالحة هيكلياً.",
    },

    # ── Rate limiting (429) ──────────────────────────────────────────────
    "rate_limited": {
        "title": "Rate Limit Exceeded",
        "title_ar": "تجاوز حد المعدل",
        "message": "Too many requests in a short period. The platform enforces rate limits to ensure fair resource allocation.",
        "message_ar": "عدد كبير جداً من الطلبات في فترة قصيرة. تفرض المنصة حدود معدل لضمان توزيع عادل للموارد.",
        "guidance": "Wait 30 seconds before retrying. For higher throughput, contact your account manager about enterprise tier access.",
        "guidance_ar": "انتظر 30 ثانية قبل إعادة المحاولة. لمعدل نقل أعلى، تواصل مع مدير حسابك بشأن الوصول للمستوى المؤسسي.",
    },

    # ── Fallback ─────────────────────────────────────────────────────────
    "unknown": {
        "title": "Unexpected Error",
        "title_ar": "خطأ غير متوقع",
        "message": "An unexpected condition occurred. The engineering team has been notified.",
        "message_ar": "حدثت حالة غير متوقعة. تم إخطار الفريق الهندسي.",
        "guidance": "Retry the request. If the issue persists, include the trace_id in your support ticket.",
        "guidance_ar": "أعد الطلب. إذا استمرت المشكلة، أرفق trace_id في تذكرة الدعم الخاصة بك.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Status code → error type mapping
# ─────────────────────────────────────────────────────────────────────────────

_STATUS_MAP: dict[int, str] = {
    400: "validation_error",
    401: "unauthorized",
    403: "forbidden",
    404: "resource_not_found",
    422: "validation_error",
    429: "rate_limited",
    500: "engine_error",
    502: "engine_error",
    503: "engine_error",
    504: "timeout",
}


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def translate_error(
    status_code: int = 500,
    error_type: str | None = None,
    raw_detail: str | None = None,
    trace_id: str | None = None,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    """Translate a technical error into a structured executive-readable brief.

    Parameters
    ----------
    status_code : int
        HTTP status code of the error.
    error_type : str, optional
        Specific error type key (e.g., 'invalid_scenario'). If None,
        inferred from status_code.
    raw_detail : str, optional
        Raw technical error message (included for debugging, not shown
        to executives).
    trace_id : str, optional
        Correlation ID for audit trail linking.
    scenario_id : str, optional
        The scenario that triggered the error, if applicable.

    Returns
    -------
    dict
        Structured error brief with bilingual messages and guidance.
    """
    # Resolve error type
    key = error_type if error_type and error_type in _ERROR_CATALOG else _STATUS_MAP.get(status_code, "unknown")
    entry = _ERROR_CATALOG[key]

    # Detect specific sub-types from raw_detail
    if raw_detail:
        detail_lower = raw_detail.lower()
        if "scenario" in detail_lower and ("not found" in detail_lower or "invalid" in detail_lower or "unknown" in detail_lower):
            entry = _ERROR_CATALOG["invalid_scenario"]
            key = "invalid_scenario"
        elif "severity" in detail_lower and ("range" in detail_lower or "between" in detail_lower):
            entry = _ERROR_CATALOG["severity_out_of_range"]
            key = "severity_out_of_range"
        elif "run" in detail_lower and "not found" in detail_lower:
            entry = _ERROR_CATALOG["run_not_found"]
            key = "run_not_found"
        elif "timeout" in detail_lower or "timed out" in detail_lower:
            entry = _ERROR_CATALOG["timeout"]
            key = "timeout"
        elif "feed" in detail_lower or "acled" in detail_lower or "opensky" in detail_lower:
            entry = _ERROR_CATALOG["feed_unavailable"]
            key = "feed_unavailable"

    result: dict[str, Any] = {
        "error": True,
        "error_type": key,
        "status_code": status_code,
        "title": entry["title"],
        "title_ar": entry["title_ar"],
        "message": entry["message"],
        "message_ar": entry["message_ar"],
        "guidance": entry["guidance"],
        "guidance_ar": entry["guidance_ar"],
    }

    if trace_id:
        result["trace_id"] = trace_id
    if scenario_id:
        result["scenario_id"] = scenario_id
    if raw_detail:
        result["technical_detail"] = raw_detail

    return result


def error_response_model() -> dict[str, Any]:
    """Return OpenAPI schema for error responses — used in FastAPI docs."""
    return {
        "description": "Structured error with bilingual executive messaging",
        "content": {
            "application/json": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "boolean", "example": True},
                        "error_type": {"type": "string", "example": "validation_error"},
                        "status_code": {"type": "integer", "example": 422},
                        "title": {"type": "string", "example": "Invalid Configuration"},
                        "title_ar": {"type": "string", "example": "إعداد غير صالح"},
                        "message": {"type": "string"},
                        "message_ar": {"type": "string"},
                        "guidance": {"type": "string"},
                        "guidance_ar": {"type": "string"},
                        "trace_id": {"type": "string", "example": "a1b2c3d4"},
                        "scenario_id": {"type": "string", "example": "hormuz_chokepoint_disruption"},
                        "technical_detail": {"type": "string"},
                    },
                    "required": ["error", "error_type", "status_code", "title", "message"],
                },
            },
        },
    }
