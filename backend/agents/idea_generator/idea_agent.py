"""Idea Generation Agent v2 — Critic-Defender adversarial loop"""

import json, random
from typing import List, Dict, Any
from core.llm_client import LLMClient
from core.utils import parse_llm_json, safe_parse_llm_json, truncate_text
from core.quality_gate import validate_ideas_batch

GEN_SYSTEM = (
    "You are a senior ML researcher proposing novel research ideas. STRICT RULES: "
    "1. problem_statement MUST be 2+ paragraphs explaining the technical context and specific issue. "
    "2. proposed_solution MUST be 2+ paragraphs with architecture details, methodology, and expected workflow. "
    "3. why_it_addresses_gap MUST be a detailed paragraph connecting the gap to the solution mechanics. "
    "4. potential_challenges MUST list at least 3 specific technical risks with mitigation strategies. "
    "5. NEVER use phrases like 'novel approach' or 'state-of-the-art' without technical justification. "
    "6. description MUST be a comprehensive 3-5 sentence overview. "
    "Return ONLY valid JSON array."
)
CRITIC_SYS = (
    "You are a harsh but fair peer reviewer at NeurIPS. Find fatal flaws in research ideas. "
    "Be specific — cite exact technical weaknesses, not vague concerns. "
    "For each idea, identify: the weakest assumption, the most likely failure mode, and whether the evaluation plan is sufficient. "
    "Return ONLY valid JSON array."
)
DEFEND_SYS = (
    "You are a senior researcher responding to peer review. Revise salvageable ideas to address critiques. "
    "When revising, strengthen the problem_statement and proposed_solution with additional technical detail. "
    "Maintain all JSON fields. Return ONLY valid JSON array."
)


async def run_idea_generation(gaps: List[Dict], papers: List[Dict], intent: Dict, llm: LLMClient) -> List[Dict]:
    try:
        return await _adversarial_generation(gaps, papers, intent, llm)
    except Exception as e:
        print(f"[Idea adversarial failed] {e} — fallback")
        return await _single_pass_ideas(gaps, papers, intent, llm)


async def _adversarial_generation(gaps: List[Dict], papers: List[Dict], intent: Dict, llm: LLMClient) -> List[Dict]:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    constraints = _format_constraints(intent.get("constraints", {}))
    gaps_summary = "\n".join(f"- {g.get('title','')}: {truncate_text(g.get('description',''), 150)}" for g in gaps[:6])
    papers_summary = "\n".join(f"- [{p.get('year','')}] {p.get('title','')}" for p in papers[:8])
    # Build exclusion list for "generate more ideas" scenario
    exclude_titles = intent.get("_exclude_titles", [])
    exclusion_hint = f"\nDo NOT repeat these already-generated ideas: {', '.join(exclude_titles[:8])}" if exclude_titles else ""

    # ── Round 1: Generate 6 raw ideas ────────────────────────────────────────
    gen_raw = await llm.complete(
        f"Domain: {domain}\nConstraints: {constraints}\n\nResearch Gaps:\n{gaps_summary}\n\nRelated Papers:\n{papers_summary}{exclusion_hint}\n\n"
        "Generate 6 specific, novel research ideas. Each idea must be a JSON object with: " + exclusion_hint + " "
        "title, description (Comprehensive 3-5 sentence overview), problem_statement (Detailed 1-2 paragraph definition of the issue and context), "
        "proposed_solution (In-depth 2-3 paragraph explanation of the technical approach, architecture, and methodology), why_it_addresses_gap (Detailed logical bridge between gap and solution), "
        "potential_challenges (realistic technical hurdles), "
        "addresses_gaps (list of gap titles), suggested_methods (list), suggested_datasets (list), "
        "complexity (Low|Medium|High), estimated_time (e.g., '3-6 months'), "
        "feasibility (high|medium|low), innovation_level (integer 1-10), expected_impact (high|medium|low), "
        "novelty_score (1-10), feasibility_score (1-10), difficulty (beginner|intermediate|advanced), "
        "assumptions (list of 3 key assumptions), failure_modes (list of 2 ways this could fail).",
        system=GEN_SYSTEM, json_mode=True
    )
    ideas = safe_parse_llm_json(gen_raw, default=[])
    if not isinstance(ideas, list) or not ideas:
        return _fallback_ideas(gaps, intent)
    ideas = ideas[:6]

    # ── Round 2: Critique each idea ──────────────────────────────────────────
    compact_ideas = "\n".join(
        f"Idea {i+1}: {idea.get('title','')}\n  Approach: {truncate_text(idea.get('approach',''), 150)}\n  Assumptions: {'; '.join(idea.get('assumptions', []))}"
        for i, idea in enumerate(ideas)
    )
    critique_raw = await llm.complete(
        f"Critique these research ideas:\n{compact_ideas}\n\n"
        "For each idea return a JSON object with: idea_title (copy exactly), fatal_flaw (1 sentence), "
        "weakness_score (1-10 where 10=very weak/unfixable), is_salvageable (true/false), suggested_fix (1 sentence).",
        system=CRITIC_SYS, json_mode=True
    )
    critiques = safe_parse_llm_json(critique_raw, default=[])
    if not isinstance(critiques, list):
        critiques = []
    critique_map = {c.get("idea_title", ""): c for c in critiques}

    # ── Round 3: Defend and refine survivors ─────────────────────────────────
    survivors = [
        idea for idea in ideas
        if critique_map.get(idea.get("title", ""), {}).get("weakness_score", 5) < 7
        and critique_map.get(idea.get("title", ""), {}).get("is_salvageable", True)
    ]
    # Enforce minimum 2 survivors
    if len(survivors) < 2:
        fallbacks = sorted(ideas, key=lambda x: critique_map.get(x.get("title",""), {}).get("weakness_score", 10))
        survivors = fallbacks[:2]
        for s in survivors:
            c = critique_map.get(s.get("title", ""), {})
            s["critique_summary"] = c.get("fatal_flaw", "Included despite weaknesses")
            s["survived_critique"] = False
    else:
        # Refine survivors
        survivors_text = json.dumps(survivors[:4], indent=2)
        critiques_text = json.dumps([critique_map.get(s.get("title",""), {}) for s in survivors[:4]], indent=2)
        defend_raw = await llm.complete(
            f"Original ideas:\n{survivors_text}\n\nCritiques:\n{critiques_text}\n\n"
            "Revise each idea to address the critique. Keep all original JSON fields. Update description, approach, and novelty to fix the identified flaw.",
            system=DEFEND_SYS, json_mode=True
        )
        refined = safe_parse_llm_json(defend_raw, default=[])
        if isinstance(refined, list) and refined:
            survivors = refined[:4]
        for s in survivors:
            c = critique_map.get(s.get("title", ""), {})
            s["critique_summary"] = c.get("fatal_flaw", "Passed peer review")
            s["survived_critique"] = True

    # Rank and return top 4
    ranked = _rank_ideas(survivors)[:4]
    return validate_ideas_batch(ranked)


