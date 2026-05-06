"""
Gap Mining Agent — 3-Pass Pipeline
Pass 1: Claim Extraction | Pass 2: Gap Identification | Pass 3: Scoring (skip for Ollama)
"""

import json
import re
import random
from typing import List, Dict, Any
from core.llm_client import LLMClient


# ── Pass 1: Claim Extraction ─────────────────────────────────────────────────

CLAIM_SYSTEM = "You are a scientific claim extractor. Return ONLY a valid JSON array."

CLAIM_PROMPT = """Read these paper abstracts and extract research claims.

Papers:
{papers_summary}

Return a JSON array of claims:
[
  {{"paper_title": "...", "claim": "...", "type": "contribution|limitation|future_work|assumption"}}
]

Extract up to 60 claims total. Each claim should be one specific sentence."""


# ── Pass 2: Gap Identification ────────────────────────────────────────────────

GAP_SYSTEM = "You are an expert research gap analyst. Return ONLY valid JSON."

GAP_PROMPT = """Given these research claims from the literature, identify 10-15 specific research gaps.

Claims:
{claims_text}

Domain: {domain}
Problem: {problem}

Return EXACTLY a JSON array with between 10 and 15 objects, no more, no less:
[
  {{
    "title": "Short gap title",
    "description": "Detailed description",
    "type": "methodological|dataset|evaluation|application|theoretical",
    "confidence": "high|medium|low",
    "supporting_papers": ["paper title 1"],
    "opportunity": "How to address this gap",
    "novelty_potential": 8,
    "evidence_strength": "strong|moderate|weak",
    "gap_category": "unexplored_combination|missed_population|evaluation_gap|scalability_gap|dataset_gap|theoretical_gap"
  }}
]"""


# ── Pass 3: Scoring ──────────────────────────────────────────────────────────

SCORE_SYSTEM = "You are a research impact evaluator. Return ONLY valid JSON."

SCORE_PROMPT = """Score each research gap on two dimensions:
- addressability (1-10): Can a single researcher address this in 6 months?
- impact (1-10): How much would solving this advance the field?

Gaps:
{gaps_text}

Return a JSON array with the same gaps, adding "addressability" and "impact" integer fields:
[
  {{"title": "...", "addressability": 7, "impact": 8}}
]"""


async def run_gap_analysis(
    papers: List[Dict[str, Any]],
    intent: Dict,
    llm: LLMClient,
) -> List[Dict]:
    """3-pass gap analysis pipeline."""
    if not papers:
        return _default_gaps()

    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    problem = intent.get("problem_statement", intent.get("task", "research problem"))
    papers_summary = _summarize_papers(papers[:15])

    try:
        # Pass 1: Extract claims
        claims = await _pass1_extract_claims(papers_summary, llm)
        if not claims:
            return _extracted_gaps_from_papers(papers)

        # Limit claims
        if len(claims) > 40:
            random.seed(42)
            claims = random.sample(claims, 40)
        # Truncate each claim
        for c in claims:
            if isinstance(c, dict) and "claim" in c:
                c["claim"] = c["claim"][:200]

        # Pass 2: Identify gaps
        gaps = await _pass2_identify_gaps(claims, domain, problem, llm)
        if not gaps:
            return _extracted_gaps_from_papers(papers)
        gaps = gaps[:15]

        # Pass 3: Score gaps (skip for Ollama)
        skip_pass3 = llm.provider.value == "ollama"
        if not skip_pass3:
            try:
                gaps = await _pass3_score_gaps(gaps, llm)
            except Exception:
                skip_pass3 = True

        if skip_pass3:
            for g in gaps:
                g.setdefault("addressability", 7)
                g.setdefault("impact", 7)

        # Compute final score
        for g in gaps:
            addr = float(g.get("addressability", 7))
            imp = float(g.get("impact", 7))
            nov = float(g.get("novelty_potential", 5))
            g["final_score"] = round(addr * 0.4 + imp * 0.4 + nov * 0.2, 2)

        gaps.sort(key=lambda g: g.get("final_score", 0), reverse=True)
        return gaps

    except Exception as e:
        print(f"Gap analysis pipeline error: {e}")
        return _extracted_gaps_from_papers(papers)


