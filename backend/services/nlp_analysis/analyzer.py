"""
NLP Analysis Service
Deep linguistic + semantic analysis of user input using spaCy, KeyBERT, SentenceTransformers
"""

import re
import logging
import asyncio
from typing import Dict, List, Optional
from core.llm_client import LLMClient

logger = logging.getLogger(__name__)

# Lazy-loaded singletons with thread safety
_nlp = None
_keybert = None
_encoder = None
_nlp_lock = asyncio.Lock()
_keybert_lock = asyncio.Lock()
_encoder_lock = asyncio.Lock()


async def _get_nlp():
    global _nlp
    if _nlp is None:
        async with _nlp_lock:
            if _nlp is None:
                import spacy
                _nlp = spacy.load("en_core_web_sm")
    return _nlp


async def _get_keybert():
    global _keybert
    if _keybert is None:
        async with _keybert_lock:
            if _keybert is None:
                from keybert import KeyBERT
                _keybert = KeyBERT()
    return _keybert


async def _get_encoder():
    global _encoder
    if _encoder is None:
        async with _encoder_lock:
            if _encoder is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _encoder = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception:
                    logger.warning("SentenceTransformers not available, embeddings disabled")
    return _encoder


async def analyze_text(text: str, llm: Optional[LLMClient] = None) -> Dict:
    """Run full NLP analysis pipeline on input text."""
    nlp = await _get_nlp()
    doc = nlp(text.strip())

    results = {}

    # 1. Basic stats
    results["stats"] = {
        "tokens": len(doc),
        "sentences": len(list(doc.sents)),
        "characters": len(text),
    }

    # 2. Named Entities
    entities = []
    for ent in doc.ents:
        entities.append({"text": ent.text, "label": ent.label_, "label_name": _label_name(ent.label_)})
    results["entities"] = entities[:20]

    # 3. Keyphrases (KeyBERT — up to 15)
    try:
        kw_model = await _get_keybert()
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 4),
            stop_words="english",
            top_n=15,
        )
        results["keyphrases"] = [{"phrase": k, "score": round(s, 3)} for k, s in keywords]
    except Exception as e:
        logger.warning(f"KeyBERT failed: {e}")
        results["keyphrases"] = []

    # 4. Embedding (SentenceTransformers — full 384 dimensions)
    try:
        encoder = await _get_encoder()
        if encoder:
            vec = encoder.encode(text)
            results["embedding"] = vec.tolist()
        else:
            results["embedding"] = []
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        results["embedding"] = []

    # 5. Domain classification (rule-based + LLM if available)
    results["domain"] = _classify_domain(text, doc)

    # 6. Query expansion (LLM if available, fallback rule-based)
    results["search_queries"] = await _generate_queries(text, doc, llm)

    # 7. Summary (LLM if available)
    results["summary"] = await _generate_summary(text, llm)

    return results


def _label_name(label: str) -> str:
    labels = {
        "PERSON": "Person", "ORG": "Organization", "GPE": "Location",
        "PRODUCT": "Product/Model", "TECHNOLOGY": "Technology",
        "FIELD": "Field of Study", "METHOD": "Method/Algorithm",
        "DATASET": "Dataset", "METRIC": "Metric",
    }
    return labels.get(label, label.replace("_", " ").title())


def _extract_dep_children(token, depth=0, max_depth=3):
    if depth >= max_depth:
        return {"word": token.text, "dep": token.dep_, "children": []}
    children = []
    for child in token.children:
        children.append(_extract_dep_children(child, depth + 1, max_depth))
    return {"word": token.text, "dep": token.dep_, "tag": token.pos_, "children": children}


def _classify_domain(text: str, doc) -> Dict:
    text_lower = text.lower()

    domains = {
        "Natural Language Processing": [
            "nlp", "language", "text", "sentiment", "translation", "summarization", "ner",
            "named entity", "question answering", "relation extraction", "token", "embedding",
        ],
        "Computer Vision": [
            "image", "vision", "object detection", "segmentation", "facial", "video",
            "cnn", "convolution", "visual", "captioning",
        ],
        "Machine Learning": [
            "machine learning", "classification", "regression", "clustering",
            "supervised", "unsupervised", "feature", "predict",
        ],
        "Deep Learning": [
            "deep learning", "neural network", "transformer", "attention", "lstm",
            "gru", "rnn", "bert", "gpt", "diffusion", "gan",
        ],
        "Cybersecurity": [
            "security", "cyber", "malware", "intrusion", "encryption", "privacy",
            "vulnerability", "authentication", "firewall",
        ],
        "Cloud Computing": [
            "cloud", "kubernetes", "docker", "container", "microservice",
            "serverless", "aws", "azure", "devops",
        ],
        "Data Science": [
            "data science", "analytics", "visualization", "dashboard",
            "etl", "data pipeline", "big data",
        ],
        "Platform Engineering": [
            "platform engineering", "infrastructure", "terraform", "ci/cd",
            "platform", "internal developer platform",
        ],
        "Blockchain": [
            "blockchain", "smart contract", "ethereum", "web3", "decentralized",
            "cryptocurrency", "defi",
        ],
        "FinTech": [
            "finance", "financial", "stock", "trading", "banking",
            "market prediction", "credit", "fraud detection",
        ],
    }

    scores = {}
    matched_keywords = {}
    for domain, keywords in domains.items():
        score = 0
        matched = []
        for kw in keywords:
            if kw in text_lower:
                score += 1
                matched.append(kw)
        if score > 0:
            scores[domain] = score
            matched_keywords[domain] = matched

    if scores:
        best = max(scores, key=scores.get)
        return {
            "broad": best,
            "confidence": round(min(scores[best] / 10, 0.95), 2),
            "matched_keywords": matched_keywords.get(best, []),
        }

    return {"broad": "General", "confidence": 0.3, "matched_keywords": []}


async def _generate_queries(text: str, doc, llm: Optional[LLMClient]) -> List[str]:
    if llm:
        try:
            prompt = f"""Given this research topic, generate exactly 5 search queries for finding academic papers.

Topic: {text}

Return a JSON array of 5 strings, each a detailed search query.
Use the format: ["query1", "query2", "query3", "query4", "query5"]"""
            raw = await llm.complete(prompt, json_mode=True)
            import json, re
            clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
            start = clean.find("[")
            end = clean.rfind("]") + 1
            if start != -1 and end > start:
                queries = json.loads(clean[start:end])
                if isinstance(queries, list) and len(queries) >= 3:
                    return queries[:8]
        except Exception:
            logger.warning("LLM query expansion failed, using rule-based")

    # Fallback: extract noun chunks as queries
    chunks = list(doc.noun_chunks)
    key_terms = [c.text for c in chunks if len(c.text.split()) <= 5][:10]
    if len(key_terms) < 3:
        key_terms = [tok.text for tok in doc if not tok.is_stop and tok.is_alpha][:10]
    queries = [" ".join(key_terms[:4])] if key_terms else [text[:100]]
    if len(key_terms) >= 4:
        queries.append(" ".join(key_terms[2:6]))
    if len(key_terms) >= 6:
        queries.append(" ".join(key_terms[4:8]))
    return queries[:5]


async def _generate_summary(text: str, llm: Optional[LLMClient]) -> str:
    if llm:
        try:
            prompt = f"""Summarize this research topic in exactly 2-3 sentences.
Focus on: what problem is being addressed, what approach is proposed, and what domain.

Topic: {text}"""
            return await llm.complete(prompt)
        except Exception:
            pass
    return text[:200]
