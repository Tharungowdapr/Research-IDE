"""
RAG Chat Agent — Answers questions about the project using retrieved paper full texts.
"""

import json
import re
from typing import Dict, List, Any, AsyncGenerator
from core.llm_client import LLMClient


CHAT_SYSTEM = """You are a helpful research assistant with deep knowledge of the retrieved papers. \
Answer the user's question based on the provided paper context. \
If the context doesn't contain enough information, say so clearly. \
Cite papers using [N] notation matching the reference numbers. \
Keep answers concise and technically accurate."""

CHAT_PROMPT = """You are helping a researcher with their project: "{project_title}"

Research Domain: {domain}
Research Problem: {problem}

Retrieved Papers Context:
{paper_context}

User Question: {question}

Answer the question based on the paper context. Use [N] citations where applicable."""


async def chat_with_papers(
    question: str,
    papers: List[Dict],
    intent: Dict,
    llm: LLMClient,
    conversation_history: List[Dict] = None,
) -> str:
    """Answer a question using RAG over paper full texts."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    problem = intent.get("problem_statement", intent.get("task", "research problem"))
    title = intent.get("title", intent.get("research_topic", "Research Project"))

    paper_context = _format_papers_for_rag(papers[:10])

    messages = []
    if conversation_history:
        for msg in conversation_history[-6:]:
            role = "user" if msg.get("role") == "user" else "assistant"
            messages.append({"role": role, "content": msg.get("content", "")})

    system_content = CHAT_SYSTEM
    user_content = CHAT_PROMPT.format(
        project_title=title,
        domain=domain,
        problem=problem,
        paper_context=paper_context,
        question=question,
    )

    try:
        response = await llm.complete(user_content, system=system_content, json_mode=False)
        return response.strip()
    except Exception as e:
        print(f"RAG chat error: {e}")
        return "I'm sorry, I encountered an error while processing your question. Please try again."


async def chat_stream(
    question: str,
    papers: List[Dict],
    intent: Dict,
    llm: LLMClient,
    conversation_history: List[Dict] = None,
) -> AsyncGenerator[str, None]:
    """Stream a RAG chat response."""
    domain = ", ".join(intent.get("domain", ["AI/ML"]))
    problem = intent.get("problem_statement", intent.get("task", "research problem"))
    title = intent.get("title", intent.get("research_topic", "Research Project"))

    paper_context = _format_papers_for_rag(papers[:10])

    system_content = CHAT_SYSTEM
    user_content = CHAT_PROMPT.format(
        project_title=title,
        domain=domain,
        problem=problem,
        paper_context=paper_context,
        question=question,
    )

    try:
        async for chunk in llm.stream_complete(user_content, system=system_content, json_mode=False):
            yield chunk
    except Exception as e:
        print(f"RAG chat streaming error: {e}")
        yield "I'm sorry, I encountered an error while processing your question."


def _format_papers_for_rag(papers: List[Dict]) -> str:
    lines = []
    for i, p in enumerate(papers, 1):
        text = p.get("full_text") or p.get("abstract", "")
        if len(text) > 2000:
            text = text[:2000] + "..."
        authors = ", ".join(p.get("authors", ["Unknown"])[:3])
        lines.append(
            f"[{i}] {p.get('title', 'Untitled')}\n"
            f"    Authors: {authors}\n"
            f"    Year: {p.get('year', 'N/A')}\n"
            f"    Source: {p.get('source', 'unknown')}\n"
            f"    Text: {text}\n"
        )
    return "\n---\n".join(lines)
