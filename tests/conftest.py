import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app


@pytest.fixture
def client():
    """Cliente de test para la API."""
    return TestClient(app)


@pytest.fixture
def mock_llm_response():
    """Respuesta simulada del LLM para tests sin Ollama."""
    return {
        "summary": "España lidera la transición energética en Europa con grandes inversiones en energía solar y eólica.",
        "sentiment": "POSITIVE",
        "sentiment_score": 0.8,
        "entities": [
            {"name": "España", "category": "LOCATION"},
            {"name": "Europa", "category": "LOCATION"}
        ],
        "key_topics": ["energía renovable", "transición energética", "inversión"],
        "language": "es"
    }


@pytest.fixture
def mock_openai_client(mock_llm_response):
    """Mock del cliente OpenAI que simula respuestas de Ollama."""
    import json
    mock_message = MagicMock()
    mock_message.content = json.dumps(mock_llm_response)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_completion = MagicMock()
    mock_completion.choices = [mock_choice]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)

    # Mock for health check
    mock_model = MagicMock()
    mock_model.id = "qwen2.5:3b"
    mock_models_list = MagicMock()
    mock_models_list.data = [mock_model]
    mock_client.models.list = AsyncMock(return_value=mock_models_list)

    return mock_client
