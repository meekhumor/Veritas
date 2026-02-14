"""LLM Integration Tests — verify real LLM calls across all agents & services.

These tests make REAL calls to the Gemini API (via langchain-google-genai).
They require a valid GOOGLE_API_KEY in the environment / .env file.

Run with:
    uv run pytest tests/test_llm_integration.py -v -s

Skip if no real key is configured:
    Tests are automatically skipped when GOOGLE_API_KEY is missing or set to
    a placeholder value like 'test-google-key'.
"""

from __future__ import annotations

import os
import json
import pytest
import logging

# ── Environment bootstrap ───────────────────────────────────────────────────
# Provide safe defaults for NON-LLM settings so the app can import without
# crashing. The real GOOGLE_API_KEY comes from .env or the environment.

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("TAVILY_API_KEY", "test-tavily-key")
os.environ.setdefault("MEDIACLOUD_API_KEY", "test-mediacloud-key")
os.environ.setdefault("GOOGLE_FACTCHECK_API_KEY", "test-factcheck-key")
os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
os.environ.setdefault("DEBUG", "true")

from app.core.config import get_settings
from app.core.llm import get_llm
from app.agents.state import InvestigationState
from app.agents.query_analyzer import query_analyzer
from app.agents.clarifier import clarifier
from app.agents.cross_reference import cross_reference_analyzer
from app.agents.impact_assessor import impact_assessor
from app.agents.verdict_synthesizer import verdict_synthesizer
from app.services.spam_filter import check_spam
from app.models.schemas import (
    Category,
    EvidenceItem,
    EvidenceType,
    CrossReferenceResult,
    ImpactScore,
    ImpactDimension,
    Verdict,
)

logger = logging.getLogger(__name__)

# ── Skip guard ──────────────────────────────────────────────────────────────

_PLACEHOLDER_KEYS = {"", "test-google-key", "your-google-key-here"}


def _has_real_api_key() -> bool:
    """Return True only when a real (non-placeholder) Google API key is set.

    We read from .env directly because conftest.py may have already populated
    os.environ with placeholder values, and `get_settings` uses lru_cache.
    """
    from dotenv import dotenv_values
    import pathlib

    env_file = pathlib.Path(__file__).resolve().parent.parent / ".env"
    env_vals = dotenv_values(env_file) if env_file.exists() else {}

    # Prefer .env value; fall back to actual env var
    key = env_vals.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    if key and key not in _PLACEHOLDER_KEYS:
        # Force into env so get_settings picks it up after cache clear
        os.environ["GOOGLE_API_KEY"] = key
        get_settings.cache_clear()
        return True
    return False


requires_llm = pytest.mark.skipif(
    not _has_real_api_key(),
    reason="Skipped: GOOGLE_API_KEY is not configured (set it in .env to run LLM integration tests)",
)


# ── Shared Fixtures ─────────────────────────────────────────────────────────

@pytest.fixture
def base_state() -> InvestigationState:
    """A minimal investigation state for testing."""
    return InvestigationState(
        query="Does 5G cause cancer?",
        investigation_id="llm-test-001",
    )


@pytest.fixture
def state_with_evidence(base_state) -> InvestigationState:
    """State pre-loaded with realistic evidence for downstream agents."""
    evidence = [
        EvidenceItem(
            investigation_id="llm-test-001",
            source_type=EvidenceType.WEB_SEARCH,
            source_name="example.com",
            source_url="https://example.com/5g-study",
            title="5G and Health: What Science Says",
            content=(
                "Multiple studies have shown no link between 5G frequencies and cancer. "
                "The WHO classifies RF radiation as a Group 2B carcinogen, but this applies "
                "to all RF not specifically 5G."
            ),
            credibility_score=0.7,
        ),
        EvidenceItem(
            investigation_id="llm-test-001",
            source_type=EvidenceType.AUTHORITY,
            source_name="who.int",
            source_url="https://www.who.int/5g",
            title="WHO Statement on 5G and Health",
            content=(
                "To date, and after much research, no adverse health effect has been "
                "causally linked with exposure to wireless technologies including 5G."
            ),
            credibility_score=0.95,
        ),
        EvidenceItem(
            investigation_id="llm-test-001",
            source_type=EvidenceType.FACT_CHECK,
            source_name="Snopes",
            source_url="https://www.snopes.com/5g-cancer",
            title="Does 5G Cause Cancer?",
            content=(
                "Claim: 5G causes cancer.\n"
                "Rating: False\n"
                "Review: No scientific evidence supports the claim that 5G causes cancer."
            ),
            credibility_score=0.85,
        ),
    ]
    base_state.evidence = evidence
    return base_state


