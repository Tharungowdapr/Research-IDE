# ResearchIDE — Viva / Evaluation Q&A

**Tharun Gowda A P — 1RV23AI114 — RVCE 2025-26**

---

## 1. NLP Core Concepts

### Q: What NLP library do you use and why?
**A:** spaCy (`en_core_web_sm`) for tokenisation, POS tagging, NER, and dependency parsing. It is fast, production-grade, and provides a pipeline architecture. KeyBERT is used on top for keyphrase extraction because it leverages BERT embeddings rather than simple TF-IDF, giving semantically aware keyphrases.

### Q: What is KeyBERT and how does it extract keywords?
**A:** KeyBERT uses a BERT-based encoder to embed both the document and n-gram candidates. It picks the candidates whose embeddings are closest (cosine similarity) to the document embedding. This is better than TF-IDF because it captures semantic similarity, not just frequency. We use `keyphrase_ngram_range=(1,4)` to find 1-to-4-word phrases.

### Q: Explain your sentence embedding model.
**A:** We use `all-MiniLM-L6-v2` from SentenceTransformers. It produces 384-dimensional dense vectors optimised for semantic similarity tasks. The model is distilled from a larger model, making it fast while retaining quality. We use it to embed the user query; in future we will embed paper abstracts too for similarity-based retrieval.

### Q: What is the difference between tokenisation and lemmatisation?
**A:** Tokenisation splits text into individual tokens (words, punctuation). Lemmatisation reduces each token to its base form (e.g., "transformers" → "transformer", "running" → "run") using morphological analysis. Lemmatisation is important for search query expansion so that "learning" and "learned" map to the same search term.

### Q: What NER entities does your system extract?
**A:** spaCy `en_core_web_sm` extracts: PERSON, ORG, GPE (location), PRODUCT. For scientific text, these are mapped to researcher names, organisations, locations, and product/model names. We acknowledge that `en_core_web_sm` is trained on news text, not scientific papers, so a domain-specific model (scispaCy) would give better results.

### Q: How does your domain classification work?
**A:** We use a rule-based keyword matching approach across 10 domains (NLP, CV, ML, Deep Learning, Cybersecurity, etc.). The domain with the highest keyword match count wins. Confidence is `score/10`, capped at 0.95. This is fast and interpretable but brittle — a zero-shot classifier (e.g., `facebook/bart-large-mnli`) would be more robust.

### Q: What is TF-IDF and does your system use it?
**A:** TF-IDF (Term Frequency-Inverse Document Frequency) measures word importance: high if a word is frequent in a document but rare across all documents. Our relevance scoring in `retrieval_service._relevance_score()` is a simplified version — it checks which query terms appear in the paper title/abstract without IDF weighting. A proper TF-IDF or BM25 implementation would improve retrieval ranking.

### Q: Explain the difference between extractive and abstractive summarisation.
**A:** Extractive: selects existing sentences from the source text. Abstractive: generates new sentences that paraphrase the source (like a human summary). Our `_generate_summary()` uses an LLM (abstractive), which can produce fluent summaries but may hallucinate details not in the original text.

### Q: What is cosine similarity? Where do you use it?
**A:** Cosine similarity measures the angle between two vectors: `sim = (A·B) / (|A||B|)`. Value range: -1 to 1, where 1 = identical direction. We embed the user query with SentenceTransformers and compute cosine similarity against paper abstract embeddings to rank papers.

### Q: What is a dependency parse tree?
**A:** A dependency parse tree represents grammatical relationships between words. Each word points to its syntactic head with a labelled edge (e.g., `nsubj` = nominal subject, `dobj` = direct object). We extract the root word and top 3 levels of the tree. The root is typically the main verb, which indicates the core action the user wants.

### Q: What is the difference between POS tagging and NER?
**A:** POS tagging assigns grammatical categories (NOUN, VERB, ADJ, etc.) to each token. NER identifies and classifies named entities (PERSON, ORG, LOCATION) in the text. POS operates on each token independently; NER identifies multi-token spans. We use both: POS for query analysis, NER for identifying research-relevant entities.

