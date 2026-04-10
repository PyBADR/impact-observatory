"""GitHub connector for repository audit and CI/CD status.

Monitors:
- Latest commits on main branch
- Open pull requests
- GitHub Actions workflow status
- Repository health metrics

Requires GITHUB_TOKEN environment variable.
Repository: PyBADR/impact-observatory
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("observatory.github")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "PyBADR")
REPO_NAME = os.getenv("GITHUB_REPO_NAME", "impact-observatory")
GITHUB_API_BASE = "https://api.github.com"


def _headers() -> dict[str, str]:
    h = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return h


async def get_latest_commits(count: int = 5) -> list[dict[str, Any]]:
    """Get latest commits on main branch."""
    if not GITHUB_TOKEN:
        logger.info("[GitHub] Not configured — skipping")
        return []

    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/commits",
                headers=_headers(),
                params={"per_page": str(count), "sha": "main"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [
                    {
                        "sha": c["sha"][:8],
                        "message": c["commit"]["message"].split("\n")[0][:80],
                        "author": c["commit"]["author"]["name"],
                        "date": c["commit"]["author"]["date"],
                    }
                    for c in data
                ]
    except Exception as e:
        logger.warning("[GitHub] Failed: %s", e)
        return []


async def get_open_prs() -> list[dict[str, Any]]:
    """Get open pull requests."""
    if not GITHUB_TOKEN:
        return []

    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/pulls",
                headers=_headers(),
                params={"state": "open", "per_page": "10"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return [
                    {
                        "number": pr["number"],
                        "title": pr["title"][:80],
                        "author": pr["user"]["login"],
                        "branch": pr["head"]["ref"],
                        "created_at": pr["created_at"],
                        "labels": [l["name"] for l in pr.get("labels", [])],
                    }
                    for pr in data
                ]
    except Exception as e:
        logger.warning("[GitHub] Failed: %s", e)
        return []


async def get_workflow_status() -> dict[str, Any]:
    """Get latest GitHub Actions workflow run status."""
    if not GITHUB_TOKEN:
        return {"status": "unknown", "configured": False}

    import aiohttp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{GITHUB_API_BASE}/repos/{REPO_OWNER}/{REPO_NAME}/actions/runs",
                headers=_headers(),
                params={"per_page": "1", "branch": "main"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return {"status": "error", "http_status": resp.status}
                data = await resp.json()
                runs = data.get("workflow_runs", [])
                if not runs:
                    return {"status": "no_runs"}
                r = runs[0]
                return {
                    "status": r.get("conclusion", r.get("status", "unknown")),
                    "name": r.get("name", ""),
                    "run_id": r.get("id"),
                    "created_at": r.get("created_at", ""),
                    "head_sha": r.get("head_sha", "")[:8],
                    "configured": True,
                }
    except Exception as e:
        logger.warning("[GitHub] Failed: %s", e)
        return {"status": "error", "error": str(e)}
