"""
Intent Extraction Service v2 — Deep NLP Analysis
Extracts rich linguistic and structural information from research descriptions.
"""

import json
import re
from typing import Optional
from core.llm_client import LLMClient
from core.utils import safe_parse_llm_json

INTENT_SYSTEM = """You are an expert NLP analyst and research assistant.
Perform deep linguistic analysis on the given research description.
Return ONLY valid JSON with no markdown, no commentary."""

INTENT_PROMPT = """Perform comprehensive NLP analysis on this research description:

"{text}"

Return this exact JSON structure with rich detail:
{{
  "domain": ["primary domain", "secondary domain if applicable"],
  "task": "specific ML/NLP/AI task being addressed",
  "problem_statement": "one clear sentence summarizing the core problem",

  "nlp_analysis": {{
    "morphological": {{
      "key_terms": ["term1", "term2"],
      "technical_morphemes": ["e.g. 'multi-lingual' splits to multi + lingual", "..."],
      "abbreviations_found": ["e.g. NLP=Natural Language Processing", "..."],
      "word_count": 0,
      "avg_word_length": 0.0
    }},
    "syntactic": {{
      "sentence_count": 0,
      "sentence_types": ["declarative", "interrogative", "imperative"],
      "main_verb_phrases": ["verb phrase 1", "verb phrase 2"],
      "noun_phrases": ["noun phrase 1", "noun phrase 2"],
      "dependency_patterns": ["subject-verb-object pattern identified", "..."],
      "complexity_level": "simple|moderate|complex"
    }},
    "semantic": {{
      "core_concepts": ["concept1", "concept2", "concept3"],
      "semantic_field": "the broad knowledge domain (e.g. biomedical NLP, computer vision, etc.)",
      "named_entities": [
        {{"text": "entity name", "type": "TECH|DATASET|METRIC|METHOD|ORG|REGION"}}
      ],
      "ambiguous_terms": [
        {{"term": "ambiguous word", "possible_meanings": ["meaning1", "meaning2"]}}
      ],
      "technical_level": "beginner|intermediate|advanced|expert"
    }},
    "pragmatic": {{
      "intent_type": "research_exploration|problem_solving|improvement|comparison|survey",
      "urgency_signals": ["urgent keyword found, e.g. 'real-time'", "..."],
      "implicit_assumptions": ["assumption 1 implied by the text", "assumption 2", "..."],
      "target_audience": "who this research is for",
      "speech_acts": ["asserting problem", "proposing solution", "requesting method"]
    }},
    "discourse": {{
      "coherence_score": 0.0,
      "topic_progression": ["topic introduced", "problem stated", "goal described"],
      "connective_words": ["however", "therefore", "because"],
      "text_structure": "problem-solution|background-method|motivation-approach"
    }}
  }},

  "constraints": {{
    "compute": "low|medium|high|unspecified",
    "data_availability": "scarce|moderate|abundant|unspecified",
    "real_time": true,
    "region": "specific region or null",
    "language": "specific language or multilingual or null",
    "domain_specific": "any specific domain constraint",
    "other": []
  }},

  "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],

  "pos_tags": [
    {{"word": "word1", "pos": "NN|VB|JJ|RB|etc", "importance": "high|medium|low"}}
  ],

  "tokenization_demo": {{
    "original_sentence": "first sentence from input",
    "word_tokens": ["token1", "token2"],
    "subword_tokens_bpe": ["sub1", "##word", "token2"],
    "sentence_tokens": ["sentence 1.", "sentence 2."],
    "char_ngrams_sample": ["3-gram examples from first word"]
  }},

  "stop_words_analysis": {{
    "total_words": 0,
    "stop_words_removed": ["the", "is", "of"],
    "content_words_kept": ["important1", "important2"],
    "reduction_percentage": 0.0
  }},

  "stemming_lemmatization": {{
    "examples": [
      {{"original": "word", "stemmed": "stem", "lemma": "lemma", "pos": "NN"}}
    ]
  }},

  "queries": [
    "specific search query 1",
    "specific search query 2",
    "specific search query 3"
  ],

  "target_audience": "who would benefit from this research",
  "expected_contribution": "what novel contribution is expected",
  "research_gap_hypothesis": "what gap this research likely addresses"
}}"""


