# API Test Results

This document records diverse Python-related queries run against `POST /ask`.

## Setup

- Dataset: bundled `data/sample_python_qa.json` (20 Stack Overflow-style Python Q&A records)
- Mode: `retrieval_only` when no `OPENAI_API_KEY` / `GROQ_API_KEY` is set; `generation` when an LLM key is configured
- Index: Pinecone + hash/OpenAI embeddings

Regenerate machine-readable output:

```bash
python scripts/run_test_queries.py
```

## Test Queries

| # | Question | Expected behavior | Observation |
|---|----------|-------------------|-------------|
| 1 | How do I read a CSV file in pandas? | Retrieve pandas CSV guidance | Returns `read_csv` guidance with pandas source |
| 2 | What is the difference between a list and a tuple? | Explain mutability and syntax | Grounded answer on list vs tuple |
| 3 | How can I handle missing values in a DataFrame? | Mention `isna`, `dropna`, `fillna` | Retrieves missing-data record |
| 4 | Explain Python list comprehensions with an example. | Provide compact syntax example | Returns comprehension syntax |
| 5 | How do I merge two DataFrames on a common key? | Mention `pd.merge` | Retrieves merge/join guidance |
| 6 | What does `if __name__ == '__main__'` do? | Explain script entry point | Returns module execution explanation |
| 7 | How do I create and use a virtual environment? | Mention `python -m venv` | Retrieves venv instructions |
| 8 | How do I train-test split data with scikit-learn? | Mention `train_test_split` | Retrieves sklearn split example |
| 9 | How do I sort a list in Python? | Compare `sort()` vs `sorted()` | Retrieves sorting guidance |
| 10 | What is a decorator in Python? | High-level decorator explanation | Retrieves decorator record |

## Edge Cases

| Case | Input | Result |
|------|-------|--------|
| Too short | `hi` | `422` validation error |
| Out of domain | Kubernetes ingress question | Returns closest available context without inventing infra specifics |
| Missing index | Pinecone namespace empty on first boot | App rebuilds index from configured dataset |

## Quality Notes

- Retrieval is strong for direct Python/pandas/sklearn questions included in the corpus.
- With an LLM key, answers are synthesized from top-k retrieved passages, reducing hallucination risk.
- For production, replace the sample JSON with the full Kaggle dataset via `scripts/download_data.py`.
