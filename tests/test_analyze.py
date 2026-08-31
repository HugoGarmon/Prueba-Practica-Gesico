import json
from unittest.mock import patch, AsyncMock, MagicMock
from openai import APIConnectionError, APITimeoutError
import httpx


class TestAnalyzeEndpoint:
    """Tests para el endpoint POST /api/v1/analyze."""

    def test_analyze_valid_text(self, client, mock_openai_client):
        """Test: texto válido devuelve análisis completo."""
        with patch("app.services.nlp_service.AsyncOpenAI", return_value=mock_openai_client):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "España lidera la transición energética en Europa con inversiones millonarias."}
            )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "sentiment" in data
        assert data["sentiment"] in ["POSITIVE", "NEUTRAL", "NEGATIVE"]
        assert "sentiment_score" in data
        assert -1.0 <= data["sentiment_score"] <= 1.0
        assert "entities" in data
        assert isinstance(data["entities"], list)
        assert "key_topics" in data
        assert "language" in data
        assert "word_count" in data
        assert data["word_count"] > 0
        assert "processing_time_ms" in data
        assert data["processing_time_ms"] >= 0

    def test_analyze_with_language(self, client, mock_openai_client):
        """Test: texto con idioma especificado."""
        with patch("app.services.nlp_service.AsyncOpenAI", return_value=mock_openai_client):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "This is a test.", "language": "en"}
            )

        assert response.status_code == 200

    def test_analyze_empty_text(self, client):
        """Test: texto vacío devuelve 422."""
        response = client.post(
            "/api/v1/analyze",
            json={"text": ""}
        )
        assert response.status_code == 422

    def test_analyze_missing_text(self, client):
        """Test: sin campo text devuelve 422."""
        response = client.post(
            "/api/v1/analyze",
            json={}
        )
        assert response.status_code == 422

    def test_analyze_text_too_long(self, client):
        """Test: texto excede max_length devuelve 422."""
        response = client.post(
            "/api/v1/analyze",
            json={"text": "a" * 10001}
        )
        assert response.status_code == 422

    def test_analyze_invalid_language_code(self, client):
        """Test: código de idioma inválido devuelve 422."""
        response = client.post(
            "/api/v1/analyze",
            json={"text": "Test text.", "language": "invalid"}
        )
        assert response.status_code == 422

    def test_analyze_ollama_down(self, client):
        """Test: Ollama no disponible devuelve 503."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=APIConnectionError(request=httpx.Request("POST", "http://localhost:11434"))
        )

        with patch("app.services.nlp_service.AsyncOpenAI", return_value=mock_client):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "Test text for connection error."}
            )

        assert response.status_code == 503
        data = response.json()
        assert data["error_code"] == "OLLAMA_CONNECTION_ERROR"

    def test_analyze_llm_timeout(self, client):
        """Test: timeout del LLM devuelve 504."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=httpx.Request("POST", "http://localhost:11434"))
        )

        with patch("app.services.nlp_service.AsyncOpenAI", return_value=mock_client):
            response = client.post(
                "/api/v1/analyze",
                json={"text": "Test text for timeout."}
            )

        assert response.status_code == 504
        data = response.json()
        assert data["error_code"] == "LLM_TIMEOUT"


class TestHealthEndpoint:
    """Tests para el endpoint GET /api/v1/health."""

    def test_health_check_ok(self, client, mock_openai_client):
        """Test: health check cuando Ollama está disponible."""
        with patch("app.services.nlp_service.AsyncOpenAI", return_value=mock_openai_client):
            response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["ollama_connected"] is True
        assert "model_loaded" in data

    def test_health_check_ollama_down(self, client):
        """Test: health check cuando Ollama no está disponible."""
        mock_client = AsyncMock()
        mock_client.models.list = AsyncMock(side_effect=Exception("Connection refused"))

        with patch("app.services.nlp_service.AsyncOpenAI", return_value=mock_client):
            response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["ollama_connected"] is False
