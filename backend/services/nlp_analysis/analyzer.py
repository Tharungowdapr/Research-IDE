"""
NLP Analysis Service
Deep linguistic + semantic analysis of user input.
Falls back to pure-Python when spaCy/KeyBERT/SentenceTransformers are unavailable.
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

# Check availability once at import time
_SPACY_AVAILABLE = False
_KEYBERT_AVAILABLE = False
_SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import spacy  # noqa: F401
    _SPACY_AVAILABLE = True
except ImportError:
    pass

try:
    from keybert import KeyBERT  # noqa: F401
    _KEYBERT_AVAILABLE = True
except ImportError:
    pass

try:
    from sentence_transformers import SentenceTransformer  # noqa: F401
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    pass

logger.info(
    "NLP packages: spacy=%s, keybert=%s, sentence_transformers=%s",
    _SPACY_AVAILABLE, _KEYBERT_AVAILABLE, _SENTENCE_TRANSFORMERS_AVAILABLE,
)

# Common English stop words for fallback
_STOP_WORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would shall should "
    "may might can could of in to for on with at by from as into through during before after "
    "above below between out off over under again further then once here there when where why "
    "how all both each few more most other some such no nor not only own same so than too "
    "very that this these those it its i me my we our you your he his she her they them their "
    "what which who whom if or because although while until about against".split()
)


async def _get_nlp():
    global _nlp
    if not _SPACY_AVAILABLE:
        return None
    if _nlp is None:
        async with _nlp_lock:
            if _nlp is None:
                try:
                    _nlp = spacy.load("en_core_web_sm")
                except Exception as e:
                    logger.warning("spaCy model load failed: %s", e)
                    return None
    return _nlp


async def _get_keybert():
    global _keybert
    if not _KEYBERT_AVAILABLE:
        return None
    if _keybert is None:
        async with _keybert_lock:
            if _keybert is None:
                try:
                    from keybert import KeyBERT as KB
                    _keybert = KB()
                except Exception as e:
                    logger.warning("KeyBERT init failed: %s", e)
                    return None
    return _keybert


async def _get_encoder():
    global _encoder
    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    if _encoder is None:
        async with _encoder_lock:
            if _encoder is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    _encoder = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception as e:
                    logger.warning("SentenceTransformers not available: %s", e)
    return _encoder


def _tokenize_simple(text: str) -> List[str]:
    """Split text into tokens (simple whitespace + punctuation)."""
    return re.findall(r"\b\w+\b", text)


def _sentences_simple(text: str) -> List[str]:
    """Split text into sentences using regex."""
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]


def _noun_phrases_simple(text: str) -> List[str]:
    """Extract simple noun-phrase-like chunks from text."""
    words = text.split()
    phrases = []
    current = []
    for w in words:
        stripped = w.strip(".,;:!?()[]{}\"'")
        if not stripped:
            if current:
                phrases.append(" ".join(current))
                current = []
            continue
        if stripped[0].isupper() or (not stripped.isalpha()):
            current.append(stripped)
        else:
            if current:
                phrases.append(" ".join(current))
                current = []
    if current:
        phrases.append(" ".join(current))
    return [p for p in phrases if len(p.split()) <= 5 and len(p) > 2]


def _extract_entities_simple(text: str) -> List[Dict]:
    """Extract named entities using simple heuristics (capitalized phrases, acronyms, patterns)."""
    entities = []
    seen = set()

    # Acronyms (e.g., NLP, CNN, LSTM)
    for m in re.finditer(r'\b([A-Z]{2,})\b', text):
        val = m.group(1)
        if val not in seen and val not in ("THE", "AND", "FOR", "WITH", "FROM"):
            entities.append({"text": val, "label": "TECHNOLOGY", "label_name": "Technology"})
            seen.add(val)

    # Capitalized multi-word phrases
    for m in re.finditer(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', text):
        val = m.group(1)
        if val not in seen:
            entities.append({"text": val, "label": "ORG", "label_name": "Organization"})
            seen.add(val)

    # Years
    for m in re.finditer(r'\b((?:19|20)\d{2})\b', text):
        val = m.group(1)
        if val not in seen:
            entities.append({"text": val, "label": "DATE", "label_name": "Date"})
            seen.add(val)

    # Single capitalized words (potential proper nouns)
    for m in re.finditer(r'\b([A-Z][a-z]{2,})\b', text):
        val = m.group(1)
        if val not in seen and val not in ("This", "That", "The", "When", "Where", "How", "What"):
            entities.append({"text": val, "label": "PERSON", "label_name": "Person"})
            seen.add(val)

    return entities[:20]


def _extract_keyphrases_simple(text: str, top_n: int = 15) -> List[Dict]:
    """Extract keyphrases using simple TF-based scoring."""
    words = _tokenize_simple(text.lower())
    # Filter stop words and short words
    content_words = [w for w in words if w not in _STOP_WORDS and len(w) > 2]

    # Count frequencies
    freq = {}
    for w in content_words:
        freq[w] = freq.get(w, 0) + 1

    # Score bigrams and trigrams too
    bigrams = {}
    trigrams = {}
    for i in range(len(content_words) - 1):
        bg = f"{content_words[i]} {content_words[i+1]}"
        bigrams[bg] = bigrams.get(bg, 0) + 1
    for i in range(len(content_words) - 2):
        tg = f"{content_words[i]} {content_words[i+1]} {content_words[i+2]}"
        trigrams[tg] = trigrams.get(tg, 0) + 1

    # Combine and score
    max_freq = max(freq.values()) if freq else 1
    scored = []
    for word, count in freq.items():
        scored.append((word, round(count / max_freq, 3)))
    for phrase, count in bigrams.items():
        if count >= 1 and len(phrase) > 5:
            scored.append((phrase, round(count / max_freq * 1.2, 3)))
    for phrase, count in trigrams.items():
        if count >= 1 and len(phrase) > 8:
            scored.append((phrase, round(count / max_freq * 1.3, 3)))

    # Sort by score, deduplicate
    scored.sort(key=lambda x: x[1], reverse=True)
    seen = set()
    results = []
    for phrase, score in scored:
        if phrase not in seen:
            seen.add(phrase)
            results.append({"phrase": phrase, "score": score})
            if len(results) >= top_n:
                break

    return results


async def analyze_text(text: str, llm: Optional[LLMClient] = None) -> Dict:
    """Run full NLP analysis pipeline on input text.

    Uses spaCy when available, falls back to pure-Python otherwise.
    """
    nlp = await _get_nlp()
    text = text.strip()

    results = {}

    # 1. Basic stats
    tokens = _tokenize_simple(text)
    sentences = _sentences_simple(text)

    if nlp:
        doc = nlp(text)
        results["stats"] = {
            "tokens": len(doc),
            "sentences": len(list(doc.sents)),
            "characters": len(text),
        }

        # Named Entities (spaCy)
        entities = []
        for ent in doc.ents:
            entities.append({"text": ent.text, "label": ent.label_, "label_name": _label_name(ent.label_)})
        results["entities"] = entities[:20]
    else:
        results["stats"] = {
            "tokens": len(tokens),
            "sentences": len(sentences),
            "characters": len(text),
        }
        results["entities"] = _extract_entities_simple(text)

    # 3. Keyphrases (KeyBERT when available, else TF-based)
    if _KEYBERT_AVAILABLE:
        try:
            kw_model = await _get_keybert()
            if kw_model:
                keywords = kw_model.extract_keywords(
                    text,
                    keyphrase_ngram_range=(1, 4),
                    stop_words="english",
                    top_n=15,
                )
                results["keyphrases"] = [{"phrase": k, "score": round(s, 3)} for k, s in keywords]
            else:
                results["keyphrases"] = _extract_keyphrases_simple(text)
        except Exception as e:
            logger.warning("KeyBERT failed: %s", e)
            results["keyphrases"] = _extract_keyphrases_simple(text)
    else:
        results["keyphrases"] = _extract_keyphrases_simple(text)

    # 4. Embedding (SentenceTransformers when available)
    if _SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            encoder = await _get_encoder()
            if encoder:
                vec = encoder.encode(text)
                results["embedding"] = vec.tolist()
            else:
                results["embedding"] = []
        except Exception as e:
            logger.warning("Embedding failed: %s", e)
            results["embedding"] = []
    else:
        results["embedding"] = []

    # 5. Domain classification (always rule-based, works with or without spaCy)
    results["domain"] = _classify_domain(text)

    # 6. Query expansion
    results["search_queries"] = await _generate_queries(text, nlp, llm)

    # 7. Summary
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


def _classify_domain(text: str, doc=None) -> Dict:
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


async def _generate_queries(text: str, nlp, llm: Optional[LLMClient]) -> List[str]:
    if llm:
        try:
            prompt = f"""Given this research topic, generate exactly 5 search queries for finding academic papers.

Topic: {text}

Return a JSON array of 5 strings, each a detailed search query.
Use the format: ["query1", "query2", "query3", "query4", "query5"]"""
            raw = await llm.complete(prompt, json_mode=True)
            import json
            clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
            start = clean.find("[")
            end = clean.rfind("]") + 1
            if start != -1 and end > start:
                queries = json.loads(clean[start:end])
                if isinstance(queries, list) and len(queries) >= 3:
                    return queries[:8]
        except Exception:
            logger.warning("LLM query expansion failed, using rule-based")

    # Fallback: extract key terms
    if nlp:
        doc = nlp(text)
        chunks = list(doc.noun_chunks)
        key_terms = [c.text for c in chunks if len(c.text.split()) <= 5][:10]
        if len(key_terms) < 3:
            key_terms = [tok.text for tok in doc if not tok.is_stop and tok.is_alpha][:10]
    else:
        # Pure-Python fallback: use significant words
        words = _tokenize_simple(text)
        key_terms = [w for w in words if w.lower() not in _STOP_WORDS and len(w) > 2][:10]
        # Also add noun phrases
        phrases = _noun_phrases_simple(text)
        key_terms = phrases[:5] + key_terms[:5]

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
