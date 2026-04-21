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
        return _fallback_report(idea, papers, gaps, intent)
    except Exception as e:
        print(f"Writer agent error: {e}")
        return _fallback_report(idea, papers, gaps, intent)


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


def _fallback_report(idea: Dict, papers: List[Dict], gaps: List[Dict], intent: Dict) -> Dict:
    """Comprehensive IEEE-format fallback report."""
    title = idea.get("title", "Novel Research Contribution")
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    approach = idea.get("approach", "a novel methodology")
    novelty = idea.get("novelty", "unexplored problem formulation")
    description = idea.get("description", "an identified research gap")

    # Build references from papers
    references = []
    for i, paper in enumerate(papers[:15], 1):
        references.append({
            "id": i,
            "authors": ", ".join(paper.get("authors", ["Unknown"])[:3]),
            "title": paper.get("title", ""),
            "venue": paper.get("source", ""),
            "year": paper.get("year", ""),
        })

    # Build related work section using actual paper titles
    related_work_paragraphs = []
    if papers:
        related_work_paragraphs.append(
            f"The field of {domain} has witnessed significant advancements in recent years. "
            f"Several notable contributions have shaped the current landscape of research in this area. "
            f"In this section, we provide a comprehensive review of the most relevant prior work."
        )
        for i, p in enumerate(papers[:4], 1):
            abstract_snippet = p.get("abstract", "")[:200]
            related_work_paragraphs.append(
                f"{p.get('title', 'Prior work')} [{i}] presented {abstract_snippet}..."
            )
        gap_names = "; ".join(g.get("title", "") for g in gaps[:2]) or "several open challenges"
        related_work_paragraphs.append(
            f"Despite these advances, {gap_names} remain unaddressed in the current literature. "
            f"Our work builds upon these foundations while addressing the identified limitations."
        )
    else:
        related_work_paragraphs.append(
            f"Prior work in {domain} has explored various approaches to related problems. "
            f"However, significant gaps remain that motivate the current research."
        )

    methods_list = ", ".join(idea.get("suggested_methods", ["deep learning", "transformer models"]))
    datasets_list = ", ".join(idea.get("suggested_datasets", ["standard benchmarks"]))

    return {
        "title": title,
        "authors": ["ResearchIDE Author"],
        "abstract": (
            f"Recent advances in {domain} have demonstrated remarkable progress, yet significant "
            f"challenges persist in addressing {description}. This paper presents a novel approach "
            f"that leverages {approach} to tackle these challenges. Our method addresses the gap of "
            f"{novelty} through a systematic methodology that combines established techniques with "
            f"innovative modifications. Preliminary analysis and theoretical foundations suggest "
            f"significant potential for improvement over existing state-of-the-art baselines, "
            f"opening new directions for future research in {domain}."
        ),
        "keywords": intent.get("keywords", ["machine learning", "deep learning", "research"])[:5],
        "sections": [
            {
                "id": "introduction",
                "heading": "I. INTRODUCTION",
                "content": (
                    f"The field of {domain} has seen rapid progress in recent years, driven by advances "
                    f"in computational methods and the availability of large-scale datasets. Despite this "
                    f"progress, significant challenges remain that limit the practical applicability of "
                    f"current approaches. This work is motivated by {novelty}.\n\n"
                    f"Specifically, we address the following research question: {description}. "
                    f"Existing approaches have made notable contributions but fall short in several "
                    f"critical aspects that our work aims to resolve.\n\n"
                    f"Our main contributions are: (1) A novel approach to {title} that addresses "
                    f"identified gaps in the literature, (2) A comprehensive experimental framework "
                    f"for evaluating the proposed method against state-of-the-art baselines, and "
                    f"(3) Detailed analysis of the method's strengths, limitations, and potential "
                    f"for future extensions."
                ),
            },
            {
                "id": "related_work",
                "heading": "II. RELATED WORK",
                "content": "\n\n".join(related_work_paragraphs),
            },
            {
                "id": "methodology",
                "heading": "III. METHODOLOGY",
                "content": (
                    f"We propose {title} to address the identified gaps in the current literature. "
                    f"Our approach builds upon established foundations while introducing key innovations "
                    f"that differentiate it from prior work.\n\n"
                    f"Technical Approach: {approach}. The methodology is designed to be modular and "
                    f"extensible, allowing researchers to adapt individual components to their specific "
                    f"requirements and constraints.\n\n"
                    f"The core methods employed include: {methods_list}. Each component is carefully "
                    f"designed to address specific aspects of the research problem while maintaining "
                    f"computational efficiency and reproducibility."
                ),
            },
            {
                "id": "experimental_setup",
                "heading": "IV. EXPERIMENTAL SETUP",
                "content": (
                    f"Datasets: We evaluate our approach on {datasets_list}. These datasets are "
                    f"selected to provide comprehensive coverage of the problem space and enable "
                    f"direct comparison with prior work.\n\n"
                    f"Evaluation Metrics: We report accuracy, F1-score, precision, recall, and "
                    f"domain-specific metrics as appropriate. Statistical significance is assessed "
                    f"using paired t-tests with p < 0.05.\n\n"
                    f"Baseline Comparisons: We compare against state-of-the-art methods reported "
                    f"in the recent literature. All experiments are conducted with fixed random seeds "
                    f"to ensure reproducibility."
                ),
            },
            {
                "id": "results",
                "heading": "V. RESULTS AND DISCUSSION",
                "content": (
                    "We anticipate that the proposed approach will demonstrate competitive or superior "
                    "performance compared to existing baselines on the primary evaluation metrics. "
                    "The experimental framework is designed to provide rigorous empirical evidence.\n\n"
                    "Ablation studies will validate the contribution of each component of the proposed "
                    "method. By systematically removing or modifying individual components, we can "
                    "quantify their impact on overall performance.\n\n"
                    "Error analysis will reveal failure modes and guide future improvements. "
                    "Understanding when and why the method fails is critical for identifying "
                    "opportunities for further research and development."
                ),
            },
            {
                "id": "conclusion",
                "heading": "VI. CONCLUSION",
                "content": (
                    f"This paper presented {title}, a novel contribution to the field of {domain}. "
                    f"The proposed approach addresses identified gaps in the literature through "
                    f"{approach}.\n\n"
                    f"The key findings of this work demonstrate the potential of the proposed method "
                    f"to advance the state of the art. The modular design of our approach facilitates "
                    f"adaptation and extension by future researchers.\n\n"
                    f"Future work includes scaling to larger datasets, cross-domain evaluation, "
                    f"real-world deployment studies, and integration with complementary techniques "
                    f"to further enhance performance and applicability."
                ),
            },
        ],
        "acknowledgements": "The authors would like to thank the research community for their valuable contributions and the developers of the open-source tools used in this work.",
        "references": references,
        "_fallback": True,
    }


def _parse_json(raw: str) -> Dict:
    """Parse JSON from LLM response."""
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
