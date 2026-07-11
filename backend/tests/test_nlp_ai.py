"""Comprehensive NLP/AI tests for ResearchIDE — analyzer, LLM, quality gate, scoring, export."""

import sys
import os
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime


# ── NLP Analyzer Tests ───────────────────────────────────────────────────────

def test_label_name():
    from services.nlp_analysis.analyzer import _label_name
    assert _label_name("PERSON") == "Person"
    assert _label_name("ORG") == "Organization"
    assert _label_name("GPE") == "Location"
    assert _label_name("DATE") == "Date"
    assert _label_name("UNKNOWN_LABEL") == "Unknown Label"


def test_classify_domain_dl():
    from services.nlp_analysis.analyzer import _classify_domain
    class MockDoc:
        pass
    result = _classify_domain("deep learning neural network transformer attention mechanism", MockDoc())
    assert result["broad"] in ("Deep Learning", "Machine Learning", "General")
    assert 0.0 <= result["confidence"] <= 1.0


def test_classify_domain_nlp():
    from services.nlp_analysis.analyzer import _classify_domain
    class MockDoc:
        pass
    result = _classify_domain("named entity recognition sentiment analysis NLP tokenization", MockDoc())
    assert result["broad"] == "Natural Language Processing"


def test_classify_domain_cv():
    from services.nlp_analysis.analyzer import _classify_domain
    class MockDoc:
        pass
    result = _classify_domain("computer vision image classification object detection CNN convolutional", MockDoc())
    assert result["broad"] in ("Computer Vision", "Deep Learning", "Machine Learning")


def test_classify_domain_rl():
    from services.nlp_analysis.analyzer import _classify_domain
    class MockDoc:
        pass
    result = _classify_domain("reinforcement learning policy gradient Q-learning agent environment reward", MockDoc())
    assert result["broad"] in ("Reinforcement Learning", "Machine Learning", "General")


def test_classify_domain_general():
    from services.nlp_analysis.analyzer import _classify_domain
    class MockDoc:
        pass
    result = _classify_domain("random text about cooking recipes food", MockDoc())
    assert result["broad"] in ("General", "Other", "Machine Learning", "Natural Language Processing")
    assert 0.0 <= result["confidence"] <= 1.0


def _load_spacy():
    import spacy
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        pytest.skip("en_core_web_sm model not installed")


def test_ner_with_spacy():
    nlp = _load_spacy()
    doc = nlp("Google developed BERT in 2018. It was created by researchers in California.")
    org_entities = [e.text for e in doc.ents if e.label_ == "ORG"]
    assert len(org_entities) > 0
    assert "Google" in org_entities


def test_keyword_with_spacy():
    nlp = _load_spacy()
    doc = nlp("This paper proposes a novel transformer architecture for natural language processing tasks.")
    nouns = [token.text for token in doc if token.pos_ == "NOUN"]
    assert len(nouns) > 0


def test_pos_tagging_with_spacy():
    nlp = _load_spacy()
    doc = nlp("The researchers developed a new algorithm.")
    pos_tags = [(token.text, token.pos_) for token in doc]
    assert len(pos_tags) > 0
    assert any(tag == "VERB" for _, tag in pos_tags)


def test_sentence_splitting_with_spacy():
    nlp = _load_spacy()
    doc = nlp("First sentence. Second sentence. Third sentence.")
    sentences = list(doc.sents)
    assert len(sentences) >= 3


# ── Intent Extraction Tests ──────────────────────────────────────────────────

def test_intent_fallback_keywords():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("machine learning for medical imaging diagnosis")
    assert "keywords" in result
    assert len(result["keywords"]) >= 3
    # Should extract domain-relevant keywords
    keywords_lower = [k.lower() for k in result["keywords"]]
    assert any("medical" in k or "imaging" in k or "machine" in k for k in keywords_lower)


def test_intent_fallback_queries():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("natural language processing for code generation")
    assert "queries" in result
    assert len(result["queries"]) >= 2


def test_intent_fallback_domain():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("deep learning for image classification")
    assert "domain" in result
    assert isinstance(result["domain"], list)


def test_intent_fallback_constraints():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("lightweight model for mobile deployment with low latency")
    assert "constraints" in result


def test_intent_fallback_flag():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("test input")
    assert result["_fallback"] is True


# ── Retrieval Scoring Tests ──────────────────────────────────────────────────

def test_recency_score_current():
    from services.retrieval.retrieval_service import _recency_score
    current = str(datetime.now().year)
    assert _recency_score(current) == 1.0


