from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=2000, examples=["How do I read a CSV file in pandas?"])


class SourceDocument(BaseModel):
    title: str
    score: float | None = None
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SourceDocument]
    mode: str = Field(description="generation | retrieval_only")


class HealthResponse(BaseModel):
    status: str
    index_ready: bool
    llm_configured: bool
    document_count: int
