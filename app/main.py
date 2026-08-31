import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.analyze import router as analyze_router
from app.exceptions.handlers import register_exception_handlers
from app.services.nlp_service import NLPService


def setup_logging() -> None:
    """Configura el logging de la aplicación."""
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    setup_logging()
    logger = logging.getLogger(__name__)
    settings = get_settings()

    # Verificar conexión con Ollama al arrancar
    logger.info(f"Iniciando servicio NLP con modelo '{settings.LLM_MODEL}'")
    nlp_service = NLPService()
    is_healthy = await nlp_service.check_health()
    if is_healthy:
        logger.info("✅ Conexión con Ollama verificada. Modelo disponible.")
    else:
        logger.warning(
            "⚠️ No se pudo verificar la conexión con Ollama o el modelo no está disponible. "
            f"Asegúrate de que Ollama está corriendo y el modelo '{settings.LLM_MODEL}' está descargado."
        )

    yield  # La app corre aquí

    logger.info("Servicio NLP detenido.")


def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title="NLP Analysis API",
        description=(
            "Mini-servicio backend para análisis de texto usando un LLM local (Ollama + Qwen2.5). "
            "Proporciona resumen, análisis de sentimiento, extracción de entidades y detección de temas."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Registrar exception handlers
    register_exception_handlers(app)

    # Registrar routers
    app.include_router(analyze_router)

    return app


app = create_app()