async def extract_intent(text: str, llm: LLMClient) -> dict:
    """Extract rich NLP-annotated intent from research description."""
    prompt = INTENT_PROMPT.format(text=text.strip()[:2000])
    try:
        raw = await llm.complete(prompt, system=INTENT_SYSTEM, json_mode=True)
        result = safe_parse_llm_json(raw, default=None)
        if not result:
            raise ValueError("LLM returned empty or invalid JSON")
        result["raw_input"] = text
        # Ensure backwards compat fields exist
        result.setdefault("keywords", _extract_keywords_fallback(text))
        result.setdefault("queries", [text[:100]])
        result.setdefault("domain", ["AI/ML"])
        result.setdefault("task", "research")
        result.setdefault("problem_statement", text[:200])
        result.setdefault("nlp_analysis", _build_basic_nlp_analysis(text))
        result.setdefault("tokenization_demo", _build_tokenization_demo(text))
        result.setdefault("stop_words_analysis", _build_stopwords_analysis(text))
        result.setdefault("stemming_lemmatization", _build_stemming_demo(text))
        return result
    except Exception as e:
        print(f"[Intent LLM failed]: {e}")
        return _fallback_intent(text, error=str(e))


def _parse_json_response(raw: str) -> dict:
    clean = re.sub(r"```(?:json)?\s*", "", raw).strip().rstrip("`").strip()
    start = clean.find("{")
    end = clean.rfind("}") + 1
    if start != -1 and end > start:
        clean = clean[start:end]
    return json.loads(clean)


def _extract_keywords_fallback(text: str) -> list:
    stopwords = {"this","that","with","from","have","will","been","they","research",
                 "using","based","study","paper","model","data","which","their","about"}
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    seen = set()
    kws = []
    for w in words:
        if w not in stopwords and w not in seen:
            seen.add(w)
            kws.append(w)
    return kws[:8]


def _build_basic_nlp_analysis(text: str) -> dict:
    """Rule-based fallback NLP analysis when LLM is unavailable."""
    import re

    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # Simple stop word list
    stopwords_set = {"the","a","an","is","in","at","of","to","and","or","but","for",
                     "with","this","that","are","was","were","be","been","have","has",
                     "it","its","by","from","as","on","into","through","during","before"}

    word_tokens = [re.sub(r'[^a-zA-Z0-9]', '', w) for w in words if w]
    content_words = [w.lower() for w in word_tokens if w.lower() not in stopwords_set and len(w) > 2]

    # Named entity detection (simple patterns)
    entities = []
    tech_patterns = {
        r'\bBERT\b|\bGPT\b|\bT5\b|\bLLM\b|\bCNN\b|\bRNN\b|\bLSTM\b|\bTransformer\b': 'METHOD',
        r'\bImageNet\b|\bSQuAD\b|\bGLUE\b|\bCOCO\b|\bWikiText\b': 'DATASET',
        r'\bF1\b|\bBLEU\b|\bROUGE\b|\baccuracy\b|\bperplexity\b': 'METRIC',
        r'\bIndia\b|\bChina\b|\bUSA\b|\bAfrica\b|\bEurope\b|\bAsia\b': 'REGION',
    }
    for pattern, ent_type in tech_patterns.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            entities.append({"text": match.group(), "type": ent_type})

    return {
        "morphological": {
            "key_terms": content_words[:8],
            "technical_morphemes": _find_morphemes(text),
            "abbreviations_found": _find_abbreviations(text),
            "word_count": len(words),
            "avg_word_length": round(sum(len(w) for w in word_tokens if w) / max(len(word_tokens), 1), 1),
        },
        "syntactic": {
            "sentence_count": len(sentences),
            "sentence_types": ["declarative"],
            "main_verb_phrases": _extract_verb_phrases(text),
            "noun_phrases": _extract_noun_phrases(text),
            "dependency_patterns": ["Subject → Verb → Object structure detected"],
            "complexity_level": "complex" if len(words) > 80 else "moderate" if len(words) > 40 else "simple",
        },
        "semantic": {
            "core_concepts": content_words[:5],
            "semantic_field": _detect_semantic_field(text),
            "named_entities": entities[:6],
            "ambiguous_terms": _find_ambiguous_terms(text),
            "technical_level": _detect_technical_level(text),
        },
        "pragmatic": {
            "intent_type": _detect_intent_type(text),
            "urgency_signals": _find_urgency_signals(text),
            "implicit_assumptions": _find_implicit_assumptions(text),
            "target_audience": "ML/AI researchers and practitioners",
            "speech_acts": ["problem assertion", "solution proposal"],
        },
        "discourse": {
            "coherence_score": round(min(len(sentences) / 5, 1.0), 2),
            "topic_progression": [s[:60] + "..." if len(s) > 60 else s for s in sentences[:3]],
            "connective_words": [w for w in ["however","therefore","because","although","while","since","thus"] if w in text.lower()],
            "text_structure": "problem-solution" if any(w in text.lower() for w in ["problem","challenge","issue","limitation"]) else "motivation-approach",
        },
    }