### Q: Why do you truncate abstracts to 800 characters?
**A:** LLM prompts have token limits. With 25 papers × full abstract = potentially 50,000 tokens in a single prompt — exceeding most model context windows. 800 chars ≈ 120 tokens per abstract × 25 papers = 3,000 tokens, manageable. The trade-off is information loss; we compensate by fetching full text for the top papers.

---

## 2. LLM & Prompt Engineering

### Q: What is prompt engineering?
**A:** Prompt engineering is the craft of structuring input text to an LLM to elicit the desired output. Techniques used: (1) System prompts to set persona ("You are a scientific claim extractor"); (2) JSON mode to enforce structured output; (3) Few-shot examples via the output schema in the prompt; (4) Chain-of-thought by decomposing the task across 3 passes (Claim → Gap → Score).

### Q: What is the 3-pass gap analysis pipeline?
**A:** Pass 1 (Claim Extraction): LLM reads paper summaries and extracts specific claims, limitations, and future work statements as a JSON array. Pass 2 (Gap Identification): LLM reads all claims and identifies 10-15 research gaps. Pass 3 (Scoring): LLM scores each gap on addressability (can a researcher fix this in 6 months?) and impact. This decomposition reduces hallucination compared to asking one prompt to do everything.

### Q: What is the adversarial idea generation loop?
**A:** Round 1: Generator LLM creates 15 research ideas. Round 2: Critic LLM (instructed to be a "harsh NeurIPS reviewer") finds fatal flaws and assigns a `weakness_score` (1-10). Round 3: Defender LLM revises ideas where `weakness_score < 8` and `is_salvageable=True`. Ideas with `weakness_score ≥ 8` are discarded. This mimics peer review in a single pipeline run.

### Q: What is hallucination in LLMs and how do you handle it?
**A:** Hallucination: the LLM generates plausible-sounding but factually incorrect content. Our mitigations: (1) JSON mode forces structured output; (2) Tenacity retry with 3 attempts on parse failures; (3) Fallback to rule-based extraction when LLM JSON fails; (4) The critic pass catches logically flawed ideas. Remaining risk: gap `supporting_papers` field is not verified against actual retrieved papers.

