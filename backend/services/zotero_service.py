"""
Zotero Integration Service
Import/export papers to/from Zotero library
"""

import httpx
from typing import List, Dict, Any, Optional


ZOTERO_API_BASE = "https://api.zotero.org"


async def get_user_libraries(zotero_key: str, user_id: str) -> List[Dict]:
    """Get list of user's Zotero libraries."""
    try:
        url = f"{ZOTERO_API_BASE}/users/{user_id}/collections"
        headers = {"Zotero-API-Key": zotero_key}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"Zotero API error: {e}")
    return []


async def search_zotero_library(
    zotero_key: str, 
    user_id: str, 
    query: str,
    limit: int = 20
) -> List[Dict]:
    """Search papers in Zotero library."""
    try:
        url = f"{ZOTERO_API_BASE}/users/{user_id}/items"
        headers = {"Zotero-API-Key": zotero_key}
        params = {
            "q": query,
            "limit": limit,
            "itemType": "journalArticle",
            "format": "json",
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                items = resp.json()
                return _parse_zotero_items(items)
    except Exception as e:
        print(f"Zotero search error: {e}")
    return []


async def export_to_zotero(
    zotero_key: str,
    user_id: str,
    papers: List[Dict],
    collection_id: Optional[str] = None
) -> Dict:
    """Export papers to Zotero library."""
    try:
        url = f"{ZOTERO_API_BASE}/users/{user_id}/items"
        if collection_id:
            url = f"{ZOTERO_API_BASE}/users/{user_id}/collections/{collection_id}/items"
        
        headers = {
            "Zotero-API-Key": zotero_key,
            "Content-Type": "application/json",
        }
        
        zotero_items = [_convert_to_zotero_format(p) for p in papers[:50]]  # Limit to 50 papers
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=zotero_items)
            if resp.status_code in (200, 201):
                return {"success": True, "exported": len(zotero_items)}
            else:
                return {"success": False, "error": f"Zotero API returned {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_zotero_items(items: List[Dict]) -> List[Dict]:
    """Convert Zotero items to our paper format."""
    papers = []
    for item in items:
        data = item.get("data", {})
        papers.append({
            "id": data.get("key", ""),
            "title": data.get("title", ""),
            "abstract": data.get("abstractNote", ""),
            "authors": [c.get("firstName", "") + " " + c.get("lastName", "") 
                       for c in data.get("creators", []) if c.get("lastName")],
            "year": str(data.get("date", "")[:4]),
            "citations": "N/A",
            "source": "zotero",
            "url": data.get("url", ""),
            "doi": data.get("DOI", ""),
        })
    return papers


def _convert_to_zotero_format(paper: Dict) -> Dict:
    """Convert our paper format to Zotero item."""
    return {
        "itemType": "journalArticle",
        "title": paper.get("title", ""),
        "abstractNote": paper.get("abstract", ""),
        "creators": [
            {"creatorType": "author", "firstName": a.split()[-1] if len(a.split()) > 1 else "", 
             "lastName": a.split()[-1] if len(a.split()) > 0 else ""}
            for a in paper.get("authors", [])[:5]
        ],
        "date": paper.get("year", ""),
        "url": paper.get("url", ""),
        "DOI": paper.get("doi", ""),
        "tags": [{"tag": "ResearchIDE"}],
    }
