# 🧠 NLP Analysis API

Mini-servicio backend para análisis de texto usando un LLM local (Ollama + Qwen2.5) desarrollado con FastAPI.

> **Prueba práctica** — Proceso de selección para puesto de Desarrollo de IA.

## 📋 Descripción

Servicio REST que recibe un texto y devuelve un análisis completo en formato JSON:

- **Resumen** conciso del contenido
- **Análisis de sentimiento** (positivo/neutro/negativo + puntuación)
- **Extracción de entidades** (personas, organizaciones, lugares, fechas, etc.)
- **Detección de temas** principales
- **Detección de idioma** automática

El procesamiento se realiza mediante un LLM local ejecutado en GPU a través de [Ollama](https://ollama.com/), lo que garantiza privacidad total de los datos y cero dependencia de servicios externos.

## 🏗️ Arquitectura

```
Cliente (curl/Postman) → FastAPI (:8000) → Ollama (:11434) → Qwen2.5:3b (GPU)
```

El servicio utiliza la API compatible con OpenAI que expone Ollama, lo que permite cambiar fácilmente entre un LLM local y una API externa (OpenAI, Groq, etc.) modificando únicamente las variables de entorno.

### Flujo de una petición

1. El cliente envía texto al endpoint `POST /api/v1/analyze`
2. FastAPI valida la entrada con Pydantic
3. El servicio NLP construye un prompt estructurado y lo envía a Ollama
4. Ollama ejecuta el modelo en la GPU con output JSON forzado
5. FastAPI valida la respuesta, añade metadatos y la devuelve al cliente

## 📁 Estructura del proyecto

```
├── app/
│   ├── config.py               # Configuración (variables de entorno)
│   ├── main.py                 # App FastAPI, middleware, lifespan
│   ├── routers/
│   │   └── analyze.py          # Endpoints de análisis y health check
│   ├── schemas/
│   │   ├── requests.py         # Modelos de entrada (validación)
│   │   └── responses.py        # Modelos de salida (contrato API)
│   ├── services/
│   │   └── nlp_service.py      # Lógica de negocio (comunicación con Ollama)
│   └── exceptions/
│       └── handlers.py         # Excepciones custom y handlers globales
├── tests/
│   ├── conftest.py             # Fixtures y mocks
│   └── test_analyze.py         # Tests del endpoint (10 tests)
├── .env.example                # Plantilla de variables de entorno
├── Dockerfile                  # Imagen de la app (multi-stage, non-root)
├── docker-compose.yml          # Stack completo: Ollama (GPU) + FastAPI
└── requirements.txt            # Dependencias Python
```

## ⚙️ Requisitos previos

- **Python** 3.12+
- **Ollama** ([descargar](https://ollama.com/download))
- **GPU NVIDIA** con ≥ 4 GB VRAM (recomendado; funciona también en CPU)
- **Docker** y **Docker Compose** (opcional, para despliegue containerizado)

## 🚀 Instalación y ejecución

### Opción 1: Ejecución local

```bash
# 1. Clonar el repositorio
git clone https://github.com/HugoGarmon/Prueba-Practica-Gesico.git
cd Prueba-Practica-Gesico

# 2. Descargar el modelo de IA (solo la primera vez, ~2 GB)
ollama pull qwen2.5:3b

# 3. Crear entorno virtual e instalar dependencias
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env si es necesario (los valores por defecto funcionan)

# 5. Arrancar el servidor
uvicorn app.main:app --reload
```

El servidor estará disponible en `http://localhost:8000`.

### Opción 2: Docker Compose

```bash
# Arrancar el stack completo (Ollama con GPU + FastAPI)
docker-compose up --build

# En otra terminal, descargar el modelo dentro del contenedor
docker exec gesico-ollama ollama pull qwen2.5:3b
```

> **Nota**: Docker requiere drivers NVIDIA y WSL2 en Windows para acceso a GPU.

## 📡 Endpoints

### `POST /api/v1/analyze` — Analizar texto

**Request:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "España lidera la transición energética en Europa con inversiones millonarias en energía solar y eólica. El gobierno ha aprobado un plan de 25.000 millones de euros para los próximos cinco años.",
    "language": "es"
  }'
```

**Response (200 OK):**
```json
{
  "summary": "España encabeza la transición energética europea con un plan de inversión de 25.000 millones de euros en energías renovables para los próximos cinco años.",
  "sentiment": "POSITIVE",
  "sentiment_score": 0.75,
  "entities": [
    {"name": "España", "category": "LOCATION"},
    {"name": "Europa", "category": "LOCATION"},
    {"name": "25.000 millones de euros", "category": "MISC"},
    {"name": "cinco años", "category": "DATE"}
  ],
  "key_topics": ["energía renovable", "transición energética", "inversión pública", "política energética"],
  "language": "es",
  "word_count": 32,
  "processing_time_ms": 1250.45
}
```

El campo `language` en el request es opcional; si no se proporciona, el modelo detecta el idioma automáticamente.

### `GET /api/v1/health` — Health check

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "ok",
  "ollama_connected": true,
  "model_loaded": "qwen2.5:3b"
}
```

### Documentación interactiva

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Tests

Los tests utilizan mocks del servicio LLM, por lo que no requieren Ollama ni GPU para ejecutarse.

```bash
# Activar el entorno virtual
.\venv\Scripts\activate    # Windows
# source venv/bin/activate # Linux/Mac

# Ejecutar tests
pytest tests/ -v
```

```
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_valid_text         PASSED
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_with_language      PASSED
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_empty_text         PASSED
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_missing_text       PASSED
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_text_too_long      PASSED
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_invalid_language   PASSED
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_ollama_down        PASSED
tests/test_analyze.py::TestAnalyzeEndpoint::test_analyze_llm_timeout        PASSED
tests/test_analyze.py::TestHealthEndpoint::test_health_check_ok             PASSED
tests/test_analyze.py::TestHealthEndpoint::test_health_check_ollama_down    PASSED

10 passed in 0.15s
```

## 🔐 Seguridad

- Las credenciales y configuración sensible se gestionan exclusivamente mediante **variables de entorno** (archivo `.env`).
- El archivo `.env` está incluido en `.gitignore` y **nunca se sube al repositorio**.
- Se proporciona `.env.example` como plantilla sin valores sensibles.
- El Dockerfile utiliza un **usuario no-root** para minimizar la superficie de ataque.

## 🔧 Variables de entorno

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `OLLAMA_BASE_URL` | URL del servicio Ollama | `http://localhost:11434` |
| `LLM_MODEL` | Modelo a utilizar | `qwen2.5:3b` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `APP_HOST` | Host de la aplicación | `0.0.0.0` |
| `APP_PORT` | Puerto de la aplicación | `8000` |

## 🛠️ Decisiones técnicas

| Decisión | Justificación |
|---|---|
| **Ollama + Qwen2.5:3b** | LLM local que corre en GPU con ~2.6 GB VRAM. Sin costes, sin dependencias externas, privacidad total. Excelente calidad en análisis de texto multilingüe. |
| **API compatible OpenAI** | Ollama expone `/v1/chat/completions`. Esto permite usar el SDK oficial de OpenAI (`openai.AsyncOpenAI`) y cambiar a una API externa sin modificar código. |
| **Prompt único multi-tarea** | Una sola llamada al LLM para obtener resumen + sentimiento + entidades + temas. Reduce latencia de ~4s a ~1s. |
| **Pydantic v2** | Validación estricta de entrada y salida. Garantiza el contrato de la API y documenta automáticamente en OpenAPI. |
| **Async/await** | Todo el I/O es asíncrono (FastAPI + AsyncOpenAI), permitiendo alta concurrencia sin bloquear el event loop. |
| **Excepciones personalizadas** | Jerarquía de excepciones con códigos HTTP apropiados (503, 504, 502, 500). Respuestas de error consistentes en JSON. |
| **Docker multi-stage** | Imagen ligera (~150 MB) con usuario no-root. `docker-compose` orquesta Ollama (GPU) + FastAPI. |
| **Tests con mocks** | Tests que no requieren GPU ni modelo descargado. Verifican validación, manejo de errores y respuestas. |

## 📝 Manejo de errores

| Código HTTP | Error | Escenario |
|---|---|---|
| `422` | Validation Error | Entrada inválida (texto vacío, demasiado largo, idioma mal formateado) |
| `500` | Internal Server Error | Error inesperado durante el procesamiento |
| `502` | Bad Gateway | El LLM devolvió un JSON malformado |
| `503` | Service Unavailable | Ollama no está corriendo o el modelo no está disponible |
| `504` | Gateway Timeout | El modelo tardó demasiado en responder |
