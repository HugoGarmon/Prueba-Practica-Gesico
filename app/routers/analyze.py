import logging
from fastapi import APIRouter, Depends

from app.schemas.requests import TextAnalysisRequest
from app.schemas.responses import TextAnalysisResponse, HealthResponse, ErrorResponse
from app.services.nlp_service import NLPService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["Análisis de Texto"])

# Dependency injection del servicio NLP
def get_nlp_service() -> NLPService:
    """Proporciona una instancia del servicio NLP."""
    return NLPService()


@router.post(
    "/analyze",
    response_model=TextAnalysisResponse,
    summary="Analizar texto",
    description="Recibe un texto y devuelve un análisis completo: resumen, sentimiento, entidades y temas.",
    responses={
        200: {"description": "Análisis completado exitosamente"},
        422: {"description": "Error de validación en la entrada", "model": ErrorResponse},
        500: {"description": "Error interno del servidor", "model": ErrorResponse},
        502: {"description": "Respuesta inválida del LLM", "model": ErrorResponse},
        503: {"description": "Servicio Ollama no disponible", "model": ErrorResponse},
        504: {"description": "Timeout del modelo", "model": ErrorResponse},
    },
)
async def analyze_text(
    request: TextAnalysisRequest,
    nlp_service: NLPService = Depends(get_nlp_service),
) -> TextAnalysisResponse:
    """Endpoint principal de análisis de texto.

    Envía el texto al modelo LLM local (Ollama) y devuelve:
    - Resumen conciso
    - Análisis de sentimiento
    - Entidades extraídas
    - Temas principales
    - Idioma detectado
    - Estadísticas del procesamiento
    """
    logger.info(f"Petición de análisis recibida ({len(request.text)} caracteres)")
    result = await nlp_service.analyze_text(
        text=request.text,
        language=request.language,
    )
    logger.info(f"Análisis completado en {result.processing_time_ms:.2f}ms")
    return result


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Verifica el estado del servicio y la conexión con Ollama.",
)
async def health_check(
    nlp_service: NLPService = Depends(get_nlp_service),
) -> HealthResponse:
    """Endpoint de health check."""
    from app.config import get_settings
    settings = get_settings()
    is_healthy = await nlp_service.check_health()
    return HealthResponse(
        status="ok" if is_healthy else "degraded",
        ollama_connected=is_healthy,
        model_loaded=settings.LLM_MODEL,
    )
