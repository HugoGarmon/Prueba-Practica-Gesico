from pydantic import BaseModel, Field
from typing import Literal


class Entity(BaseModel):
    """Entidad extraída del texto."""
    name: str = Field(description="Nombre de la entidad")
    category: Literal["PERSON", "ORGANIZATION", "LOCATION", "DATE", "PRODUCT", "EVENT", "MISC"] = Field(
        description="Categoría de la entidad"
    )


class TextAnalysisResponse(BaseModel):
    """Modelo de salida del análisis de texto."""
    summary: str = Field(description="Resumen conciso del texto (2-3 frases)")
    sentiment: Literal["POSITIVE", "NEUTRAL", "NEGATIVE"] = Field(
        description="Sentimiento general del texto"
    )
    sentiment_score: float = Field(
        ge=-1.0, le=1.0,
        description="Puntuación de sentimiento (-1.0 negativo, 0 neutro, 1.0 positivo)"
    )
    entities: list[Entity] = Field(
        default_factory=list,
        description="Entidades extraídas del texto"
    )
    key_topics: list[str] = Field(
        default_factory=list,
        description="Temas principales (2-5)"
    )
    language: str = Field(description="Idioma detectado (código ISO 639-1)")
    word_count: int = Field(ge=0, description="Número de palabras en el texto")
    processing_time_ms: float = Field(ge=0, description="Tiempo de procesamiento en milisegundos")


class HealthResponse(BaseModel):
    """Modelo de respuesta del health check."""
    status: str = Field(description="Estado general del servicio")
    ollama_connected: bool = Field(description="Si Ollama está accesible")
    model_loaded: str = Field(description="Modelo LLM configurado")


class ErrorResponse(BaseModel):
    """Modelo de respuesta de error."""
    detail: str = Field(description="Descripción del error")
    error_code: str = Field(description="Código de error interno")
