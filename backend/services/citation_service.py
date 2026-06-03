"""
Citation Graph Service - Build citation networks from papers
"""

from typing import List, Dict, Any, Set
import asyncio
import httpx
from core.utils import RateLimiter


# Semantic Scholar rate limit: ~1 request per 3 seconds (100 per 5 min)
ss_rate_limiter = RateLimiter(max_concurrent=1, delay_seconds=3.0)


async def build_citation_graph(papers: List[Dict[str, Any]], max_depth: int = 2) -> Dict:
    """
    Build a citation graph from a list of papers.
    Returns nodes and edges for visualization.
    """
    nodes = []
    edges = []
    visited: Set[str] = set()
    
    # Add initial papers as nodes
    for paper in papers[:20]:  # Limit to 20 papers
        paper_id = paper.get("id", paper.get("title", ""))
        if paper_id in visited:
            continue
        visited.add(paper_id)
        
        nodes.append({
            "id": paper_id,
            "title": paper.get("title", "Unknown")[:100],
            "year": paper.get("year", ""),
            "citations": paper.get("citations", "0"),
            "source": paper.get("source", ""),
            "url": paper.get("url", ""),
        })
    
    # Fetch citations for each paper concurrently with rate limiting
    ss_papers = [p for p in papers[:10] if p.get("source") == "semantic_scholar" and p.get("id")]
    
    async def fetch_with_rate_limit(paper):
        paper_id = paper.get("id", "")
        async with ss_rate_limiter:
            try:
                citations = await _fetch_citations_ss(paper_id)
                return paper_id, citations[:5]  # Top 5 citations per paper
            except Exception as e:
                print(f"Error fetching citations for {paper_id}: {e}")
                return paper_id, []
    
    # Fetch concurrently with rate limiting
    tasks = [fetch_with_rate_limit(p) for p in ss_papers]
    results = await asyncio.gather(*tasks)
    
    for paper_id, citations in results:
        for citing_paper in citations:
            citing_id = citing_paper.get("paperId", citing_paper.get("title", ""))
            if citing_id not in visited:
                visited.add(citing_id)
                nodes.append({
                    "id": citing_id,
                    "title": citing_paper.get("title", "Unknown")[:100],
                    "year": str(citing_paper.get("year", "")),
                    "citations": str(citing_paper.get("citationCount", 0)),
                    "source": "semantic_scholar",
                    "url": citing_paper.get("url", ""),
                })
            
            edges.append({
                "source": citing_id,
                "target": paper_id,
                "type": "cites",
            })
    
    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "papers_analyzed": min(len(papers), 20),
        }
    }


async def _fetch_citations_ss(paper_id: str) -> List[Dict]:
    """Fetch papers that cite this paper from Semantic Scholar."""
    try:
        url = f"https://api.semanticscholar.org/graph/v1/paper/{paper_id}/citations"
        params = {
            "fields": "title,year,citationCount,url,paperId",
            "limit": 10,
        }
        headers = {"User-Agent": "ResearchIDE/1.0"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                # Extract citing paper details
                citing_papers = []
                for entry in data.get("data", []):
                    citing = entry.get("citingPaper", {})
                    if citing.get("paperId"):
                        citing_papers.append(citing)
                return citing_papers
            elif resp.status_code == 429:
                print(f"Semantic Scholar rate limit hit for {paper_id}")
    except Exception as e:
        print(f"Semantic Scholar citation fetch error: {e}")
    return []


async def find_related_papers(paper_title: str, max_results: int = 10) -> List[Dict]:
    """Find papers related to a given paper title."""
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": paper_title,
            "fields": "title,year,citationCount,authors,abstract,url,paperId",
            "limit": max_results,
        }
        headers = {"User-Agent": "ResearchIDE/1.0"}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", [])
    except Exception as e:
        print(f"Related papers fetch error: {e}")
    return []
