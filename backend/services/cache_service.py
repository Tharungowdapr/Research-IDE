"""
Paper Cache Service - Persistent caching using PaperCache model
"""

from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from models.project import PaperCache


def get_cached_paper(db: Session, external_id: str) -> Optional[Dict]:
    """Retrieve cached paper by external ID."""
    cache = db.query(PaperCache).filter(PaperCache.external_id == external_id).first()
    if cache:
        return {
            "id": cache.external_id,
            "title": cache.title,
            "abstract": cache.abstract,
            "authors": cache.authors,
            "year": cache.year,
            "citations": cache.citations,
            "source": cache.source,
            "url": cache.url,
            "methods": cache.methods,
            "datasets": cache.datasets,
            "limitations": cache.limitations,
            "full_text": cache.full_text if hasattr(cache, 'full_text') else None,
        }
    return None


def cache_paper(db: Session, paper: Dict, full_text: Optional[str] = None) -> PaperCache:
    """Cache a paper with optional full text."""
    existing = db.query(PaperCache).filter(PaperCache.external_id == paper.get("id")).first()
    
    if existing:
        # Update existing cache
        existing.title = paper.get("title", existing.title)
        existing.abstract = paper.get("abstract", existing.abstract)
        existing.authors = paper.get("authors", existing.authors)
        existing.year = paper.get("year", existing.year)
        existing.citations = str(paper.get("citations", existing.citations))
        existing.source = paper.get("source", existing.source)
        existing.url = paper.get("url", existing.url)
        existing.methods = paper.get("methods", existing.methods)
        existing.datasets = paper.get("datasets", existing.datasets)
        existing.limitations = paper.get("limitations", existing.limitations)
        if full_text:
            existing.full_text = full_text
        existing.cached_at = __import__('datetime').datetime.utcnow()
    else:
        # Create new cache entry
        cache = PaperCache(
            external_id=paper.get("id"),
            title=paper.get("title", ""),
            abstract=paper.get("abstract"),
            authors=paper.get("authors", []),
            year=paper.get("year"),
            citations=str(paper.get("citations", "0")),
            source=paper.get("source"),
            url=paper.get("url"),
            methods=paper.get("methods", []),
            datasets=paper.get("datasets", []),
            limitations=paper.get("limitations", []),
            full_text=full_text,
        )
        db.add(cache)
    
    db.commit()
    return existing if existing else cache


def cache_full_text(db: Session, external_id: str, full_text: str) -> bool:
    """Update cached paper with full text."""
    cache = db.query(PaperCache).filter(PaperCache.external_id == external_id).first()
    if cache:
        cache.full_text = full_text
        cache.cached_at = __import__('datetime').datetime.utcnow()
        db.commit()
        return True
    return False


def search_cached_papers(db: Session, query: str, limit: int = 20) -> List[Dict]:
    """Search cached papers by title or abstract."""
    from sqlalchemy import or_
    results = db.query(PaperCache).filter(
        or_(
            PaperCache.title.ilike(f"%{query}%"),
            PaperCache.abstract.ilike(f"%{query}%")
        )
    ).limit(limit).all()
    
    return [{
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
        "full_text": r.full_text,
    } for r in results]
