from __future__ import annotations

import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStore
from langchain_openai import ChatOpenAI

from app.config import Settings
from app.models.schemas import AskResponse, SourceDocument
from app.rag.embeddings_factory import create_embeddings
from app.rag.ingest import load_qa_records, prepare_documents
from app.rag.prompts import RAG_SYSTEM_PROMPT, RAG_USER_TEMPLATE
from app.rag.vectorstore import clear_namespace, connect_vectorstore, embedding_dimension, vector_count


class RAGPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._embeddings = create_embeddings(settings)
        self._vectorstore: VectorStore | None = None
        self._document_count = 0

    @property
    def is_ready(self) -> bool:
        return self._vectorstore is not None and self._document_count > 0

    @property
    def document_count(self) -> int:
        return self._document_count

    def build_index(self, data_path: Path | None = None) -> int:
        path = data_path or self.settings.dataset_path
        records = load_qa_records(path)
        texts, metadatas, ids = prepare_documents(records)
        if not texts:
            raise ValueError("No valid documents found in dataset")

        documents = [
            Document(page_content=text, metadata=metadata)
            for text, metadata in zip(texts, metadatas, strict=True)
        ]

        clear_namespace(self.settings)
        self._vectorstore = connect_vectorstore(self.settings, self._embeddings)
        self._vectorstore.add_documents(documents, ids=ids)
        self._document_count = len(documents)
        return self._document_count

    def load_index(self) -> int:
        try:
            self._vectorstore = connect_vectorstore(self.settings, self._embeddings)
            self._document_count = vector_count(self.settings)
        except ValueError:
            self._vectorstore = None
            self._document_count = 0
        return self._document_count

    def ensure_index(self) -> None:
        if self.is_ready:
            return
        loaded = self.load_index()
        if loaded == 0:
            self.build_index()

    def _get_llm(self):
        if self.settings.llm_provider == "openrouter":
            if not self.settings.openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY is not configured")
            return ChatOpenAI(
                api_key=self.settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                model=self.settings.openrouter_model,
                temperature=0.1,
                default_headers={
                    "HTTP-Referer": self.settings.openrouter_site_url,
                    "X-Title": self.settings.openrouter_app_name,
                },
            )

        if self.settings.llm_provider == "groq":
            if not self.settings.groq_api_key:
                raise ValueError("GROQ_API_KEY is not configured")
            return ChatOpenAI(
                api_key=self.settings.groq_api_key,
                base_url="https://api.groq.com/openai/v1",
                model=self.settings.groq_model,
                temperature=0.1,
            )

        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not configured")
        return ChatOpenAI(
            api_key=self.settings.openai_api_key,
            model=self.settings.openai_model,
            temperature=0.1,
        )

    def _keyword_score(self, question: str, doc: Document) -> float:
        question_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
        if not question_terms:
            return 0.0

        stopwords = {"how", "do", "i", "a", "an", "the", "in", "to", "is", "what", "with", "and", "or", "for", "of"}
        weighted_terms = [term for term in question_terms if term not in stopwords] or list(question_terms)

        title = str(doc.metadata.get("title", "")).lower()
        content = doc.page_content.lower()
        field_terms = set(re.findall(r"[a-z0-9]+", f"{title} {content}"))

        overlap = sum(1 for term in weighted_terms if term in field_terms)
        missing = sum(1 for term in weighted_terms if term not in field_terms)
        title_overlap = sum(1 for term in weighted_terms if term in title)

        return (overlap / len(weighted_terms)) + (title_overlap * 0.5) - (missing * 0.35)

    def _retrieve(self, question: str) -> list[tuple[Document, float]]:
        if not self._vectorstore:
            raise RuntimeError("Vector store is not initialized")
        results = self._vectorstore.similarity_search_with_relevance_scores(
            question, k=max(self.settings.top_k * 3, self.settings.top_k)
        )
        reranked = sorted(
            results,
            key=lambda item: (self._keyword_score(question, item[0]) * 2.0 + float(item[1])),
            reverse=True,
        )
        return reranked[: self.settings.top_k]

    def _format_context(self, docs: list[tuple[Document, float]]) -> tuple[str, list[SourceDocument]]:
        context_blocks: list[str] = []
        sources: list[SourceDocument] = []

        for rank, (doc, score) in enumerate(docs, start=1):
            title = str(doc.metadata.get("title", f"Source {rank}"))
            excerpt = doc.page_content[:500].strip()
            context_blocks.append(f"[{rank}] {doc.page_content}")
            sources.append(SourceDocument(title=title, score=round(float(score), 4), excerpt=excerpt))

        return "\n\n".join(context_blocks), sources

    def _retrieval_only_answer(self, question: str, docs: list[tuple[Document, float]]) -> str:
        if not docs:
            return "I could not find relevant Python Q&A context for this question."

        best_doc, _ = docs[0]
        lines = best_doc.page_content.splitlines()
        answer_lines = [line for line in lines if line.startswith("Answer:")]
        if answer_lines:
            return answer_lines[0].replace("Answer:", "", 1).strip()

        return (
            "Here is the closest matching Stack Overflow context I found:\n\n"
            f"{best_doc.page_content[:1200]}"
        )

    def ask(self, question: str) -> AskResponse:
        self.ensure_index()
        retrieved = self._retrieve(question)
        context, sources = self._format_context(retrieved)

        if not self.settings.has_llm_credentials():
            return AskResponse(
                question=question,
                answer=self._retrieval_only_answer(question, retrieved),
                sources=sources,
                mode="retrieval_only",
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RAG_SYSTEM_PROMPT),
                ("human", RAG_USER_TEMPLATE),
            ]
        )
        chain = prompt | self._get_llm() | StrOutputParser()
        answer = chain.invoke({"context": context, "question": question})

        return AskResponse(
            question=question,
            answer=answer.strip(),
            sources=sources,
            mode="generation",
        )
