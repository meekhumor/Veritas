"""Tests for the LangGraph pipeline structure."""

import pytest
from app.agents.pipeline import build_investigation_graph, investigation_graph
from app.agents.state import InvestigationState
from app.models.schemas import InvestigationReport


def test_graph_compiles():
    """The investigation graph should compile without errors."""
    graph = build_investigation_graph()
    assert graph is not None


def test_graph_singleton():
    """The pre-compiled graph should be available."""
    assert investigation_graph is not None


def test_investigation_state_defaults():
    """State should have sensible defaults."""
    state = InvestigationState(query="test query")
    assert state.query == "test query"
    assert state.refined_query == ""
    assert state.needs_clarification is False
    assert state.evidence == []
    assert state.verdict.value == "UNVERIFIED"
    assert state.confidence == 0.0


def test_investigation_report_model():
    """Report model should serialize correctly."""
    report = InvestigationReport(
        query="Test",
        summary="Test summary",
        verdict="TRUE",
        confidence=0.9,
    )
    data = report.model_dump()
    assert data["query"] == "Test"
    assert data["verdict"] == "TRUE"
    assert data["id"] is not None
