# Mario DB Finger Tracker 🎮🖐️

Captura la posicion de los 5 dedos de la mano en tiempo real via camara web usando OpenCV + MediaPipe y los guarda en PostgreSQL. Incluye un servidor web con stream de video y un juego plataformero controlado por gestos.

## Estructura

```
mario_db_tracker/
├── server.py              # Servidor Flask: camara + deteccion + DB + web
├── templates/
│   └── index.html         # Pagina web: video stream + juego canvas
├── requirements.txt       # Dependencias
├── schema.sql             # Tabla PostgreSQL
└── README.md
```

## Requisitos

- Python 3.8 - 3.11
- Camara web
- PostgreSQL 14+

## Instalacion

### 1. Entorno virtual

```bash
conda create -n mario_tracker python=3.11 -y
conda activate mario_tracker
```

### 2. Dependencias

```bash
pip install -r requirements.txt
```

### 3. PostgreSQL

**Instalacion directa:** https://www.postgresql.org/download/

**O con Docker:**
```bash
docker run --name pg-mario -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres
```

### 4. Crear base de datos (1 vez)

```bash
psql -U postgres -c "CREATE DATABASE mario_db;"
psql -U postgres -d mario_db -f schema.sql
```

### 5. Configurar

Abrir `server.py` y editar la contraseña de PostgreSQL en la linea 12:
```python
DB_PASSWORD = "admin"   # <-- tu contraseña real
```

## Ejecutar

```bash
conda activate mario_tracker
python server.py
```

Abrir en el navegador: **http://localhost:5000**

## Controles

### Dedos → Juego

| Dedo | Accion |
|------|--------|
| Pulgar | Saltar |
| Indice | Moverse derecha |
| Medio | Moverse izquierda |

### Teclado (alternativa)

| Tecla | Accion |
|-------|--------|
| `↑` | Saltar |
| `→` | Derecha |
| `←` | Izquierda |
| `1`-`5` | Cambiar nivel |
| `R` | Reiniciar (Game Over) |

## Envio a DB

Los datos se guardan en PostgreSQL en un hilo separado:
- **Por cambio**: cuando cualquier dedo cambia de estado
- **Heartbeat**: cada 200ms aunque no haya cambio
