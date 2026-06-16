"""
Chat Agent — Conversational research assistant that answers questions
using project context (papers, gaps, ideas, plans, reports).
"""

import json
import re
from typing import Dict, List, Any, AsyncGenerator
from core.llm_client import LLMClient


CHAT_SYSTEM = """You are a research assistant AI embedded in the ResearchIDE platform. 
You help researchers understand their project context including papers, gaps, ideas, 
and plans. Be concise, accurate, and cite specific papers when relevant. 
You have access to the project's full research context."""


def build_chat_prompt(
    question: str,
    history: List[Dict[str, str]],
    project_context: Dict[str, Any],
) -> str:
    """Build a conversation prompt with project context."""
    context_parts = []

    intent = project_context.get("intent", {})
    if intent:
        context_parts.append(f"Research Domain: {intent.get('domain', 'N/A')}")
        context_parts.append(f"Research Question: {intent.get('description', 'N/A')}")

    papers_data = project_context.get("papers", {}) or {}
    papers = papers_data.get("papers", [])
    if papers:
        context_parts.append(f"\nRetrieved Papers ({len(papers)}):")
        for i, p in enumerate(papers[:5], 1):
            title = p.get("title", "Untitled")
            context_parts.append(f"  {i}. {title}")

    gaps = project_context.get("gaps", {}) or {}
    gap_list = gaps.get("gaps", [])
    if gap_list:
        context_parts.append(f"\nIdentified Research Gaps ({len(gap_list)}):")
        for g in gap_list[:3]:
            context_parts.append(f"  - {g.get('title', '')}")

    ideas_data = project_context.get("ideas", {}) or {}
    ideas = ideas_data.get("ideas", [])
    if ideas:
        context_parts.append(f"\nGenerated Ideas ({len(ideas)}):")
        for i, idea in enumerate(ideas[:3], 1):
            context_parts.append(f"  {i}. {idea.get('title', '')}")

    selected = project_context.get("selected_idea", {}) or {}
    if selected:
        idea = selected.get("idea", {})
        context_parts.append(f"\nSelected Idea: {idea.get('title', '')}")
        context_parts.append(f"Approach: {idea.get('approach', '')}")

    plan = project_context.get("plan", {})
    if plan:
        context_parts.append(f"\nExecution Plan: {plan.get('overview', plan.get('introduction', ''))[:500]}")

    report = project_context.get("report", {})
    if report:
        context_parts.append(f"\nReport Generated: {report.get('title', 'Yes')}")

    context = "\n".join(context_parts)

    history_text = ""
    for msg in history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text += f"{'User' if role == 'user' else 'Assistant'}: {content}\n"

    return f"""Project Context:
{context}

Conversation History:
{history_text}

User Question: {question}

Answer the question based on the project context. If the answer isn't in the context, say so."""


async def run_chat(
    question: str,
    history: List[Dict[str, str]],
    project_context: Dict[str, Any],
    llm: LLMClient,
) -> str:
    """Non-streaming chat response."""
    prompt = build_chat_prompt(question, history, project_context)

    try:
        response = await llm.complete(prompt, system=CHAT_SYSTEM)
        return response.strip()
    except Exception as e:
        print(f"Chat agent error: {e}")
        return f"I encountered an error processing your question. Please try again."


async def run_chat_stream(
    question: str,
    history: List[Dict[str, str]],
    project_context: Dict[str, Any],
    llm: LLMClient,
) -> AsyncGenerator[str, None]:
    """Streaming chat response."""
    prompt = build_chat_prompt(question, history, project_context)

    try:
        async for chunk in llm.stream_complete(prompt, system=CHAT_SYSTEM):
            yield chunk
    except Exception as e:
        print(f"Chat streaming error: {e}")
        yield f"I encountered an error processing your question. Please try again."