@pytest.fixture
def state_with_cross_ref(state_with_evidence) -> InvestigationState:
    """State with evidence + cross-reference result for verdict/impact agents."""
    state_with_evidence.refined_query = "Does 5G radiation cause cancer in humans?"
    state_with_evidence.category = Category.HEALTH
    state_with_evidence.cross_reference = CrossReferenceResult(
        consensus_points=[
            "No scientific evidence links 5G to cancer",
            "WHO has not found adverse health effects from 5G",
        ],
        contradictions=[
            "Some alternative health sources claim RF is harmful",
        ],
        unique_findings=[
            "WHO classification of RF as Group 2B applies broadly, not specifically to 5G",
        ],
        source_agreement_score=0.85,
        summary="Strong consensus across sources that 5G does not cause cancer.",
    )
    state_with_evidence.impact = ImpactScore(
        overall=72,
        topic_sensitivity=ImpactDimension(score=85, explanation="Health topic"),
        geographic_reach=ImpactDimension(score=80, explanation="Global"),
        emotional_charge=ImpactDimension(score=70, explanation="Fear-based"),
        actionability=ImpactDimension(score=60, explanation="Could deter 5G adoption"),
        vulnerable_populations=ImpactDimension(score=65, explanation="Elderly concerned"),
    )
    return state_with_evidence


# ═══════════════════════════════════════════════════════════════════════════
# 1.  get_llm — LLM instantiation & basic invocation
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestLLMConnection:
    """Verify that we can create an LLM instance and get a response."""

    @pytest.mark.asyncio
    async def test_llm_instantiation(self):
        """get_llm() should return a ChatGoogleGenerativeAI instance."""
        llm = get_llm()
        assert llm is not None

    @pytest.mark.asyncio
    async def test_llm_basic_invoke(self):
        """A simple prompt should return a non-empty string."""
        from langchain_core.messages import HumanMessage

        llm = get_llm(temperature=0.0)
        response = await llm.ainvoke([HumanMessage(content="Say hello")])
        assert response.content
        assert len(response.content.strip()) > 0

    @pytest.mark.asyncio
    async def test_llm_json_capable(self):
        """LLM should be able to return valid JSON when instructed."""
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = get_llm(temperature=0.0)
        response = await llm.ainvoke([
            SystemMessage(content="You must respond with valid JSON only. No markdown."),
            HumanMessage(content='Return this JSON: {"status": "ok", "value": 42}'),
        ])
        content = response.content.strip()
        # Strip possible markdown code fences
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        parsed = json.loads(content)
        assert "status" in parsed

    @pytest.mark.asyncio
    async def test_llm_temperature_zero_is_deterministic(self):
        """Two calls with temperature=0 should return very similar results."""
        from langchain_core.messages import HumanMessage

        llm = get_llm(temperature=0.0)
        prompt = [HumanMessage(content="What is 2 + 2? Reply with just the number.")]
        r1 = await llm.ainvoke(prompt)
        r2 = await llm.ainvoke(prompt)
        # Both should contain "4"
        assert "4" in r1.content
        assert "4" in r2.content


