"""
Literature Review Agent - Automated literature review generation
"""

import json
from typing import List, Dict, Any
from core.llm_client import LLMClient
from agents.shared.context_builder import format_project_context, parse_json


LITERATURE_REVIEW_SYSTEM = """You are an expert academic writer specializing in literature reviews.
Return ONLY valid JSON in the specified format."""

LITERATURE_REVIEW_PROMPT = """Generate a comprehensive, structured literature review based on these papers and project context.

Full Project Context:
{full_context}

Papers for Review:
{papers_summary}

Return EXACTLY this JSON structure:
{{
  "title": "Literature Review: [Domain-specific title]",
  "introduction": "2-3 paragraph introduction to the field and the specific research area",
  "themes": [
    {{
      "name": "Specific theme name related to the project",
      "description": "Detailed 3-4 sentence description of this theme",
      "papers": ["paper title 1", "paper title 2"],
      "key_findings": "2-3 sentence summary of key findings across papers in this theme",
      "relevance_to_project": "How this theme relates to the selected research idea"
    }}
  ],
  "methodology_comparison": "2-3 paragraph comparison of methods used across the literature, with specific examples",
  "gaps_identified": [
    {{"gap": "Specific gap description", "supporting_papers": ["paper 1"], "relevance": "How this gap connects to the project"}}
  ],
  "future_directions": [
    {{"direction": "Specific future research direction", "rationale": "Why this direction is promising"}}
  ],
  "conclusion": "2-3 paragraph conclusion synthesizing the literature and positioning the project within it",
  "detailed_explanation": "3-4 paragraph synthesis connecting the literature review to the specific research idea, highlighting how the project fills identified gaps"
}}

Include 4-6 themes minimum. Each theme must reference specific papers. Make the content project-specific, NOT generic."""


async def generate_literature_review(
    papers: List[Dict[str, Any]],
    intent: Dict,
    llm: LLMClient,
    idea: Dict = None,
    gaps: list = None,
) -> Dict:
    if not papers:
        return {"error": "No papers provided"}
    
    papers_summary = _summarize_papers(papers[:20])
    full_context = format_project_context(
        idea=idea, gaps=gaps, papers=papers, intent=intent,
    )
    
    try:
        prompt = LITERATURE_REVIEW_PROMPT.format(
            full_context=full_context or f"Domain: {intent.get('domain', 'research')}",
            papers_summary=papers_summary,
        )
        
        raw = await llm.complete(
            prompt,
            system=LITERATURE_REVIEW_SYSTEM,
            json_mode=True
        )
        
        result = parse_json(raw)
        if isinstance(result, dict) and "themes" in result:
            return result
        return result or {"error": "Failed to parse LLM response"}
            
    except Exception as e:
        print(f"Literature review generation error: {e}")
        return {
            "error": str(e),
            "title": f"Literature Review: {intent.get('domain', 'Research')}",
            "introduction": f"Failed to generate review: {str(e)}"
        }


def _summarize_papers(papers: List[Dict]) -> str:
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
    if not papers:
        return []
    
    annotations = []
    for paper in papers[:15]:
        try:
            annotation = await _generate_annotation(paper, llm)
            annotations.append(annotation)
        except Exception as e:
            print(f"Annotation error for {paper.get('title')}: {e}")
    
    return annotations


async def _generate_annotation(paper: Dict, llm: LLMClient) -> Dict:
    prompt = f"""Generate a detailed annotation for this paper:

Title: {paper.get('title', '')}
Year: {paper.get('year', '')}
Abstract: {paper.get('abstract', '')[:500]}

Return JSON:
{{
  "citation": "APA/MLA citation format",
  "summary": "3-4 sentence summary covering problem, method, key finding, and limitation",
  "key_contribution": "Main contribution in one sentence",
  "methodology": "Method used with key details",
  "relevance": "Relevance to research project",
  "strengths": ["strength 1", "strength 2"],
  "limitations": ["limitation 1", "limitation 2"]
}}
"""
    
    raw = await llm.complete(prompt, system="You are an academic writing assistant. Return only JSON.", json_mode=True)
    result = parse_json(raw)
    if isinstance(result, dict) and "citation" in result:
        return result
    return {
        "citation": paper.get("title", ""),
        "summary": paper.get("abstract", "")[:200],
        "key_contribution": "N/A",
        "methodology": "N/A",
        "relevance": "N/A",
        "strengths": [],
        "limitations": [],
    }
