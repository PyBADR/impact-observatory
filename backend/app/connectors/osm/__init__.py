"""
OpenStreetMap (OSM) Reference Data Loader.

Loads infrastructure reference data from OpenStreetMap via Overpass API
with offline caching support for GCC region data.
"""

from app.connectors.osm.connector import OSMReferenceLoader, OSMFeature

__all__ = ["OSMReferenceLoader", "OSMFeature"]