async def _single_pass_ideas(gaps: List[Dict], papers: List[Dict], intent: Dict, llm: LLMClient) -> List[Dict]:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    gaps_text = "\n".join(f"- {g.get('title','')}" for g in gaps[:5])
    try:
        raw = await llm.complete(
            f"Generate 4 research ideas for domain: {domain}\nGaps:\n{gaps_text}\n\n"
            "Return JSON array with: title, description (Comprehensive 3-5 sentence overview), problem_statement (Detailed 1-2 paragraph definition of the issue and context), "
            "proposed_solution (In-depth 2-3 paragraph explanation of the technical approach, architecture, and methodology), why_it_addresses_gap (Detailed logical bridge between gap and solution), "
            "potential_challenges (realistic technical hurdles), addresses_gaps, suggested_methods, suggested_datasets, complexity, estimated_time, feasibility, innovation_level, novelty_score, feasibility_score, difficulty.",
            system=GEN_SYSTEM, json_mode=True
        )
        ideas = safe_parse_llm_json(raw, default=[])
        if isinstance(ideas, list) and ideas:
            for i in ideas:
                i.setdefault("survived_critique", False)
                i.setdefault("critique_summary", "Single-pass generation (no critique)")
            return _rank_ideas(ideas)[:4]
    except Exception:
        pass
    return _fallback_ideas(gaps, intent)


def _rank_ideas(ideas: List[Dict]) -> List[Dict]:
    def score(idea):
        n = float(idea.get("novelty_score", 5))
        f = float(idea.get("feasibility_score", 5))
        return n * 0.6 + f * 0.4
    return sorted(ideas, key=score, reverse=True)


def _format_constraints(c: Dict) -> str:
    parts = []
    if c.get("compute"): parts.append(f"Compute: {c['compute']}")
    if c.get("region"):  parts.append(f"Region: {c['region']}")
    if c.get("real_time"): parts.append("Real-time required")
    return ", ".join(parts) or "None specified"


def _fallback_ideas(gaps: List[Dict], intent: Dict) -> List[Dict]:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    return [
        {
            "title": f"Novel approach to: {g.get('title','research gap')[:50]}",
            "description": f"Address the gap: {truncate_text(g.get('description',''), 200)}",
            "problem_statement": "Addressing an identified gap in the literature.",
            "proposed_solution": "Literature-driven methodology with empirical validation.",
            "why_it_addresses_gap": "Directly tackles the mentioned limitations.",
            "potential_challenges": "Data availability and evaluation metrics.",
            "addresses_gaps": [g.get("title", "")], "suggested_methods": [],
            "suggested_datasets": [], "feasibility": "medium", "expected_impact": "medium",
            "complexity": "Medium", "estimated_time": "3-6 months", "innovation_level": 5,
            "novelty_score": 6.0, "feasibility_score": 5.0,
            "difficulty": "intermediate", "assumptions": [], "failure_modes": [],
            "survived_critique": False, "critique_summary": "Fallback idea",
        }
        for g in gaps[:3]
    ]
