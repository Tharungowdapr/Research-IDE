
import asyncio
import sys
import os
from sqlalchemy.orm import Session

# Add backend to path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal, engine, Base
from models.project import PaperCache
from services.retrieval.retrieval_service import _fetch_semantic_scholar, _fetch_arxiv

# Seed topics
TOPICS = [
    "Machine Learning",
    "Natural Language Processing",
    "Computer Vision",
    "Reinforcement Learning",
    "Graph Neural Networks",
    "Large Language Models",
    "Generative AI",
    "Bioinformatics",
    "Cybersecurity",
    "Robotics"
]

async def seed_papers():
    print("🚀 Starting paper seeding...")
    db: Session = SessionLocal()
    
    total_added = 0
    
    for topic in TOPICS:
        print(f"🔍 Fetching papers for: {topic}...")
        try:
            # Fetch from Semantic Scholar directly to avoid cache checks
            papers = await _fetch_semantic_scholar(topic, max_results=20)
            # Also try arXiv if it works
            arxiv_papers = await _fetch_arxiv(topic, max_results=10)
            papers.extend(arxiv_papers)
            
            for p_data in papers:
                # Check if already in cache
                existing = db.query(PaperCache).filter(PaperCache.external_id == p_data["id"]).first()
                if not existing:
                    paper = PaperCache(
                        external_id=p_data["id"],
                        title=p_data["title"],
                        abstract=p_data["abstract"],
                        authors=p_data["authors"],
                        year=p_data["year"],
                        citations=p_data["citations"],
                        source=p_data["source"],
                        url=p_data["url"],
                        methods=p_data.get("methods", []),
                        datasets=p_data.get("datasets", []),
                        limitations=p_data.get("limitations", [])
                    )
                    db.add(paper)
                    total_added += 1
            
            db.commit()
            print(f"✅ Added/Updated papers for {topic}")
            # Small sleep to be nice to APIs
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"❌ Error fetching for {topic}: {e}")
            db.rollback()

    db.close()
    print(f"\n🎉 Seeding complete! Added {total_added} new papers to the local dataset.")

if __name__ == "__main__":
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    asyncio.run(seed_papers())
