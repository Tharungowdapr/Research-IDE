"""
Gap Mining Agent — 3-Pass Pipeline with Full Text Analysis
Pass 1: Claim Extraction | Pass 2: Gap Identification | Pass 3: Scoring (skip for Ollama)
"""

import json
import re
import random
import asyncio
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from core.llm_client import LLMClient
from core.pdf_extractor import extract_full_text
from services.cache_service import get_cached_paper, cache_full_text


# ── Pass 1: Claim Extraction ─────────────────────────────────────────────────

CLAIM_SYSTEM = "You are a scientific claim extractor. Return ONLY a valid JSON array."

CLAIM_PROMPT = """Read these paper summaries (including full text where available) and extract research claims.

Papers:
{papers_summary}

Return a JSON array of claims:
[
  {{"paper_title": "...", "claim": "...", "type": "contribution|limitation|future_work|assumption|method|result"}}
]

Extract up to 60 claims total. Focus on:
- Methodological limitations and gaps
- Unexplored aspects mentioned in the paper
- Future work suggestions from the authors
- Assumptions that may not hold
- Evaluation gaps or dataset limitations

Each claim should be one specific sentence."""


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
    db: Session = None,
    progress_callback: callable = None,
) -> List[Dict]:
    """3-pass gap analysis pipeline with full text analysis."""
    if not papers:
        return _default_gaps()

    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    problem = intent.get("problem_statement", intent.get("task", "research problem"))

    # Fetch full text for top papers with persistent caching
    if progress_callback:
        progress_callback("Fetching full text for papers...", 10)
    print(f"Fetching full text for {min(15, len(papers))} papers...")
    enriched_papers = await _enrich_papers_with_full_text(papers[:15], db, progress_callback)
    papers_summary = _summarize_papers(enriched_papers)

    try:
        # Pass 1: Extract claims from full text
        if progress_callback:
            progress_callback("Extracting claims from papers...", 40)
        try:
            claims = await _pass1_extract_claims(papers_summary, llm)
        except Exception as e:
            print(f"Pass 1 JSON parse error: {e}")
            claims = []
        
        if not claims:
            return _extracted_gaps_from_papers(enriched_papers)

        # Limit claims
        if len(claims) > 40:
            random.seed(42)
            claims = random.sample(claims, 40)
        # Truncate each claim for pass 2
        for c in claims:
            if isinstance(c, dict) and "claim" in c:
                c["claim"] = c["claim"][:300]

        # Pass 2: Identify gaps
        gaps = await _pass2_identify_gaps(claims, domain, problem, llm)
        if not gaps:
            return _extracted_gaps_from_papers(enriched_papers)
        gaps = gaps[:15]

        # Normalize supporting_papers early
        for g in gaps:
            papers_list = g.get("supporting_papers", [])
            normalized = []
            for p in papers_list:
                if isinstance(p, dict):
                    normalized.append(p.get("title", p.get("paper_title", str(p)[:120])))
                elif isinstance(p, str):
                    normalized.append(p)
                else:
                    normalized.append(str(p))
            g["supporting_papers"] = normalized

        # Pass 3: Score gaps (skip for Ollama)
        skip_pass3 = llm.provider.value == "ollama"
        if not skip_pass3:
            try:
                gaps = await _pass3_score_gaps(gaps, llm)
            except Exception:
                skip_pass3 = True

        if skip_pass3:
            for g in gaps:
                g.setdefault("addressability", _estimate_addressability(g))
                g.setdefault("impact", _estimate_impact(g))

        # Compute final score
        for g in gaps:
            addr = float(g.get("addressability", 7))
            imp = float(g.get("impact", 7))
            nov = float(g.get("novelty_potential", 5))
            g["final_score"] = round(addr * 0.4 + imp * 0.4 + nov * 0.2, 2)

        gaps.sort(key=lambda g: g.get("final_score", 0), reverse=True)

        # Normalize supporting_papers to always be list of strings
        for g in gaps:
            papers_list = g.get("supporting_papers", [])
            normalized = []
            for p in papers_list:
                if isinstance(p, dict):
                    normalized.append(p.get("title", p.get("paper_title", str(p)[:120])))
                elif isinstance(p, str):
                    normalized.append(p)
                else:
                    normalized.append(str(p))
            g["supporting_papers"] = normalized

        return gaps

    except Exception as e:
        print(f"Gap analysis pipeline error: {e}")
        # Return fallback gaps using enriched papers if available
        gaps = _extracted_gaps_from_papers(enriched_papers if 'enriched_papers' in locals() else papers)
        for g in gaps:
            papers_list = g.get("supporting_papers", [])
            normalized = []
            for p in papers_list:
                if isinstance(p, dict):
                    normalized.append(p.get("title", p.get("paper_title", str(p)[:120])))
                elif isinstance(p, str):
                    normalized.append(p)
                else:
                    normalized.append(str(p))
            g["supporting_papers"] = normalized
        return gaps


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

