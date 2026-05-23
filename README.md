# Mario DB Finger Tracker

Captura la posicion de los 5 dedos de la mano en tiempo real via camara web usando OpenCV + MediaPipe y los guarda en PostgreSQL. Disenado como interfaz de entrada gestual para un juego de Mario Bros de 5 niveles.

Cada dedo se representa como un bit (1 = arriba, 0 = abajo) y se almacena con el nivel actual del juego.

## Requisitos

- Python 3.8 - 3.11
- Camara web
- PostgreSQL 14+

## Instalacion (Windows con Anaconda)

```powershell
# 1. Crear entorno
conda create -n mario_tracker python=3.11 -y
conda activate mario_tracker

# 2. Ir al proyecto
cd C:\Users\ander\OneDrive\Escritorio\juegoIO\mario_db_tracker

# 3. Instalar librerias
pip install opencv-python mediapipe psycopg2-binary
```

## Instalacion PostgreSQL

**Op A - Instalacion directa:**
1. Descargar desde https://www.postgresql.org/download/windows/
2. Ejecutar el instalador, **anotar la contrasena** que asignes al usuario `postgres`
3. Marcar **pgAdmin** y **Command Line Tools**

**Op B - Docker (si lo tienes):**
```powershell
docker run --name pg-mario -e POSTGRES_PASSWORD=admin -p 5432:5432 -d postgres
```

## Crear base de datos (1 vez)

```powershell
# Abrir psql
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres

# Dentro de psql:
CREATE DATABASE mario_db;
\c mario_db
\i C:/Users/ander/OneDrive/Escritorio/juegoIO/mario_db_tracker/schema.sql
\q
```

O directo:
```powershell
psql -U postgres -c "CREATE DATABASE mario_db;"
psql -U postgres -d mario_db -f schema.sql
```

## Configurar y ejecutar

1. **Abrir `test_tracker.py`** y editar la contrasena de PostgreSQL en la linea 14:
   ```python
   DB_PASSWORD = "admin"   # <-- pon tu contraseña real aqui
   ```

2. **Ejecutar:**
   ```powershell
   conda activate mario_tracker
   python test_tracker.py
   ```

### Controles en pantalla

| Tecla | Accion |
|-------|--------|
| `1` - `5` | Cambia el nivel del juego |
| `q` | Salir |

## Logica de deteccion de dedos

| Dedo    | Logica |
|---------|--------|
| Pulgar  | Eje X (diferente segun mano derecha/izquierda) |
| Indice  | `y[8] < y[6]` |
| Medio   | `y[12] < y[10]` |
| Anular  | `y[16] < y[14]` |
| Menique | `y[20] < y[18]` |

## Envio a base de datos

Los datos se envian a PostgreSQL en un hilo separado (asincono) para no bloquear la camara:
- **Por cambio de estado**: cuando cualquier dedo cambia (0 a 1 o viceversa)
- **Heartbeat**: cada 200ms aunque el estado no cambie

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

**Error conexion PostgreSQL:**
- Verifica que el servicio este corriendo: `Get-Service postgresql*`
- Revisa que la contrasena en `test_tracker.py` linea 14 sea la correcta
- Prueba: `psql -U postgres -d mario_db`

**Error de camara:**
- Cambia `cv2.VideoCapture(0)` a `1` o `2` si tienes multiples camaras
- Revisa permisos de camara en Windows

**MediaPipe no se instala:**
- Usa Python 3.11 (no 3.12+)
- `pip install --upgrade mediapipe`
