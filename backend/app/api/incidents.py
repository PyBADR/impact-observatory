"""
Global incident intelligence endpoints for Impact Observatory platform.

Provides comprehensive incident querying, timeline analysis, and correlation
detection across natural disasters, infrastructure failures, and other events.
"""

import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.auth import api_key_auth
from app.api.models import (
    IncidentListResponse,
    IncidentDetailResponse,
    IncidentTimelineResponse,
    CorrelationResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory incident storage
incidents_db = {
    "INC001": {
        "id": "INC001",
        "title": "Flash Flood - Wadi Dima, Saudi Arabia",
        "incident_type": "natural_disaster",
        "description": "Severe flash flooding affecting infrastructure and population centers",
        "location": {"latitude": 25.2, "longitude": 55.3, "region": "Saudi Arabia"},
        "severity": "high",
        "status": "ongoing",
        "start_time": datetime(2026, 3, 15, 10, 30),
        "end_time": None,
        "affected_population": 15000,
        "economic_impact_usd": 45000000,
        "casualties": 12,
        "affected_sectors": ["infrastructure", "agriculture"],
        "reporting_sources": ["government", "news"],
    },
    "INC002": {
        "id": "INC002",
        "title": "Port Disruption - Jebel Ali, UAE",
        "incident_type": "infrastructure_failure",
        "description": "Port operations partially halted due to equipment failure",
        "location": {"latitude": 25.0, "longitude": 55.1, "region": "UAE"},
        "severity": "medium",
        "status": "resolved",
        "start_time": datetime(2026, 3, 10, 8, 0),
        "end_time": datetime(2026, 3, 12, 16, 30),
        "affected_population": 5000,
        "economic_impact_usd": 12000000,
        "casualties": 0,
        "affected_sectors": ["trade", "logistics"],
        "reporting_sources": ["news", "industry"],
    },
    "INC003": {
        "id": "INC003",
        "title": "Dust Storm - Greater GCC Region",
        "incident_type": "natural_disaster",
        "description": "Widespread dust storm reducing visibility and air quality",
        "location": {"latitude": 27.5, "longitude": 52.0, "region": "GCC"},
        "severity": "medium",
        "status": "ongoing",
        "start_time": datetime(2026, 3, 25, 6, 0),
        "end_time": None,
        "affected_population": 2000000,
        "economic_impact_usd": 25000000,
        "casualties": 3,
        "affected_sectors": ["health", "transportation"],
        "reporting_sources": ["government", "news", "meteorological"],
    },
}


@router.get(
    "/incidents",
    response_model=IncidentListResponse,
    tags=["Incidents"],
    summary="List all incidents",
)
async def list_incidents(
    api_key: str = Depends(api_key_auth),
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    severity: Optional[str] = Query(None, description="Filter by severity level"),
    status: Optional[str] = Query(None, description="Filter by incident status"),
    region: Optional[str] = Query(None, description="Filter by geographic region"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
) -> IncidentListResponse:
    """
    Retrieve a list of global incidents with filtering and pagination.

    Provides access to incidents spanning natural disasters, infrastructure failures,
    and other significant events affecting the GCC region and global supply chains.

    Args:
        api_key: API key for authentication (injected via header)
        incident_type: Optional filter by incident classification
        severity: Optional filter by severity level (low, medium, high, critical)
        status: Optional filter by status (ongoing, resolved, under_investigation)
        region: Optional filter by affected region
        skip: Pagination offset
        limit: Pagination limit

    Returns:
        IncidentListResponse with paginated list of incidents

    Raises:
        HTTPException: If API authentication fails
    """
    try:
        # Filter incidents based on criteria
        filtered = list(incidents_db.values())

        if incident_type:
            filtered = [i for i in filtered if i["incident_type"] == incident_type]
        if severity:
            filtered = [i for i in filtered if i["severity"] == severity]
        if status:
            filtered = [i for i in filtered if i["status"] == status]
        if region:
            filtered = [
                i for i in filtered if i["location"]["region"].lower() == region.lower()
            ]

        # Apply pagination
        total = len(filtered)
        incidents = filtered[skip : skip + limit]

        logger.info(
            f"Listed {len(incidents)} incidents with filters: "
            f"type={incident_type}, severity={severity}, status={status}, region={region}"
        )

        return IncidentListResponse(
            incidents=[
                {
                    "id": i["id"],
                    "title": i["title"],
                    "incident_type": i["incident_type"],
                    "location": i["location"],
                    "severity": i["severity"],
                    "status": i["status"],
                    "start_time": i["start_time"],
                    "affected_population": i["affected_population"],
                    "economic_impact_usd": i["economic_impact_usd"],
                }
                for i in incidents
            ],
            total=total,
            skip=skip,
            limit=limit,
        )
    except Exception as e:
        logger.error(f"Error listing incidents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list incidents")


@router.get(
    "/incidents/{incident_id}",
    response_model=IncidentDetailResponse,
    tags=["Incidents"],
    summary="Get incident details",
)
async def get_incident_detail(
    incident_id: str, api_key: str = Depends(api_key_auth)
) -> IncidentDetailResponse:
    """
    Retrieve detailed information about a specific incident.

    Provides comprehensive incident data including full timeline, affected sectors,
    reporting sources, and economic impact assessment.

    Args:
        incident_id: Unique incident identifier
        api_key: API key for authentication (injected via header)

    Returns:
        IncidentDetailResponse with complete incident details

    Raises:
        HTTPException: 404 if incident not found, 500 on server error
    """
    try:
        if incident_id not in incidents_db:
            logger.warning(f"Incident {incident_id} not found")
            raise HTTPException(status_code=404, detail="Incident not found")

        incident = incidents_db[incident_id]
        logger.info(f"Retrieved details for incident {incident_id}")

        return IncidentDetailResponse(
            id=incident["id"],
            title=incident["title"],
            incident_type=incident["incident_type"],
            description=incident["description"],
            location=incident["location"],
            severity=incident["severity"],
            status=incident["status"],
            start_time=incident["start_time"],
            end_time=incident["end_time"],
            affected_population=incident["affected_population"],
            economic_impact_usd=incident["economic_impact_usd"],
            casualties=incident["casualties"],
            affected_sectors=incident["affected_sectors"],
            reporting_sources=incident["reporting_sources"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving incident {incident_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve incident")


@router.get(
    "/incidents/timeline/events",
    response_model=IncidentTimelineResponse,
    tags=["Incidents"],
    summary="Get incidents as timeline",
)
async def get_incident_timeline(
    api_key: str = Depends(api_key_auth),
    days_back: int = Query(30, ge=1, description="Number of days to look back"),
    min_severity: Optional[str] = Query(None, description="Minimum severity threshold"),
) -> IncidentTimelineResponse:
    """
    Retrieve incidents organized as a chronological timeline.

    Useful for temporal analysis, trend identification, and understanding
    incident patterns over specified time periods.

    Args:
        api_key: API key for authentication (injected via header)
        days_back: Number of days in the past to include
        min_severity: Optional minimum severity filter (low, medium, high, critical)

    Returns:
        IncidentTimelineResponse with chronologically ordered incidents

    Raises:
        HTTPException: If API authentication fails
    """
    try:
        # Severity levels for filtering
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}

        events = []
        for incident in incidents_db.values():
            # Filter by severity if specified
            if min_severity and severity_order.get(incident["severity"], 0) < severity_order.get(
                min_severity, 0
            ):
                continue

            events.append(
                {
                    "id": incident["id"],
                    "title": incident["title"],
                    "incident_type": incident["incident_type"],
                    "timestamp": incident["start_time"],
                    "severity": incident["severity"],
                    "location": incident["location"],
                }
            )

        # Sort by timestamp descending
        events.sort(key=lambda x: x["timestamp"], reverse=True)

        logger.info(f"Retrieved timeline with {len(events)} incidents (severity filter: {min_severity})")

        return IncidentTimelineResponse(
            events=events,
            total_count=len(events),
            period_days=days_back,
        )
    except Exception as e:
        logger.error(f"Error retrieving timeline: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve timeline")


@router.post(
    "/incidents/correlate",
    response_model=CorrelationResponse,
    tags=["Incidents"],
    summary="Find correlated incidents",
)
async def correlate_incidents(
    api_key: str = Depends(api_key_auth),
    incident_ids: Optional[List[str]] = Query(None, description="Incident IDs to correlate"),
    correlation_threshold: float = Query(
        0.6, ge=0.0, le=1.0, description="Minimum correlation score"
    ),
) -> CorrelationResponse:
    """
    Detect correlations between incidents across multiple domains.

    Identifies related incidents based on temporal proximity, geographic clustering,
    sector interdependencies, and shared causal factors to reveal supply chain
    cascade risks.

    Args:
        api_key: API key for authentication (injected via header)
        incident_ids: Optional list of specific incidents to analyze
        correlation_threshold: Minimum correlation score (0-1) for inclusion

    Returns:
        CorrelationResponse with incident correlations and patterns

    Raises:
        HTTPException: If API authentication fails or validation fails
    """
    try:
        # Validate incident IDs if provided
        if incident_ids:
            for inc_id in incident_ids:
                if inc_id not in incidents_db:
                    logger.warning(f"Incident {inc_id} not found in correlation analysis")
                    raise HTTPException(status_code=400, detail=f"Incident {inc_id} not found")
            incidents_to_analyze = [incidents_db[inc_id] for inc_id in incident_ids]
        else:
            incidents_to_analyze = list(incidents_db.values())

        # Compute correlations between incidents
        correlations = []
        for i, inc1 in enumerate(incidents_to_analyze):
            for inc2 in incidents_to_analyze[i + 1 :]:
                # Simple correlation scoring based on:
                # - Temporal proximity (within 30 days)
                # - Geographic proximity (within 500km)
                # - Shared affected sectors
                # - Economic impact similarity

                time_diff = abs(
                    (inc1["start_time"] - inc2["start_time"]).total_seconds() / 86400
                )
                time_score = max(0, 1 - (time_diff / 30)) if time_diff < 30 else 0

                # Geographic proximity (simplified lat/lon distance)
                lat_diff = abs(inc1["location"]["latitude"] - inc2["location"]["latitude"])
                lon_diff = abs(inc1["location"]["longitude"] - inc2["location"]["longitude"])
                dist_degrees = (lat_diff**2 + lon_diff**2) ** 0.5
                geo_score = max(0, 1 - (dist_degrees / 10)) if dist_degrees < 10 else 0

                # Sector overlap
                shared_sectors = set(inc1["affected_sectors"]) & set(
                    inc2["affected_sectors"]
                )
                sector_score = len(shared_sectors) / max(
                    len(inc1["affected_sectors"]), len(inc2["affected_sectors"])
                )

                # Weighted correlation score
                correlation_score = (
                    0.3 * time_score + 0.2 * geo_score + 0.5 * sector_score
                )

                if correlation_score >= correlation_threshold:
                    correlations.append(
                        {
                            "incident_1": inc1["id"],
                            "incident_2": inc2["id"],
                            "correlation_score": round(correlation_score, 3),
                            "shared_sectors": list(shared_sectors),
                            "temporal_gap_days": round(time_diff, 1),
                        }
                    )

        logger.info(
            f"Correlated {len(incidents_to_analyze)} incidents, "
            f"found {len(correlations)} correlations above {correlation_threshold}"
        )

        return CorrelationResponse(
            correlations=correlations,
            total_pairs_analyzed=len(incidents_to_analyze) * (len(incidents_to_analyze) - 1) // 2,
            correlation_threshold=correlation_threshold,
            cascade_risk_identified=len(correlations) > 0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error correlating incidents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to correlate incidents")
