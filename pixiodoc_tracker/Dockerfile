FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema: WeasyPrint (GTK/Pango/Cairo)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
    libgdk-pixbuf-2.0-0 libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar librerías Python desde wheels locales (sin internet)
COPY py_deps/ /app/py_deps/
COPY requirements.txt .
RUN pip install --no-cache-dir --no-index --find-links=/app/py_deps -r requirements.txt && \
    rm -rf /app/py_deps

# Copiar el resto del código fuente (incluye vendor/ ya descargado en el repo)
COPY . .

EXPOSE 5000

CMD ["python", "server.py"]
