"""Writer Agent - generates a structured research paper/report."""

import json, re
from typing import Dict, List, Any
from core.llm_client import LLMClient

WRITER_SYSTEM = "You are an expert academic writer. Generate well-structured research paper content. Return ONLY valid JSON."

WRITER_PROMPT = """Write a structured research paper for this project.

Title: {title}
Domain: {domain}
Idea: {description}
Approach: {approach}
Novelty: {novelty}
Related Papers: {related_papers}
Gaps Addressed: {gaps}
Plan Overview: {overview}

Return JSON:
{{
  "title": "Full paper title",
  "abstract": "150-200 word abstract summarizing problem, method, and expected contributions",
  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "sections": [
    {{
      "heading": "1. Introduction",
      "content": "Full section content (3-4 paragraphs)..."
    }},
    {{
      "heading": "2. Related Work",
      "content": "Full section content discussing related approaches..."
    }},
    {{
      "heading": "3. Methodology",
      "content": "Detailed method description..."
    }},
    {{
      "heading": "4. Experimental Setup",
      "content": "Datasets, metrics, baselines..."
    }},
    {{
      "heading": "5. Expected Results",
      "content": "Anticipated outcomes and analysis..."
    }},
    {{
      "heading": "6. Conclusion",
      "content": "Summary and future work..."
    }}
  ],
  "references": [
    "Author et al. (Year). Title. Venue.",
    "..."
  ]
}}"""


async def run_report_generation(
    idea: Dict,
    papers: List[Dict],
    gaps: List[Dict],
    plan: Dict,
    intent: Dict,
    llm: LLMClient,
) -> Dict:
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    related = [p.get("title", "") for p in papers[:5]]
    gap_titles = [g.get("title", "") for g in gaps[:3]]

    prompt = WRITER_PROMPT.format(
        title=idea.get("title", "Research Project"),
        domain=domain,
        description=idea.get("description", ""),
        approach=idea.get("approach", ""),
        novelty=idea.get("novelty", ""),
        related_papers=", ".join(related) or "various recent works",
        gaps=", ".join(gap_titles) or "identified gaps",
        overview=plan.get("overview", ""),
    )

    try:
        raw = await llm.complete(prompt, system=WRITER_SYSTEM, json_mode=True)
        result = _parse_json(raw)
        if "sections" in result:
            return result
        return _fallback_report(idea, papers, gaps, intent)
    except Exception as e:
        return _fallback_report(idea, papers, gaps, intent)


def _fallback_report(idea: Dict, papers: List[Dict], gaps: List[Dict], intent: Dict) -> Dict:
    title = idea.get("title", "Novel Research Contribution")
    domain = ", ".join(intent.get("domain", ["AI/ML"]))

    return {
        "title": title,
        "abstract": (
            f"This paper presents a novel approach to address {idea.get('description', 'an identified research gap')} "
            f"in the domain of {domain}. Motivated by limitations in existing literature, we propose "
            f"{idea.get('approach', 'a new methodology')}. The proposed approach addresses the gap of "
            f"{idea.get('novelty', 'unexplored problem formulation')}. Preliminary analysis suggests "
            f"significant potential for improvement over existing baselines."
        ),
        "keywords": intent.get("keywords", ["machine learning", "deep learning", "research"]),
        "sections": [
            {
                "heading": "1. Introduction",
                "content": (
                    f"The field of {domain} has seen rapid progress in recent years, yet significant "
                    f"challenges remain. This work is motivated by {idea.get('novelty', 'identified gaps in the literature')}.\n\n"
                    f"Specifically, we address: {idea.get('description', 'the research problem')}.\n\n"
                    f"Our main contributions are: (1) A novel approach to {idea.get('title', 'the problem')}, "
                    f"(2) Empirical evaluation on standard benchmarks, (3) Analysis of the proposed method's strengths and limitations."
                ),
            },
            {
                "heading": "2. Related Work",
                "content": (
                    f"Prior work in {domain} has explored various approaches. "
                    + "\n\n".join(
                        f"[{p.get('year','')}] {p.get('title','')}: {p.get('abstract','')[:200]}..."
                        for p in papers[:4]
                    )
                    + "\n\nDespite these advances, " + "; ".join(g.get("title","") for g in gaps[:2]) + " remain unaddressed."
                ),
            },
            {
                "heading": "3. Methodology",
                "content": (
                    f"We propose {idea.get('title', 'our method')} to address the identified gaps.\n\n"
                    f"Technical Approach: {idea.get('approach', 'The proposed methodology consists of several key components.')}\n\n"
                    f"Methods Used: {', '.join(idea.get('suggested_methods', ['deep learning', 'transformer models']))}."
                ),
            },
            {
                "heading": "4. Experimental Setup",
                "content": (
                    f"Datasets: {', '.join(idea.get('suggested_datasets', ['standard benchmarks']))}.\n\n"
                    "Evaluation Metrics: We report accuracy, F1-score, and domain-specific metrics.\n\n"
                    "Baseline Comparisons: We compare against state-of-the-art methods in the literature."
                ),
            },
            {
                "heading": "5. Expected Results",
                "content": (
                    "We anticipate that the proposed approach will outperform existing baselines on the primary evaluation metrics. "
                    "Ablation studies will validate the contribution of each component. "
                    "Error analysis will reveal failure modes and guide future improvements."
                ),
            },
            {
                "heading": "6. Conclusion",
                "content": (
                    f"This paper presented {idea.get('title', 'a novel research contribution')} for {domain}. "
                    "The proposed approach addresses identified gaps in the literature and demonstrates promising potential. "
                    "Future work includes scaling to larger datasets, cross-domain evaluation, and real-world deployment studies."
                ),
            },
        ],
        "references": [
            f"{', '.join(p.get('authors', ['et al.'])[:2])} ({p.get('year', 'N/A')}). {p.get('title', '')}."
            for p in papers[:10]
        ],
        "_fallback": True,
    }


def _parse_json(raw: str) -> Dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    s, e = clean.find("{"), clean.rfind("}") + 1
    return json.loads(clean[s:e]) if s != -1 and e > s else {}
