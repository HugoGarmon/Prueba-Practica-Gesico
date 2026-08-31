from pydantic import BaseModel, Field

class TextAnalysisRequest(BaseModel):
    """Modelo de entrada para el análisis de texto."""
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Texto a analizar",
        json_schema_extra={"examples": ["España lidera la transición energética en Europa."]}
    )
    language: str | None = Field(
        default=None,
        pattern=r"^[a-z]{2}$",
        description="Código ISO 639-1 del idioma (ej: 'es', 'en'). Si no se especifica, se detecta automáticamente."
    )
