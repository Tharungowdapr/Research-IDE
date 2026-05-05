"""Writer Agent v2 — IEEE-format research paper generation"""

import json, re
from typing import Dict, List, Any
from core.llm_client import LLMClient
from core.utils import safe_parse_llm_json, truncate_text

WRITER_SYSTEM = (
    "You are an expert academic writer. Generate a complete IEEE-format research paper. "
    "Use formal academic English. Every section must be substantive (minimum 3 paragraphs). "
    "Cite papers using [N] notation matching the references array id fields. "
    "In related_work cite at least 3 references. In methodology cite at least 2. "
    "Return ONLY valid JSON."
)


async def run_report_generation(idea: Dict, papers: List[Dict], gaps: List[Dict], plan: Dict, intent: Dict, llm: LLMClient) -> Dict:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    refs = _build_references(papers[:15])
    refs_text = "\n".join(f"[{r['id']}] {r['authors']} ({r['year']}). {r['title']}." for r in refs[:12])
    gaps_text = "; ".join(g.get("title","") for g in gaps[:3])
    datasets_text = ", ".join(d.get("name","") for d in plan.get("datasets",[])[:3]) or "standard benchmarks"
    metrics_text = ", ".join(plan.get("evaluation_metrics",[])[:4]) or "accuracy, F1"
    github_refs = [p.get("github_url","") for p in papers if p.get("github_url")][:2]

    prompt = f"""Write a complete IEEE-format research paper for this study.

Title: {idea.get('title','')}
Domain: {domain}
Description: {idea.get('description','')}
Approach: {idea.get('approach','')}
Novelty: {idea.get('novelty','')}
Gaps Addressed: {gaps_text}
Datasets: {datasets_text}
Evaluation Metrics: {metrics_text}
{'GitHub references: ' + ', '.join(github_refs) if github_refs else ''}

Available References (use [N] citations in text):
{refs_text}

Return this exact JSON structure:
{{
  "title": "Full IEEE-style paper title",
  "authors": ["Author Name"],
  "abstract": "150-200 words: motivation sentence, problem sentence, approach sentence, key result sentence, significance sentence",
  "keywords": ["keyword1","keyword2","keyword3","keyword4","keyword5"],
  "sections": [
    {{"id":"introduction","heading":"I. INTRODUCTION","content":"3+ paragraphs with [N] citations..."}},
    {{"id":"related_work","heading":"II. RELATED WORK","content":"3+ paragraphs discussing related work with [N] citations..."}},
    {{"id":"methodology","heading":"III. METHODOLOGY","content":"3+ paragraphs with technical detail and [N] citations..."}},
    {{"id":"experimental_setup","heading":"IV. EXPERIMENTAL SETUP","content":"datasets, metrics, baselines..."}},
    {{"id":"results","heading":"V. RESULTS AND DISCUSSION","content":"expected results analysis..."}},
    {{"id":"conclusion","heading":"VI. CONCLUSION","content":"summary and future work..."}}
  ],
  "acknowledgements": "This work was conducted as part of an AI-assisted research pipeline.",
  "references": {json.dumps(refs[:12])}
}}"""

    try:
        raw = await llm.complete(prompt, system=WRITER_SYSTEM, json_mode=True)
        result = safe_parse_llm_json(raw, default={})
        if isinstance(result, dict) and "sections" in result:
            result = _validate_citations(result)
            return result
    except Exception as e:
        print(f"[Writer] LLM failed: {e}")

    return _fallback_report(idea, papers, gaps, plan, intent)


def _build_references(papers: List[Dict]) -> List[Dict]:
    refs = []
    for i, p in enumerate(papers, 1):
        authors_list = p.get("authors", [])
        if isinstance(authors_list, list) and authors_list:
            authors_str = authors_list[0] + (" et al." if len(authors_list) > 1 else "")
        else:
            authors_str = "Unknown Authors"
        refs.append({
            "id": i,
            "authors": authors_str,
            "title": p.get("title", "Unknown Title"),
            "venue": p.get("source", "").replace("_", " ").title(),
            "year": p.get("year", "n.d."),
            "url": p.get("url", ""),
        })
    return refs


def _validate_citations(report: Dict) -> Dict:
    """Remove [N] citations that have no matching reference."""
    valid_ids = {str(r["id"]) for r in report.get("references", [])}
    for section in report.get("sections", []):
        content = section.get("content", "")
        # Remove invalid citations
        def replace_cite(m):
            n = m.group(1)
            return m.group(0) if n in valid_ids else ""
        section["content"] = re.sub(r"\[(\d+)\]", replace_cite, content)
    return report


