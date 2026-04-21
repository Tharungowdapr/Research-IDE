"""
Paper Retrieval Service
Fetches papers from: arXiv API, Semantic Scholar API, OpenAlex API
Falls back gracefully if any API is unavailable.
"""

import httpx
import asyncio
from typing import List, Dict, Any
import xml.etree.ElementTree as ET
from sqlalchemy.orm import Session
from sqlalchemy import or_
from core.database import SessionLocal
from models.project import PaperCache


async def retrieve_papers(
    queries: List[str],
    keywords: List[str],
    max_results: int = 20,
) -> List[Dict[str, Any]]:
    """
    Retrieve papers from multiple sources and deduplicate.
    """
    # 1. Check local cache first
    cached_papers = _check_local_cache(queries, keywords, max_results)
    
    # 2. Fetch from APIs for variety or if cache is insufficient
    # If we already have enough cached papers, we can skip API calls to stay fast,
    # but for now we'll always try to get a few fresh ones if possible.
    api_max = max(10, max_results - len(cached_papers))
    
    papers = list(cached_papers)
    
    if api_max > 0:
        # Run retrievals concurrently with a strict timeout
        tasks = []
        for query in queries[:2]:  # Limit to 2 queries for speed
            tasks.append(_fetch_arxiv(query, max_results=5))
            tasks.append(_fetch_semantic_scholar(query, max_results=5))

        if tasks:
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, list):
                        papers.extend(result)
                    elif isinstance(result, Exception):
                        print(f"API task error: {result}")
            except Exception as e:
                print(f"Gather error: {e}")

    # 3. If still empty, try a broader search in local cache using keywords only
    if not papers and keywords:
        papers = _check_local_cache([], keywords, max_results)

    # Deduplicate by title similarity
    papers = _deduplicate(papers)

    # Limit and sort by year (newest first)
    papers.sort(key=lambda p: int(p.get("year", "0") or "0"), reverse=True)
    return papers[:max_results]


def _check_local_cache(queries: List[str], keywords: List[str], max_results: int) -> List[Dict]:
    """Search for papers in the local database cache."""
    db: Session = SessionLocal()
    try:
        # Build search filters
        search_terms = [q for q in (queries + keywords) if len(q) > 2]
        if not search_terms:
            return []
            
        filters = []
        for q in search_terms:
            filters.append(PaperCache.title.ilike(f"%{q}%"))
            filters.append(PaperCache.abstract.ilike(f"%{q}%"))
        
        results = db.query(PaperCache).filter(or_(*filters)).limit(max_results).all()
        
        papers = []
        for r in results:
            papers.append({
                "id": r.external_id,
                "title": r.title,
                "abstract": r.abstract,
                "authors": r.authors,
                "year": r.year,
                "citations": r.citations,
                "source": r.source,
                "url": r.url,
                "methods": r.methods,
                "datasets": r.datasets,
                "limitations": r.limitations,
                "is_cached": True
            })
        return papers
    except Exception as e:
        print(f"Local cache search error: {e}")
        return []
    finally:
        db.close()


async def _fetch_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    """Fetch papers from arXiv API."""
    try:
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()

        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []

        for entry in root.findall("atom:entry", ns):
            paper_id = entry.find("atom:id", ns)
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            authors = entry.findall("atom:author", ns)

            if not title or not summary:
                continue

            paper = {
                "id": paper_id.text.split("/")[-1] if paper_id is not None else "",
                "title": " ".join(title.text.strip().split()) if title is not None else "",
                "abstract": summary.text.strip()[:800] if summary is not None else "",
                "authors": [
                    a.find("atom:name", ns).text
                    for a in authors
                    if a.find("atom:name", ns) is not None
                ][:5],
                "year": published.text[:4] if published is not None else "",
                "citations": "N/A",
                "source": "arxiv",
                "url": f"https://arxiv.org/abs/{paper_id.text.split('/')[-1]}" if paper_id is not None else "",
                "methods": [],
                "datasets": [],
                "limitations": [],
            }
            papers.append(paper)

        return papers
    except httpx.TimeoutException:
        print("arXiv fetch timeout")
        return []
    except Exception as e:
        print(f"arXiv fetch error: {type(e).__name__}: {e}")
        return []


async def _fetch_semantic_scholar(query: str, max_results: int = 10) -> List[Dict]:
    """Fetch papers from Semantic Scholar API (no auth required for basic use)."""
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,year,citationCount,authors,externalIds,url",
        }
        headers = {"User-Agent": "ResearchIDE/1.0"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 429:
                return []  # Rate limited
            resp.raise_for_status()
            data = resp.json()

        papers = []
        for item in data.get("data", []):
            abstract = item.get("abstract") or ""
            if not abstract:
                continue  # Skip papers without abstracts

            paper = {
                "id": item.get("paperId", ""),
                "title": item.get("title", ""),
                "abstract": abstract[:800],
                "authors": [
                    a["name"] for a in item.get("authors", [])[:5]
                ],
                "year": str(item.get("year") or ""),
                "citations": str(item.get("citationCount") or "0"),
                "source": "semantic_scholar",
                "url": item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                "methods": [],
                "datasets": [],
                "limitations": [],
            }
            papers.append(paper)

        return papers
    except Exception as e:
        print(f"Semantic Scholar fetch error: {e}")
        return []


def _deduplicate(papers: List[Dict]) -> List[Dict]:
    """Remove duplicate papers by title similarity."""
    seen_titles = set()
    unique = []
    for paper in papers:
        title_key = _normalize_title(paper.get("title", ""))
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique.append(paper)
    return unique


def _normalize_title(title: str) -> str:
    """Normalize title for deduplication comparison."""
    import re
    return re.sub(r'[^a-z0-9]', '', title.lower())[:50]
