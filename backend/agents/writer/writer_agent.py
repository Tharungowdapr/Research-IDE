"""
Writer Agent — IEEE-format Research Paper Generation
Generates a complete IEEE-format research paper with proper citations.
"""

import json
import re
from typing import Dict, List, Any
from core.llm_client import LLMClient


WRITER_SYSTEM = """You are an expert academic writer. Generate a complete IEEE-format research paper. \
Use formal academic English. Every section must be substantive (minimum 3 paragraphs). \
Cite papers using [N] notation where N matches the id field in the references array. \
The references array must be numbered starting from 1. Every paper mentioned in any section \
must appear in the references array. Section content must mention at least 3 different [N] \
citations in related_work and at least 2 in methodology. Return ONLY valid JSON."""

WRITER_PROMPT = """Write a complete IEEE-format research paper for this project.

Title: {title}
Domain: {domain}
Idea: {description}
Approach: {approach}
Novelty: {novelty}
Related Papers (use these as references with [N] citations):
{related_papers}
Gaps Addressed: {gaps}
Plan Overview: {overview}

Return this EXACT JSON structure:
{{
  "title": "Full Paper Title — Descriptive and Specific",
  "authors": ["Author Name"],
  "abstract": "150-200 words structured as: motivation sentence, problem sentence, approach sentence, key result sentence, significance sentence",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "sections": [
    {{"id": "introduction", "heading": "I. INTRODUCTION", "content": "3+ paragraphs with [N] citations..."}},
    {{"id": "related_work", "heading": "II. RELATED WORK", "content": "3+ paragraphs discussing related approaches with [1], [2], [3] citations..."}},
    {{"id": "methodology", "heading": "III. METHODOLOGY", "content": "3+ paragraphs detailing the proposed method with [N] citations..."}},
    {{"id": "experimental_setup", "heading": "IV. EXPERIMENTAL SETUP", "content": "3+ paragraphs on datasets, metrics, baselines..."}},
    {{"id": "results", "heading": "V. RESULTS AND DISCUSSION", "content": "3+ paragraphs on expected/anticipated results and analysis..."}},
    {{"id": "conclusion", "heading": "VI. CONCLUSION", "content": "3+ paragraphs summarizing contributions and future work..."}}
  ],
  "acknowledgements": "This work was supported by...",
  "references": [
    {{"id": 1, "authors": "Author1, Author2", "title": "Paper Title", "venue": "Conference/Journal", "year": "2024"}}
  ]
}}

IMPORTANT: Every [N] citation in section content MUST have a matching reference with that id number."""


async def run_report_generation(
    idea: Dict,
    papers: List[Dict],
    gaps: List[Dict],
    plan: Dict,
    intent: Dict,
    llm: LLMClient,
) -> Dict:
    """Generate an IEEE-format research paper."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    related = _format_papers_for_prompt(papers[:15])
    gap_titles = [g.get("title", "") for g in gaps[:3]]

    prompt = WRITER_PROMPT.format(
        title=idea.get("title", "Research Project"),
        domain=domain,
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        novelty=idea.get("novelty", ""),
        related_papers=related,
        gaps=", ".join(gap_titles) or "identified gaps",
        overview=plan.get("overview", ""),
    )

    try:
        raw = await llm.complete(prompt, system=WRITER_SYSTEM, json_mode=True)
        result = _parse_json(raw)
        if "sections" in result:
            result = _postprocess_citations(result, papers)
            return result
        raise ValueError("Report generation failed: LLM response missing required sections")
    except Exception as e:
        raise ValueError(f"Report generation failed: {e}") from e


def _format_papers_for_prompt(papers: List[Dict]) -> str:
    """Format papers for the LLM prompt with reference numbers."""
    lines = []
    for i, p in enumerate(papers, 1):
        authors = ", ".join(p.get("authors", ["Unknown"])[:3])
        title = p.get("title", "Untitled")
        year = p.get("year", "N/A")
        venue = p.get("source", "")
        lines.append(f"[{i}] {authors} ({year}). \"{title}\". {venue}.")
    return "\n".join(lines)


def _postprocess_citations(report: Dict, papers: List[Dict]) -> Dict:
    """Validate and fix citations in the report."""
    refs = report.get("references", [])

    # Build set of valid reference ids
    valid_ids = {r.get("id") for r in refs if isinstance(r, dict) and "id" in r}

    # If references array is empty, auto-build from papers
    if not refs:
        refs = []
        for i, paper in enumerate(papers[:15], 1):
            refs.append({
                "id": i,
                "authors": ", ".join(paper.get("authors", ["Unknown"])[:3]),
                "title": paper.get("title", ""),
                "venue": paper.get("source", ""),
                "year": paper.get("year", ""),
            })
        report["references"] = refs
        valid_ids = {r["id"] for r in refs}

    # Scan all section content and validate [N] references
    for section in report.get("sections", []):
        content = section.get("content", "")
        # Find all [N] patterns
        citation_pattern = re.compile(r'\[(\d+)\]')
        matches = citation_pattern.findall(content)
        for match in matches:
            ref_id = int(match)
            if ref_id not in valid_ids:
                # Remove invalid citation
                content = content.replace(f"[{match}]", "")
        section["content"] = content

    # Ensure sections have proper id fields
    section_ids = ["introduction", "related_work", "methodology",
                   "experimental_setup", "results", "conclusion"]
    for i, section in enumerate(report.get("sections", [])):
        if "id" not in section and i < len(section_ids):
            section["id"] = section_ids[i]

    # Ensure acknowledgements exists
    if "acknowledgements" not in report:
        report["acknowledgements"] = "The authors would like to thank the research community for their valuable contributions."

    return report



def _parse_json(raw: str) -> Dict:
    """Parse JSON from LLM response."""
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
