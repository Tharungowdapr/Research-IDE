"""
Idea Generation Agent — Critic-Defender Adversarial Loop
Round 1: Generate 6 ideas | Round 2: Critique | Round 3: Defend & Refine
"""

import json
import re
from typing import List, Dict, Any
from core.llm_client import LLMClient


# ── Round 1: Generate ────────────────────────────────────────────────────────

GEN_SYSTEM = "You are a creative research idea generator. Generate specific, actionable, novel ideas. Return ONLY valid JSON."

GEN_PROMPT = """Generate 15 innovative research ideas based on these gaps.

Research Domain: {domain}
Problem: {problem}
Constraints: {constraints}

Identified Research Gaps:
{gaps_summary}

Key Papers Context:
{papers_summary}

Generate 15 ideas as a JSON array. Each idea must include:
[
  {{
    "title": "Concise idea title",
    "description": "2-3 sentence description",
    "novelty": "Why this is novel",
    "approach": "High-level technical approach",
    "addresses_gaps": ["gap title 1"],
    "related_papers": ["paper 1"],
    "suggested_datasets": ["dataset 1"],
    "suggested_methods": ["method 1"],
    "feasibility": "high|medium|low",
    "expected_impact": "high|medium|low",
    "novelty_score": 7.5,
    "feasibility_score": 6.0,
    "time_estimate": "2-3 months",
    "difficulty": "beginner|intermediate|advanced",
    "assumptions": ["assumption 1", "assumption 2", "assumption 3"],
    "failure_modes": ["failure mode 1", "failure mode 2"]
  }}
]"""

# ── Round 2: Critique ────────────────────────────────────────────────────────

CRITIQUE_SYSTEM = "You are a harsh but fair peer reviewer at NeurIPS. Your job is to find fatal flaws in research ideas. Be specific. Return ONLY a JSON array."

CRITIQUE_PROMPT = """Critically evaluate each research idea. Find fatal flaws and weaknesses.

Ideas:
{ideas_json}

For each idea, return:
[
  {{
    "idea_title": "...",
    "fatal_flaw": "Specific description of the biggest problem",
    "weakness_score": 5,
    "is_salvageable": true,
    "suggested_fix": "How to fix the main issue"
  }}
]

weakness_score: 1=very strong idea, 10=fatally flawed.
is_salvageable: can the idea be fixed with modifications?"""

# ── Round 3: Defend & Refine ─────────────────────────────────────────────────

DEFEND_SYSTEM = "You are a senior researcher responding to peer review. Revise each salvageable idea to address the critique. Maintain all original JSON fields. Return ONLY a JSON array."

DEFEND_PROMPT = """Revise these research ideas based on peer review critiques.

Original Ideas:
{ideas_json}

Critiques:
{critiques_json}

For each idea where is_salvageable=true AND weakness_score < 7:
- Address the fatal_flaw in the description and approach
- Incorporate the suggested_fix
- Update novelty_score and feasibility_score if the fix changes them
- Keep ALL original fields

Return refined ideas as a JSON array with all original fields preserved."""