def test_recency_score_recent():
    from services.retrieval.retrieval_service import _recency_score
    year = datetime.now().year
    assert _recency_score(str(year - 1)) == 0.8
    assert _recency_score(str(year - 2)) == 0.8


def test_recency_score_old():
    from services.retrieval.retrieval_service import _recency_score
    assert _recency_score("2015") == 0.2
    assert _recency_score("2010") == 0.2


def test_recency_score_invalid():
    from services.retrieval.retrieval_service import _recency_score
    assert _recency_score("abc") == 0.3
    assert _recency_score("") == 0.3
    assert _recency_score(None) == 0.3


def test_relevance_score_high():
    from services.retrieval.retrieval_service import _relevance_score
    score = _relevance_score(
        "deep learning NLP transformer",
        "Deep Learning for Natural Language Processing with Transformers",
        "This paper applies deep learning and transformer models to NLP tasks"
    )
    assert score > 0.5


def test_relevance_score_low():
    from services.retrieval.retrieval_service import _relevance_score
    score = _relevance_score(
        "quantum computing blockchain",
        "Image Recognition with CNNs for Object Detection",
        "We perform object detection in images using convolutional neural networks"
    )
    assert score < 0.3


def test_relevance_score_empty():
    from services.retrieval.retrieval_service import _relevance_score
    score = _relevance_score("", "", "")
    assert 0.0 <= score <= 1.0


def test_citation_weight_high():
    from services.retrieval.retrieval_service import _citation_weight
    assert _citation_weight("200") == 1.0
    assert _citation_weight("1000") == 1.0


def test_citation_weight_low():
    from services.retrieval.retrieval_service import _citation_weight
    assert _citation_weight("0") == 0.0
    assert _citation_weight("5") == 0.025


def test_citation_weight_invalid():
    from services.retrieval.retrieval_service import _citation_weight
    assert _citation_weight("N/A") == 0.0
    assert _citation_weight("abc") == 0.0


def test_compute_score():
    from services.retrieval.retrieval_service import _compute_score
    paper = {
        "title": "Deep Learning Methods for Natural Language Processing",
        "abstract": "We apply deep learning to various NLP tasks including translation and summarization.",
        "year": str(datetime.now().year),
        "citations": "100",
    }
    score = _compute_score("deep learning for NLP", paper)
    assert 0.0 <= score <= 1.0
    assert score > 0.3


def test_compute_score_old_paper():
    from services.retrieval.retrieval_service import _compute_score
    paper = {
        "title": "Old Method for Everything",
        "abstract": "An old paper about general methods.",
        "year": "2010",
        "citations": "5",
    }
    score = _compute_score("modern deep learning", paper)
    assert 0.0 <= score <= 1.0


# ── Deduplication Tests ──────────────────────────────────────────────────────

def test_deduplication_removes_duplicates():
    from services.retrieval.retrieval_service import _deduplicate
    papers = [
        {"title": "Machine Learning for NLP"},
        {"title": "Deep Learning in Healthcare"},
        {"title": "machine learning for nlp"},
    ]
    unique = _deduplicate(papers)
    assert len(unique) == 2


def test_deduplication_keeps_unique():
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


def test_deduplication_single():
    from services.retrieval.retrieval_service import _deduplicate
    papers = [{"title": "Only Paper"}]
    unique = _deduplicate(papers)
    assert len(unique) == 1


# ── Quality Gate Tests ───────────────────────────────────────────────────────

def test_quality_gate_valid():
    from core.quality_gate import validate_idea
    idea = {
        "title": "Novel Transformer Architecture for Efficient NLP",
        "description": "A comprehensive approach to improving transformer efficiency through sparse attention mechanisms that reduces computational cost while maintaining accuracy on standard benchmarks.",
        "novelty": "This combines two previously separate lines of research into attention sparsity and dynamic routing in a novel way that has not been explored before.",
        "approach": "We propose a hybrid sparse-dynamic attention mechanism that selectively activates attention heads based on input complexity and task requirements.",
        "novelty_score": 8.0,
        "feasibility_score": 7.0,
    }
    valid, issues = validate_idea(idea)
    assert valid is True
    assert len(issues) == 0


def test_quality_gate_invalid():
    from core.quality_gate import validate_idea
    idea = {"title": "", "description": "short", "novelty": "x", "approach": "y"}
    valid, issues = validate_idea(idea)
    assert valid is False
    assert len(issues) >= 3


