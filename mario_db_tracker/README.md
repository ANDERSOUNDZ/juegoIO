# Mario DB Finger Tracker

Captura la posicion de los 5 dedos de la mano en tiempo real via camara web usando OpenCV + MediaPipe y los guarda en PostgreSQL. Disenado como interfaz de entrada gestual para un juego de Mario Bros de 5 niveles.

Cada dedo se representa como un bit (1 = arriba, 0 = abajo) y se almacena con el nivel actual del juego.

## Requisitos

- Python 3.8 - 3.11
- Camara web
- PostgreSQL 14+

## Instalacion

### 1. Clonar / ir al proyecto

```bash
cd mario_db_tracker
```

### 2. Crear entorno virtual

**Windows (Anaconda):**
```bash
conda create -n mario_tracker python=3.11 -y
conda activate mario_tracker
```

**Windows (venv):**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Instalar y configurar PostgreSQL

**Windows:**
1. Descargar desde https://www.postgresql.org/download/windows/
2. Ejecutar el instalador, anotar la contrasena del usuario `postgres`
3. Durante la instalacion marcar **pgAdmin** y **Command Line Tools**

**Linux (Debian/Ubuntu):**
```bash
sudo apt update
sudo apt install postgresql postgresql-client -y
sudo systemctl start postgresql
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install postgresql-server postgresql-contrib -y
sudo postgresql-setup --initdb
sudo systemctl start postgresql
```

**macOS (Homebrew):**
```bash
brew install postgresql@16
brew services start postgresql@16
```

**O usar Docker (cualquier SO):**
```bash
docker run --name pg-mario -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres
```

### 5. Crear base de datos y tabla

```bash
# Conectar a PostgreSQL
psql -U postgres

# Dentro de psql ejecutar:
CREATE DATABASE mario_db;
\c mario_db
\i ruta/completa/a/schema.sql
\q
```

O directamente:
```bash
psql -U postgres -c "CREATE DATABASE mario_db;"
psql -U postgres -d mario_db -f schema.sql
```

### 6. Configurar credenciales

Copia `.env.example` a `.env` y editalo con tus datos:

```bash
cp .env.example .env   # Linux / macOS
# En Windows: copia manual o: copy .env.example .env
```

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mario_db
DB_USER=postgres
DB_PASSWORD=admin
```

## Uso

```bash
# Activar entorno (si no lo esta)
conda activate mario_tracker   # Anaconda
# o
source venv/bin/activate       # Linux/macOS
# o
venv\Scripts\activate          # Windows venv

# Ejecutar
python test_tracker.py
```

### Controles

| Tecla | Accion |
|-------|--------|
| `1` - `5` | Cambia el nivel del juego |
| `q` | Salir |

### Logica de deteccion de dedos

| Dedo    | Logica |
|---------|--------|
| Pulgar  | Eje X (diferente segun mano derecha/izquierda) |
| Indice  | `y[8] < y[6]` |
| Medio   | `y[12] < y[10]` |
| Anular  | `y[16] < y[14]` |
| Menique | `y[20] < y[18]` |

### Envio a base de datos

Los datos se envian a PostgreSQL en un hilo separado (asincono) para no bloquear la camara:

- **Por cambio de estado**: cuando cualquier dedo cambia (0 a 1 o viceversa)
- **Heartbeat**: cada 200ms aunque el estado no cambie, para mantener la senal de vida

## Esquema de base de datos

```sql
CREATE TABLE control_juego (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    nivel INT CHECK (nivel BETWEEN 1 AND 5),
    pulgar INT CHECK (pulgar IN (0, 1)),
    indice INT CHECK (indice IN (0, 1)),
    medio INT CHECK (medio IN (0, 1)),
    anular INT CHECK (anular IN (0, 1)),
    menique INT CHECK (menique IN (0, 1))
);
```

## Solucion de problemas

**Error: "No se puede conectar a PostgreSQL"**
- Verifica que PostgreSQL este corriendo: `sudo systemctl status postgresql` (Linux) o `Get-Service postgresql*` (Windows)
- Revisa las credenciales en `.env`
- Prueba conexion manual: `psql -U postgres -d mario_db`

**Error: "No se detecta camara"**
- Prueba con otra aplicacion de camara primero
- Revisa permisos de camara en el SO
- Cambia el indice en `cv2.VideoCapture(0)` a `1` o `2` si tienes multiples camaras

**Error: "mediapipe no instalado"**
- Asegurate de usar Python 3.8 - 3.11 (MediaPipe no soporta 3.12+)
- Reinstala: `pip install --upgrade mediapipe`
