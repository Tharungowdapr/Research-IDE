import asyncio
from core.llm_client import LLMClient
from agents.gap_miner.gap_agent import _analyze_single_paper

async def main():
    llm = LLMClient()
    paper = {"title": "Test", "abstract": "This is a test abstract.", "source": "arxiv", "id": "arxiv_1706.03762", "url": "https://arxiv.org/abs/1706.03762"}
    sem = asyncio.Semaphore(1)
    res = await _analyze_single_paper(paper, "AI", llm, sem)
    print("Result:", res)

asyncio.run(main())
