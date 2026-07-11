"""
Writer Agent — IEEE-format Research Paper Generation
Generates a complete IEEE-format research paper with proper citations.
"""

import json
import re
from typing import Dict, List, Any
from core.llm_client import LLMClient


WRITER_SYSTEM = """You are an expert IEEE academic writer producing a full-length conference paper (5-6 pages, two-column format). \
Use formal academic English throughout. Every section MUST be detailed and substantive with DEPTH. \
Each section must contain at least 4-5 substantial paragraphs (200-300 words each minimum). \
Cite papers using [N] notation where N matches the id field in the references array. \
The references array must be numbered starting from 1 with at least 15-20 references. \
Every paper mentioned in any section must appear in the references array. \
Section content must mention at least 3-4 different [N] citations in related_work, \
at least 3 in methodology, and at least 2 in results/discussion. \
Write with technical depth: include formulas described in text, algorithm descriptions, \
specific metrics, comparison tables described in prose, ablation study details, \
hyperparameter choices with justification, computational cost analysis, \
error analysis, and statistical significance discussion. \
Return ONLY valid JSON."""

WRITER_PROMPT = """Write a COMPLETE, DETAILED IEEE-format research paper (targeting 5-6 pages in two-column format) for this project.

Title: {title}
Domain: {domain}
Idea: {description}
Approach: {approach}
Novelty: {novelty}
Related Papers (use these as references with [N] citations):
{related_papers}
Gaps Addressed: {gaps}
Plan Overview: {overview}

CRITICAL REQUIREMENTS FOR LENGTH AND DETAIL:
- Introduction: 4-5 paragraphs. Include: broad motivation, specific problem statement, limitations of existing work with specific examples, your approach overview with key contributions listed, paper organization paragraph.
- Related Work: 4-5 paragraphs. Group related work into 3-4 sub-themes. Compare and contrast approaches within each group. Discuss strengths and weaknesses of each. End with how your work differs.
- Research Gap: 3-4 paragraphs. Provide detailed analysis of identified gaps. Quantify where possible. Discuss implications of each gap. Explain how your work addresses each gap.
- Methodology: 5-6 paragraphs. Include: problem formulation, architecture overview, detailed component descriptions, training procedure, loss functions, optimization details, complexity analysis.
- Experimental Setup: 4-5 paragraphs. Include: dataset descriptions with statistics, preprocessing steps, baseline methods with brief descriptions, evaluation metrics with definitions, implementation details, hyperparameters, hardware specifications.
- Results and Analysis: 5-6 paragraphs. Include: main results comparison with baselines, detailed per-metric analysis, ablation study results, statistical significance tests, computational efficiency comparison, visual/qualitative analysis discussion.
- Discussion: 4-5 paragraphs. Include: interpretation of key findings, comparison with state-of-the-art, limitations with specific examples, potential failure modes, broader impact considerations.
- Conclusion: 3-4 paragraphs. Include: summary of contributions, key findings, practical implications.
- Future Work: 2-3 paragraphs. Specific directions with justification.

Return this EXACT JSON structure:
{{
  "title": "Full Paper Title -- Descriptive and Specific",
  "authors": ["Author 1", "Author 2"],
  "affiliations": ["Department, University Name, City, Country"],
  "emails": ["author@university.edu"],
  "abstract": "200-250 words structured as: motivation sentence, problem sentence, approach sentence, key result sentences with specific numbers, significance sentence",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5", "keyword6", "keyword7"],
  "sections": [
    {{"id": "introduction", "heading": "I. INTRODUCTION", "content": "4-5 detailed paragraphs with [N] citations, specific numbers, and technical depth..."}},
    {{"id": "related_work", "heading": "II. RELATED WORK", "content": "4-5 paragraphs grouping related approaches into sub-themes with detailed comparison and [N] citations..."}},
    {{"id": "research_gap", "heading": "III. RESEARCH GAP ANALYSIS", "content": "3-4 paragraphs with detailed gap analysis, quantified limitations, and [N] citations..."}},
    {{"id": "methodology", "heading": "IV. PROPOSED METHODOLOGY", "content": "5-6 paragraphs with architecture, formulation, algorithms, training procedure, and [N] citations..."}},
    {{"id": "experimental_setup", "heading": "V. EXPERIMENTAL SETUP", "content": "4-5 paragraphs on datasets, metrics, baselines, implementation, hyperparameters..."}},
    {{"id": "results", "heading": "VI. RESULTS AND ANALYSIS", "content": "5-6 paragraphs with main results, ablation studies, efficiency analysis, statistical tests..."}},
    {{"id": "discussion", "heading": "VII. DISCUSSION", "content": "4-5 paragraphs on implications, limitations, comparison with SOTA, failure modes..."}},
    {{"id": "conclusion", "heading": "VIII. CONCLUSION", "content": "3-4 paragraphs summarizing contributions and findings..."}},
    {{"id": "future_work", "heading": "IX. FUTURE WORK", "content": "2-3 paragraphs with specific future research directions..."}}
  ],
  "acknowledgements": "This work was supported by...",
  "conflicts_of_interest": "The authors declare no conflicts of interest.",
  "references": [
    {{"id": 1, "authors": "Author1, Author2", "title": "Paper Title", "venue": "Conference/Journal", "year": "2024"}}
  ]
}}

REMEMBER: Each paragraph MUST be 150-300 words. The total paper should be 5-6 pages. \
Every [N] citation in section content MUST have a matching reference with that id number. \
Aim for at least 15 references total. Write with technical precision and academic rigor."""


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
    section_ids = ["introduction", "related_work", "research_gap", "methodology",
                   "experimental_setup", "results", "discussion", "conclusion", "future_work"]
    for i, section in enumerate(report.get("sections", [])):
        if "id" not in section and i < len(section_ids):
            section["id"] = section_ids[i]

    # Ensure acknowledgements exists
    if "acknowledgements" not in report:
        report["acknowledgements"] = "The authors would like to thank the research community for their valuable contributions."

    # Ensure affiliations and emails exist
    authors = report.get("authors", ["Author"])
    if "affiliations" not in report or not report["affiliations"]:
        report["affiliations"] = ["Department of Computer Science, University, City, Country"]
    if "emails" not in report or not report["emails"]:
        report["emails"] = ["author@university.edu"]

    return report



def _parse_json(raw: str) -> Dict:
    """Parse JSON from LLM response."""
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
