# Presentation Brief — Python Programming Q&A Assistant

> **How to use this file:** Copy the entire document into Gemini, Claude, or ChatGPT and use the prompt at the bottom to generate a professional slide deck (max 10 slides) for the Analytics Vidhya AI Engineer assessment submission.

---

## 1. Project Title

**Python Programming Q&A Assistant**

A retrieval-augmented generation (RAG) system that helps data science learners get accurate, grounded answers to Python programming questions.

**Context:** Analytics Vidhya AI Engineer Assessment — Round 1 Take-Home Project

**Author:** Priyansh (GitHub: [Priyansh202/AI-codeassit](https://github.com/Priyansh202/AI-codeassit))

---

## 2. Problem Statement

- Data science learners frequently ask repetitive Python questions (pandas, NumPy, scikit-learn, core Python syntax).
- Generic LLMs can **hallucinate** APIs, invent functions, or give outdated patterns.
- Learners need **fast, accurate, source-grounded** answers — not open-ended chat.
- The assessment required building a system on top of **Stack Overflow Python Q&A data** that can answer any Python-related query with proper grounding and testing.

---

## 3. Solution Overview

Built an end-to-end AI tutoring system with:

1. **RAG pipeline** — retrieves relevant Stack Overflow Q&A, then synthesizes an answer from that context only.
2. **FastAPI backend** — REST API with `/ask`, `/health`, and full OpenAPI documentation.
3. **Pinecone vector database** — managed cloud storage for embeddings and similarity search.
4. **OpenRouter LLM** — free-tier model for answer generation (`liquid/lfm-2.5-1.2b-instruct:free`).
5. **Node.js frontend** — chat-style UI with example prompts, system status, and source citations.
6. **Deployed on Render** — publicly accessible frontend and backend.

---

## 4. Live URLs (Deployed)

| Service | URL |
|---------|-----|
| **Frontend (Chat UI)** | https://ai-codeassit-1.onrender.com |
| **Backend API** | https://ai-codeassit.onrender.com |
| **Swagger API Docs** | https://ai-codeassit.onrender.com/docs |
| **JSON API Docs** | https://ai-codeassit.onrender.com/api/docs |
| **Health Check** | https://ai-codeassit.onrender.com/health |
| **GitHub Repository** | https://github.com/Priyansh202/AI-codeassit |

---

## 5. System Architecture

```
User (Browser)
    │
    ▼
Node.js Frontend (Express)  ── port 3000 / Render
    │  proxies /api/ask, /api/health
    ▼
FastAPI Backend  ── port 8000 / Render (Docker)
    │
    ├── RAG Pipeline (LangChain)
    │       │
    │       ├── 1. Embed user question
    │       ├── 2. Similarity search in Pinecone (top-k=5)
    │       ├── 3. Keyword reranking for better relevance
    │       ├── 4. Build grounded prompt with retrieved context
    │       └── 5. LLM generation (OpenRouter) OR retrieval-only fallback
    │
    ├── Pinecone Vector DB (cloud, namespace: production)
    └── OpenRouter API (LLM)
```

**Data flow for a single question:**
1. User types question in chat UI
2. Frontend sends `POST /api/ask` → proxied to FastAPI `POST /ask`
3. Question is embedded and searched against Pinecone
4. Top 5 relevant Stack Overflow Q&A passages retrieved
5. Keyword reranking boosts best matches
6. Context + question sent to OpenRouter LLM with strict grounding prompt
7. Answer + source citations returned to user

---

## 6. Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend framework** | FastAPI | Async, auto OpenAPI docs, Pydantic validation |
| **RAG framework** | LangChain | Retrieval chains, prompt templates, LLM integration |
| **Vector database** | Pinecone | Managed, scalable, no infra to maintain |
| **Embeddings** | Hash embeddings (384-dim) | Lightweight, no GPU/RAM, works on free tier |
| **LLM** | OpenRouter (`liquid/lfm-2.5-1.2b-instruct:free`) | Free model, OpenAI-compatible API |
| **Frontend** | Node.js + Express | API proxy, static chat UI |
| **UI** | HTML/CSS/Vanilla JS | No build step, fast deploy |
| **Testing** | Pytest + FastAPI TestClient | API endpoint tests |
| **Deployment** | Render (Docker + Node) | Free tier, auto-deploy from GitHub |
| **Dataset** | Stack Overflow Python Q&A (sample JSON + Kaggle script) | Ground truth for RAG |

---

## 7. Key Design Decisions

### 7.1 RAG over pure LLM
- Answers are grounded in retrieved Stack Overflow passages, reducing hallucination.
- Sources are returned with every answer so users can verify.

### 7.2 Pinecone over ChromaDB
- Started with ChromaDB locally, migrated to Pinecone for production.
- Cloud-hosted vectors survive Render restarts (no volume needed).
- Namespaces isolate environments (`default`, `production`, `pytest`).

### 7.3 Configurable embedding providers
- `hash` — lightweight, deterministic, works without API keys (used in production).
- `openai` — `text-embedding-3-small` for higher quality.
- `huggingface` — local `all-MiniLM-L6-v2` when GPU/RAM available.

### 7.4 Keyword reranking
- Vector similarity alone missed some queries (e.g. list vs tuple).
- Added keyword overlap scoring with title boosting and missing-term penalties.
- Retrieves 3× top-k candidates, reranks, returns best 5.

### 7.5 Retrieval-only fallback
- If no LLM API key is configured, system still returns the best matching answer from sources.
- Ensures the API always works even without paid LLM access.

### 7.6 Grounded prompt engineering
- System prompt: "Answer ONLY from provided Stack Overflow context."
- If context is insufficient, model says what's missing instead of inventing.
- Temperature set to 0.1 for factual consistency.

---

## 8. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | API overview with links |
| `GET` | `/api/docs` | JSON API documentation |
| `GET` | `/docs` | Swagger UI (interactive) |
| `GET` | `/redoc` | ReDoc documentation |
| `GET` | `/openapi.json` | OpenAPI schema |
| `GET` | `/health` | Status, index readiness, document count, LLM config |
| `POST` | `/ask` | Submit question → get grounded answer + sources |

### Example request

```json
POST /ask
{ "question": "How do I read a CSV file in pandas?" }
```

### Example response

```json
{
  "question": "How do I read a CSV file in pandas?",
  "answer": "Use pandas.read_csv(). Example: import pandas as pd; df = pd.read_csv('data.csv')...",
  "sources": [
    {
      "title": "How to read a CSV file in pandas?",
      "score": 0.9772,
      "excerpt": "Title: How to read a CSV file in pandas?..."
    }
  ],
  "mode": "generation"
}
```

---

## 9. Data Pipeline

1. **Source:** Stack Overflow Python Q&A ([Kaggle dataset](https://www.kaggle.com/datasets/stackoverflow/pythonquestions))
2. **Sample data:** 20 curated Python Q&A records in `data/sample_python_qa.json`
3. **Ingestion:** `scripts/download_data.py` downloads full Kaggle CSV
4. **Normalization:** Each record → `Title + Question + Tags + Answer` document
5. **Embedding:** Hash embeddings (384 dimensions)
6. **Indexing:** `scripts/build_index.py` → upserts to Pinecone
7. **Namespaces:** `production` for Render, `pytest` for tests

---

## 10. Testing & Quality Evaluation

### Automated tests (Pytest)
- `GET /health` — returns ok, index ready, document count
- `POST /ask` — returns grounded answer with sources
- Validation — rejects questions shorter than 3 characters (422)
- Edge case — handles out-of-domain questions gracefully

### Manual evaluation (10 test queries)

| # | Question | Result |
|---|----------|--------|
| 1 | How do I read a CSV file in pandas? | Correct `read_csv` guidance |
| 2 | What is the difference between a list and a tuple? | Correct mutability explanation |
| 3 | How can I handle missing values in a DataFrame? | Correct `isna`/`dropna`/`fillna` |
| 4 | Explain Python list comprehensions | Correct syntax example |
| 5 | How do I merge two DataFrames? | Correct `pd.merge` guidance |
| 6 | What does `if __name__ == '__main__'` do? | Correct module explanation |
| 7 | How do I create a virtual environment? | Correct `python -m venv` |
| 8 | How do I train-test split with scikit-learn? | Correct `train_test_split` |
| 9 | How do I sort a list in Python? | Correct `sort()` vs `sorted()` |
| 10 | What is a decorator in Python? | Correct decorator explanation |

### Edge cases tested
- Too-short input → 422 validation error
- Out-of-domain (Kubernetes) → closest available context, no hallucination
- Empty Pinecone namespace → auto-rebuilds index on startup

---

## 11. Project Structure

```
AI-codeassit/
├── app/                    # FastAPI application
│   ├── main.py             # API routes + CORS
│   ├── config.py           # Environment settings
│   ├── models/schemas.py   # Pydantic request/response models
│   └── rag/
│       ├── pipeline.py     # RAG orchestration
│       ├── vectorstore.py  # Pinecone integration
│       ├── embeddings.py   # Hash embedding implementation
│       ├── embeddings_factory.py
│       ├── ingest.py       # Data loading + document prep
│       └── prompts.py      # System + user prompt templates
├── frontend/               # Node.js chat UI
│   ├── server.js           # Express proxy server
│   └── public/             # HTML, CSS, JS
├── scripts/
│   ├── build_index.py      # Build Pinecone index
│   ├── download_data.py    # Download Kaggle dataset
│   └── run_test_queries.py # Generate test results
├── tests/                  # Pytest API tests
├── test_results/           # Documented evaluation results
├── data/                   # Sample Q&A dataset
├── docs/                   # Slides + this brief
├── Dockerfile              # Backend container
├── render.yaml             # Render deployment blueprint
└── requirements.txt
```

---

## 12. Deployment Architecture

| Component | Platform | Runtime | URL |
|-----------|----------|---------|-----|
| Backend | Render Web Service | Docker (Python 3.11) | ai-codeassit.onrender.com |
| Frontend | Render Web Service | Node.js | ai-codeassit-1.onrender.com |
| Vector DB | Pinecone (serverless) | Cloud | aws/us-east-1 |
| LLM | OpenRouter | API | liquid/lfm-2.5-1.2b-instruct:free |

**CI/CD:** Push to `main` branch on GitHub → Render auto-deploys both services.

---

## 13. Scaling Plan (100+ Concurrent Users)

| Challenge | Solution |
|-----------|----------|
| **Latency** | Async FastAPI + Uvicorn workers (4–8 workers) |
| **Vector search** | Pinecone serverless auto-scales; increase pod size if needed |
| **LLM cost** | Redis cache for frequent questions (hash → cached answer) |
| **Embedding cost** | Pre-compute at ingest time; never embed at request time |
| **LLM routing** | Small model for simple queries, large model for complex |
| **Rate limiting** | Per-IP rate limits on `/ask`; queue for burst traffic |
| **Cold starts** | Render paid tier or keep-alive ping; Pinecone always warm |
| **Observability** | Log retrieval scores, latency, token usage; alert on errors |
| **Database** | Pinecone namespaces per environment; no migration needed |
| **Cost control** | Top-k tuning, caching, batch inference, free-tier LLM |

---

## 14. What Was Delivered (Assessment Checklist)

| Requirement | Status | Details |
|-------------|--------|---------|
| RAG pipeline or agent | Done | LangChain + Pinecone + OpenRouter |
| FastAPI with POST /ask | Done | Grounded answers with sources |
| FastAPI with GET /health | Done | Index status, LLM config, doc count |
| API testing | Done | Pytest + 10 documented test queries |
| GitHub repo with README | Done | github.com/Priyansh202/AI-codeassit |
| .env.example | Done | All required env vars documented |
| Test results | Done | test_results/TEST_RESULTS.md + JSON |
| Slide deck | Done | docs/SLIDES.md + this brief |
| Deployed app (bonus) | Done | ai-codeassit-1.onrender.com |
| Node.js frontend (extra) | Done | Chat UI with status + sources |

---

## 15. Future Improvements

- Ingest full Kaggle Stack Overflow dataset (millions of Q&A pairs)
- Upgrade to OpenAI embeddings for better retrieval quality
- Add user feedback (thumbs up/down) to improve retrieval over time
- Streaming responses for faster perceived latency
- Conversation history (multi-turn Q&A)
- Admin dashboard for index management and analytics

---

## 16. Prompt for AI Slide Generation

Copy everything below this line into Gemini or Claude:

---

**PROMPT:**

Create a professional slide deck (maximum 10 slides) for the Analytics Vidhya AI Engineer assessment submission based on all the information above.

Requirements:
- Clean, modern design suitable for a technical interview presentation
- Include architecture diagram descriptions (I will add visuals separately)
- Cover: problem, solution, architecture, tech stack, key design decisions, API demo, testing results, deployment, scaling plan
- End with live demo URLs and GitHub link
- Tone: confident, technical, concise — not marketing fluff
- Each slide should have a clear title, 3–5 bullet points max, and a speaker note
- Format output as slide-by-slide markdown with `---` separators

Live URLs to include on the final slide:
- Frontend: https://ai-codeassit-1.onrender.com
- Backend: https://ai-codeassit.onrender.com
- API Docs: https://ai-codeassit.onrender.com/docs
- GitHub: https://github.com/Priyansh202/AI-codeassit
