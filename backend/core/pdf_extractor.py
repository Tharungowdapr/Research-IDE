"""
PDF and Full-Text Extractor
Fetches full text from arXiv HTML/PDF, or direct PDF links.
"""

import httpx
import asyncio
import io
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None
from bs4 import BeautifulSoup
from typing import Optional
import logging

logger = logging.getLogger(__name__)


async def extract_full_text(paper: dict) -> str:
    """Attempt to get the full text of a paper. Fall back to abstract if all fails."""
    source = paper.get("source", "")
    pid = paper.get("id", "")
    url = paper.get("url", "")

    # 1. arXiv: Try ar5iv HTML first, then PDF
    if source == "arxiv" or "arxiv.org" in url:
        # Extract arXiv ID handling versions (v2) and new-style IDs
        raw_id = pid.replace("arxiv_", "") if pid.startswith("arxiv_") else url.split("/")[-1]
        raw_id = raw_id.replace(".pdf", "").split("v")[0]  # Remove version suffix
        
        # Try ar5iv HTML (fast and clean)
        ar5iv_url = f"https://ar5iv.labs.arxiv.org/html/{raw_id}"
        html_text = await _fetch_html_text(ar5iv_url)
        if html_text and len(html_text) > 1000:
            return html_text
            
        # Fallback to arXiv PDF
        pdf_url = f"https://arxiv.org/pdf/{raw_id}.pdf"
        pdf_text = await _fetch_pdf_text(pdf_url)
        if pdf_text and len(pdf_text) > 500:
            return pdf_text

    # 2. General PDF if URL ends with .pdf
    if url.endswith(".pdf"):
        pdf_text = await _fetch_pdf_text(url)
        if pdf_text and len(pdf_text) > 500:
            return pdf_text
            
    # 3. If openalex or semanticscholar provided a pdf_url (we might need to check if we stored one)
    if paper.get("pdf_url"):
        pdf_text = await _fetch_pdf_text(paper["pdf_url"])
        if pdf_text and len(pdf_text) > 500:
            return pdf_text

    # Fallback to abstract if full text extraction fails
    return paper.get("abstract", "")


async def _fetch_html_text(url: str) -> Optional[str]:
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                # Remove non-content elements
                for el in soup(["script", "style", "nav", "header", "footer", "aside"]):
                    el.extract()
                # Remove ar5iv-specific noise
                for el in soup.select(".ltx_note, .ltx_equation, .ltx_title_bibliography"):
                    el.extract()
                # Extract only prose elements
                prose_elements = soup.find_all(["p", "h1", "h2", "h3", "h4", "h5", "h6", "li", "td", "th"])
                if prose_elements:
                    text = "\n".join(el.get_text(strip=True) for el in prose_elements if el.get_text(strip=True))
                else:
                    text = soup.get_text(separator="\n", strip=True)
                return text
    except Exception as e:
        print(f"[HTML Extract Error] {url}: {e}")
    return None


async def _fetch_pdf_text(url: str) -> Optional[str]:
    if not fitz:
        logger.warning(f"PyMuPDF not installed, skipping PDF extraction for {url}")
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200 and resp.content:
                pdf_stream = io.BytesIO(resp.content)
                doc = fitz.open(stream=pdf_stream, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text() + "\n"
                doc.close()
                return text
    except Exception as e:
        logger.error(f"[PDF Extract Error] {url}: {e}")
    return None

