"""Comprehensive tests for ResearchIDE backend — scoring, validation, parsing, fallbacks."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime


# ── Retrieval scoring tests ─────────────────────────────────────────────────

def test_recency_score_current_year():
    from services.retrieval.retrieval_service import _recency_score
    current = str(datetime.now().year)
    assert _recency_score(current) == 1.0


def test_recency_score_two_years_old():
    from services.retrieval.retrieval_service import _recency_score
    current = datetime.now().year
    assert _recency_score(str(current - 2)) == 0.8


def test_recency_score_three_years_old():
    from services.retrieval.retrieval_service import _recency_score
    current = datetime.now().year
    assert _recency_score(str(current - 3)) == 0.6


def test_recency_score_five_years_old():
    from services.retrieval.retrieval_service import _recency_score
    current = datetime.now().year
    assert _recency_score(str(current - 5)) == 0.4


def test_recency_score_very_old():
    from services.retrieval.retrieval_service import _recency_score
    assert _recency_score("2010") == 0.2


def test_recency_score_invalid():
    from services.retrieval.retrieval_service import _recency_score
    assert _recency_score("abc") == 0.3
    assert _recency_score("") == 0.3
    assert _recency_score(None) == 0.3


def test_relevance_score_perfect_match():
    from services.retrieval.retrieval_service import _relevance_score
    score = _relevance_score("deep learning NLP transformer", "Deep Learning for NLP with Transformers", "This paper uses deep learning for NLP tasks")
    assert score > 0.5


def test_relevance_score_no_match():
    from services.retrieval.retrieval_service import _relevance_score
    score = _relevance_score("quantum computing blockchain", "Image Recognition with CNNs", "Object detection in images")
    assert score < 0.3


def test_citation_weight_high():
    from services.retrieval.retrieval_service import _citation_weight
    assert _citation_weight("200") == 1.0
    assert _citation_weight("1000") == 1.0  # capped


def test_citation_weight_low():
    from services.retrieval.retrieval_service import _citation_weight
    assert _citation_weight("0") == 0.0
    assert _citation_weight("10") == 0.05


def test_citation_weight_na():
    from services.retrieval.retrieval_service import _citation_weight
    assert _citation_weight("N/A") == 0.0


def test_compute_score():
    from services.retrieval.retrieval_service import _compute_score
    query = "deep learning for NLP"
    paper = {
        "title": "Deep Learning Methods for Natural Language Processing",
        "abstract": "We apply deep learning to various NLP tasks.",
        "year": str(datetime.now().year),
        "citations": "100",
    }
    score = _compute_score(query, paper)
    assert 0.0 <= score <= 1.0
    assert score > 0.3  # should score reasonably well


# ── Deduplication tests ─────────────────────────────────────────────────────

def test_deduplication_basic():
    from services.retrieval.retrieval_service import _deduplicate
    papers = [
        {"title": "Machine Learning for NLP"},
        {"title": "Deep Learning in Healthcare"},
        {"title": "machine learning for nlp"},  # duplicate
    ]
    unique = _deduplicate(papers)
    assert len(unique) == 2


def test_deduplication_all_unique():
    from services.retrieval.retrieval_service import _deduplicate
    papers = [
        {"title": "Alpha"},
        {"title": "Beta"},
        {"title": "Gamma"},
    ]
    unique = _deduplicate(papers)
    assert len(unique) == 3


def test_deduplication_empty():
    from services.retrieval.retrieval_service import _deduplicate
    assert _deduplicate([]) == []


# ── Quality gate tests ──────────────────────────────────────────────────────

def test_quality_gate_valid_idea():
    from core.quality_gate import validate_idea
    idea = {
        "title": "Novel Transformer Architecture",
        "description": "A comprehensive approach to improving transformer efficiency through sparse attention mechanisms that reduces computational cost while maintaining accuracy on standard benchmarks.",
        "novelty": "This combines two previously separate lines of research into attention sparsity and dynamic routing in a novel way that has not been explored before.",
        "approach": "We propose a hybrid sparse-dynamic attention mechanism that selectively activates attention heads based on input complexity and task requirements.",
        "novelty_score": 8.0,
        "feasibility_score": 7.0,
    }
    valid, issues = validate_idea(idea)
    assert valid is True
    assert len(issues) == 0


def test_quality_gate_invalid_idea():
    from core.quality_gate import validate_idea
    idea = {"title": "", "description": "short", "novelty": "x", "approach": "y"}
    valid, issues = validate_idea(idea)
    assert valid is False
    assert len(issues) >= 3  # missing title, desc too short, novelty too short, approach too short


def test_quality_gate_score_out_of_range():
    from core.quality_gate import validate_idea
    idea = {
        "title": "Test",
        "description": "A" * 80,
        "novelty": "B" * 50,
        "approach": "C" * 50,
        "novelty_score": 15,
        "feasibility_score": -2,
    }
    valid, issues = validate_idea(idea)
    assert valid is False
    assert any("out of range" in i for i in issues)


def test_validate_ideas_batch():
    from core.quality_gate import validate_ideas_batch
    ideas = [
        {"title": "Good Idea", "description": "A" * 80, "novelty": "B" * 50, "approach": "C" * 50},
        {"title": "", "description": "short"},
    ]
    result = validate_ideas_batch(ideas)
    assert result[0]["_quality_valid"] is True
    assert result[1]["_quality_valid"] is False


# ── Gap validation tests ────────────────────────────────────────────────────

def test_validate_gap_valid():
    from core.quality_gate import validate_gap
    gap = {
        "title": "Methodological Gap",
        "description": "A" * 80,
        "explanation": "B" * 100,
        "direct_references": ["Paper A"],
        "type": "methodological",
    }
    valid, issues = validate_gap(gap)
    assert valid is True


def test_validate_gap_invalid():
    from core.quality_gate import validate_gap
    gap = {"title": "", "description": "short", "explanation": "x", "type": "invalid_type"}
    valid, issues = validate_gap(gap)
    assert valid is False
    assert len(issues) >= 3


# ── Gap agent tests ─────────────────────────────────────────────────────────

def test_gap_defaults():
    from agents.gap_miner.gap_agent import _default_gaps
    gaps = _default_gaps()
    assert len(gaps) >= 1
    gap = gaps[0]
    assert "title" in gap
    assert "description" in gap
    assert "type" in gap
    assert "confidence" in gap
    assert "novelty_potential" in gap
    assert "evidence_strength" in gap
    assert "gap_category" in gap


def test_extract_key_sections():
    from agents.gap_miner.gap_agent import _extract_key_sections
    text = "This is the abstract of the paper. It describes the work.\nDiscussion: We found that the method works well.\nConclusion: The results are promising."
    result = _extract_key_sections(text)
    assert "Discussion" in result or "Conclusion" in result


def test_parse_json_list_valid():
    from agents.gap_miner.gap_agent import _parse_json_list
    raw = '[{"title": "Gap 1", "type": "methodological"}, {"title": "Gap 2"}]'
    result = _parse_json_list(raw)
    assert len(result) == 2
    assert result[0]["title"] == "Gap 1"


def test_parse_json_list_with_fences():
    from agents.gap_miner.gap_agent import _parse_json_list
    raw = '```json\n[{"title": "Gap 1"}]\n```'
    result = _parse_json_list(raw)
    assert len(result) == 1


def test_parse_json_list_empty():
    from agents.gap_miner.gap_agent import _parse_json_list
    assert _parse_json_list("") == []
    assert _parse_json_list(None) == []


def test_parse_json_list_object_with_list():
    from agents.gap_miner.gap_agent import _parse_json_list
    raw = '{"gaps": [{"title": "A"}, {"title": "B"}]}'
    result = _parse_json_list(raw)
    assert len(result) == 2


def test_estimate_addressability():
    from agents.gap_miner.gap_agent import _estimate_addressability
    gap_strong = {"evidence_strength": "strong", "gap_category": "evaluation_gap"}
    gap_weak = {"evidence_strength": "weak", "gap_category": "scalability_gap"}
    assert _estimate_addressability(gap_strong) > _estimate_addressability(gap_weak)


def test_estimate_impact():
    from agents.gap_miner.gap_agent import _estimate_impact
    gap_novel = {"gap_category": "unexplored_combination", "novelty_potential": 9}
    gap_low = {"gap_category": "dataset_gap", "novelty_potential": 2}
    assert _estimate_impact(gap_novel) > _estimate_impact(gap_low)


def test_extracted_gaps_returns_list():
    from agents.gap_miner.gap_agent import _extracted_gaps_from_papers
    papers = [
        {"title": "Paper A", "abstract": "This has a limitation in methodology. However, future work should address this gap.", "full_text": ""},
        {"title": "Paper B", "abstract": "There is a lack of sufficient datasets for evaluation.", "full_text": ""},
    ]
    gaps = _extracted_gaps_from_papers(papers)
    assert isinstance(gaps, list)
    assert len(gaps) > 0
    for g in gaps:
        assert "title" in g
        assert "description" in g
        assert "supporting_papers" in g


# ── Idea ranking tests ──────────────────────────────────────────────────────

def test_idea_ranking():
    from agents.idea_generator.idea_agent import _rank_ideas
    ideas = [
        {"title": "A", "novelty_score": 5, "feasibility_score": 5},
        {"title": "B", "novelty_score": 9, "feasibility_score": 8},
        {"title": "C", "novelty_score": 7, "feasibility_score": 3},
    ]
    ranked = _rank_ideas(ideas)
    assert ranked[0]["title"] == "B"
    assert ranked[-1]["title"] == "A"


def test_idea_ranking_equal():
    from agents.idea_generator.idea_agent import _rank_ideas
    ideas = [
        {"title": "A", "novelty_score": 5, "feasibility_score": 5},
        {"title": "B", "novelty_score": 5, "feasibility_score": 5},
    ]
    ranked = _rank_ideas(ideas)
    assert len(ranked) == 2


# ── Intent fallback tests ───────────────────────────────────────────────────

def test_intent_fallback():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("machine learning for medical imaging")
    assert "keywords" in result
    assert len(result["keywords"]) > 0
    assert "queries" in result
    assert len(result["queries"]) > 0
    assert result["_fallback"] is True


# ── Rate limiter tests ──────────────────────────────────────────────────────

def test_rate_limit_allows():
    from api.routes.auth import _check_rate_limit
    # Fresh key should always be allowed
    assert _check_rate_limit("test_fresh_key", 5, 60) is True


def test_rate_limit_blocks():
    from api.routes.auth import _check_rate_limit
    key = "test_block_key_2026"
    # Exhaust the limit
    for _ in range(5):
        _check_rate_limit(key, 5, 60)
    # Next one should be blocked
    assert _check_rate_limit(key, 5, 60) is False


# ── NLP analyzer tests (import-only, no model loading) ──────────────────────

def test_label_name():
    from services.nlp_analysis.analyzer import _label_name
    assert _label_name("PERSON") == "Person"
    assert _label_name("ORG") == "Organization"
    assert _label_name("UNKNOWN_LABEL") == "Unknown Label"


def test_classify_domain():
    from services.nlp_analysis.analyzer import _classify_domain
    # Mock a minimal doc-like object
    class MockDoc:
        pass
    result = _classify_domain("deep learning neural network transformer attention", MockDoc())
    assert result["broad"] in ("Deep Learning", "Machine Learning", "General")
    assert 0.0 <= result["confidence"] <= 1.0


def test_classify_domain_nlp():
    from services.nlp_analysis.analyzer import _classify_domain
    class MockDoc:
        pass
    result = _classify_domain("named entity recognition sentiment analysis NLP", MockDoc())
    assert result["broad"] == "Natural Language Processing"


# ── PDF extractor tests ─────────────────────────────────────────────────────

def test_extract_key_sections_no_sections():
    from agents.gap_miner.gap_agent import _extract_key_sections
    text = "This is plain text with no section headers at all."
    result = _extract_key_sections(text)
    # Should return truncated text when no sections found
    assert len(result) > 0


# ── Writer agent citation tests ─────────────────────────────────────────────

def test_postprocess_citations_empty_refs():
    from agents.writer.writer_agent import _postprocess_citations
    report = {
        "sections": [{"content": "This is a test with no citations."}],
        "references": [],
    }
    result = _postprocess_citations(report, [])
    assert "references" in result
    assert isinstance(result["references"], list)


def test_postprocess_citations_valid_refs():
    from agents.writer.writer_agent import _postprocess_citations
    report = {
        "sections": [{"content": "As shown in [1] and [2], this works."}],
        "references": [{"id": 1}, {"id": 2}],
    }
    result = _postprocess_citations(report, [])
    # Valid citations should be preserved
    assert "[1]" in result["sections"][0]["content"]
    assert "[2]" in result["sections"][0]["content"]


def test_postprocess_citations_invalid_refs():
    from agents.writer.writer_agent import _postprocess_citations
    report = {
        "sections": [{"content": "As shown in [99], this works."}],
        "references": [{"id": 1}, {"id": 2}],
    }
    result = _postprocess_citations(report, [])
    # Invalid citation [99] should be removed
    assert "[99]" not in result["sections"][0]["content"]