async def _pass1_extract_claims(papers_summary: str, llm: LLMClient) -> List[Dict]:
    prompt = CLAIM_PROMPT.format(papers_summary=papers_summary)
    raw = await llm.complete(prompt, system=CLAIM_SYSTEM, json_mode=True)
    return _parse_json_list(raw)


async def _pass2_identify_gaps(claims: List[Dict], domain: str, problem: str, llm: LLMClient) -> List[Dict]:
    claims_text = json.dumps(claims[:60], indent=1)
    prompt = GAP_PROMPT.format(claims_text=claims_text, domain=domain, problem=problem)
    raw = await llm.complete(prompt, system=GAP_SYSTEM, json_mode=True)
    return _parse_json_list(raw)


async def _pass3_score_gaps(gaps: List[Dict], llm: LLMClient) -> List[Dict]:
    gaps_text = json.dumps([{"title": g["title"], "description": g.get("description", "")} for g in gaps], indent=1)
    prompt = SCORE_PROMPT.format(gaps_text=gaps_text)
    raw = await llm.complete(prompt, system=SCORE_SYSTEM, json_mode=True)
    scores = _parse_json_list(raw)

    # Merge scores into gaps
    score_map = {s.get("title", "").lower(): s for s in scores}
    for g in gaps:
        match = score_map.get(g.get("title", "").lower(), {})
        g["addressability"] = match.get("addressability", 7)
        g["impact"] = match.get("impact", 7)

    return gaps


# ── Helpers ───────────────────────────────────────────────────────────────────

def _summarize_papers(papers: List[Dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Unknown")
        abstract = p.get("abstract", "")[:200]
        year = p.get("year", "")
        citations = p.get("citations", "N/A")
        lines.append(f"{i}. [{year}] {title} (citations: {citations})\n   {abstract}...")
    return "\n\n".join(lines)


def _parse_json_list(raw: str) -> List[Dict]:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start = clean.find("[")
    end = clean.rfind("]") + 1
    if start != -1 and end > start:
        return json.loads(clean[start:end])
    obj = json.loads(clean)
    for v in obj.values():
        if isinstance(v, list):
            return v
    return []


def _extracted_gaps_from_papers(papers: List[Dict]) -> List[Dict]:
    """Rule-based fallback gap extraction."""
    limitation_keywords = ["however", "limitation", "future work", "not considered",
                           "lack of", "insufficient", "limited", "cannot handle"]
    gaps = []
    for paper in papers[:10]:
        abstract = paper.get("abstract", "").lower()
        for kw in limitation_keywords:
            if kw in abstract:
                idx = abstract.find(kw)
                snippet = abstract[max(0, idx - 20):idx + 100]
                gaps.append({
                    "title": f"Gap from: {paper.get('title', 'Unknown')[:50]}",
                    "description": snippet,
                    "type": "methodological",
                    "confidence": "low",
                    "supporting_papers": [paper.get("title", "")],
                    "opportunity": "Address the mentioned limitation",
                    "novelty_potential": 5,
                    "evidence_strength": "weak",
                    "gap_category": "evaluation_gap",
                    "addressability": 7,
                    "impact": 5,
                    "final_score": 5.8,
                })
                break
    return gaps[:6] if gaps else _default_gaps()


def _default_gaps() -> List[Dict]:
    return [{
        "title": "Insufficient paper data",
        "description": "Could not retrieve enough papers for proper gap analysis.",
        "type": "methodological",
        "confidence": "low",
        "supporting_papers": [],
        "opportunity": "Manually search for papers in your domain",
        "novelty_potential": 5,
        "evidence_strength": "weak",
        "gap_category": "dataset_gap",
        "addressability": 7,
        "impact": 5,
        "final_score": 5.8,
    }]