# ═══════════════════════════════════════════════════════════════════════════
# 2.  Spam Filter — LLM-based spam/abuse detection
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestSpamFilterLLM:
    """Integration tests for the LLM-based spam filter."""

    @pytest.mark.asyncio
    async def test_genuine_query_allowed(self):
        """A real misinformation query should not be flagged as spam."""
        is_spam, reason = await check_spam("Is the earth flat?")
        assert is_spam is False, f"Genuine query wrongly rejected: {reason}"

    @pytest.mark.asyncio
    async def test_health_claim_allowed(self):
        is_spam, reason = await check_spam("Does drinking bleach cure COVID-19?")
        assert is_spam is False, f"Health claim wrongly rejected: {reason}"

    @pytest.mark.asyncio
    async def test_political_claim_allowed(self):
        is_spam, reason = await check_spam("Did the 2020 US election have widespread voter fraud?")
        assert is_spam is False, f"Political claim wrongly rejected: {reason}"

    @pytest.mark.asyncio
    async def test_obvious_spam_rejected(self):
        is_spam, _ = await check_spam(
            "BUY CHEAP VIAGRA NOW!!! BEST PRICES!!! CLICK HERE!!! www.spam.com FREE OFFER"
        )
        assert is_spam is True, "Obvious spam was not detected"

    @pytest.mark.asyncio
    async def test_gibberish_handled(self):
        """Gibberish should be caught or at least not crash."""
        is_spam, reason = await check_spam("asdjkl fhaweuif hawefiuh 123 !@# asdfjkl")
        # Either flagged or allowed — just verify no crash and valid return
        assert isinstance(is_spam, bool)
        assert isinstance(reason, str)

    @pytest.mark.asyncio
    async def test_off_topic_detected(self):
        is_spam, _ = await check_spam("Write me a poem about flowers and sunshine")
        assert is_spam is True, "Off-topic query should be rejected"

    @pytest.mark.asyncio
    async def test_short_query_heuristic(self):
        """Queries < 3 chars are rejected by heuristic before hitting LLM."""
        is_spam, reason = await check_spam("ab")
        assert is_spam is True
        assert "short" in reason.lower()

    @pytest.mark.asyncio
    async def test_long_query_heuristic(self):
        """Queries > 1000 chars are rejected by heuristic."""
        is_spam, reason = await check_spam("x" * 1001)
        assert is_spam is True
        assert "long" in reason.lower()

    @pytest.mark.asyncio
    async def test_return_types(self):
        """check_spam should always return (bool, str)."""
        result = await check_spam("Does 5G cause cancer?")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)


# ═══════════════════════════════════════════════════════════════════════════
# 3.  Query Analyzer — claim parsing, categorization, refinement
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestQueryAnalyzerLLM:
    """Integration tests for the Query Analyzer agent."""

    @pytest.mark.asyncio
    async def test_returns_valid_state_update(self, base_state):
        result = await query_analyzer(base_state)
        assert isinstance(result, dict)
        assert "refined_query" in result
        assert "category" in result
        assert "current_agent" in result
        assert result["current_agent"] == "query_analyzer"

    @pytest.mark.asyncio
    async def test_refined_query_is_nonempty(self, base_state):
        result = await query_analyzer(base_state)
        assert len(result["refined_query"].strip()) > 0

    @pytest.mark.asyncio
    async def test_category_is_valid_enum(self, base_state):
        result = await query_analyzer(base_state)
        assert isinstance(result["category"], Category)

    @pytest.mark.asyncio
    async def test_health_claim_categorized(self):
        state = InvestigationState(
            query="Does drinking bleach cure COVID-19?",
            investigation_id="llm-test-qa-health",
        )
        result = await query_analyzer(state)
        assert result["category"] == Category.HEALTH

    @pytest.mark.asyncio
    async def test_politics_claim_categorized(self):
        state = InvestigationState(
            query="Did the 2020 US election have widespread voter fraud?",
            investigation_id="llm-test-qa-politics",
        )
        result = await query_analyzer(state)
        assert result["category"] == Category.POLITICS

    @pytest.mark.asyncio
    async def test_tech_claim_categorized(self):
        state = InvestigationState(
            query="Does 5G cause cancer?",
            investigation_id="llm-test-qa-tech",
        )
        result = await query_analyzer(state)
        # Could be Tech or Health — both are reasonable
        assert result["category"] in (Category.TECH, Category.HEALTH)

    @pytest.mark.asyncio
    async def test_clear_query_does_not_need_clarification(self):
        state = InvestigationState(
            query="Is the earth flat according to NASA?",
            investigation_id="llm-test-qa-clear",
        )
        result = await query_analyzer(state)
        assert result["needs_clarification"] is False

    @pytest.mark.asyncio
    async def test_vague_query_may_need_clarification(self):
        state = InvestigationState(
            query="Is it safe?",
            investigation_id="llm-test-qa-vague",
        )
        result = await query_analyzer(state)
        # A vague query should ideally need clarification
        if result["needs_clarification"]:
            assert len(result.get("clarification_questions", [])) > 0

    @pytest.mark.asyncio
    async def test_investigation_trail_populated(self, base_state):
        result = await query_analyzer(base_state)
        assert "investigation_trail" in result
        assert len(result["investigation_trail"]) > 0
        assert "Query Analyzer" in result["investigation_trail"][0]


