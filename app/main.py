"""API do Project Aether. Não executa código nem realiza scans."""
from logging import getLogger
from time import perf_counter
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.analysis.static_review import review_code
from app.ai import get_provider
from app.ai.ollama_provider import OllamaProviderError
from app.core.config import get_settings
from app.rag.embeddings import OllamaEmbedder, OllamaEmbeddingError
from app.rag.retriever import retrieve


settings = get_settings()
logger = getLogger("project_aether.api")
app = FastAPI(
    title="Project Aether API",
    description="Assistente de IA para cibersegurança defensiva e programação.",
    version="0.6.0",
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.exception_handler(RequestValidationError)
async def validation_error_response(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Devolve erros de validação sem ecoar valores enviados pelo cliente."""
    errors = [
        {
            "loc": list(error.get("loc", ())),
            "msg": error.get("msg", "Dados inválidos."),
            "type": error.get("type", "value_error"),
        }
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})


@app.middleware("http")
async def request_observability(request, call_next):
    """Regista metadados mínimos e aplica cabeçalhos HTTP de segurança."""
    request_id = str(uuid4())
    started = perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        logger.error(
            "request_failed request_id=%s method=%s path=%s error_type=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            type(exc).__name__,
            (perf_counter() - started) * 1000,
        )
        raise

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path == "/analyze":
        response.headers["Cache-Control"] = "no-store"

    logger.info(
        "request_completed request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        (perf_counter() - started) * 1000,
    )
    return response


provider = get_provider()
embedder = (
    OllamaEmbedder(settings)
    if settings.rag_provider == "ollama"
    else None
)


class AnalysisRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    category: Literal["cybersecurity", "programming", "general"] = "general"

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("O conteúdo não pode conter apenas espaços.")
        return value


class CodeReviewRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)

    @field_validator("content")
    @classmethod
    def code_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("O código não pode conter apenas espaços.")
        return value


class CodeReviewResponse(BaseModel):
    status: str
    analysis_mode: str
    findings: list[dict[str, object]]


class SourceResponse(BaseModel):
    title: str
    path: str
    excerpt: str
    reference: str


class AnalysisResponse(BaseModel):
    category: str
    status: str
    provider: str
    guidance: list[str]
    sources: list[SourceResponse]


@app.get("/")
def root() -> dict[str, str]:
    return {
        "project": "Project Aether",
        "description": "Assistente de cibersegurança defensiva e programação",
        "version": "0.6.0",
    }


@app.get("/ui", include_in_schema=False)
def web_interface() -> FileResponse:
    """Serve a interface web estática, sem guardar conteúdo do utilizador."""
    return FileResponse("app/static/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(request: AnalysisRequest) -> AnalysisResponse:
    try:
        sources = retrieve(request.content, embedder=embedder)
    except (OllamaEmbeddingError, ValueError):
        # A indisponibilidade de embeddings nunca impede a análise lexical.
        sources = retrieve(request.content)

    context = "\n\n".join(
        f"[Documento: {source.path} | Secção: {source.title}]\n{source.excerpt}"
        for source in sources
    )
    try:
        guidance = provider.analyze(
            request.content, request.category, context=context
        )
    except OllamaProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return AnalysisResponse(
        category=request.category,
        status="completed" if provider.name == "ollama_local" else "starter_mode",
        provider=provider.name,
        guidance=guidance,
        sources=[
            SourceResponse(
                title=source.title,
                path=source.path,
                excerpt=source.excerpt,
                reference=source.reference,
            )
            for source in sources
        ],
    )


@app.post("/review-code", response_model=CodeReviewResponse)
def review_submitted_code(request: CodeReviewRequest) -> CodeReviewResponse:
    """Revê código como texto; nunca o importa, compila ou executa."""
    try:
        findings = review_code(request.content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return CodeReviewResponse(
        status="completed",
        analysis_mode="static_text_only",
        findings=findings,
    )