async def run_idea_generation(
    gaps: List[Dict],
    papers: List[Dict],
    intent: Dict,
    llm: LLMClient,
) -> List[Dict]:
    """Critic-Defender adversarial idea generation."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    problem = intent.get("problem_statement", "")
    constraints = _format_constraints(intent.get("constraints", {}))
    gaps_summary = _summarize_gaps(gaps)
    papers_summary = _summarize_papers_brief(papers[:8])

    try:
        # Round 1: Generate 10 ideas
        ideas = await _round1_generate(domain, problem, constraints, gaps_summary, papers_summary, llm)
        if not ideas:
            return _fallback_ideas(gaps, intent)

        # Round 2: Critique
        try:
            critiques = await _round2_critique(ideas, llm)
        except Exception as e:
            print(f"Critique round failed: {e}")
            # Skip rounds 2+3, return originals
            for idea in ideas:
                idea["survived_critique"] = False
                idea["critique_summary"] = "Critique unavailable"
            return _rank_ideas(ideas)[:8]

        # Apply critique filter
        critique_map = {c.get("idea_title", "").lower(): c for c in critiques}
        survivors = []
        rejected = []

        for idea in ideas:
            crit = critique_map.get(idea.get("title", "").lower(), {})
            ws = crit.get("weakness_score", 5)
            salvageable = crit.get("is_salvageable", True)
            idea["_weakness_score"] = ws
            idea["_critique"] = crit

            if ws < 8 and salvageable:
                survivors.append(idea)
            else:
                rejected.append(idea)

        # Ensure we return at least 8 ideas if possible
        if len(survivors) < 8:
            # Add back some rejected ideas with lowest weakness scores
            rejected.sort(key=lambda x: x.get("_weakness_score", 10))
            needed = 8 - len(survivors)
            survivors.extend(rejected[:needed])

        # Minimum survivors rule
        if len(survivors) < 4:
            rejected.sort(key=lambda x: x.get("_weakness_score", 10))
            while len(survivors) < 4 and rejected:
                forced = rejected.pop(0)
                forced["_forced"] = True
                survivors.append(forced)

        # Round 3: Defend & Refine
        try:
            refined = await _round3_defend(survivors, critiques, llm)
            if refined:
                survivors = refined
        except Exception as e:
            print(f"Defend round failed: {e}")

        # Add critique metadata
        for idea in survivors:
            crit = idea.pop("_critique", {})
            idea.pop("_weakness_score", None)
            idea.pop("_forced", None)
            idea["survived_critique"] = True
            idea["critique_summary"] = crit.get("fatal_flaw", "Passed review")[:100]
            idea.setdefault("assumptions", [])
            idea.setdefault("failure_modes", [])

        return _rank_ideas(survivors)[:8]

    except Exception as e:
        print(f"Idea generation error: {e}")
        return _fallback_ideas(gaps, intent)


async def _round1_generate(domain, problem, constraints, gaps_summary, papers_summary, llm):
    prompt = GEN_PROMPT.format(
        domain=domain, problem=problem, constraints=constraints,
        gaps_summary=gaps_summary, papers_summary=papers_summary,
    )
    raw = await llm.complete(prompt, system=GEN_SYSTEM, json_mode=True)
    return _parse_json_list(raw)


async def _round2_critique(ideas, llm):
    ideas_json = json.dumps([{"title": i["title"], "description": i.get("description", ""),
                              "approach": i.get("approach", ""), "assumptions": i.get("assumptions", [])}
                             for i in ideas], indent=1)
    prompt = CRITIQUE_PROMPT.format(ideas_json=ideas_json)
    raw = await llm.complete(prompt, system=CRITIQUE_SYSTEM, json_mode=True)
    return _parse_json_list(raw)


async def _round3_defend(survivors, critiques, llm):
    ideas_json = json.dumps(survivors, indent=1, default=str)
    critiques_json = json.dumps(critiques, indent=1, default=str)
    prompt = DEFEND_PROMPT.format(ideas_json=ideas_json, critiques_json=critiques_json)
    raw = await llm.complete(prompt, system=DEFEND_SYSTEM, json_mode=True)
    return _parse_json_list(raw)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_constraints(constraints: Dict) -> str:
    parts = []
    if constraints.get("compute"):
        parts.append(f"Compute: {constraints['compute']}")
    if constraints.get("region"):
        parts.append(f"Region: {constraints['region']}")
    if constraints.get("real_time"):
        parts.append("Real-time required")
    return ", ".join(parts) or "No specific constraints"


def _summarize_gaps(gaps: List[Dict]) -> str:
    return "\n".join(f"- {g.get('title', 'Unknown')}: {g.get('description', '')[:150]}" for g in gaps[:6])


def _summarize_papers_brief(papers: List[Dict]) -> str:
    return "\n".join(f"- [{p.get('year', '')}] {p.get('title', '')}: {p.get('abstract', '')[:100]}..." for p in papers)


def _rank_ideas(ideas: List[Dict]) -> List[Dict]:
    def score(idea):
        n = float(idea.get("novelty_score", 5))
        f = float(idea.get("feasibility_score", 5))
        return n * 0.6 + f * 0.4
    return sorted(ideas, key=score, reverse=True)


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


def _fallback_ideas(gaps: List[Dict], intent: Dict) -> List[Dict]:
    return [
        {
            "title": f"Novel approach addressing {g.get('title', 'research gap')}",
            "description": f"Develop a new approach that addresses: {g.get('description', '')[:200]}",
            "novelty": "Addresses an identified gap in the literature",
            "approach": "Literature-driven methodology development",
            "addresses_gaps": [g.get("title", "")],
            "related_papers": g.get("supporting_papers", []),
            "suggested_datasets": [],
            "suggested_methods": [],
            "feasibility": "medium",
            "expected_impact": "medium",
            "novelty_score": 6.0,
            "feasibility_score": 5.0,
            "time_estimate": "3-6 months",
            "difficulty": "intermediate",
            "assumptions": ["Standard compute available", "Public datasets exist", "Method generalizes"],
            "failure_modes": ["Data may not be sufficient", "Approach may not scale"],
            "survived_critique": False,
            "critique_summary": "Critique unavailable — fallback idea",
        }
        for g in gaps[:3]
    ]
