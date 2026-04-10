"""
Tests — Edge Registry and Dedup
================================
Validates edge schemas, merge key computation, and dedup registry.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.banking_intelligence.schemas.edges import (
    BaseEdge,
    RegulatesEdge,
    OperatesInEdge,
    DependsOnEdge,
    ExposedToEdge,
    PropagatesToEdge,
    HasPlaybookEdge,
    TriggersEdge,
    EdgeType,
    SourceReference,
    EDGE_TYPE_MAP,
)
from src.banking_intelligence.ingestion.dedup import DedupRegistry


def _source_ref() -> dict:
    return {"source_system": "test", "asserted_by": "pytest"}


class TestEdgeMergeKeys:
    def test_merge_key_deterministic(self):
        e1 = RegulatesEdge(
            from_entity_id="authority:sa_sama",
            to_entity_id="bank:sa_snb",
            confidence=0.99,
            source_references=[SourceReference(**_source_ref())],
        )
        e2 = RegulatesEdge(
            from_entity_id="authority:sa_sama",
            to_entity_id="bank:sa_snb",
            confidence=0.95,  # different confidence
            source_references=[SourceReference(**_source_ref())],
        )
        # Same from/to/type → same merge key
        assert e1.merge_key == e2.merge_key

    def test_different_direction_different_key(self):
        e1 = DependsOnEdge(
            from_entity_id="fintech:sa_stcpay",
            to_entity_id="rail:sa_sarie",
            confidence=0.90,
            dependency_type="settlement",
            criticality=0.85,
            degradation_impact_description="Settlement delayed",
            source_references=[SourceReference(**_source_ref())],
        )
        e2 = DependsOnEdge(
            from_entity_id="rail:sa_sarie",
            to_entity_id="fintech:sa_stcpay",
            confidence=0.90,
            dependency_type="settlement",
            criticality=0.85,
            degradation_impact_description="Settlement delayed",
            source_references=[SourceReference(**_source_ref())],
        )
        assert e1.merge_key != e2.merge_key


class TestRegulatesEdge:
    def test_valid_regulates(self):
        e = RegulatesEdge(
            from_entity_id="authority:sa_sama",
            to_entity_id="bank:sa_snb",
            confidence=0.99,
            regulatory_powers=["license_grant", "fine"],
            regulation_ids=["SAMA_BCR"],
            source_references=[SourceReference(**_source_ref())],
        )
        assert e.edge_type == EdgeType.REGULATES
        assert len(e.merge_key) == 24


class TestDependsOnEdge:
    def test_valid_dependency(self):
        e = DependsOnEdge(
            from_entity_id="fintech:sa_stcpay",
            to_entity_id="rail:sa_sarie",
            confidence=0.90,
            dependency_type="settlement",
            criticality=0.85,
            fallback_available=True,
            fallback_entity_id="rail:sa_sadad",
            degradation_impact_description="Settlement delayed from real-time to batch",
            source_references=[SourceReference(**_source_ref())],
        )
        assert e.criticality == 0.85

    def test_rejects_criticality_over_1(self):
        with pytest.raises(ValidationError):
            DependsOnEdge(
                from_entity_id="fintech:sa_stcpay",
                to_entity_id="rail:sa_sarie",
                confidence=0.90,
                dependency_type="settlement",
                criticality=1.5,  # invalid
                degradation_impact_description="Test",
                source_references=[SourceReference(**_source_ref())],
            )


class TestPropagatesToEdge:
    def test_valid_propagation_edge(self):
        e = PropagatesToEdge(
            from_entity_id="bank:sa_snb",
            to_entity_id="bank:sa_rajhi",
            confidence=0.75,
            transfer_mechanism="liquidity_channel",
            delay_hours=4.0,
            severity_transfer=0.35,
            is_breakable=True,
            intervention_lever="liquidity_injection",
            source_references=[SourceReference(**_source_ref())],
        )
        assert e.severity_transfer == 0.35


class TestEdgeTypeMap:
    def test_all_edge_types_have_schemas(self):
        for et in EdgeType:
            assert et in EDGE_TYPE_MAP, f"Missing schema for {et.value}"

    def test_requires_source_reference(self):
        with pytest.raises(ValidationError):
            RegulatesEdge(
                from_entity_id="authority:sa_sama",
                to_entity_id="bank:sa_snb",
                confidence=0.99,
                source_references=[],  # empty — must have at least 1
            )


class TestDedupRegistry:
    def test_register_new(self):
        reg = DedupRegistry()
        assert reg.register("bank", "key1") is True
        assert reg.register("bank", "key1") is False

    def test_exists(self):
        reg = DedupRegistry()
        reg.register("bank", "key1")
        assert reg.exists("bank", "key1") is True
        assert reg.exists("bank", "key2") is False

    def test_count(self):
        reg = DedupRegistry()
        reg.register("bank", "k1")
        reg.register("bank", "k2")
        reg.register("fintech", "k3")
        assert reg.count() == 3
        assert reg.count("bank") == 2
        assert reg.count("fintech") == 1

    def test_clear(self):
        reg = DedupRegistry()
        reg.register("bank", "k1")
        reg.register("fintech", "k2")
        cleared = reg.clear("bank")
        assert cleared == 1
        assert reg.count() == 1

    def test_stats(self):
        reg = DedupRegistry()
        reg.register("bank", "k1")
        reg.register("bank", "k2")
        reg.register("fintech", "k3")
        stats = reg.stats()
        assert stats == {"bank": 2, "fintech": 1}
