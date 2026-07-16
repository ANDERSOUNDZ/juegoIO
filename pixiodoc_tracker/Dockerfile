FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema: WeasyPrint (GTK/Pango/Cairo) + curl (para vendor)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
    libgdk-pixbuf-2.0-0 libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código fuente (incluye vendor/ ya descargado en el repo)
COPY . .

EXPOSE 5000

CMD ["python", "server.py"]
