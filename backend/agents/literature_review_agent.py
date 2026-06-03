"""
Literature Review Agent - Automated literature review generation
"""

import json
from typing import List, Dict, Any
from core.llm_client import LLMClient


LITERATURE_REVIEW_SYSTEM = """You are an expert academic writer specializing in literature reviews.
Return ONLY valid JSON in the specified format."""

LITERATURE_REVIEW_PROMPT = """Generate a structured literature review based on these papers:

Papers:
{papers_summary}

Focus on:
1. Identifying key themes and trends
2. Comparing methodologies across papers
3. Highlighting conflicting findings
4. Identifying research evolution over time
5. Summarizing key contributions

Return a JSON object:
{
  "title": "Literature Review: [Domain]",
  "introduction": "Brief overview of the field",
  "themes": [
    {
      "name": "Theme name",
      "description": "Theme description",
      "papers": ["paper title 1", "paper title 2"],
      "key_findings": "Summary of findings"
    }
  ],
  "methodology_comparison": "Comparison of methods used",
  "gaps_identified": ["gap 1", "gap 2"],
  "future_directions": ["direction 1", "direction 2"],
  "conclusion": "Summary of the literature review"
}
"""

async def generate_literature_review(
    papers: List[Dict[str, Any]],
    intent: Dict,
    llm: LLMClient,
) -> Dict:
    """Generate automated literature review from papers."""
    if not papers:
        return {"error": "No papers provided"}
    
    # Summarize top 20 papers
    papers_summary = _summarize_papers(papers[:20])
    
    try:
        prompt = LITERATURE_REVIEW_PROMPT.format(
            papers_summary=papers_summary
        )
        
        raw = await llm.complete(
            prompt,
            system=LITERATURE_REVIEW_SYSTEM,
            json_mode=True
        )
        
        # Parse JSON response
        import re
        clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(clean[start:end])
        
        return json.loads(clean)
        
    except Exception as e:
        print(f"Literature review generation error: {e}")
        return {
            "error": str(e),
            "title": "Literature Review (Error)",
            "introduction": f"Failed to generate review: {str(e)}"
        }


def _summarize_papers(papers: List[Dict]) -> str:
    """Create a summary of papers for the LLM."""
    lines = []
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Unknown")
        year = p.get("year", "")
        abstract = p.get("abstract", "")[:300]
        lines.append(f"{i}. [{year}] {title}\n   {abstract}...")
    return "\n\n".join(lines)


async def generate_annotated_bibliography(
    papers: List[Dict[str, Any]],
    llm: LLMClient,
) -> List[Dict]:
    """Generate annotated bibliography entries."""
    if not papers:
        return []
    
    annotations = []
    for paper in papers[:15]:  # Limit to 15 papers
        try:
            annotation = await _generate_annotation(paper, llm)
            annotations.append(annotation)
        except Exception as e:
            print(f"Annotation error for {paper.get('title')}: {e}")
    
    return annotations


async def _generate_annotation(paper: Dict, llm: LLMClient) -> Dict:
    """Generate annotation for a single paper."""
    prompt = f"""Generate a concise annotation for this paper:

Title: {paper.get('title', '')}
Year: {paper.get('year', '')}
Abstract: {paper.get('abstract', '')[:500]}

Return JSON:
{{
  "citation": "APA/MLA citation format",
  "summary": "2-3 sentence summary",
  "key_contribution": "Main contribution",
  "methodology": "Method used",
  "relevance": "Relevance to research"
}}
"""
    
    raw = await llm.complete(prompt, system="You are an academic writing assistant. Return only JSON.", json_mode=True)
    
    import re
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(clean)
    except:
        return {
            "citation": paper.get("title", ""),
            "summary": paper.get("abstract", "")[:200],
            "key_contribution": "N/A",
            "methodology": "N/A",
            "relevance": "N/A"
        }