def _fallback_report(idea: Dict, papers: List[Dict], gaps: List[Dict], plan: Dict, intent: Dict) -> Dict:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    refs = _build_references(papers[:10])
    title = idea.get("title", "Novel Research Contribution")
    approach = idea.get("approach", "the proposed methodology")
    novelty = idea.get("novelty", "an unexplored problem formulation")
    gap_titles = "; ".join(g.get("title","") for g in gaps[:2])
    datasets = ", ".join(d.get("name","") for d in plan.get("datasets",[])[:2]) or "standard benchmarks"
    metrics = ", ".join(plan.get("evaluation_metrics",[])[:3]) or "accuracy, F1-score, AUC"
    ref_text = lambda i: f"[{i}]" if i <= len(refs) else ""

    return {
        "title": title,
        "authors": ["ResearchIDE User"],
        "abstract": (
            f"Recent advances in {domain} have highlighted significant limitations in existing approaches. "
            f"In particular, {gap_titles or 'identified gaps in the literature'} remain inadequately addressed. "
            f"This paper proposes {approach} as a novel solution to these challenges. "
            f"The proposed method is evaluated on {datasets} using {metrics}. "
            f"Our approach demonstrates the potential to advance the state-of-the-art in {domain}, "
            f"with implications for both research and practical deployment."
        ),
        "keywords": intent.get("keywords", ["machine learning","deep learning","research"])[:5],
        "sections": [
            {
                "id": "introduction",
                "heading": "I. INTRODUCTION",
                "content": (
                    f"The field of {domain} has witnessed remarkable progress in recent years, driven by advances in computational resources and large-scale datasets {ref_text(1)}. "
                    f"Despite these advances, critical challenges persist that limit the practical applicability of existing methods {ref_text(2)}.\n\n"
                    f"This work is motivated by the observation that {novelty}. "
                    f"Specifically, we identify the following gaps in the existing literature: {gap_titles or 'methodological and dataset limitations'} {ref_text(3)}.\n\n"
                    f"To address these limitations, we propose {approach}. "
                    f"Our main contributions are: (1) a novel approach to {title}, "
                    f"(2) empirical evaluation on {datasets}, and "
                    f"(3) analysis of strengths, limitations, and future directions."
                ),
            },
            {
                "id": "related_work",
                "heading": "II. RELATED WORK",
                "content": (
                    f"Prior work in {domain} has explored a variety of approaches. "
                    + " ".join(
                        f"{ref_text(i+1)} {truncate_text(p.get('abstract',''), 150)}"
                        for i, p in enumerate(papers[:4])
                    )
                    + f"\n\nDespite these contributions, {gap_titles or 'key gaps'} remain unresolved, motivating the present work.\n\n"
                    f"Our approach builds upon and extends these prior works by addressing the identified limitations through {approach}."
                ),
            },
            {
                "id": "methodology",
                "heading": "III. METHODOLOGY",
                "content": (
                    f"We propose {title} to address the identified research gaps. "
                    f"The methodology consists of the following key components.\n\n"
                    f"Technical Approach: {approach} {ref_text(1)}. "
                    f"The design choices are motivated by the need to overcome {gap_titles or 'existing limitations'}.\n\n"
                    f"Implementation Details: The system is implemented using the tech stack described in the experimental setup. "
                    f"All hyperparameters are tuned via grid search on the validation set."
                ),
            },
            {
                "id": "experimental_setup",
                "heading": "IV. EXPERIMENTAL SETUP",
                "content": (
                    f"Datasets: We evaluate our approach on {datasets}. "
                    f"These datasets were chosen for their relevance to {domain} and their widespread use as benchmarks {ref_text(2)}.\n\n"
                    f"Evaluation Metrics: We report {metrics}. "
                    f"These metrics capture both the accuracy and robustness of the proposed approach.\n\n"
                    f"Baselines: We compare against {plan.get('baseline_comparison', 'state-of-the-art methods in the literature')}. "
                    f"All baselines are evaluated under identical experimental conditions to ensure fair comparison."
                ),
            },
            {
                "id": "results",
                "heading": "V. RESULTS AND DISCUSSION",
                "content": (
                    f"We anticipate that the proposed approach will demonstrate competitive or superior performance compared to existing baselines on the evaluation metrics ({metrics}).\n\n"
                    f"Ablation studies will validate the contribution of each component of our proposed system. "
                    f"Specifically, we will analyze the impact of the key design decisions described in Section III.\n\n"
                    f"Error analysis will reveal failure modes and provide insights for future improvements. "
                    f"We expect our approach to be particularly effective in scenarios characterized by {domain} constraints."
                ),
            },
            {
                "id": "conclusion",
                "heading": "VI. CONCLUSION",
                "content": (
                    f"This paper presented {title}, a novel approach to addressing identified gaps in {domain}. "
                    f"The proposed methodology targets {gap_titles or 'key research gaps'} and offers a principled solution grounded in {approach}.\n\n"
                    f"The empirical evaluation on {datasets} is expected to demonstrate the effectiveness of our approach. "
                    f"The results will contribute to the advancement of {domain} and provide practical guidance for practitioners.\n\n"
                    f"Future work includes scaling to larger datasets, cross-domain transfer evaluation, "
                    f"and integration with downstream applications. "
                    f"We release our code and models to facilitate reproducibility and further research."
                ),
            },
        ],
        "acknowledgements": "This research was conducted using AI-assisted tools for literature analysis and paper drafting.",
        "references": refs,
        "_fallback": True,
    }
