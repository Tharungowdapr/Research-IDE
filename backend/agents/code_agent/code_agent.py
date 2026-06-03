"""
Code Generation Agent - generates code based on research findings
"""

import json
import logging
from typing import Optional, Any, AsyncIterator

logger = logging.getLogger(__name__)


async def run_code_generation(
    project_id: str,
    intent: str,
    retrieved_papers: list,
    user_id: str,
    llm_client: Any,
) -> dict:
    """
    Generate code implementation based on research papers and intent.
    
    Args:
        project_id: Project ID
        intent: Research intent/goal
        retrieved_papers: List of retrieved research papers
        user_id: User ID
        llm_client: LLM client instance
        
    Returns:
        Dictionary with generated code structure
    """
    try:
        # Build context from papers
        papers_summary = "\n".join([
            f"- {p.get('title', 'N/A')}: {p.get('abstract', '')[:200]}"
            for p in retrieved_papers[:5]
        ])
        
        prompt = f"""Based on the following research papers and intent, generate a Python implementation plan.

Intent: {intent}

Research Papers:
{papers_summary}

Generate a code structure with:
1. Module organization
2. Key classes/functions
3. Implementation notes

Respond in JSON format with 'modules', 'classes', 'functions', 'notes' keys."""
        
        response = await llm_client.agenerate_text(prompt)
        
        try:
            code_data = json.loads(response)
        except json.JSONDecodeError:
            code_data = {
                "modules": ["core", "utils"],
                "classes": ["ResearchImpl"],
                "functions": ["main", "process"],
                "notes": response
            }
        
        return {
            "project_id": project_id,
            "code": code_data,
            "status": "completed"
        }
    except Exception as e:
        logger.error(f"Code generation error: {e}")
        return {
            "project_id": project_id,
            "code": {"error": str(e)},
            "status": "error"
        }


async def run_code_generation_stream(
    project_id: str,
    intent: str,
    retrieved_papers: list,
    user_id: str,
    llm_client: Any,
) -> AsyncIterator[str]:
    """
    Stream code generation output.
    
    Args:
        project_id: Project ID
        intent: Research intent/goal
        retrieved_papers: List of retrieved research papers
        user_id: User ID
        llm_client: LLM client instance
        
    Yields:
        JSON chunks of generated code
    """
    try:
        papers_summary = "\n".join([
            f"- {p.get('title', 'N/A')}: {p.get('abstract', '')[:200]}"
            for p in retrieved_papers[:5]
        ])
        
        prompt = f"""Based on the following research papers and intent, generate a Python implementation plan.

Intent: {intent}

Research Papers:
{papers_summary}

Generate a code structure with:
1. Module organization
2. Key classes/functions
3. Implementation notes

Respond in JSON format with 'modules', 'classes', 'functions', 'notes' keys."""
        
        # Stream the response
        async for chunk in llm_client.astream_text(prompt):
            yield chunk
            
    except Exception as e:
        logger.error(f"Code generation stream error: {e}")
        yield json.dumps({"error": str(e)})
