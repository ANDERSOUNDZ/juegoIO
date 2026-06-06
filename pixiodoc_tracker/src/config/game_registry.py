GAMES = {
    # Tipo genérico y reutilizable para CUALQUIER ROM de emulador (NES, SNES,
    # GB, GBA, Genesis, …) vía Nostalgist.js. Para agregar un juego nuevo basta
    # una fila en `games` con metadata.type == 'emulator' y el bloque config
    # `emulator` (core, rom, aspectRatio) + controls.fingerMap — sin tocar código.
    'emulator': {
        'dir': 'emulator',
        'label': 'Emulador Retro',
        'type': 'emulator',
    },
    # Juegos Phaser: se renderizan con templates/play.html directamente
    # (no usan una carpeta propia aquí), por eso no llevan 'dir'.
    'platformer': {
        'label': 'Juegos Terapeuticos',
        'type': 'phaser',
    },
}


def get_game_info(game_type):
    return GAMES.get(game_type, GAMES['platformer'])
