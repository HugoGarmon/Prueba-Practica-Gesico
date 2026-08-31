import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


# --- Excepciones personalizadas ---

class NLPServiceError(Exception):
    """Error base del servicio NLP."""
    def __init__(self, detail: str, error_code: str = "NLP_ERROR"):
        self.detail = detail
        self.error_code = error_code
        super().__init__(self.detail)


class OllamaConnectionError(NLPServiceError):
    """Ollama no está accesible."""
    def __init__(self, detail: str = "No se pudo conectar con el servicio Ollama"):
        super().__init__(detail=detail, error_code="OLLAMA_CONNECTION_ERROR")


class ModelNotFoundError(NLPServiceError):
    """El modelo solicitado no está disponible en Ollama."""
    def __init__(self, model: str):
        super().__init__(
            detail=f"El modelo '{model}' no está disponible. Ejecuta 'ollama pull {model}'",
            error_code="MODEL_NOT_FOUND"
        )


class LLMProcessingError(NLPServiceError):
    """Error durante el procesamiento del LLM."""
    def __init__(self, detail: str = "Error durante el procesamiento del texto"):
        super().__init__(detail=detail, error_code="LLM_PROCESSING_ERROR")


class LLMTimeoutError(NLPServiceError):
    """Timeout esperando respuesta del LLM."""
    def __init__(self, detail: str = "Timeout esperando respuesta del modelo"):
        super().__init__(detail=detail, error_code="LLM_TIMEOUT")


class InvalidLLMResponseError(NLPServiceError):
    """La respuesta del LLM no tiene el formato esperado."""
    def __init__(self, detail: str = "La respuesta del modelo no tiene el formato JSON esperado"):
        super().__init__(detail=detail, error_code="INVALID_LLM_RESPONSE")


# --- Handlers de excepciones para FastAPI ---

def register_exception_handlers(app: FastAPI) -> None:
    """Registra los handlers de excepciones personalizadas en la app FastAPI."""

    @app.exception_handler(OllamaConnectionError)
    async def ollama_connection_handler(request: Request, exc: OllamaConnectionError) -> JSONResponse:
        logger.error(f"Error de conexión con Ollama: {exc.detail}")
        return JSONResponse(
            status_code=503,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )

    @app.exception_handler(ModelNotFoundError)
    async def model_not_found_handler(request: Request, exc: ModelNotFoundError) -> JSONResponse:
        logger.error(f"Modelo no encontrado: {exc.detail}")
        return JSONResponse(
            status_code=503,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )

    @app.exception_handler(LLMTimeoutError)
    async def llm_timeout_handler(request: Request, exc: LLMTimeoutError) -> JSONResponse:
        logger.warning(f"Timeout del LLM: {exc.detail}")
        return JSONResponse(
            status_code=504,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )

    @app.exception_handler(InvalidLLMResponseError)
    async def invalid_response_handler(request: Request, exc: InvalidLLMResponseError) -> JSONResponse:
        logger.error(f"Respuesta inválida del LLM: {exc.detail}")
        return JSONResponse(
            status_code=502,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )

    @app.exception_handler(LLMProcessingError)
    async def llm_processing_handler(request: Request, exc: LLMProcessingError) -> JSONResponse:
        logger.error(f"Error de procesamiento: {exc.detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )

    @app.exception_handler(NLPServiceError)
    async def nlp_service_handler(request: Request, exc: NLPServiceError) -> JSONResponse:
        logger.error(f"Error del servicio NLP: {exc.detail}")
        return JSONResponse(
            status_code=500,
            content={"detail": exc.detail, "error_code": exc.error_code}
        )
