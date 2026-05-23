-- Creación de la tabla para almacenar la posición de los dedos en tiempo real
CREATE TABLE IF NOT EXISTS control_juego (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    nivel INT NOT NULL CHECK (nivel BETWEEN 1 AND 5),
    pulgar INT NOT NULL CHECK (pulgar IN (0, 1)),
    indice INT NOT NULL CHECK (indice IN (0, 1)),
    medio INT NOT NULL CHECK (medio IN (0, 1)),
    anular INT NOT NULL CHECK (anular IN (0, 1)),
    menique INT NOT NULL CHECK (menique IN (0, 1))
);

-- Índice para mejorar consultas rápidas ordenadas por tiempo
CREATE INDEX IF NOT EXISTS idx_control_juego_timestamp ON control_juego(timestamp DESC);
