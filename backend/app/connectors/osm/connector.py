"""
OpenStreetMap (OSM) Reference Data Connector.

Provides OSMReferenceLoader for querying infrastructure data from Overpass API
with support for offline caching and GCC-region focused queries.
"""

import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import requests

logger = logging.getLogger(__name__)


@dataclass
class OSMFeature:
    """Represents a normalized OSM feature for canonical schema matching."""
    osm_id: str
    osm_type: str  # 'node', 'way', 'relation'
    name: str
    feature_type: str  # 'airport', 'port', 'road', 'building'
    latitude: float
    longitude: float
    tags: Dict[str, str]
    country: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert feature to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OSMFeature':
        """Create feature from dictionary."""
        return cls(**data)


class OSMReferenceLoader:
    """
    Loads infrastructure reference data from OpenStreetMap.

    Provides methods to query airports, ports, roads, and buildings in GCC region.
    Supports offline caching with JSON serialization.
    """

    # GCC Bounding box: lat 12-32, lon 34-60
    GCC_BBOX = {
        'south': 12.0,
        'west': 34.0,
        'north': 32.0,
        'east': 60.0
    }

    # Overpass API endpoint
    OVERPASS_API = "https://overpass-api.de/api/interpreter"

    # Cache directory path
    CACHE_DIR = Path(__file__).parent / "cache"

    def __init__(self, use_cache: bool = True, cache_dir: Optional[Path] = None):
        """
        Initialize OSM Reference Loader.

        Args:
            use_cache: Whether to use cached data
            cache_dir: Optional custom cache directory path
        """
        self.use_cache = use_cache
        self.cache_dir = cache_dir or self.CACHE_DIR

        if self.use_cache:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def query_airports(self) -> List[OSMFeature]:
        """
        Query GCC airports from OpenStreetMap.

        Returns:
            List of OSMFeature objects representing airports
        """
        logger.info("Querying GCC airports from OpenStreetMap")

        query = self._build_query(
            feature_type="aeroway=aerodrome",
            bbox=self.GCC_BBOX
        )

        features = self._execute_query("airports", query)
        return features

    def query_ports(self) -> List[OSMFeature]:
        """
        Query GCC ports from OpenStreetMap.

        Returns:
            List of OSMFeature objects representing ports
        """
        logger.info("Querying GCC ports from OpenStreetMap")

        query = self._build_query(
            feature_type="seamark:type=harbour OR landuse=port",
            bbox=self.GCC_BBOX
        )

        features = self._execute_query("ports", query)
        return features

    def query_roads(self) -> List[OSMFeature]:
        """
        Query GCC roads from OpenStreetMap.

        Returns:
            List of OSMFeature objects representing major roads
        """
        logger.info("Querying GCC roads from OpenStreetMap")

        query = self._build_query(
            feature_type="highway=motorway OR highway=trunk OR highway=primary",
            bbox=self.GCC_BBOX
        )

        features = self._execute_query("roads", query)
        return features

    def query_buildings(self) -> List[OSMFeature]:
        """
        Query GCC buildings from OpenStreetMap.

        Returns:
            List of OSMFeature objects representing industrial/commercial buildings
        """
        logger.info("Querying GCC buildings from OpenStreetMap")

        query = self._build_query(
            feature_type="building=industrial OR building=commercial OR building=warehouse",
            bbox=self.GCC_BBOX
        )

        features = self._execute_query("buildings", query)
        return features

    def _build_query(self, feature_type: str, bbox: Dict[str, float]) -> str:
        """
        Build Overpass API query string.

        Args:
            feature_type: OSM tag filter
            bbox: Bounding box with south, west, north, east

        Returns:
            Overpass QL query string
        """
        bbox_str = f"{bbox['south']},{bbox['west']},{bbox['north']},{bbox['east']}"

        query = f"""
        [bbox:{bbox_str}];
        (
            {feature_type};
        );
        out center;
        """
        return query.strip()

    def _execute_query(self, feature_name: str, query: str) -> List[OSMFeature]:
        """
        Execute Overpass query with caching support.

        Args:
            feature_name: Name of feature type for cache
            query: Overpass QL query string

        Returns:
            List of normalized OSMFeature objects
        """
        cache_file = self.cache_dir / f"osm_{feature_name}.json"

        # Try loading from cache first
        if self.use_cache and cache_file.exists():
            logger.info(f"Loading {feature_name} from cache: {cache_file}")
            return self._load_cache(cache_file)

        try:
            logger.info(f"Executing Overpass query for {feature_name}")
            response = requests.post(
                self.OVERPASS_API,
                data={"data": query},
                timeout=30
            )
            response.raise_for_status()

            features = self._parse_overpass_response(
                response.json(),
                feature_name
            )

            # Cache results if enabled
            if self.use_cache:
                self._save_cache(cache_file, features)

            logger.info(f"Retrieved {len(features)} {feature_name} from Overpass API")
            return features

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query Overpass API: {e}")

            # Fall back to empty seed data or previous cache
            if cache_file.exists():
                logger.warning(f"Falling back to cache for {feature_name}")
                return self._load_cache(cache_file)

            logger.warning(f"No cached data available for {feature_name}, returning empty list")
            return []

    def _parse_overpass_response(self, data: Dict[str, Any], feature_type: str) -> List[OSMFeature]:
        """
        Parse Overpass API JSON response.

        Args:
            data: Response JSON from Overpass API
            feature_type: Type of feature being parsed

        Returns:
            List of normalized OSMFeature objects
        """
        features = []

        if "elements" not in data:
            logger.warning(f"No elements in Overpass response for {feature_type}")
            return features

        for element in data.get("elements", []):
            try:
                # Extract coordinates
                lat = element.get("lat") or element.get("center", {}).get("lat")
                lon = element.get("lon") or element.get("center", {}).get("lon")

                if lat is None or lon is None:
                    continue

                # Extract name
                tags = element.get("tags", {})
                name = tags.get("name", f"OSM_{element['id']}")

                # Determine feature type
                osm_type = element.get("type", "node")

                # Extract country from tags or default
                country = tags.get("addr:country", "unknown")

                feature = OSMFeature(
                    osm_id=str(element["id"]),
                    osm_type=osm_type,
                    name=name,
                    feature_type=feature_type.lower(),
                    latitude=lat,
                    longitude=lon,
                    tags=tags,
                    country=country
                )

                features.append(feature)

            except (KeyError, ValueError) as e:
                logger.warning(f"Failed to parse OSM element: {e}")
                continue

        logger.info(f"Parsed {len(features)} features from Overpass response")
        return features

    def _load_cache(self, cache_file: Path) -> List[OSMFeature]:
        """
        Load features from cache file.

        Args:
            cache_file: Path to cache JSON file

        Returns:
            List of OSMFeature objects
        """
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)

            features = [OSMFeature.from_dict(item) for item in data.get("features", [])]
            logger.info(f"Loaded {len(features)} features from {cache_file}")
            return features

        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load cache file {cache_file}: {e}")
            return []

    def _save_cache(self, cache_file: Path, features: List[OSMFeature]) -> None:
        """
        Save features to cache file.

        Args:
            cache_file: Path to cache JSON file
            features: List of OSMFeature objects to cache
        """
        try:
            cache_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "feature_count": len(features),
                "features": [f.to_dict() for f in features]
            }

            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"Cached {len(features)} features to {cache_file}")

        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to save cache file {cache_file}: {e}")