# ═══════════════════════════════════════════════════════════════════════════
# 4.  Clarifier — query refinement with clarification answers
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestClarifierLLM:
    """Integration tests for the Clarifier agent."""

    @pytest.mark.asyncio
    async def test_skip_when_no_clarification_needed(self):
        """If needs_clarification is False, clarifier should pass through."""
        state = InvestigationState(
            query="Is the earth flat?",
            investigation_id="llm-test-clar-skip",
            needs_clarification=False,
        )
        result = await clarifier(state)
        assert result["current_agent"] == "clarifier"
        assert "investigation_trail" in result

    @pytest.mark.asyncio
    async def test_skip_when_no_answers_provided(self):
        """If clarification needed but no answers, clarifier passes through."""
        state = InvestigationState(
            query="Is it safe?",
            investigation_id="llm-test-clar-noans",
            needs_clarification=True,
            clarification_questions=["What are you referring to?"],
            clarification_answers=[],
        )
        result = await clarifier(state)
        assert result["current_agent"] == "clarifier"

    @pytest.mark.asyncio
    async def test_refine_with_answers(self):
        """Given Q&A, clarifier should produce a refined query via LLM."""
        state = InvestigationState(
            query="Is it safe?",
            investigation_id="llm-test-clar-refine",
            needs_clarification=True,
            clarification_questions=["What specific product or topic are you asking about?"],
            clarification_answers=["I'm asking about the COVID-19 vaccine"],
            refined_query="Is it safe?",
        )
        result = await clarifier(state)
        assert "refined_query" in result
        assert len(result["refined_query"].strip()) > 0
        # The refined query should now mention vaccine or COVID
        refined_lower = result["refined_query"].lower()
        assert "vaccine" in refined_lower or "covid" in refined_lower

    @pytest.mark.asyncio
    async def test_clarifier_sets_needs_clarification_false(self):
        """After refinement, needs_clarification should be set to False."""
        state = InvestigationState(
            query="Is it dangerous?",
            investigation_id="llm-test-clar-flag",
            needs_clarification=True,
            clarification_questions=["What is 'it'?"],
            clarification_answers=["Artificial sweetener aspartame"],
            refined_query="Is it dangerous?",
        )
        result = await clarifier(state)
        assert result["needs_clarification"] is False


# ═══════════════════════════════════════════════════════════════════════════
# 5.  Cross-Reference Analyzer — consensus & contradictions
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestCrossReferenceAnalyzerLLM:
    """Integration tests for the Cross-Reference Analyzer agent."""

    @pytest.mark.asyncio
    async def test_no_evidence_returns_empty(self):
        """Without evidence, should return an empty CrossReferenceResult."""
        state = InvestigationState(
            query="Does 5G cause cancer?",
            investigation_id="llm-test-xref-empty",
        )
        result = await cross_reference_analyzer(state)
        assert result["current_agent"] == "cross_reference_analyzer"
        assert result["cross_reference"].source_agreement_score == 0.0

    @pytest.mark.asyncio
    async def test_returns_cross_reference_result(self, state_with_evidence):
        result = await cross_reference_analyzer(state_with_evidence)
        cr = result["cross_reference"]
        assert isinstance(cr, CrossReferenceResult)

    @pytest.mark.asyncio
    async def test_consensus_points_found(self, state_with_evidence):
        result = await cross_reference_analyzer(state_with_evidence)
        cr = result["cross_reference"]
        assert len(cr.consensus_points) > 0, "Should find at least one consensus point"

    @pytest.mark.asyncio
    async def test_agreement_score_in_range(self, state_with_evidence):
        result = await cross_reference_analyzer(state_with_evidence)
        cr = result["cross_reference"]
        assert 0.0 <= cr.source_agreement_score <= 1.0

    @pytest.mark.asyncio
    async def test_summary_is_nonempty(self, state_with_evidence):
        result = await cross_reference_analyzer(state_with_evidence)
        cr = result["cross_reference"]
        assert len(cr.summary.strip()) > 0

    @pytest.mark.asyncio
    async def test_high_agreement_for_consistent_evidence(self, state_with_evidence):
        """All 3 evidence sources agree — agreement score should be >0.6."""
        result = await cross_reference_analyzer(state_with_evidence)
        cr = result["cross_reference"]
        assert cr.source_agreement_score > 0.6, (
            f"Agreement score too low ({cr.source_agreement_score}) for consistent evidence"
        )

    @pytest.mark.asyncio
    async def test_investigation_trail(self, state_with_evidence):
        result = await cross_reference_analyzer(state_with_evidence)
        assert len(result["investigation_trail"]) > 0
        assert "Cross-Reference" in result["investigation_trail"][0]


