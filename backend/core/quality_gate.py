"""Quality Gate — validates AI outputs to ensure depth and traceability."""

from typing import Dict, List, Tuple

VALID_GAP_TYPES = {
    "methodological", "dataset", "evaluation", "application",
    "theoretical", "limitation", "unexplored_assumption", "contradiction",
}

VALID_COMPLEXITY = {"Low", "Medium", "High", "low", "medium", "high"}
VALID_FEASIBILITY = {"high", "medium", "low", "High", "Medium", "Low"}


def validate_gap(gap: dict) -> Tuple[bool, List[str]]:
    """Returns (is_valid, list_of_issues). Gaps that fail are flagged but not discarded."""
    issues: List[str] = []
    desc = gap.get("description", "")
    expl = gap.get("explanation", "")
    refs = gap.get("direct_references", [])

    if len(desc) < 80:
        issues.append(f"Description too short ({len(desc)} chars, need 80+)")
    if len(expl) < 100:
        issues.append(f"Explanation too short ({len(expl)} chars, need 100+)")
    if not refs or len(refs) == 0:
        issues.append("Missing direct paper references")
    if gap.get("type") and gap["type"] not in VALID_GAP_TYPES:
        issues.append(f"Invalid gap type: {gap.get('type')}")
    if not gap.get("title"):
        issues.append("Missing title")

    return len(issues) == 0, issues


def validate_idea(idea: dict) -> Tuple[bool, List[str]]:
    """Returns (is_valid, list_of_issues). Ideas that fail are flagged but not discarded."""
    issues: List[str] = []
    ps = idea.get("problem_statement", "")
    sol = idea.get("proposed_solution", "")
    why = idea.get("why_it_addresses_gap", "")

    if len(ps) < 100:
        issues.append(f"Problem statement too shallow ({len(ps)} chars, need 100+)")
    if len(sol) < 150:
        issues.append(f"Proposed solution lacks depth ({len(sol)} chars, need 150+)")
    if len(why) < 50:
        issues.append(f"Gap connection too brief ({len(why)} chars, need 50+)")
    if not idea.get("title"):
        issues.append("Missing title")

    return len(issues) == 0, issues


def validate_gaps_batch(gaps: List[Dict]) -> List[Dict]:
    """Validate a batch of gaps. Adds '_quality_issues' field to each gap."""
    for gap in gaps:
        is_valid, issues = validate_gap(gap)
        gap["_quality_valid"] = is_valid
        gap["_quality_issues"] = issues
    return gaps


def validate_ideas_batch(ideas: List[Dict]) -> List[Dict]:
    """Validate a batch of ideas. Adds '_quality_issues' field to each idea."""
    for idea in ideas:
        is_valid, issues = validate_idea(idea)
        idea["_quality_valid"] = is_valid
        idea["_quality_issues"] = issues
    return ideas