def _build_tokenization_demo(text: str) -> dict:
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    first_sentence = sentences[0] if sentences else text[:100]
    word_tokens = re.findall(r'\b\w+\b|[^\w\s]', first_sentence)

    # Simple BPE-like simulation
    def fake_bpe(word):
        if len(word) <= 4:
            return [word]
        mid = len(word) // 2
        return [word[:mid], f"##{word[mid:]}"]

    bpe_tokens = []
    for tok in word_tokens[:8]:
        if tok.isalpha() and len(tok) > 5:
            bpe_tokens.extend(fake_bpe(tok))
        else:
            bpe_tokens.append(tok)

    first_word = re.findall(r'\b\w+\b', text)[0] if text else "example"
    char_ngrams = [first_word[i:i+3] for i in range(min(len(first_word)-2, 5))]

    return {
        "original_sentence": first_sentence[:120],
        "word_tokens": word_tokens[:15],
        "subword_tokens_bpe": bpe_tokens[:12],
        "sentence_tokens": [s[:80] for s in sentences[:4]],
        "char_ngrams_sample": char_ngrams,
    }


def _build_stopwords_analysis(text: str) -> dict:
    import re
    stopwords = {"the","a","an","is","in","at","of","to","and","or","but","for",
                 "with","this","that","are","was","were","be","been","have","has",
                 "it","its","by","from","as","on","into","we","our","their","which",
                 "i","you","he","she","they","my","your","his","her","its","us"}
    words = re.findall(r'\b[a-z]+\b', text.lower())
    stops = [w for w in words if w in stopwords]
    content = [w for w in words if w not in stopwords and len(w) > 2]
    total = len(words)
    return {
        "total_words": total,
        "stop_words_removed": list(dict.fromkeys(stops))[:10],
        "content_words_kept": list(dict.fromkeys(content))[:10],
        "reduction_percentage": round((len(stops) / max(total, 1)) * 100, 1),
    }


def _build_stemming_demo(text: str) -> dict:
    import re
    _stemming_rules = [
        (r'ing$', ''), (r'tion$', 'te'), (r'ness$', ''), (r'ment$', ''),
        (r'ful$', ''), (r'less$', ''), (r'ly$', ''), (r'er$', ''),
        (r'ed$', ''), (r'es$', ''), (r's$', ''), (r'ization$', 'ize'),
    ]
    _lemma_map = {
        'running':'run','predicting':'predict','improving':'improve',
        'using':'use','training':'train','learning':'learn',
        'detecting':'detect','generating':'generate','analyzing':'analyze',
        'processing':'process','classifying':'classify','identifying':'identify',
    }
    _pos_map = {
        r'ing$':'VBG', r'tion$':'NN', r'ness$':'NN', r'ment$':'NN',
        r'ful$':'JJ', r'less$':'JJ', r'ly$':'RB', r'ed$':'VBD',
    }

    words = list(dict.fromkeys(re.findall(r'\b[a-z]{5,}\b', text.lower())))[:8]
    examples = []
    for word in words:
        stem = word
        for pattern, replacement in _stemming_rules:
            if re.search(pattern, word):
                stem = re.sub(pattern, replacement, word)
                break
        lemma = _lemma_map.get(word, stem if len(stem) > 2 else word)
        pos = "NN"
        for pattern, tag in _pos_map.items():
            if re.search(pattern, word):
                pos = tag
                break
        if stem != word or lemma != word:
            examples.append({"original": word, "stemmed": stem, "lemma": lemma, "pos": pos})
    return {"examples": examples[:6]}