async def _enrich_papers_with_full_text(papers: List[Dict], db: Session = None, progress_callback: callable = None) -> List[Dict]:
    """Fetch full text for papers concurrently. Uses persistent cache if db is provided."""
    enriched = []
    total = len(papers)
    
    async def _fetch_one(paper, index):
        enriched_paper = paper.copy()
        paper_id = paper.get("id", paper.get("title", ""))
        
        # Check persistent cache first if db is available
        if db:
            cached = get_cached_paper(db, paper_id)
            if cached and cached.get("full_text"):
                print(f"Using persistently cached full text for: {paper.get('title', 'Unknown')[:50]}")
                enriched_paper["full_text"] = cached["full_text"]
                enriched_paper["full_text_summary"] = cached["full_text"][:2000] if len(cached["full_text"]) > 2000 else cached["full_text"]
                if progress_callback:
                    progress_callback(f"Loaded cached paper {index+1}/{total}", int(10 + (index+1) * 30 / total))
                return enriched_paper
        
        # Fetch full text with timeout
        try:
            if progress_callback:
                progress_callback(f"Fetching full text for paper {index+1}/{total}...", int(10 + (index+1) * 30 / total))
            full_text = await asyncio.wait_for(
                extract_full_text(paper),
                timeout=30.0  # 30 second timeout per paper
            )
            # Cache in persistent storage if db is available
            if db and full_text:
                cache_full_text(db, paper_id, full_text)
        except asyncio.TimeoutError:
            print(f"Timeout fetching full text for {paper.get('title', 'Unknown')[:50]}")
            full_text = paper.get("abstract", "")
        except Exception as e:
            print(f"Error extracting full text for {paper.get('title', 'Unknown')}: {e}")
            full_text = paper.get("abstract", "")
        
        enriched_paper["full_text"] = full_text
        # Store truncated version for summary (first 2000 chars for better analysis)
        enriched_paper["full_text_summary"] = full_text[:2000] if full_text and len(full_text) > 2000 else full_text
        if progress_callback:
            progress_callback(f"Processed paper {index+1}/{total}", int(10 + (index+1) * 30 / total))
        return enriched_paper
    
    # Fetch concurrently with a limit to avoid overwhelming the system
    tasks = [_fetch_one(paper, i) for i, paper in enumerate(papers)]
    enriched = await asyncio.gather(*tasks)
    return enriched


def _summarize_papers(papers: List[Dict]) -> str:
    """Summarize papers prioritizing key sections from full text."""
    lines = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Unknown")
        year = p.get("year", "")
        citations = p.get("citations", "N/A")
        
        # Prioritize: full_text_summary > abstract
        full_text = p.get("full_text", "")
        if full_text and len(full_text) > 2000:
            # Try to extract key sections (abstract, conclusion, limitations)
            content = _extract_key_sections(full_text[:3000])
        elif full_text:
            content = full_text
        else:
            content = p.get("abstract", "")[:500]
        
        lines.append(f"{i}. [{year}] {title} (citations: {citations})\n   {content}...")
    return "\n\n".join(lines)


def _extract_key_sections(text: str) -> str:
    """Extract key sections like abstract, conclusion, limitations from full text."""
    import re
    # Look for section headers
    sections = []
    patterns = [
        (r"abstract[:\s]*", "Abstract"),
        (r"conclusion[:\s]*", "Conclusion"),
        (r"limitation[:\s]*", "Limitations"),
        (r"future work[:\s]*", "Future Work"),
        (r"discussion[:\s]*", "Discussion"),
    ]
    
    for pattern, name in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            start = match.end()
            # Get next 500 chars after section header
            sections.append(f"[{name}] {text[start:start+500]}")
    
    if sections:
        return " | ".join(sections)
    return text[:2000]