# ═══════════════════════════════════════════════════════════════════════════
# 6.  Impact Assessor — societal risk scoring
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestImpactAssessorLLM:
    """Integration tests for the Impact Assessor agent."""

    @pytest.mark.asyncio
    async def test_returns_impact_score(self, state_with_evidence):
        result = await impact_assessor(state_with_evidence)
        assert isinstance(result["impact"], ImpactScore)

    @pytest.mark.asyncio
    async def test_overall_score_in_range(self, state_with_evidence):
        result = await impact_assessor(state_with_evidence)
        assert 0.0 <= result["impact"].overall <= 100.0

    @pytest.mark.asyncio
    async def test_all_dimensions_present(self, state_with_evidence):
        result = await impact_assessor(state_with_evidence)
        impact = result["impact"]
        for dim_name in [
            "topic_sensitivity",
            "geographic_reach",
            "emotional_charge",
            "actionability",
            "vulnerable_populations",
        ]:
            dim = getattr(impact, dim_name)
            assert isinstance(dim, ImpactDimension), f"{dim_name} is not ImpactDimension"
            assert 0.0 <= dim.score <= 100.0, f"{dim_name} score out of range"
            assert len(dim.explanation.strip()) > 0, f"{dim_name} has no explanation"

    @pytest.mark.asyncio
    async def test_health_claim_has_high_sensitivity(self, state_with_evidence):
        """A health/cancer claim should rate highly on topic sensitivity."""
        state_with_evidence.category = Category.HEALTH
        state_with_evidence.refined_query = "Does 5G radiation cause cancer in humans?"
        result = await impact_assessor(state_with_evidence)
        sensitivity = result["impact"].topic_sensitivity.score
        assert sensitivity >= 50, f"Health claim sensitivity too low: {sensitivity}"

    @pytest.mark.asyncio
    async def test_benign_claim_lower_impact(self):
        """A trivial claim should have lower overall impact."""
        state = InvestigationState(
            query="Is water wet?",
            investigation_id="llm-test-impact-benign",
            refined_query="Is water wet?",
            category=Category.GENERAL,
        )
        result = await impact_assessor(state)
        assert result["impact"].overall < 60, (
            f"Benign claim overall impact unexpectedly high: {result['impact'].overall}"
        )

    @pytest.mark.asyncio
    async def test_current_agent_set(self, state_with_evidence):
        result = await impact_assessor(state_with_evidence)
        assert result["current_agent"] == "impact_assessor"


