# Servicio de Análisis de Texto (NLP / IA)

Mini-servicio backend desarrollado con FastAPI para el análisis de texto y documentos utilizando un LLM local a través de Ollama.

Proyecto realizado como prueba práctica para el proceso de selección de Desarrollo de IA (Candidato: Hugo Garmón Rey).

## Descripción

El servicio expone una API REST que recibe un texto y devuelve una estructura JSON con:
- Resumen del contenido.
- Análisis de sentimiento (clasificación y puntuación).
- Extracción de entidades clave (ubicaciones, personas, fechas, etc.).
- Temas principales detectados.
- Detección de idioma.

El procesamiento se apoya en Ollama mediante su API compatible con OpenAI (`/v1/chat/completions`), lo que permite desacoplar la lógica de negocio y cambiar el modelo o proveedor cambiando variables de entorno.

## Estructura del proyecto

```
├── app/
│   ├── config.py          # Configuración mediante pydantic-settings
│   ├── main.py            # Inicialización de FastAPI y middleware
│   ├── routers/
│   │   └── analyze.py     # Endpoints (/analyze y /health)
│   ├── schemas/
│   │   ├── requests.py    # Validación de entrada
│   │   └── responses.py   # Estructura y contrato de salida
│   ├── services/
│   │   └── nlp_service.py # Integración con Ollama / LLM
│   └── exceptions/
│       └── handlers.py    # Excepciones custom y manejadores HTTP
├── tests/
│   ├── conftest.py        # Mocks y fixtures para pytest
│   └── test_analyze.py    # Tests unitarios e integración
├── .env.example           # Plantilla de variables de entorno
├── Dockerfile             # Configuración Docker (multi-stage)
├── docker-compose.yml     # Orquestación de servicios
└── requirements.txt       # Dependencias del proyecto
```

## Requisitos previos

- Python 3.10+
- Ollama instalado y en ejecución
- Docker y Docker Compose (opcional)

## Instalación y ejecución local

1. Clonar el repositorio:
```bash
git clone https://github.com/HugoGarmon/Prueba-Practica-Gesico.git
cd Prueba-Practica-Gesico
```

2. Crear entorno virtual e instalar dependencias:
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

3. Variables de entorno:
```bash
cp .env.example .env
```
Asegurarse de tener en Ollama el modelo configurado en `LLM_MODEL` (por defecto `qwen2.5-coder:7b` o `qwen2.5:3b`):
```bash
ollama pull qwen2.5-coder:7b
```

4. Iniciar el servicio:
```bash
uvicorn app.main:app --reload
```
La API estará disponible en `http://localhost:8000`.

## Despliegue con Docker Compose

Para arrancar el servicio en contenedor:

```bash
docker-compose up -d --build
```

Nota: Si se ejecuta Ollama dentro del contenedor, será necesario asegurar la descarga del modelo en el volumen correspondiente (`docker exec -it gesico-ollama ollama pull qwen2.5-coder:7b`).

## Endpoints

### POST /api/v1/analyze

Analiza el texto enviado en el cuerpo de la petición.

**Ejemplo de petición:**
```bash
curl -X POST http://localhost:8000/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "text": "España e Italia firmaron un acuerdo comercial en Madrid para impulsar energías renovables en Europa.",
    "language": "es"
  }'
```

**Respuesta (200 OK):**
```json
{
  "summary": "España e Italia alcanzan un acuerdo en Madrid para fomentar las energías renovables en Europa.",
  "sentiment": "POSITIVE",
  "sentiment_score": 0.8,
  "entities": [
    {"name": "España", "category": "LOCATION"},
    {"name": "Italia", "category": "LOCATION"},
    {"name": "Madrid", "category": "LOCATION"}
  ],
  "key_topics": ["acuerdo comercial", "energías renovables"],
  "language": "es",
  "word_count": 16,
  "processing_time_ms": 1240.5
}
```

### GET /api/v1/health

Verifica el estado del servicio y la comunicación con Ollama.

```bash
curl http://localhost:8000/api/v1/health
```

### Documentación de la API

FastAPI genera la documentación OpenAPI de forma automática:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Tests

Las pruebas unitarias están aisladas con mocks del cliente del LLM, por lo que no requieren una instancia activa de Ollama para ejecutarse.

```bash
pytest tests/ -v
```

## Decisiones de diseño y seguridad

- **Seguridad**: Las variables sensibles y configuraciones de entorno se gestionan mediante `.env`, el cual está ignorado en `.gitignore`. En el Dockerfile se utiliza un usuario sin privilegios root.
- **Validación estricta**: Uso de Pydantic v2 para garantizar el formato del input y del output JSON devuelto.
- **Resiliencia**: Excepciones personalizadas para controlar caídas de servicio, timeouts y errores en las respuestas del LLM con códigos HTTP descriptivos (422, 502, 503, 504).
