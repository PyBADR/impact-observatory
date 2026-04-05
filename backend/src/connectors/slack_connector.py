"""Slack connector for HITL notifications and decision audit alerts.

Sends structured alerts when:
- Scenario runs complete (run_id, severity, total_loss)
- Decision actions need review (PENDING_REVIEW)
- Actions are approved/rejected (HITL audit trail)
- Pipeline errors occur (observability)

Requires SLACK_WEBHOOK_URL environment variable.
Falls back to logger.info if not configured.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger("observatory.slack")

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")


def _format_usd(usd: float) -> str:
    if usd >= 1e9:
        return f"${usd / 1e9:.1f}B"
    if usd >= 1e6:
        return f"${usd / 1e6:.0f}M"
    return f"${usd:,.0f}"


async def send_slack_message(text: str, blocks: list[dict] | None = None) -> bool:
    """Send a message to Slack via webhook. Returns True on success."""
    if not SLACK_WEBHOOK_URL:
        logger.info("[Slack-Dry] %s", text)
        return False

    import aiohttp

    payload: dict[str, Any] = {"text": text}
    if blocks:
        payload["blocks"] = blocks

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                SLACK_WEBHOOK_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status == 200:
                    logger.info("[Slack] Sent: %s", text[:80])
                    return True
                logger.warning("[Slack] HTTP %d: %s", resp.status, await resp.text())
                return False
    except Exception as e:
        logger.warning("[Slack] Failed: %s", e)
        return False


async def notify_run_complete(result: dict[str, Any]) -> bool:
    """Notify Slack that a scenario run completed."""
    run_id = result.get("run_id", "unknown")
    scenario_id = result.get("scenario_id", "unknown")
    headline = result.get("headline", {})
    total_loss = headline.get("total_loss_usd", 0)
    risk_level = result.get("risk_level", "UNKNOWN")
    duration_ms = result.get("duration_ms", 0)

    decisions = result.get("decisions", result.get("decision_plan", {}))
    action_count = len(decisions.get("actions", []))

    risk_emoji = {
        "SEVERE": "🔴", "HIGH": "🟠", "ELEVATED": "🟡",
        "GUARDED": "🟢", "LOW": "🟢", "NOMINAL": "⚪",
    }.get(risk_level, "⚫")

    text = (
        f"{risk_emoji} *Scenario Run Complete*\n"
        f"• Scenario: `{scenario_id}`\n"
        f"• Loss: {_format_usd(total_loss)} | Risk: {risk_level}\n"
        f"• Actions: {action_count} pending review\n"
        f"• Run ID: `{run_id}` ({duration_ms}ms)"
    )

    return await send_slack_message(text)


async def notify_action_decision(
    run_id: str, action_id: str, action_text: str, status: str, owner: str
) -> bool:
    """Notify Slack that a HITL decision was made on an action."""
    emoji = "✅" if status == "APPROVED" else "❌"
    text = (
        f"{emoji} *Action {status}*\n"
        f"• Action: {action_text[:100]}\n"
        f"• Owner: {owner}\n"
        f"• Run: `{run_id}` | Action: `{action_id}`"
    )
    return await send_slack_message(text)


async def notify_pipeline_error(
    scenario_id: str, trace_id: str, error: str
) -> bool:
    """Notify Slack of a pipeline error."""
    text = (
        f"🚨 *Pipeline Error*\n"
        f"• Scenario: `{scenario_id}`\n"
        f"• Error: {error[:200]}\n"
        f"• Trace: `{trace_id}`"
    )
    return await send_slack_message(text)
