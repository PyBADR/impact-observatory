"""Tests for underwriting watch list."""

import pytest

from src.engines.insurance_intelligence.underwriting_watch import (
    evaluate_watch,
    generate_watch_list,
    WatchPriority,
)


class TestEvaluateWatch:
    def test_no_triggers(self):
        item = evaluate_watch("e1", risk_score=0.3, exposure_score=0.2, surge_score=0.1)
        assert item is None

    def test_risk_breach(self):
        item = evaluate_watch("e1", risk_score=0.8, exposure_score=0.3, surge_score=0.2)
        assert item is not None
        assert any(t.trigger_type == "risk_breach" for t in item.triggers)

    def test_multiple_triggers_escalate(self):
        item = evaluate_watch(
            "e1", risk_score=0.9, exposure_score=0.8, surge_score=0.7,
            chokepoint_dependency=0.8,
        )
        assert item is not None
        assert item.priority in (WatchPriority.IMMEDIATE, WatchPriority.URGENT)
        assert len(item.triggers) >= 3

    def test_priority_ordering(self):
        immediate = evaluate_watch("e1", 0.9, 0.9, 0.9, 0.9)
        elevated = evaluate_watch("e2", 0.65, 0.3, 0.2)
        assert immediate.priority == WatchPriority.IMMEDIATE
        assert elevated.priority in (WatchPriority.ELEVATED, WatchPriority.ROUTINE)


class TestWatchList:
    def test_empty(self):
        wl = generate_watch_list(["a", "b"], [0.1, 0.2], [0.1, 0.2], [0.1, 0.1])
        assert wl.total_flagged == 0

    def test_mixed(self):
        wl = generate_watch_list(
            ["a", "b", "c"],
            [0.9, 0.7, 0.1],
            [0.8, 0.3, 0.1],
            [0.7, 0.2, 0.1],
        )
        assert wl.total_flagged >= 1
        # Sorted by priority
        if len(wl.items) >= 2:
            priorities = [i.priority for i in wl.items]
            order = {WatchPriority.IMMEDIATE: 0, WatchPriority.URGENT: 1,
                     WatchPriority.ELEVATED: 2, WatchPriority.ROUTINE: 3}
            assert all(order[priorities[i]] <= order[priorities[i+1]]
                       for i in range(len(priorities) - 1))

    def test_summary(self):
        wl = generate_watch_list(["a"], [0.9], [0.8], [0.7])
        assert "flagged" in wl.summary