def _find_morphemes(text: str) -> list:
    compound_words = re.findall(r'\b\w+[-_]\w+\b', text)
    prefixed = re.findall(r'\b(?:pre|post|multi|bi|tri|semi|anti|non|re|un|sub|super)\w+\b', text, re.I)
    result = []
    for w in compound_words[:3]:
        parts = re.split(r'[-_]', w)
        result.append(f"'{w}' → {' + '.join(parts)}")
    for w in prefixed[:3]:
        m = re.match(r'(pre|post|multi|bi|tri|semi|anti|non|re|un|sub|super)', w, re.I)
        if m:
            prefix = m.group(1)
            base = w[len(prefix):]
            result.append(f"'{w}' → prefix '{prefix}' + base '{base}'")
    return result[:4] if result else ["No compound morphemes detected in input"]


def _find_abbreviations(text: str) -> list:
    abbrevs = re.findall(r'\b[A-Z]{2,6}\b', text)
    known = {
        "NLP": "Natural Language Processing", "ML": "Machine Learning",
        "AI": "Artificial Intelligence", "DL": "Deep Learning",
        "CNN": "Convolutional Neural Network", "RNN": "Recurrent Neural Network",
        "LSTM": "Long Short-Term Memory", "BERT": "Bidirectional Encoder Representations from Transformers",
        "GPT": "Generative Pre-trained Transformer", "CV": "Computer Vision",
        "OCR": "Optical Character Recognition", "ASR": "Automatic Speech Recognition",
        "NER": "Named Entity Recognition", "POS": "Part-of-Speech",
        "IR": "Information Retrieval", "QA": "Question Answering",
        "MT": "Machine Translation", "IE": "Information Extraction",
    }
    result = []
    seen = set()
    for abbr in abbrevs:
        if abbr not in seen:
            seen.add(abbr)
            if abbr in known:
                result.append(f"{abbr} = {known[abbr]}")
            else:
                result.append(abbr)
    return result[:6]


def _extract_verb_phrases(text: str) -> list:
    patterns = [
        r'\b(?:predict|classify|detect|generate|improve|analyze|train|evaluate|compare|propose|develop|implement|use|apply|build|create)\w*\b'
    ]
    found = []
    for p in patterns:
        found.extend(re.findall(p, text, re.I))
    return list(dict.fromkeys(found))[:5]


def _extract_noun_phrases(text: str) -> list:
    patterns = re.findall(r'\b(?:[A-Z][a-z]+ )?(?:neural network|language model|deep learning|machine learning|natural language|computer vision|data set|benchmark|baseline|attention mechanism|transformer|embedding|classification|detection|generation|translation|summarization)\b', text, re.I)
    return list(dict.fromkeys(patterns))[:5]


def _detect_semantic_field(text: str) -> str:
    fields = {
        "biomedical NLP": ["medical","clinical","health","patient","disease","drug","genomic"],
        "computer vision": ["image","vision","visual","pixel","detection","segmentation","object"],
        "speech processing": ["speech","audio","voice","spoken","acoustic","phoneme"],
        "information retrieval": ["search","retrieval","ranking","query","document","index"],
        "machine translation": ["translation","multilingual","cross-lingual","language pair"],
        "sentiment analysis": ["sentiment","opinion","emotion","review","stance","subjectivity"],
        "question answering": ["question","answer","reading comprehension","factoid","QA"],
        "text generation": ["generation","summarization","story","creative","dialogue","chatbot"],
        "low-resource NLP": ["low-resource","under-resourced","few-shot","zero-shot","scarce data"],
        "general NLP/ML": []
    }
    text_l = text.lower()
    for field, keywords in fields.items():
        if any(k in text_l for k in keywords):
            return field
    return "general NLP/ML"


