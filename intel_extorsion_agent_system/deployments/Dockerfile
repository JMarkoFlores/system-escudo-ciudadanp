# IntelExtorsión Agent System - Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema para OCR, audio, build, etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-spa \
    libtesseract-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    build-essential \
    python3-dev \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

# Actualizar pip y setuptools para evitar errores con whisper
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Precargar modelo de embeddings fastembed para evitar descarga en el primer arranque
RUN python - <<'PY'
from fastembed import TextEmbedding
TextEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
print("Modelo fastembed precargado")
PY

# Crear directorio de uploads
RUN mkdir -p /app/uploads/evidencias

# Copiar código fuente
COPY app/ ./app/
COPY main.py .
COPY alembic.ini .
COPY alembic/ ./alembic/

# Puerto de la API
EXPOSE 8000

# Comando de inicio
CMD ["python", "main.py"]
