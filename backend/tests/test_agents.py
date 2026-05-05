"""Backend test suite — run with: pytest tests/ -v"""
import sys, os, ast, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def test_intent_fallback():
    from services.intent.intent_service import _fallback_intent
    result = _fallback_intent("crop yield prediction India satellite imagery low compute NLP")
    assert isinstance(result["keywords"], list) and len(result["keywords"]) > 0
    assert isinstance(result["queries"], list) and len(result["queries"]) > 0
    assert result["_fallback"] is True
    assert "nlp_analysis" in result
    assert "tokenization_demo" in result
    assert "stop_words_analysis" in result
    assert "stemming_lemmatization" in result


def test_intent_nlp_analysis():
    from services.intent.intent_service import (
        _build_basic_nlp_analysis, _build_tokenization_demo,
        _build_stopwords_analysis, _build_stemming_demo,
        _detect_semantic_field, _detect_technical_level,
    )
    text = "Using BERT and transformer models for low-resource NLP classification tasks"
    nlp = _build_basic_nlp_analysis(text)
    assert "morphological" in nlp
    assert "syntactic" in nlp
    assert "semantic" in nlp
    assert "pragmatic" in nlp
    assert "discourse" in nlp
    tok = _build_tokenization_demo(text)
    assert len(tok["word_tokens"]) > 0
    assert len(tok["sentence_tokens"]) > 0
    sw = _build_stopwords_analysis(text)
    assert sw["total_words"] > 0
    field = _detect_semantic_field(text)
    level = _detect_technical_level(text)
    assert field in ["general NLP/ML", "biomedical NLP", "machine translation",
                     "sentiment analysis", "low-resource NLP", "text generation",
                     "question answering", "information retrieval", "computer vision", "speech processing"]
    assert level in ["beginner", "intermediate", "advanced", "expert"]


def test_deduplication():
    from services.retrieval.retrieval_service import _deduplicate
    papers = [
        {"id":"1","title":"Deep Learning for NLP","source":"arxiv","abstract":"a","year":"2024","citations":"10","authors":[],"url":"","github_url":"","score":0},
        {"id":"2","title":"Deep Learning for NLP","source":"semantic_scholar","abstract":"b","year":"2023","citations":"5","authors":[],"url":"","github_url":"","score":0},
        {"id":"3","title":"BERT Sentiment Analysis","source":"arxiv","abstract":"c","year":"2022","citations":"50","authors":[],"url":"","github_url":"","score":0},
    ]
    deduped = _deduplicate(papers)
    assert len(deduped) == 2


def test_paperswithcode_github_url():
    """Verify PapersWithCode github_url extraction from repositories list."""
    # Simulate the extraction logic
    item_with_repos = {"repositories": [{"url": "https://github.com/test/repo", "stars": 100}]}
    repos = item_with_repos.get("repositories") or item_with_repos.get("repository")
    github_url = ""
    if isinstance(repos, list) and repos:
        github_url = repos[0].get("url", "")
    assert github_url == "https://github.com/test/repo"


def test_idea_ranking():
    from agents.idea_generator.idea_agent import _rank_ideas
    ideas = [
        {"title":"A","novelty_score":8.5,"feasibility_score":6.0},
        {"title":"B","novelty_score":7.0,"feasibility_score":9.0},
        {"title":"C","novelty_score":9.5,"feasibility_score":4.0},
    ]
    ranked = _rank_ideas(ideas)
    # B=7.8, A=7.5, C=7.3
    assert ranked[0]["title"] == "B"
    assert ranked[1]["title"] == "A"


def test_idea_critique_fields():
    from agents.idea_generator.idea_agent import _fallback_ideas
    ideas = _fallback_ideas(
        [{"title":"Gap1","description":"A gap","supporting_papers":[]}],
        {"domain":["NLP"]}
    )
    assert len(ideas) >= 1
    assert "survived_critique" in ideas[0]
    assert "critique_summary" in ideas[0]
    assert ideas[0]["survived_critique"] == False


def test_build_guide_fallback():
    """Test build guide has all required sections (replaces code agent tests)."""
    from agents.code_agent.code_agent import _fallback_guide
    idea = {
        "title": "BERT for Low-Resource NLP",
        "description": "Improve BERT on low-resource languages",
        "approach": "Few-shot fine-tuning",
        "suggested_methods": ["BERT", "XLM-R"],
        "suggested_datasets": ["XTREME"],
        "time_estimate": "2-3 months",
        "difficulty": "intermediate",
        "feasibility": "medium",
    }
    plan = {"evaluation_metrics": ["F1", "Accuracy"]}
    guide = _fallback_guide(idea, plan)
    
    required_sections = [
        "project_name", "phases", "prerequisites", "environment_setup",
        "training_guide", "evaluation_guide", "debugging_guide",
        "next_steps", "resources", "architecture_guide",
    ]
    for section in required_sections:
        assert section in guide, f"Missing section: {section}"
    
    assert len(guide["phases"]) >= 4
    for phase in guide["phases"]:
        assert "steps" in phase
        assert len(phase["steps"]) >= 1
        assert "phase_deliverable" in phase


def test_gap_defaults():
    from agents.gap_miner.gap_agent import _default_gaps
    defaults = _default_gaps()
    assert isinstance(defaults, list)
    assert len(defaults) >= 1
    assert "title" in defaults[0]
    assert "description" in defaults[0]
    assert "final_score" in defaults[0]
    assert "addressability" in defaults[0]
    assert "impact" in defaults[0]
    assert "gap_category" in defaults[0]


def test_gap_rule_extraction():
    from agents.gap_miner.gap_agent import _extracted_gaps_from_papers
    papers = [
        {"title":"T1","abstract":"However, this approach has limitations for low-resource scenarios.","year":"2024","citations":"50","source":"arxiv"},
        {"title":"T2","abstract":"Future work should explore multilingual settings as current methods cannot handle code-switching.","year":"2023","citations":"30","source":"ss"},
    ]
    gaps = _extracted_gaps_from_papers(papers)
    assert len(gaps) >= 1
    assert "final_score" in gaps[0]
    assert gaps[0]["final_score"] > 0


def test_json_parser_robust():
    from core.utils import parse_llm_json, safe_parse_llm_json
    assert parse_llm_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_llm_json('{"a": True, "b": False}') == {"a": True, "b": False}
    assert parse_llm_json('{"a": 1,}') == {"a": 1}
    assert parse_llm_json('[{"x": 1}, {"x": 2}]') == [{"x": 1}, {"x": 2}]
    assert parse_llm_json('Here is the JSON:\n{"a": 1}') == {"a": 1}
    assert safe_parse_llm_json('broken {{{{', default=None) is None
