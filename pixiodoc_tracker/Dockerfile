FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema: WeasyPrint (GTK/Pango/Cairo) + curl (para vendor)
RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
    libgdk-pixbuf-2.0-0 libffi-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Descargar dependencias frontend (Phaser, Fomantic, MediaPipe, etc.)
COPY tools/download-vendor.sh .
RUN bash download-vendor.sh && rm download-vendor.sh

# Copiar el resto del código fuente
COPY . .

EXPOSE 5000

CMD ["python", "server.py"]