def _parse_json_list(raw: str) -> List[Dict]:
    if not raw or not raw.strip():
        return []
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    # Try direct array parse first
    start = clean.find("[")
    end = clean.rfind("]") + 1
    if start != -1 and end > start:
        try:
            return json.loads(clean[start:end])
        except json.JSONDecodeError:
            pass
    # Try object with list values
    try:
        obj = json.loads(clean)
        for v in obj.values():
            if isinstance(v, list):
                return v
    except json.JSONDecodeError:
        pass
    # Try partial recovery: find innermost complete objects
    try:
        cleaned = clean.strip().rstrip(",").rstrip(".").strip()
        if cleaned.startswith("{"):
            # Might be truncated — try to find any array within
            arr_start = cleaned.find("[")
            arr_end = cleaned.rfind("]")
            if arr_start != -1 and arr_end > arr_start + 1:
                partial = cleaned[arr_start:arr_end+1]
                return json.loads(partial)
    except (json.JSONDecodeError, Exception):
        pass
    return []


def _extracted_gaps_from_papers(papers: List[Dict]) -> List[Dict]:
    """Rule-based fallback gap extraction using full text when available."""
    limitation_keywords = ["however", "limitation", "future work", "not considered",
                           "lack of", "insufficient", "limited", "cannot handle", 
                           "drawback", "shortcoming", "gap", "challenge"]
    type_keywords = {"methodological": ["method", "approach", "technique", "algorithm"],
                     "dataset": ["dataset", "data", "benchmark", "corpus"],
                     "evaluation": ["evaluation", "metric", "measure", "assess"],
                     "application": ["application", "domain", "real-world", "practical"],
                     "theoretical": ["theory", "theorem", "assumption", "bound"]}
    category_keywords = {"unexplored_combination": ["combine", "integration", "hybrid"],
                         "evaluation_gap": ["evaluation", "metric", "benchmark"],
                         "dataset_gap": ["dataset", "data", "corpus"],
                         "scalability_gap": ["scalable", "large-scale", "efficiency"],
                         "theoretical_gap": ["theory", "theoretical", "analysis"]}
    
    gaps = []
    for paper in papers[:10]:
        text = paper.get("full_text", paper.get("abstract", "")).lower()
        title = paper.get("title", "Unknown")
        seen_snippets = set()
        # Find multiple keyword matches (not just the first)
        for kw in limitation_keywords:
            idx = 0
            while True:
                idx = text.find(kw, idx)
                if idx == -1:
                    break
                snippet = text[max(0, idx - 60):idx + 250].strip()
                # Deduplicate by snippet content
                snippet_key = snippet[:100]
                if snippet_key not in seen_snippets:
                    seen_snippets.add(snippet_key)
                    # Determine type and category from surrounding context
                    context = text[max(0, idx-100):idx+300]
                    gap_type = "methodological"
                    for t, kws in type_keywords.items():
                        if any(k in context for k in kws):
                            gap_type = t
                            break
                    gap_category = "evaluation_gap"
                    for c, kws in category_keywords.items():
                        if any(k in context for k in kws):
                            gap_category = c
                            break
                    has_full_text = bool(paper.get("full_text"))
                    gaps.append({
                        "title": f"{kw.title()} in {title[:60]}",
                        "description": snippet,
                        "type": gap_type,
                        "confidence": "low",
                        "supporting_papers": [title],
                        "opportunity": f"Investigate the mentioned {kw} to identify research directions",
                        "novelty_potential": 6,
                        "evidence_strength": "weak",
                        "gap_category": gap_category,
                        "addressability": 7,
                        "impact": 5,
                        "final_score": 5.8,
                        "from_full_text": has_full_text,
                    })
                idx += len(kw)
    gaps = gaps[:15]
    return gaps if gaps else _default_gaps()


def _estimate_addressability(gap: dict) -> int:
    """Rule-based estimate: how addressable is this gap for a single researcher in 6 months."""
    evidence = gap.get("evidence_strength", "moderate")
    category = gap.get("gap_category", "")
    score = 6
    if evidence == "strong":
        score += 1
    elif evidence == "weak":
        score -= 1
    if category in ("unexplored_combination", "evaluation_gap"):
        score += 1
    elif category in ("scalability_gap", "theoretical_gap"):
        score -= 1
    return max(3, min(score, 9))


def _estimate_impact(gap: dict) -> int:
    """Rule-based estimate: potential impact if this gap is addressed."""
    category = gap.get("gap_category", "")
    novelty = gap.get("novelty_potential", 5)
    score = 5
    if category in ("unexplored_combination", "theoretical_gap"):
        score += 2
    elif category in ("dataset_gap", "evaluation_gap"):
        score += 1
    if novelty >= 8:
        score += 1
    elif novelty <= 3:
        score -= 1
    return max(3, min(score, 9))


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
