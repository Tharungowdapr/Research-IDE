import asyncio
from core.pdf_extractor import extract_full_text
async def main():
    p = {"title": "Test Paper", "url": "https://arxiv.org/abs/1706.03762", "source": "arxiv", "id": "arxiv_1706.03762"}
    text = await extract_full_text(p)
    print(f"Extracted {len(text)} chars from {p['url']}")
    print(text[:200])
asyncio.run(main())