### Q: Why do you use `json_mode=True` in your LLM calls?
**A:** `json_mode=True` instructs the LLM to output valid JSON only (supported by OpenAI, Groq, Gemini). This eliminates markdown fences, preamble text, and explanatory sentences that break `JSON.parse()`. We also do post-processing: strip ````json` fences, extract the first `[ ]` or `{ }` block, with a partial recovery fallback for truncated responses.

### Q: How do you handle LLM provider switching?
**A:** The `LLMClient` class accepts a provider enum (openai/anthropic/groq/gemini/cohere/ollama). Each provider has its own `_complete` method handling API-specific headers, request format, and response parsing. The `complete()` method routes to the correct handler. Users set their provider and API key in Settings; keys are AES-encrypted before DB storage.

---

## 3. Retrieval & Information Extraction

### Q: What APIs do you use for paper retrieval and why?
**A:** arXiv (CS/Math/Physics, free, XML API), Semantic Scholar (cross-domain, 200M papers, free GraphQL), OpenAlex (open replacement for Microsoft Academic, 240M works, inverted-index abstracts), PapersWithCode (ML + code links). We chose these for free access, broad coverage, and structured metadata including citation counts.

### Q: How does the inverted index abstract reconstruction work?
**A:** OpenAlex returns abstracts as an inverted index: `{word: [position1, position2, ...]}`. We reconstruct by creating a dict `{position: word}` and joining words sorted by position. This is because abstract text has copyright restrictions but position-indexed form is provided freely. Example: `{"the": [0,5], "cat": [1]}` → `{0:"the", 1:"cat", 5:"the"}` → `"the cat ... the"`.

### Q: Explain your paper deduplication approach.
**A:** We normalise each title by lowercasing, removing all non-alphanumeric characters, and taking the first 50 characters as a key. Papers sharing the same key are duplicates. This handles minor formatting differences but misses papers with very similar but not identical titles.

### Q: How do you score paper relevance?
**A:** Three-component weighted score: Relevance (0.5 weight) = fraction of query terms found in title+abstract; Recency (0.3) = year bracket score (5 tiers from current to 5+ years); Citations (0.2) = `min(count/200, 1.0)`. Final = 0.5R + 0.3Re + 0.2C.

### Q: What is full-text extraction and how does it work?
**A:** For arXiv papers, we first try ar5iv (HTML rendering of arXiv papers at `ar5iv.labs.arxiv.org`) which gives clean text. If that fails, we download the PDF via `arxiv.org/pdf/{id}.pdf` and extract text using PyMuPDF (fitz). PyMuPDF reads the PDF byte stream and extracts text page by page. Non-arXiv papers with `.pdf` URLs are also handled.

### Q: What is PDF parsing and what library do you use?
**A:** PDF parsing extracts machine-readable text from the binary PDF format. We use PyMuPDF (fitz): open the PDF bytes as a stream, iterate pages with `doc.page_count`, call `page.get_text()` for each page. PDF text extraction is imperfect — multi-column layouts, mathematical equations, and scanned PDFs cause errors.

---

## 4. System & Architecture Questions

### Q: Explain the backend architecture.
**A:** FastAPI (Python) with SQLAlchemy ORM on SQLite. Routes are split by domain: auth, project, pipeline, agents, system. The pipeline route orchestrates 13 sequential agents, streaming progress via Server-Sent Events (SSE). Each agent is a standalone async function that takes inputs and returns a JSON-serialisable dict. Outputs are persisted to the Output table keyed by `(project_id, output_type)`.

### Q: What is Server-Sent Events (SSE)?
**A:** SSE is a browser API where the server pushes events over a persistent HTTP connection. The client uses EventSource or `fetchEventSource`. Each event is `text/event-stream` format: `"data: {json}\n\n"`. Our pipeline streams stage progress so the user sees real-time updates without polling. Unlike WebSockets, SSE is unidirectional (server→client only) and HTTP-based.

### Q: Why FastAPI over Flask or Django?
**A:** FastAPI: native async/await support (critical for concurrent LLM + HTTP calls), automatic OpenAPI docs generation, Pydantic validation, and significantly faster than Flask. Django would be overkill for an API-only backend. Flask lacks native async and type safety.

### Q: How is authentication implemented?
**A:** JWT (JSON Web Token) with bcrypt password hashing. Login returns an access token (1h expiry) and refresh token (7d expiry). The access token is sent as Bearer in Authorization header. The `get_current_user` dependency decodes and validates the JWT on every protected route. User API keys for LLM providers are AES-encrypted using the `ENCRYPTION_KEY` before being stored in the DB.

### Q: What is your database schema?
**A:** Five tables: **User** (id, email, bcrypt_hash, name, skill_level, encrypted LLM keys), **Project** (id, user_id FK, title, input_text, status, current_stage), **Output** (id, project_id FK, output_type, data JSON), **UsageLog** (id, user_id FK, provider, model, prompt_tokens INT, completion_tokens INT, total_tokens INT, cost_usd FLOAT, energy_wh FLOAT), **PaperCache** (external_id, title, abstract, full_text, authors, year, citations, source, url), **PipelineLog** (project_id FK, stage, status, started_at, finished_at, output_size_bytes, error_message).

### Q: How do you handle concurrent LLM requests?
**A:** All LLM calls are async using `httpx.AsyncClient`. The tenacity `@retry` decorator retries up to 3 times with exponential backoff on transient failures. Gap analysis fetches full text for 15 papers concurrently via `asyncio.gather`. Independent pipeline stages (objectives+planner, data+code+experiments) also run concurrently, saving ~3 minutes per run.

---

## 5. What Would You Improve?

### Q: What is BM25 and is it better than your current retrieval?
**A:** BM25 (Best Match 25) is a probabilistic retrieval function that extends TF-IDF with document length normalisation and term saturation. It is the standard baseline in information retrieval. Our current relevance scoring is a binary keyword-presence check — weaker than BM25. Adding `rank_bm25` (Python library) over stored paper abstracts would improve retrieval quality significantly.

### Q: What is RAG and how does your project relate?
**A:** Retrieval-Augmented Generation (RAG): retrieve relevant documents, then pass them as context to an LLM to generate answers grounded in the retrieved text. Our entire pipeline is a domain-specific RAG system: we retrieve papers (retrieval), then feed them to agents that generate gaps, ideas, and the paper (augmented generation). We currently lack a vector store for semantic retrieval.

### Q: How would you add vector similarity search?
**A:** Store paper abstract embeddings (384-dim `all-MiniLM-L6-v2` vectors) in ChromaDB or pgvector. At retrieval time, embed the user query and find the k-nearest abstracts by cosine similarity. Combine with keyword search results (BM25) using Reciprocal Rank Fusion (RRF). This hybrid retrieval is the current state-of-the-art for RAG systems.

### Q: Why is `en_core_web_sm` not ideal for this domain?
**A:** `en_core_web_sm` is trained on OntoNotes (news articles, web text). Scientific papers have different vocabulary: acronyms (BERT, LSTM, IoU), domain-specific entities (datasets like ImageNet, methods like attention mechanism), and sentence structures. scispaCy models (trained on biomedical/scientific text) would give better tokenisation, NER, and dependency parsing.

### Q: How would you evaluate your NLP pipeline quality?
**A:** Keyword extraction: compare KeyBERT keyphrases against human-annotated keywords using Precision@K and NDCG. Domain classification: accuracy on a labelled dataset. Query expansion: measure if expanded queries retrieve more relevant papers (MRR, MAP). Retrieval: NDCG@10 comparing against a gold standard. Gap analysis: human evaluation rubric (specificity, evidence grounding, novelty).

---

## 6. Testing Results

### Q: What tests do you have and what do they cover?
**A:** We have unit tests covering:
- **Intent fallback** (`test_intent_fallback`): Verifies rule-based intent extraction returns keywords and queries
- **Paper deduplication** (`test_deduplication`): Tests title normalization and duplicate removal
- **Idea ranking** (`test_idea_ranking`): Validates novelty×feasibility scoring sorts correctly
- **Code fallback** (`test_code_fallback`): Ensures skeleton project structure has all 12 expected files
- **Gap defaults** (`test_gap_defaults`): Checks default gap structure has all required fields
- **Quality gate validation** (`test_quality_gate_valid_idea`, `test_quality_gate_invalid_idea`): Tests that the quality gate correctly validates/rejects ideas based on schema fields
- **Recency scoring** (`test_recency_score_current_year`, `test_recency_score_old_year`): Verifies year-bracket scoring
- **Relevance scoring** (`test_relevance_score_match`, `test_relevance_score_no_match`): Tests keyword overlap calculation
- **Citation weighting** (`test_citation_weight`): Checks min(count/200, 1.0) cap
- **Parse JSON list** (`test_parse_json_list_valid`, `test_parse_json_list_fallback`): Tests LLM response JSON parsing with recovery
- **Rule-based scoring** (`test_estimate_addressability`, `test_estimate_impact`): Tests Ollama fallback scoring
- **Rate limiting** (`test_rate_limit_allows`, `test_rate_limit_blocks`): Tests auth endpoint rate limiter

### Q: How do you run the tests?
**A:** `cd backend && python -m pytest tests/ -v`. The tests use `pytest-asyncio` for async test functions. No external services (LLM, database) are required — all tests use mocked or in-memory data. The test suite runs in under 5 seconds.

### Q: What would you test next?
**A:** Integration tests for the full pipeline (with a mock LLM), API endpoint tests using FastAPI's `TestClient`, and frontend component tests using React Testing Library. Property-based testing (Hypothesis) for the scoring functions would also be valuable.

---

## 7. Deployment

### Q: Where is this deployed?
**A:** Backend: Render.com (free tier, 750h/month). Frontend: Vercel (free, unlimited deploys). Database: Neon.tech (free PostgreSQL). The backend auto-deploys from the `main` branch on GitHub push. Environment variables (SECRET_KEY, ENCRYPTION_KEY, DATABASE_URL) are set in the Render dashboard.

### Q: What are the free LLM APIs you use?
**A:** Primary: Groq + `llama-3.3-70b-versatile` (free, 30 req/min, 128k context). Fallback: Google Gemini 1.5 Flash (free, 15 req/min, 1M context). Local: Ollama + `llama3.2` (unlimited, no API key needed). These are all supported by changing the provider in the app settings — no code changes required.
