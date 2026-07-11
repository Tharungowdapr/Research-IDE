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
    title = idea.get("title", "")
    desc = idea.get("description", "")
    novelty = idea.get("novelty", "")
    approach = idea.get("approach", "")
    novelty_score = idea.get("novelty_score")
    feasibility_score = idea.get("feasibility_score")

    if not title:
        issues.append("Missing title")
    if len(desc) < 80:
        issues.append(f"Description too short ({len(desc)} chars, need 80+)")
    if len(novelty) < 50:
        issues.append(f"Novelty explanation too short ({len(novelty)} chars, need 50+)")
    if len(approach) < 50:
        issues.append(f"Approach too short ({len(approach)} chars, need 50+)")
    if novelty_score is not None and not (1 <= float(novelty_score) <= 10):
        issues.append(f"Novelty score out of range: {novelty_score}")
    if feasibility_score is not None and not (1 <= float(feasibility_score) <= 10):
        issues.append(f"Feasibility score out of range: {feasibility_score}")

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