def _find_ambiguous_terms(text: str) -> list:
    ambiguous = {
        "model": ["statistical model", "deep learning model", "language model"],
        "bank": ["financial institution", "river bank", "data bank"],
        "plant": ["manufacturing facility", "living organism"],
        "network": ["neural network", "computer network", "social network"],
        "classification": ["text classification", "image classification", "biological classification"],
        "translation": ["machine translation", "code translation", "cultural translation"],
        "corpus": ["text corpus", "anatomical corpus"],
        "token": ["word token", "authentication token"],
        "attention": ["attention mechanism", "human attention"],
        "embedding": ["word embedding", "physical embedding"],
    }
    result = []
    text_l = text.lower()
    for term, meanings in ambiguous.items():
        if term in text_l:
            result.append({"term": term, "possible_meanings": meanings})
    return result[:3]


def _detect_technical_level(text: str) -> str:
    expert_terms = ['transformer','attention mechanism','backpropagation','gradient descent',
                    'perplexity','BLEU','cross-entropy','fine-tuning','tokenization','embedding']
    intermediate_terms = ['neural network','deep learning','classification','regression',
                          'dataset','training','model','accuracy','precision','recall']
    expert_count = sum(1 for t in expert_terms if t.lower() in text.lower())
    inter_count = sum(1 for t in intermediate_terms if t.lower() in text.lower())
    if expert_count >= 2:
        return "expert"
    elif expert_count == 1 or inter_count >= 3:
        return "advanced"
    elif inter_count >= 1:
        return "intermediate"
    return "beginner"


def _detect_intent_type(text: str) -> str:
    text_l = text.lower()
    if any(w in text_l for w in ["survey","review","overview","summarize existing"]):
        return "survey"
    if any(w in text_l for w in ["compare","versus","vs","better than","outperform"]):
        return "comparison"
    if any(w in text_l for w in ["improve","enhance","optimize","boost","increase"]):
        return "improvement"
    if any(w in text_l for w in ["solve","address","tackle","fix","handle"]):
        return "problem_solving"
    return "research_exploration"


def _find_urgency_signals(text: str) -> list:
    signals = []
    urgent_words = {"real-time":"requires low latency","online":"streaming/live processing",
                    "fast":"speed is a priority","efficient":"computational efficiency needed",
                    "scalable":"must handle large scale","lightweight":"resource-constrained",
                    "low-resource":"limited data/compute","edge":"on-device deployment"}
    text_l = text.lower()
    for word, meaning in urgent_words.items():
        if word in text_l:
            signals.append(f"'{word}' → {meaning}")
    return signals[:4]


def _find_implicit_assumptions(text: str) -> list:
    assumptions = []
    text_l = text.lower()
    if "english" not in text_l and "language" in text_l:
        assumptions.append("English may be assumed as primary language")
    if "gpu" not in text_l and "compute" not in text_l:
        assumptions.append("Standard computing resources assumed available")
    if "label" not in text_l and "annotate" not in text_l:
        assumptions.append("Labeled training data assumed to be obtainable")
    if "deploy" not in text_l and "production" not in text_l:
        assumptions.append("Research/experimental setting, not production deployment")
    if any(w in text_l for w in ["improve","better","outperform"]):
        assumptions.append("Existing baseline systems are available for comparison")
    return assumptions[:4]


def _fallback_intent(text: str, error: str = "") -> dict:
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
    stopwords = {"this","that","with","from","have","will","been","they","research",
                 "using","based","study","paper","model","data","which","their"}
    keywords = list(dict.fromkeys([w for w in words if w not in stopwords]))[:8]
    return {
        "domain": ["general AI/ML"],
        "task": "research",
        "problem_statement": text[:200],
        "nlp_analysis": _build_basic_nlp_analysis(text),
        "tokenization_demo": _build_tokenization_demo(text),
        "stop_words_analysis": _build_stopwords_analysis(text),
        "stemming_lemmatization": _build_stemming_demo(text),
        "constraints": {"compute":"unspecified","data_availability":"unspecified",
                        "real_time":False,"region":None,"language":None,
                        "domain_specific":"","other":[]},
        "keywords": keywords[:5],
        "pos_tags": [],
        "queries": [text[:100]],
        "target_audience": "researchers",
        "expected_contribution": "novel approach",
        "research_gap_hypothesis": "addresses identified gap in literature",
        "raw_input": text,
        "_fallback": True,
        "_error": error,
    }
