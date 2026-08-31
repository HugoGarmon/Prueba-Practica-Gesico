import json
import logging
import time
from openai import AsyncOpenAI, APIConnectionError, APITimeoutError, APIStatusError

from app.config import get_settings
from app.exceptions.handlers import (
    OllamaConnectionError,
    LLMProcessingError,
    LLMTimeoutError,
    InvalidLLMResponseError,
    ModelNotFoundError,
)
from app.schemas.responses import TextAnalysisResponse, Entity

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres un asistente experto en análisis de texto y procesamiento de lenguaje natural.
Tu tarea es analizar el texto proporcionado y devolver un JSON con la siguiente estructura exacta:

{
    "summary": "Resumen conciso del texto en 2-3 frases",
    "sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
    "sentiment_score": <float entre -1.0 y 1.0>,
    "entities": [
        {"name": "nombre de la entidad", "category": "PERSON|ORGANIZATION|LOCATION|DATE|PRODUCT|EVENT|MISC"}
    ],
    "key_topics": ["tema1", "tema2", ...],
    "language": "código ISO 639-1 del idioma detectado (ej: es, en, fr)"
}

Reglas:
- El resumen debe ser conciso y capturar las ideas principales.
- El sentimiento debe reflejar el tono general del texto.
- Extrae TODAS las entidades relevantes (personas, organizaciones, lugares, fechas, productos, eventos).
- Identifica entre 2 y 5 temas principales.
- Detecta el idioma del texto.
- Responde ÚNICAMENTE con el JSON, sin texto adicional."""


class NLPService:
    """Servicio de análisis de texto usando un LLM local a través de Ollama."""

    def __init__(self) -> None:
        """Inicializa el servicio NLP con la configuración de Ollama."""
        settings = get_settings()
        self._client = AsyncOpenAI(
            base_url=f"{settings.OLLAMA_BASE_URL}/v1",
            api_key="ollama",  # Ollama no requiere API key real
        )
        self._model = settings.LLM_MODEL
        logger.info(f"Servicio NLP inicializado con modelo '{self._model}' en {settings.OLLAMA_BASE_URL}")

    async def analyze_text(self, text: str, language: str | None = None) -> TextAnalysisResponse:
        """Analiza un texto y devuelve un análisis completo.

        Args:
            text: Texto a analizar.
            language: Código ISO 639-1 del idioma (opcional).

        Returns:
            TextAnalysisResponse con el análisis completo.

        Raises:
            OllamaConnectionError: Si no se puede conectar con Ollama.
            LLMTimeoutError: Si la respuesta tarda demasiado.
            InvalidLLMResponseError: Si la respuesta no es JSON válido.
            LLMProcessingError: Si ocurre un error durante el procesamiento.
        """
        word_count = len(text.split())
        start_time = time.perf_counter()

        user_message = f"Analiza el siguiente texto:\n\n{text}"
        if language:
            user_message += f"\n\nNota: El idioma del texto es '{language}'."

        try:
            logger.info(f"Enviando texto al LLM ({word_count} palabras)")
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,  # Baja temperatura para resultados consistentes
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise InvalidLLMResponseError("El modelo devolvió una respuesta vacía")

            logger.debug(f"Respuesta cruda del LLM: {raw_content[:200]}...")

            # Parsear la respuesta JSON del LLM
            try:
                analysis_data = json.loads(raw_content)
            except json.JSONDecodeError as e:
                logger.error(f"Error parseando JSON del LLM: {e}")
                raise InvalidLLMResponseError(
                    f"La respuesta del modelo no es JSON válido: {str(e)}"
                )

            processing_time = (time.perf_counter() - start_time) * 1000

            # Construir la respuesta validada con Pydantic
            # Handle entities safely
            entities = []
            for ent in analysis_data.get("entities", []):
                try:
                    entities.append(Entity(**ent))
                except Exception:
                    logger.warning(f"Entidad ignorada por formato inválido: {ent}")

            return TextAnalysisResponse(
                summary=analysis_data.get("summary", "No se pudo generar un resumen."),
                sentiment=analysis_data.get("sentiment", "NEUTRAL"),
                sentiment_score=max(-1.0, min(1.0, float(analysis_data.get("sentiment_score", 0.0)))),
                entities=entities,
                key_topics=analysis_data.get("key_topics", []),
                language=analysis_data.get("language", language or "unknown"),
                word_count=word_count,
                processing_time_ms=round(processing_time, 2),
            )

        except APITimeoutError as e:
            logger.error(f"Timeout del LLM: {e}")
            raise LLMTimeoutError()
        except APIConnectionError as e:
            logger.error(f"No se pudo conectar con Ollama: {e}")
            raise OllamaConnectionError(
                "No se pudo conectar con Ollama. ¿Está el servicio ejecutándose?"
            )
        except APIStatusError as e:
            logger.error(f"Error de la API de Ollama: {e.status_code} - {e.message}")
            if e.status_code == 404:
                raise ModelNotFoundError(self._model)
            raise LLMProcessingError(f"Error de la API: {e.message}")
        except (InvalidLLMResponseError, OllamaConnectionError, LLMTimeoutError, ModelNotFoundError):
            raise  # Re-raise our custom exceptions
        except Exception as e:
            logger.error(f"Error inesperado en el servicio NLP: {e}", exc_info=True)
            raise LLMProcessingError(f"Error inesperado: {str(e)}")

    async def check_health(self) -> bool:
        """Verifica si Ollama está accesible y el modelo está disponible.

        Returns:
            True si Ollama responde correctamente.
        """
        try:
            models = await self._client.models.list()
            model_ids = [m.id for m in models.data]
            return self._model in model_ids
        except Exception as e:
            logger.warning(f"Health check fallido: {e}")
            return False
