"""
Example Plugin: Crossref Paper Retrieval
Demonstrates how to create a plugin for ResearchIDE
"""

import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Plugin metadata (required)
PLUGIN_NAME = "crossref_retrieval"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Fetch paper metadata from Crossref API for DOI-based research"
PLUGIN_AUTHOR = "ResearchIDE Contributors"


async def retrieve_papers(
    query: str,
    limit: int = 10,
    year_from: int = 2018,
    year_to: int = 2024
) -> List[Dict[str, Any]]:
    """
    Retrieve papers from Crossref API
    
    Args:
        query: Search query (keywords, authors, title)
        limit: Maximum number of papers to retrieve
        year_from: Start year for filtering
        year_to: End year for filtering
    
    Returns:
        List of paper metadata dicts
    """
    papers = []
    crossref_url = "https://api.crossref.org/v1/works"
    
    params = {
        "query": query,
        "rows": min(limit, 100),  # Crossref allows max 100 per request
        "sort": "relevance",
        "order": "desc",
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(crossref_url, params=params, timeout=30.0)
            response.raise_for_status()
            
            data = response.json()
            items = data.get("message", {}).get("items", [])
            
            for item in items:
                # Extract published year
                pub_date = item.get("published-online") or item.get("published-print")
                year = None
                if pub_date:
                    year = pub_date.get("date-parts", [[None]])[0][0]
                
                # Filter by year
                if year and not (year_from <= year <= year_to):
                    continue
                
                # Extract metadata
                paper = {
                    "title": item.get("title", ["Unknown"])[0] if isinstance(item.get("title"), list) else item.get("title"),
                    "authors": extract_authors(item.get("author", [])),
                    "year": year,
                    "doi": item.get("DOI"),
                    "url": item.get("URL"),
                    "journal": item.get("container-title", ["Unknown"])[0] if isinstance(item.get("container-title"), list) else item.get("container-title"),
                    "abstract": item.get("abstract"),
                    "external_id": item.get("DOI"),  # Use DOI as external ID
                    "source": "crossref",
                }
                
                if paper["abstract"]:  # Only include papers with abstracts
                    papers.append(paper)
                    if len(papers) >= limit:
                        break
            
            logger.info(f"Crossref: Retrieved {len(papers)} papers for query '{query}'")
            
    except Exception as e:
        logger.error(f"Crossref retrieval error: {e}")
        raise
    
    return papers


async def get_paper_full_url(doi: str) -> str:
    """
    Get full-text URL for a paper by DOI
    
    Args:
        doi: Digital Object Identifier
    
    Returns:
        URL to access the paper
    """
    return f"https://doi.org/{doi}"


def extract_authors(author_list: List[Dict[str, Any]]) -> str:
    """Extract author names from Crossref format"""
    if not author_list:
        return "Unknown"
    
    names = []
    for author in author_list[:3]:  # First 3 authors
        family = author.get("family", "")
        given = author.get("given", "")
        if family:
            names.append(f"{given} {family}".strip())
    
    result = ", ".join(names)
    if len(author_list) > 3:
        result += f", et al."
    
    return result or "Unknown"


# Plugin lifecycle hooks (optional)

async def on_load():
    """Called when plugin is loaded"""
    logger.info(f"Loading {PLUGIN_NAME} v{PLUGIN_VERSION}")
    # Initialize connections, load models, etc.
    pass


async def on_unload():
    """Called when plugin is unloaded"""
    logger.info(f"Unloading {PLUGIN_NAME}")
    # Cleanup resources
    pass


# Plugin configuration (optional)
CONFIG = {
    "timeout": 30,
    "max_retries": 3,
    "rate_limit": 50,  # requests per minute
}
