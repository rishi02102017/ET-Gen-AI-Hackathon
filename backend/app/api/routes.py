from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.analysis import AnalysisResponse, AnalyzeRequest, HealthResponse
from app.services.llm import PIPELINE_VERSION
from app.services.llm_client import resolve_llm_api_host
from app.services.orchestrator import AnalysisInputError, run_analysis

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    live = settings.llm_live_enabled
    return HealthResponse(
        pipeline_version=PIPELINE_VERSION,
        llm_mode="live" if live else "mock",
        llm_api_host=resolve_llm_api_host(settings),
        llm_fallback_ready=settings.llm_fallback_configured,
    )


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: AnalyzeRequest) -> AnalysisResponse:
    settings = get_settings()
    try:
        return await run_analysis(request, settings)
    except AnalysisInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
