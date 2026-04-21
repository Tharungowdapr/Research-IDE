"""
Paper Retrieval Service — Multi-source with scoring and deduplication.
Sources: arXiv, Semantic Scholar, OpenAlex, PapersWithCode
"""

import httpx
import asyncio
import re
from datetime import datetime
from typing import List, Dict, Any


async def retrieve_papers(
    queries: List[str],
    keywords: List[str],
    max_results: int = 25,
) -> List[Dict[str, Any]]:
    """Retrieve, deduplicate, score, and rank papers from multiple sources."""
    all_papers = []

    tasks = []
    for query in queries[:2]:
        tasks.append(_fetch_arxiv(query, max_results=10))
        tasks.append(_fetch_semantic_scholar(query, max_results=10))
        tasks.append(_fetch_openalex(query, max_results=10))
        tasks.append(_fetch_paperswithcode(query, max_results=5))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            all_papers.extend(result)
        elif isinstance(result, Exception):
            print(f"Retrieval task error: {result}")

    # Deduplicate
    all_papers = _deduplicate(all_papers)

    # Score and rank
    query_text = " ".join(queries + keywords)
    for paper in all_papers:
        paper["score"] = _compute_score(query_text, paper)

    all_papers.sort(key=lambda p: p.get("score", 0), reverse=True)
    return all_papers[:max_results]


# ── Scoring ───────────────────────────────────────────────────────────────────

def _compute_score(query: str, paper: Dict) -> float:
    """Compute ranking score: relevance*0.5 + recency*0.3 + citation*0.2"""
    relevance = _relevance_score(query, paper.get("title", ""), paper.get("abstract", ""))
    recency = _recency_score(paper.get("year", ""))
    citation = _citation_weight(paper.get("citations", "0"))
    return round(relevance * 0.5 + recency * 0.3 + citation * 0.2, 4)


def _relevance_score(query: str, title: str, abstract: str) -> float:
    query_terms = set(w.lower() for w in query.split() if len(w) > 3)
    if not query_terms:
        return 0.5
    paper_text = (title + " " + abstract).lower()
    matches = sum(1 for term in query_terms if term in paper_text)
    return min(matches / max(len(query_terms), 1), 1.0)


def _recency_score(year: str) -> float:
    try:
        y = int(year)
        current = datetime.now().year
        if y >= current - 1:
            return 1.0
        elif y >= current - 2:
            return 0.7
        else:
            return 0.4
    except (ValueError, TypeError):
        return 0.3


def _citation_weight(citations: str) -> float:
    try:
        c = int(str(citations).replace("N/A", "0").replace(",", ""))
        return min(c / 500, 1.0)
    except (ValueError, TypeError):
        return 0.0


# ── arXiv ─────────────────────────────────────────────────────────────────────

async def _fetch_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    try:
        import xml.etree.ElementTree as ET
        url = "https://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        async with httpx.AsyncClient(timeout=12.0) as client:
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
            papers.append({
                "id": paper_id.text.split("/")[-1] if paper_id is not None else "",
                "title": " ".join(title.text.strip().split()) if title is not None else "",
                "abstract": summary.text.strip()[:800] if summary is not None else "",
                "authors": [a.find("atom:name", ns).text for a in authors if a.find("atom:name", ns) is not None][:5],
                "year": published.text[:4] if published is not None else "",
                "citations": "N/A",
                "source": "arxiv",
                "url": f"https://arxiv.org/abs/{paper_id.text.split('/')[-1]}" if paper_id is not None else "",
                "github_url": "",
                "score": 0,
                "methods": [],
                "datasets": [],
                "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"arXiv fetch error: {e}")
        return []


# ── Semantic Scholar ──────────────────────────────────────────────────────────

async def _fetch_semantic_scholar(query: str, max_results: int = 10) -> List[Dict]:
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,year,citationCount,authors,externalIds,url",
        }
        headers = {"User-Agent": "ResearchIDE/1.0"}
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 429:
                return []
            resp.raise_for_status()
            data = resp.json()

        papers = []
        for item in data.get("data", []):
            abstract = item.get("abstract") or ""
            if not abstract:
                continue
            papers.append({
                "id": item.get("paperId", ""),
                "title": item.get("title", ""),
                "abstract": abstract[:800],
                "authors": [a["name"] for a in item.get("authors", [])[:5]],
                "year": str(item.get("year") or ""),
                "citations": str(item.get("citationCount") or "0"),
                "source": "semantic_scholar",
                "url": item.get("url") or f"https://www.semanticscholar.org/paper/{item.get('paperId', '')}",
                "github_url": "",
                "score": 0,
                "methods": [],
                "datasets": [],
                "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"Semantic Scholar fetch error: {e}")
        return []


# ── OpenAlex ──────────────────────────────────────────────────────────────────

async def _fetch_openalex(query: str, max_results: int = 10) -> List[Dict]:
    try:
        url = "https://api.openalex.org/works"
        params = {"search": query, "per_page": max_results, "mailto": "research@ide.app"}
        headers = {"User-Agent": "ResearchIDE/1.0 (mailto:research@ide.app)"}
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 429:
                return []
            resp.raise_for_status()
            data = resp.json()

        papers = []
        for item in data.get("results", []):
            abstract = _reconstruct_abstract(item.get("abstract_inverted_index"))
            if not abstract:
                continue
            title = item.get("title") or ""
            year = str(item.get("publication_year") or "")
            citations = str(item.get("cited_by_count") or "0")
            authors = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])[:5]]
            doi = item.get("doi") or ""
            url_link = doi if doi.startswith("http") else item.get("id", "")
            papers.append({
                "id": item.get("id", "").split("/")[-1] if item.get("id") else "",
                "title": title,
                "abstract": abstract[:800],
                "authors": [a for a in authors if a],
                "year": year,
                "citations": citations,
                "source": "openalex",
                "url": url_link,
                "github_url": "",
                "score": 0,
                "methods": [],
                "datasets": [],
                "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"OpenAlex fetch error: {e}")
        return []


def _reconstruct_abstract(inverted_index: dict) -> str:
    if not inverted_index:
        return ""
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    return " ".join(words[i] for i in sorted(words.keys()))


# ── PapersWithCode ────────────────────────────────────────────────────────────

async def _fetch_paperswithcode(query: str, max_results: int = 5) -> List[Dict]:
    try:
        url = "https://paperswithcode.com/api/v1/papers/"
        params = {"q": query, "items_per_page": max_results}
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                return []
            resp.raise_for_status()
            data = resp.json()

        papers = []
        for item in data.get("results", []):
            abstract = item.get("abstract") or ""
            if not abstract:
                continue
            title = item.get("title") or ""
            url_link = item.get("url_abs") or item.get("paper_url") or ""
            papers.append({
                "id": item.get("id", ""),
                "title": title,
                "abstract": abstract[:800],
                "authors": [],
                "year": (item.get("published") or "")[:4],
                "citations": "0",
                "source": "paperswithcode",
                "url": url_link,
                "github_url": item.get("repository_url") or "",
                "score": 0,
                "methods": [],
                "datasets": [],
                "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"PapersWithCode fetch error: {e}")
        return []


# ── Deduplication ─────────────────────────────────────────────────────────────

def _deduplicate(papers: List[Dict]) -> List[Dict]:
    seen_titles = set()
    unique = []
    for paper in papers:
        title_key = _normalize_title(paper.get("title", ""))
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique.append(paper)
    return unique


def _normalize_title(title: str) -> str:
    return re.sub(r'[^a-z0-9]', '', title.lower())[:50]
