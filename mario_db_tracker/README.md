# PIXO Therapy - Juegos Terapéuticos

Plataforma de juegos terapéuticos controlados por gestos de la mano mediante MediaPipe Hand Tracking. Terapeutas gestionan pacientes, configuran sensibilidad, ejecutan sesiones y monitorean el progreso.

## Requisitos

- **Docker Desktop** instalado y corriendo
- **Python 3.8 - 3.14**
- **Cámara web**

## Inicio rápido

```powershell
# 1. Levantar PostgreSQL + pgAdmin
docker compose up -d

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Iniciar servidor
python server.py

# 4. Abrir http://localhost:5000
```

## Servicios Docker

| Contenedor | Puerto | Acceso |
|---|---|---|
| **PostgreSQL 16** | `5432` | Localhost |
| **pgAdmin 4** | `5050` | http://localhost:5050 |

pgAdmin: `admin@admin.com` / `admin`

## Estructura del proyecto

```
mario_db_tracker/
├── server.py                  # Entry point Flask
├── docker-compose.yml         # PostgreSQL + pgAdmin
├── requirements.txt           # Dependencias Python
├── app/
│   ├── __init__.py            # App factory
│   ├── config.py              # Configuración
│   ├── models.py              # Modelos SQLAlchemy
│   ├── auth.py                # Login/registro
│   ├── routes.py              # Rutas de páginas
│   ├── db_worker.py           # Worker async para inserts
│   ├── hand_tracking.py       # Detección MediaPipe
│   ├── ws.py                  # WebSocket (mano en tiempo real)
│   └── api/                   # APIs REST
│       ├── patients.py        # Pacientes + sensibilidad
│       ├── games.py           # Juegos + config por paciente
│       ├── sessions.py        # Sesiones + reportes
│       ├── sensitivity.py     # Presets de sensibilidad
│       └── sprites.py         # Sprites reutilizables
├── static/
│   ├── css/platform.css       # Tema retro pixel art
│   └── js/
│       ├── hand-input.js      # Cliente WebSocket + cámara
│       ├── game-loader.js     # Intérprete Phaser 3
│       └── sprite-generator.js# Renderizador de sprites
└── templates/
    ├── base.html              # Layout principal
    ├── login.html             # Inicio de sesión
    ├── register.html          # Registro
    ├── dashboard.html         # Panel del terapeuta
    ├── patients.html          # Lista de pacientes
    ├── patient_detail.html    # Detalle + sensibilidad
    ├── games.html             # Catálogo de juegos
    ├── play.html              # Ejecutor Phaser 3
    └── report.html            # Reportes con Chart.js
```

## Controles del juego

### Gestos de mano

| Dedo | Acción por defecto |
|---|---|
| Pulgar | Saltar |
| Índice | Derecha |
| Medio | Izquierda |

Configurable por paciente en la interfaz.

### Teclado (alternativa)

| Tecla | Acción |
|---|---|
| `↑` | Saltar |
| `→` | Derecha |
| `←` | Izquierda |

## Comandos útiles

```powershell
# Docker
docker compose up -d          # Iniciar servicios
docker compose down           # Detener (conserva datos)
docker compose down -v        # Detener y borrar datos
docker compose logs -f        # Ver logs
docker compose exec postgres psql -U postgres -d mario_db  # Acceder a DB

# Servidor
python server.py              # Iniciar (Ctrl+C para detener)
```
