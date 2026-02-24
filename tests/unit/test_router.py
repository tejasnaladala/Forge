"""Tests for forge.models."""
from forge.models.cost import CostTracker, COST_TABLE


def test_cost_table_has_entries():
    assert "gpt-4o" in COST_TABLE
    assert "claude-sonnet-4-20250514" in COST_TABLE
    assert "default_local" in COST_TABLE


def test_cost_tracker_estimate():
    tracker = CostTracker()
    cost = tracker.estimate_cost("gpt-4o", 1000, 500)
    assert cost > 0


def test_cost_tracker_local_free():
    tracker = CostTracker()
    cost = tracker.estimate_cost("default_local", 1000, 500)
    assert cost == 0.0


def test_cost_tracker_track():
    tracker = CostTracker()
    tracker.track("gpt-4o", 1000, 500, 0.01)
    assert tracker.total_cost == 0.01
    assert tracker.total_tokens_in == 1000
    assert tracker.total_tokens_out == 500
    assert len(tracker.records) == 1


def test_cost_tracker_summary():
    tracker = CostTracker()
    tracker.track("gpt-4o", 1000, 500, 0.01)
    tracker.track("gpt-4o", 2000, 1000, 0.02)
    tracker.track("claude-sonnet-4-20250514", 500, 200, 0.005)
    summary = tracker.get_summary()
    assert summary["total_cost"] == pytest.approx(0.035)
    assert summary["total_calls"] == 3
    assert "gpt-4o" in summary["by_model"]
    assert summary["by_model"]["gpt-4o"]["calls"] == 2


# Need pytest import for approx
import pytest
