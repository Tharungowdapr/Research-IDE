"""Tests for agent fallbacks and utility functions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_intent_fallback():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("machine learning for medical imaging")
    assert "keywords" in result
    assert len(result["keywords"]) > 0
    assert "queries" in result
    assert len(result["queries"]) > 0
    assert result["_fallback"] is True


def test_deduplication():
    from services.retrieval.retrieval_service import _deduplicate
    papers = [
        {"title": "Machine Learning for NLP"},
        {"title": "Deep Learning in Healthcare"},
        {"title": "machine learning for nlp"},  # duplicate
    ]
    unique = _deduplicate(papers)
    assert len(unique) == 2


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


def test_code_fallback():
    from agents.code_agent.code_agent import _fallback_code
    result = _fallback_code({"title": "Test"}, {})
    filenames = [f["filename"] for f in result["files"]]
    expected = [
        "main.py", "config.py", "experiment_config.yaml", "model.py",
        "dataset.py", "train.py", "evaluate.py", "utils.py",
        "requirements.txt", "Makefile", "tests/test_model.py", "README.md",
    ]
    for name in expected:
        assert name in filenames, f"Missing file: {name}"
    assert len(filenames) == 12


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