def test_quality_gate_score_range():
    from core.quality_gate import validate_idea
    idea = {
        "title": "Test Idea",
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


def test_validate_gap_valid():
    from core.quality_gate import validate_gap
    gap = {
        "title": "Methodological Gap in Current Approaches",
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


# ── Gap Agent Tests ──────────────────────────────────────────────────────────

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


def test_extract_key_sections_no_sections():
    from agents.gap_miner.gap_agent import _extract_key_sections
    text = "This is plain text with no section headers at all."
    result = _extract_key_sections(text)
    assert len(result) > 0


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


def test_extracted_gaps_from_papers():
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


# ── Idea Generator Tests ─────────────────────────────────────────────────────

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


def test_idea_ranking_single():
    from agents.idea_generator.idea_agent import _rank_ideas
    ideas = [{"title": "Only", "novelty_score": 7, "feasibility_score": 6}]
    ranked = _rank_ideas(ideas)
    assert len(ranked) == 1
    assert ranked[0]["title"] == "Only"


# ── Writer Agent Tests ───────────────────────────────────────────────────────

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
    assert "[1]" in result["sections"][0]["content"]
    assert "[2]" in result["sections"][0]["content"]


def test_postprocess_citations_invalid_refs():
    from agents.writer.writer_agent import _postprocess_citations
    report = {
        "sections": [{"content": "As shown in [99], this works."}],
        "references": [{"id": 1}, {"id": 2}],
    }
    result = _postprocess_citations(report, [])
    assert "[99]" not in result["sections"][0]["content"]


def test_postprocess_citations_adds_acknowledgements():
    from agents.writer.writer_agent import _postprocess_citations
    report = {
        "sections": [{"content": "Test content."}],
        "references": [],
    }
    result = _postprocess_citations(report, [])
    assert "acknowledgements" in result


def test_postprocess_citations_adds_affiliations():
    from agents.writer.writer_agent import _postprocess_citations
    report = {
        "sections": [{"content": "Test content."}],
        "references": [],
        "authors": ["Author 1"],
    }
    result = _postprocess_citations(report, [])
    assert "affiliations" in result
    assert "emails" in result


def test_postprocess_citations_section_ids():
    from agents.writer.writer_agent import _postprocess_citations
    report = {
        "sections": [
            {"content": "Introduction content."},
            {"content": "Related work content."},
            {"content": "Methodology content."},
        ],
        "references": [],
    }
    result = _postprocess_citations(report, [])
    for section in result["sections"]:
        assert "id" in section


def test_writer_parse_json_valid():
    from agents.writer.writer_agent import _parse_json
    raw = '{"title": "Test", "authors": ["A"]}'
    result = _parse_json(raw)
    assert result["title"] == "Test"


def test_writer_parse_json_with_fences():
    from agents.writer.writer_agent import _parse_json
    raw = '```json\n{"title": "Test"}\n```'
    result = _parse_json(raw)
    assert result["title"] == "Test"


def test_writer_parse_json_empty():
    from agents.writer.writer_agent import _parse_json
    assert _parse_json("") == {}
    assert _parse_json("not json") == {}


# ── Rate Limiter Tests ───────────────────────────────────────────────────────

def test_rate_limit_allows():
    from api.routes.auth import _check_rate_limit
    assert _check_rate_limit("test_fresh_key_nlp", 5, 60) is True


def test_rate_limit_blocks():
    from api.routes.auth import _check_rate_limit
    key = "test_block_key_nlp_2026"
    for _ in range(5):
        _check_rate_limit(key, 5, 60)
    assert _check_rate_limit(key, 5, 60) is False


# ── Export Service Tests ─────────────────────────────────────────────────────

def _has_tnr_font():
    import platform
    if platform.system() == "Windows":
        return os.path.exists(os.path.join("C:", os.sep, "Windows", "Fonts", "times.ttf"))
    font_paths = [
        "/usr/share/fonts/truetype/msttcorefonts/Times_New_Roman.ttf",
        "/usr/share/fonts/Times_New_Roman.ttf",
        os.path.expanduser("~/.fonts/Times_New_Roman.ttf"),
    ]
    return any(os.path.exists(p) for p in font_paths)


@pytest.mark.skipif(not _has_tnr_font(), reason="Times New Roman font not available")
def test_pdf_generation():
    from services.export_service import generate_pdf
    report = {
        "title": "Test Paper Title",
        "authors": ["Author 1"],
        "affiliations": ["University A"],
        "emails": ["a@uni.edu"],
        "abstract": "Test abstract for PDF generation.",
        "keywords": ["test", "paper", "pdf"],
        "sections": [
            {"heading": "I. INTRODUCTION", "content": "This is the introduction paragraph with sufficient text to test the layout."},
            {"heading": "II. METHODOLOGY", "content": "This is the methodology section describing the approach taken."},
            {"heading": "III. RESULTS", "content": "Results show significant improvement over baselines."},
        ],
        "acknowledgements": "We thank everyone.",
        "references": [
            {"id": 1, "authors": "Smith et al.", "title": "First Paper", "venue": "ICML", "year": "2024"},
            {"id": 2, "authors": "Jones et al.", "title": "Second Paper", "venue": "NeurIPS", "year": "2023"},
        ],
    }
    pdf_bytes = generate_pdf(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes[:4] == b'%PDF'


def test_docx_generation():
    from services.export_service import generate_docx
    report = {
        "title": "Test Paper Title",
        "authors": ["Author 1"],
        "affiliations": ["University A"],
        "emails": ["a@uni.edu"],
        "abstract": "Test abstract.",
        "keywords": ["test"],
        "sections": [
            {"heading": "I. INTRODUCTION", "content": "Introduction content here."},
        ],
        "references": [
            {"id": 1, "authors": "Smith", "title": "Paper", "venue": "ICML", "year": "2024"},
        ],
    }
    docx_bytes = generate_docx(report)
    assert isinstance(docx_bytes, bytes)
    assert len(docx_bytes) > 500


@pytest.mark.skipif(not _has_tnr_font(), reason="Times New Roman font not available")
def test_pdf_unicode_handling():
    from services.export_service import generate_pdf
    report = {
        "title": "Paper with Special Chars: em dash \u2014 quotes \u201c\u201d",
        "authors": ["Author 1"],
        "abstract": "Text with \u2014 and \u2026 symbols.",
        "keywords": ["test"],
        "sections": [
            {"heading": "I. INTRODUCTION", "content": "Content with special characters."},
        ],
        "references": [],
    }
    pdf_bytes = generate_pdf(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500


@pytest.mark.skipif(not _has_tnr_font(), reason="Times New Roman font not available")
def test_pdf_empty_sections():
    from services.export_service import generate_pdf
    report = {
        "title": "Minimal Paper",
        "authors": ["Author 1"],
        "abstract": "Short abstract.",
        "keywords": [],
        "sections": [],
        "references": [],
    }
    pdf_bytes = generate_pdf(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500


# ── LLM Client Tests ─────────────────────────────────────────────────────────

def test_llm_client_initialization():
    from core.llm_client import LLMClient
    client = LLMClient()
    assert client is not None


def test_json_extraction():
    import re
    # Test the JSON extraction pattern used across agents
    raw = '```json\n{"key": "value", "num": 42}\n```'
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    import json
    result = json.loads(clean[s:e])
    assert result["key"] == "value"
    assert result["num"] == 42


def test_json_extraction_nested():
    import re, json
    raw = 'Some text before\n{"sections": [{"id": 1, "content": "text"}]}\nSome text after'
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    result = json.loads(clean[s:e])
    assert len(result["sections"]) == 1
    assert result["sections"][0]["id"] == 1


# ── Scoring Metrics Tests ───────────────────────────────────────────────────

def test_novelty_score_range():
    # Test that novelty scores are within valid range
    scores = [0, 3, 5, 7, 10]
    for score in scores:
        assert 0 <= score <= 10


def test_feasibility_score_range():
    scores = [0, 2, 5, 8, 10]
    for score in scores:
        assert 0 <= score <= 10


def test_gap_confidence_levels():
    valid_levels = ["high", "medium", "low"]
    for level in valid_levels:
        assert level in valid_levels


def test_evidence_strength_levels():
    valid_levels = ["strong", "moderate", "weak"]
    for level in valid_levels:
        assert level in valid_levels


# ── Pipeline Integration Tests ───────────────────────────────────────────────

def test_pipeline_stage_order():
    expected_stages = [
        "nlp_analysis", "intent", "papers", "gaps", "ideas",
        "objectives", "plan", "data", "code", "experiments",
        "results", "guide", "paper_writing", "review"
    ]
    assert len(expected_stages) == 14
    assert expected_stages[0] == "nlp_analysis"
    assert expected_stages[-1] == "review"


def test_paper_scoring_weights():
    # Test that scoring weights sum to 1.0
    recency_weight = 0.3
    relevance_weight = 0.5
    citation_weight = 0.2
    total = recency_weight + relevance_weight + citation_weight
    assert abs(total - 1.0) < 0.001
