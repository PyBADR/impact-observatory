"""Oil & Energy Data Connector.

Fetches real oil price data from public APIs and converts to P1 OilEnergySignal format.

Primary source: US EIA (Energy Information Administration) API
  - Free, no auth required for summary data
  - Brent and WTI spot prices
  - Updated daily

Fallback: Yahoo Finance via public endpoint (no API key)

Architecture Layer: Data (Layer 1) — Ingestion
Owner: Data Engineering
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from src.data_foundation.schemas.oil_energy_signals import OilEnergySignal
from src.data_foundation.schemas.enums import ConfidenceMethod, Currency


class OilPriceRecord(BaseModel):
    """Intermediate model for raw oil price data."""
    benchmark: str
    price_usd: float
    date: date
    source: str
    change_pct: Optional[float] = None


class ConnectorResult(BaseModel):
    """Result of a connector fetch operation."""
    success: bool
    records: List[OilEnergySignal] = Field(default_factory=list)
    raw_count: int = 0
    error: Optional[str] = None
    source: str = ""
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── EIA API ──────────────────────────────────────────────────────────────────

EIA_PETROLEUM_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"

# Free EIA series for Brent and WTI spot prices
EIA_SERIES = {
    "BRENT": "RBRTE",
    "WTI": "RWTC",
}


async def fetch_eia_prices(
    api_key: str = "",
    days_back: int = 30,
) -> List[OilPriceRecord]:
    """Fetch oil prices from EIA API.

    Note: EIA API v2 requires an API key for most endpoints.
    If no key is provided, falls back to a summary endpoint.
    """
    records: List[OilPriceRecord] = []

    if not api_key:
        # Use the free summary endpoint (no key required)
        url = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
        params = {
            "frequency": "daily",
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": str(min(days_back * 2, 100)),
        }
    else:
        url = EIA_PETROLEUM_URL
        params = {
            "api_key": api_key,
            "frequency": "daily",
            "data[0]": "value",
            "sort[0][column]": "period",
            "sort[0][direction]": "desc",
            "length": str(min(days_back * 2, 100)),
        }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        for row in data.get("response", {}).get("data", []):
            try:
                series = row.get("series", "")
                benchmark = "BRENT" if "RBRTE" in series else "WTI" if "RWTC" in series else series
                records.append(OilPriceRecord(
                    benchmark=benchmark,
                    price_usd=float(row["value"]),
                    date=date.fromisoformat(row["period"]),
                    source="eia-api",
                ))
            except (KeyError, ValueError):
                continue

    except Exception:
        pass

    return records


# ── Yahoo Finance fallback ───────────────────────────────────────────────────

YAHOO_BRENT_URL = "https://query1.finance.yahoo.com/v8/finance/chart/BZ=F"
YAHOO_WTI_URL = "https://query1.finance.yahoo.com/v8/finance/chart/CL=F"


async def fetch_yahoo_oil(days_back: int = 30) -> List[OilPriceRecord]:
    """Fetch Brent and WTI from Yahoo Finance public API (no auth)."""
    records: List[OilPriceRecord] = []

    for benchmark, url in [("BRENT", YAHOO_BRENT_URL), ("WTI", YAHOO_WTI_URL)]:
        try:
            params = {
                "interval": "1d",
                "range": f"{days_back}d",
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params, headers={
                    "User-Agent": "Mozilla/5.0 (impact-observatory)"
                })
                resp.raise_for_status()
                data = resp.json()

            result = data.get("chart", {}).get("result", [{}])[0]
            timestamps = result.get("timestamp", [])
            closes = result.get("indicators", {}).get("quote", [{}])[0].get("close", [])

            prev = None
            for ts, price in zip(timestamps, closes):
                if price is None:
                    continue
                d = date.fromtimestamp(ts)
                change_pct = None
                if prev is not None:
                    change_pct = round((price - prev) / prev * 100, 4)
                records.append(OilPriceRecord(
                    benchmark=benchmark,
                    price_usd=round(price, 2),
                    date=d,
                    source="yahoo-finance",
                    change_pct=change_pct,
                ))
                prev = price
        except Exception:
            continue

    return records


# ── Converter: OilPriceRecord → OilEnergySignal ─────────────────────────────

def _to_signal(rec: OilPriceRecord) -> OilEnergySignal:
    """Convert a raw price record to a P1 OilEnergySignal."""
    signal_id = f"{rec.benchmark}-SPOT-{rec.date.isoformat()}"
    return OilEnergySignal(
        signal_id=signal_id,
        signal_type="CRUDE_PRICE_SPOT",
        benchmark=rec.benchmark,
        country=None,  # Global benchmark
        entity_id=None,
        value=rec.price_usd,
        unit="usd_per_barrel",
        currency=Currency.USD,
        observation_date=rec.date,
        previous_value=None,
        change_pct=rec.change_pct,
        fiscal_breakeven_price=None,
        source_id=rec.source,
        confidence_score=0.90,
        confidence_method=ConfidenceMethod.SOURCE_DECLARED,
    )


# ── Main connector function ─────────────────────────────────────────────────

async def fetch_oil_energy_signals(
    eia_api_key: str = "",
    days_back: int = 30,
) -> ConnectorResult:
    """Fetch oil/energy signals from real sources.

    Strategy:
      1. Try EIA API (authoritative, government source)
      2. Fall back to Yahoo Finance (free, no auth)
      3. Return empty result if both fail
    """
    # Try EIA first
    raw = await fetch_eia_prices(api_key=eia_api_key, days_back=days_back)
    source = "eia-api"

    # Fallback to Yahoo
    if not raw:
        raw = await fetch_yahoo_oil(days_back=days_back)
        source = "yahoo-finance"

    if not raw:
        return ConnectorResult(
            success=False,
            error="All oil price sources unavailable",
            source="none",
        )

    signals = [_to_signal(r) for r in raw]

    return ConnectorResult(
        success=True,
        records=signals,
        raw_count=len(raw),
        source=source,
    )


# ── FastAPI route for connector ──────────────────────────────────────────────

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.data_foundation.api.deps import get_session
from src.data_foundation.models.tables import OilEnergySignalORM
from src.data_foundation.models.converters import _base_fields, _enum_val

connector_router = APIRouter(
    prefix="/foundation/connectors/oil-energy",
    tags=["Data Foundation — Connectors"],
)


def _oil_signal_to_orm(s: OilEnergySignal) -> OilEnergySignalORM:
    return OilEnergySignalORM(
        **_base_fields(s),
        signal_id=s.signal_id,
        signal_type=s.signal_type,
        benchmark=s.benchmark,
        country=_enum_val(s.country) if s.country else None,
        entity_id=s.entity_id,
        value=s.value,
        unit=s.unit,
        currency=_enum_val(s.currency),
        observation_date=s.observation_date,
        previous_value=s.previous_value,
        change_pct=s.change_pct,
        fiscal_breakeven_price=s.fiscal_breakeven_price,
        source_id=s.source_id,
        confidence_score=s.confidence_score,
        confidence_method=_enum_val(s.confidence_method),
    )


@connector_router.post("/fetch")
async def fetch_and_store(
    days_back: int = Query(7, ge=1, le=90),
    persist: bool = Query(True),
    session: AsyncSession = Depends(get_session),
):
    """Fetch oil prices from real sources and optionally persist to DB."""
    result = await fetch_oil_energy_signals(days_back=days_back)

    if not result.success:
        return {
            "success": False,
            "error": result.error,
            "records_fetched": 0,
            "records_persisted": 0,
        }

    persisted = 0
    if persist:
        for signal in result.records:
            try:
                orm = _oil_signal_to_orm(signal)
                await session.merge(orm)
                persisted += 1
            except Exception:
                continue
        await session.commit()

    return {
        "success": True,
        "source": result.source,
        "records_fetched": result.raw_count,
        "records_persisted": persisted,
        "sample": [s.model_dump(mode="json") for s in result.records[:3]],
        "fetched_at": result.fetched_at.isoformat(),
    }


@connector_router.get("/status")
async def connector_status():
    """Check connectivity to oil price data sources."""
    results = {}

    # Test EIA
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.eia.gov/v2/petroleum/pri/spt/data/", params={"length": "1"})
            results["eia"] = {"status": "reachable", "http_code": resp.status_code}
    except Exception as e:
        results["eia"] = {"status": "unreachable", "error": str(e)}

    return results