# ═══════════════════════════════════════════════════════════════════════════
# 7.  Verdict Synthesizer — final verdict & confidence
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestVerdictSynthesizerLLM:
    """Integration tests for the Verdict Synthesizer agent."""

    @pytest.mark.asyncio
    async def test_returns_verdict(self, state_with_cross_ref):
        result = await verdict_synthesizer(state_with_cross_ref)
        assert "verdict" in result
        assert isinstance(result["verdict"], Verdict)

    @pytest.mark.asyncio
    async def test_confidence_in_range(self, state_with_cross_ref):
        result = await verdict_synthesizer(state_with_cross_ref)
        assert 0.0 <= result["confidence"] <= 1.0

    @pytest.mark.asyncio
    async def test_5g_cancer_verdict_is_false(self, state_with_cross_ref):
        """Given strong counter-evidence, '5G causes cancer' should be FALSE."""
        result = await verdict_synthesizer(state_with_cross_ref)
        assert result["verdict"] == Verdict.FALSE, (
            f"Expected FALSE but got {result['verdict']} for debunked 5G claim"
        )

    @pytest.mark.asyncio
    async def test_high_confidence_with_strong_evidence(self, state_with_cross_ref):
        """Multiple authoritative sources agreeing → confidence should be high."""
        result = await verdict_synthesizer(state_with_cross_ref)
        assert result["confidence"] >= 0.7, (
            f"Confidence too low ({result['confidence']}) given strong evidence"
        )

    @pytest.mark.asyncio
    async def test_summary_is_nonempty(self, state_with_cross_ref):
        result = await verdict_synthesizer(state_with_cross_ref)
        assert len(result["summary"].strip()) > 0

    @pytest.mark.asyncio
    async def test_detailed_analysis_is_nonempty(self, state_with_cross_ref):
        result = await verdict_synthesizer(state_with_cross_ref)
        assert len(result["detailed_analysis"].strip()) > 0

    @pytest.mark.asyncio
    async def test_no_evidence_gives_unverified(self):
        """Without evidence, verdict should be UNVERIFIED."""
        state = InvestigationState(
            query="Some obscure claim nobody has heard of",
            investigation_id="llm-test-verdict-noevidene",
        )
        result = await verdict_synthesizer(state)
        assert result["verdict"] == Verdict.UNVERIFIED

    @pytest.mark.asyncio
    async def test_current_agent_set(self, state_with_cross_ref):
        result = await verdict_synthesizer(state_with_cross_ref)
        assert result["current_agent"] == "verdict_synthesizer"

    @pytest.mark.asyncio
    async def test_investigation_trail(self, state_with_cross_ref):
        result = await verdict_synthesizer(state_with_cross_ref)
        assert len(result["investigation_trail"]) > 0
        assert "Verdict Synthesizer" in result["investigation_trail"][0]


# ═══════════════════════════════════════════════════════════════════════════
# 8.  End-to-End: Multi-agent sequence (QA → Cross-Ref → Impact → Verdict)
# ═══════════════════════════════════════════════════════════════════════════

@requires_llm
class TestMultiAgentSequenceLLM:
    """Run a realistic sequence of LLM agents in order and verify
    the data flows correctly between stages."""

    @pytest.mark.asyncio
    async def test_query_analyzer_then_cross_ref(self, state_with_evidence):
        """QA → Cross-Ref: refined query is used in cross-reference."""
        qa_result = await query_analyzer(state_with_evidence)
        state_with_evidence.refined_query = qa_result["refined_query"]
        state_with_evidence.category = qa_result["category"]

        xref_result = await cross_reference_analyzer(state_with_evidence)
        assert isinstance(xref_result["cross_reference"], CrossReferenceResult)
        assert xref_result["cross_reference"].source_agreement_score > 0

    @pytest.mark.asyncio
    async def test_full_llm_chain(self, state_with_evidence):
        """QA → Cross-Ref → Impact → Verdict in sequence."""
        # 1. Query Analyzer
        qa_result = await query_analyzer(state_with_evidence)
        state_with_evidence.refined_query = qa_result["refined_query"]
        state_with_evidence.category = qa_result["category"]

        # 2. Cross-Reference Analyzer
        xref_result = await cross_reference_analyzer(state_with_evidence)
        state_with_evidence.cross_reference = xref_result["cross_reference"]

        # 3. Impact Assessor
        impact_result = await impact_assessor(state_with_evidence)
        state_with_evidence.impact = impact_result["impact"]

        # 4. Verdict Synthesizer
        verdict_result = await verdict_synthesizer(state_with_evidence)

        # Verify the full chain produced a coherent result
        assert isinstance(verdict_result["verdict"], Verdict)
        assert 0.0 <= verdict_result["confidence"] <= 1.0
        assert len(verdict_result["summary"]) > 0
        assert len(verdict_result["detailed_analysis"]) > 0

        # For the 5G cancer claim with counter-evidence, expect FALSE
        assert verdict_result["verdict"] == Verdict.FALSE
        logger.info(
            f"Full chain result: {verdict_result['verdict'].value} "
            f"(confidence: {verdict_result['confidence']:.0%})"
        )
