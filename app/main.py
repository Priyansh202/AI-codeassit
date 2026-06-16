from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models.schemas import AskRequest, AskResponse, DocsResponse, EndpointDoc, HealthResponse
from app.rag.pipeline import RAGPipeline

settings = get_settings()
pipeline = RAGPipeline(settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        pipeline.ensure_index()
    except Exception as exc:
        print(f"Warning: failed to initialize index on startup: {exc}")
    yield


app = FastAPI(
    title="Python Programming Q&A Assistant",
    description="RAG-powered API for grounded Python answers using Stack Overflow Q&A.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _api_docs() -> DocsResponse:
    return DocsResponse(
        name="Python Programming Q&A Assistant",
        version="1.0.0",
        description="RAG-powered API for grounded Python answers using Stack Overflow Q&A.",
        swagger_ui="/docs",
        redoc="/redoc",
        openapi_schema="/openapi.json",
        endpoints=[
            EndpointDoc(
                method="GET",
                path="/",
                description="API overview and documentation links.",
            ),
            EndpointDoc(
                method="GET",
                path="/api/docs",
                description="Machine-readable API documentation.",
            ),
            EndpointDoc(
                method="GET",
                path="/health",
                description="Service health, index status, and document count.",
            ),
            EndpointDoc(
                method="POST",
                path="/ask",
                description="Submit a Python question and receive a grounded answer with sources.",
            ),
        ],
    )


@app.get("/")
async def root() -> dict:
    docs = _api_docs()
    return {
        "message": docs.name,
        "version": docs.version,
        "docs": docs.swagger_ui,
        "redoc": docs.redoc,
        "openapi": docs.openapi_schema,
        "api_docs": "/api/docs",
        "health": "/health",
        "ask": "/ask",
    }


@app.get("/api/docs", response_model=DocsResponse)
async def api_docs() -> DocsResponse:
    return _api_docs()


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        index_ready=pipeline.is_ready,
        llm_configured=settings.has_llm_credentials(),
        document_count=pipeline.document_count,
    )


@app.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest) -> AskResponse:
    try:
        return pipeline.ask(payload.question.strip())
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {exc}") from exc
