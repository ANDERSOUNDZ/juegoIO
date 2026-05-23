# Mario DB Finger Tracker

Captura la posicion de los 5 dedos de la mano en tiempo real via camara web usando OpenCV + MediaPipe y los guarda en PostgreSQL. Incluye un servidor web con stream de video y un juego plataformero (Doodle Jump) controlado por gestos.

## Estructura del proyecto

```
juegoIO/
├── schema.sql                     # Esquema de la base de datos PostgreSQL
├── test_tracker.py                # Version standalone (sin servidor web)
├── mario_db_tracker/
│   ├── server.py                  # Servidor Flask: camara + deteccion + DB + web
│   ├── docker-compose.yml         # PostgreSQL + pgAdmin en Docker
│   ├── requirements.txt           # Dependencias Python
│   ├── templates/
│   │   └── index.html             # Cliente web: video stream + juego canvas
│   └── README.md                  # Esta documentacion
```

## Requisitos

- **Windows** con **Docker Desktop** instalado y corriendo
- **Python 3.8 - 3.14** (cualquier version moderna)
- **Camara web**

## Paso 1: Levantar PostgreSQL + pgAdmin con Docker

```powershell
# Desde la carpeta mario_db_tracker
cd mario_db_tracker

# Iniciar los contenedores
docker compose up -d
```

Esto levanta dos servicios:

| Contenedor | Puerto | Acceso |
|---|---|---|
| **mario-postgres** (PostgreSQL 16) | `5432` | Localhost |
| **mario-pgadmin** (pgAdmin 4) | `5050` | Navegador web |

La base de datos `mario_db` y la tabla `control_juego` se crean automaticamente al iniciar por primera vez.

Para verificar que estan corriendo:

```powershell
docker compose ps
```

## Paso 2: Acceder a pgAdmin (opcional)

1. Abre **http://localhost:5050** en tu navegador
2. Inicia sesion con:
   - **Email:** `admin@admin.com`
   - **Contrasena:** `admin`
3. Para conectar al servidor PostgreSQL:
   - Click en "Add New Server"
   - **Name:** `Mario DB` (o el que quieras)
   - **Pestaña Connection:**
     - **Host:** `postgres` (nombre del servicio Docker)
     - **Port:** `5432`
     - **Maintenance DB:** `mario_db`
     - **Username:** `postgres`
     - **Password:** `admin`
   - Click "Save"

Ahora puedes explorar la tabla `control_juego` y ver los datos en tiempo real mientras juegas.

## Paso 3: Instalar dependencias Python

```powershell
pip install -r requirements.txt
```

Esto instala: `opencv-python`, `mediapipe`, `psycopg2-binary`, `flask`

## Paso 4: Configurar la contrasena de PostgreSQL

Si usas el Docker Compose (recomendado), **no necesitas cambiar nada**. La configuracion en `server.py` ya coincide:

```python
DB_HOST = "localhost"    # mario-postgres expuesto en localhost
DB_PORT = 5432
DB_NAME = "mario_db"
DB_USER = "postgres"
DB_PASSWORD = "admin"    # misma contrasena que en docker-compose.yml
```

## Paso 5: Iniciar el servidor

```powershell
python server.py
```

La primera vez descargara el modelo `hand_landmarker.task` (~15MB). Luego veras:

```
[SERVER] Camara iniciada
[SERVER] Abre http://localhost:5000 en tu navegador
```

## Paso 6: Abrir el juego

Ve a **http://localhost:5000**

Veras dos paneles:
- **Izquierda:** Stream de la camara con deteccion de mano y estado de cada dedo
- **Derecha:** Juego plataformero (Doodle Jump)

## Controles del juego

### Gestos de la mano

| Dedo | Accion |
|---|---|
| Pulgar arriba | Saltar |
| Indice arriba | Moverse derecha |
| Medio arriba | Moverse izquierda |

### Teclado (alternativa)

| Tecla | Accion |
|---|---|
| `Flecha arriba` | Saltar |
| `Flecha derecha` | Derecha |
| `Flecha izquierda` | Izquierda |
| `1` - `5` | Cambiar nivel de dificultad |
| `R` | Reiniciar despues de Game Over |

### Niveles

Cada nivel aumenta la dificultad reduciendo la separacion entre plataformas. La dificultad se refleja en el espaciado de las plataformas y la velocidad del juego.

## Base de datos

La tabla `control_juego` guarda:

| Columna | Tipo | Descripcion |
|---|---|---|
| `id` | SERIAL | Identificador unico |
| `timestamp` | TIMESTAMPTZ | Momento del registro |
| `nivel` | INT (1-5) | Nivel actual del juego |
| `pulgar` | INT (0/1) | Estado del pulgar |
| `indice` | INT (0/1) | Estado del indice |
| `medio` | INT (0/1) | Estado del medio |
| `anular` | INT (0/1) | Estado del anular |
| `menique` | INT (0/1) | Estado del menique |

Los datos se guardan:
- **Por cambio de estado:** cuando cualquier dedo cambia
- **Heartbeat:** cada 200ms aunque no haya cambio

## Comandos utiles

### Docker

```powershell
# Iniciar contenedores
docker compose up -d

# Ver logs
docker compose logs -f

# Detener (sin borrar datos)
docker compose down

# Detener y borrar datos de la DB
docker compose down -v

# Ver estado
docker compose ps

# Acceder a PostgreSQL dentro del contenedor
docker compose exec postgres psql -U postgres -d mario_db
```

### Servidor Python

```powershell
# Iniciar servidor
python server.py

# Detener servidor: Ctrl + C en la terminal
```

## Solucion de problemas

**Error: "python" abre Microsoft Store**
- Usa `py server.py` en lugar de `python server.py`
- O desactiva los alias de Python en: Configuracion > Aplicaciones > Aliases de ejecucion

**Error de conexion a PostgreSQL**
- Verifica que Docker Desktop este corriendo
- Verifica que los contenedores esten activos: `docker compose ps`
- Revisa logs: `docker compose logs postgres`

**Error de camara**
- Cambia `cv2.VideoCapture(0)` a `1` o `2` en `server.py` si tienes multiples camaras
- Revisa permisos de camara en Windows (Configuracion > Privacidad > Camara)
