"""
Paper Retrieval Service v2
Sources: arXiv, Semantic Scholar, OpenAlex, PapersWithCode
"""

import httpx
import asyncio
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from core.utils import normalize_title, compute_paper_score, truncate_text, api_rate_limiter


async def retrieve_papers(queries: List[str], keywords: List[str], max_results: int = 20) -> List[Dict[str, Any]]:
    query_terms = list({
        w.lower() for q in queries for w in q.split() if len(w) > 3
    } | {k.lower() for k in keywords if len(k) > 3})

    primary = queries[0] if queries else " ".join(keywords[:3])
    secondary = queries[1] if len(queries) > 1 else primary

    tasks = [
        _fetch_arxiv(primary, 10),
        _fetch_arxiv(secondary, 6),
        _fetch_semantic_scholar(primary, 10),
        _fetch_openalex(primary, 10),
        _fetch_paperswithcode(primary, 6),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    papers = []
    for r in results:
        if isinstance(r, list):
            papers.extend(r)

    papers = _deduplicate(papers)
    for p in papers:
        p["score"] = round(compute_paper_score(p, query_terms), 3)
    papers.sort(key=lambda p: p["score"], reverse=True)
    
    # Enforce minimum of 10 if possible, maximum of 20
    # The minimum is implicitly handled if we fetch enough. The max is enforced here.
    return papers[:max_results]


async def _fetch_arxiv(query: str, max_results: int = 10) -> List[Dict]:
    try:
        params = {"search_query": f"all:{query}", "max_results": max_results, "sortBy": "relevance"}
        async with api_rate_limiter:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get("http://export.arxiv.org/api/query", params=params)
                resp.raise_for_status()
        root = ET.fromstring(resp.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []
        for entry in root.findall("atom:entry", ns):
            pid = entry.find("atom:id", ns)
            title = entry.find("atom:title", ns)
            summary = entry.find("atom:summary", ns)
            published = entry.find("atom:published", ns)
            authors = entry.findall("atom:author", ns)
            if not title or not summary or not summary.text:
                continue
            raw_id = pid.text.split("/")[-1] if pid is not None else ""
            papers.append({
                "id": f"arxiv_{raw_id}", "title": " ".join(title.text.strip().split()),
                "abstract": truncate_text(summary.text.strip(), 600),
                "authors": [a.find("atom:name", ns).text for a in authors if a.find("atom:name", ns) is not None][:5],
                "year": published.text[:4] if published is not None else "", "citations": "0",
                "source": "arxiv", "url": f"https://arxiv.org/abs/{raw_id}", "github_url": "",
                "score": 0.0, "methods": [], "datasets": [], "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"[arXiv] {e}"); return []


async def _fetch_semantic_scholar(query: str, max_results: int = 10) -> List[Dict]:
    try:
        params = {"query": query, "limit": max_results, "fields": "title,abstract,year,citationCount,authors,url"}
        headers = {"User-Agent": "ResearchIDE/2.0 (research@ide.app)"}
        async with api_rate_limiter:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get("https://api.semanticscholar.org/graph/v1/paper/search", params=params, headers=headers)
                if resp.status_code == 429: return []
                resp.raise_for_status()
                data = resp.json()
        papers = []
        for item in data.get("data", []):
            abstract = item.get("abstract") or ""
            if not abstract.strip(): continue
            papers.append({
                "id": f"ss_{item.get('paperId','')}", "title": item.get("title", ""),
                "abstract": truncate_text(abstract, 600),
                "authors": [a["name"] for a in item.get("authors", [])[:5]],
                "year": str(item.get("year") or ""), "citations": str(item.get("citationCount") or "0"),
                "source": "semantic_scholar", "url": item.get("url") or "", "github_url": "",
                "score": 0.0, "methods": [], "datasets": [], "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"[Semantic Scholar] {e}"); return []


async def _fetch_openalex(query: str, max_results: int = 10) -> List[Dict]:
    try:
        params = {"search": query, "per_page": max_results, "select": "id,title,abstract_inverted_index,publication_year,cited_by_count,authorships"}
        headers = {"User-Agent": "ResearchIDE/2.0 (mailto:research@ide.app)"}
        async with api_rate_limiter:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get("https://api.openalex.org/works", params=params, headers=headers)
                if resp.status_code == 429:
                    # Back off and retry once
                    import asyncio as _asyncio
                    await _asyncio.sleep(2.0)
                    resp = await client.get("https://api.openalex.org/works", params=params, headers=headers)
                    if resp.status_code == 429: return []
                resp.raise_for_status()
                data = resp.json()
        papers = []
        for item in data.get("results", []):
            abstract = _reconstruct_abstract(item.get("abstract_inverted_index"))
            if not abstract.strip(): continue
            authors = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])[:5] if a.get("author")]
            oa_id = item.get("id", "").split("/")[-1]
            papers.append({
                "id": f"oa_{oa_id}", "title": item.get("title") or "",
                "abstract": truncate_text(abstract, 600), "authors": authors,
                "year": str(item.get("publication_year") or ""), "citations": str(item.get("cited_by_count") or "0"),
                "source": "openalex", "url": f"https://openalex.org/{oa_id}", "github_url": "",
                "score": 0.0, "methods": [], "datasets": [], "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"[OpenAlex] {e}"); return []


def _reconstruct_abstract(inverted_index) -> str:
    if not isinstance(inverted_index, dict) or not inverted_index:
        return ""
    try:
        words: Dict[int, str] = {}
        for word, positions in inverted_index.items():
            for pos in positions:
                words[pos] = word
        return " ".join(words[i] for i in sorted(words.keys()))
    except Exception:
        return ""


async def _fetch_paperswithcode(query: str, max_results: int = 6) -> List[Dict]:
    try:
        params = {"q": query, "items_per_page": max_results}
        headers = {"User-Agent": "ResearchIDE/2.0 (research@ide.app)"}
        async with api_rate_limiter:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get("https://paperswithcode.com/api/v1/papers/", params=params, headers=headers)
                if resp.status_code in (429, 403): return []
                resp.raise_for_status()
                data = resp.json()
        papers = []
        for item in data.get("results", []):
            abstract = item.get("abstract") or ""
            if not abstract.strip(): continue
            github_url = ""
            repos = item.get("repositories") or item.get("repository")
            if isinstance(repos, list) and repos:
                github_url = repos[0].get("url", "")
            elif isinstance(repos, dict):
                github_url = repos.get("url", "")
            papers.append({
                "id": f"pwc_{item.get('id','')}", "title": item.get("title", ""),
                "abstract": truncate_text(abstract, 600), "authors": item.get("authors", [])[:5],
                "year": str(item.get("published", ""))[:4], "citations": "0",
                "source": "paperswithcode", "url": item.get("url_pdf") or item.get("url_abs") or "",
                "github_url": github_url, "score": 0.0, "methods": item.get("methods", []), "datasets": [], "limitations": [],
            })
        return papers
    except Exception as e:
        print(f"[PapersWithCode] {e}"); return []


def _deduplicate(papers: List[Dict]) -> List[Dict]:
    seen: set = set()
    unique = []
    for paper in papers:
        key = normalize_title(paper.get("title", ""))
        if key and len(key) > 5 and key not in seen:
            seen.add(key)
            unique.append(paper)
    return unique
