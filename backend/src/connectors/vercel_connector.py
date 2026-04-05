"""Vercel connector for deployment status monitoring.

Checks deployment state of the Impact Observatory frontend.
Used by observability layer to verify production health after code pushes.

Requires VERCEL_TOKEN and VERCEL_PROJECT_ID environment variables.
Falls back to status "unknown" if not configured.
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("observatory.vercel")

VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
VERCEL_PROJECT_ID = os.getenv("VERCEL_PROJECT_ID", "")
VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")
VERCEL_API_BASE = "https://api.vercel.com"


async def get_latest_deployment() -> dict[str, Any]:
    """Get the latest deployment for the Impact Observatory frontend.

    Returns dict with: id, url, state, created_at, ready_at, meta.
    Falls back to empty dict if Vercel not configured.
    """
    if not VERCEL_TOKEN or not VERCEL_PROJECT_ID:
        logger.info("[Vercel] Not configured — skipping deployment check")
        return {"state": "unknown", "configured": False}

    import aiohttp

    headers = {"Authorization": f"Bearer {VERCEL_TOKEN}"}
    params: dict[str, str] = {"projectId": VERCEL_PROJECT_ID, "limit": "1"}
    if VERCEL_TEAM_ID:
        params["teamId"] = VERCEL_TEAM_ID

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{VERCEL_API_BASE}/v6/deployments",
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning("[Vercel] HTTP %d", resp.status)
                    return {"state": "error", "http_status": resp.status}

                data = await resp.json()
                deployments = data.get("deployments", [])
                if not deployments:
                    return {"state": "no_deployments"}

                d = deployments[0]
                return {
                    "id": d.get("uid", ""),
                    "url": d.get("url", ""),
                    "state": d.get("state", ""),
                    "created_at": d.get("created", ""),
                    "ready_at": d.get("ready", ""),
                    "meta": {
                        "git_branch": d.get("meta", {}).get("githubCommitRef", ""),
                        "git_sha": d.get("meta", {}).get("githubCommitSha", "")[:8],
                        "git_message": d.get("meta", {}).get("githubCommitMessage", ""),
                    },
                    "configured": True,
                }
    except Exception as e:
        logger.warning("[Vercel] Failed: %s", e)
        return {"state": "error", "error": str(e)}


async def get_deployment_status() -> str:
    """Get simple deployment status: READY, BUILDING, ERROR, or UNKNOWN."""
    deployment = await get_latest_deployment()
    state = deployment.get("state", "unknown").upper()
    return state if state in ("READY", "BUILDING", "ERROR", "QUEUED") else "UNKNOWN"
