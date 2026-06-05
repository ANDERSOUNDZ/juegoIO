GAMES = {
    'prince': {
        'dir': 'prince',
        'label': 'Prince of Persia',
        'type': 'wasm',
    },
    'smb3': {
        'dir': 'smb3',
        'label': 'Super Mario Bros. 3',
        'type': 'emulator',
    },
    # Tipo genérico y reutilizable para CUALQUIER ROM de emulador (NES, SNES,
    # GB, GBA, Genesis, …) vía Nostalgist.js. Para agregar un juego nuevo basta
    # una fila en `games` con metadata.type == 'emulator' y el bloque config
    # `emulator` (core, rom, aspectRatio) + controls.fingerMap — sin tocar código.
    'emulator': {
        'dir': 'emulator',
        'label': 'Emulador Retro',
        'type': 'emulator',
    },
    'platformer': {
        'dir': 'therapeutic',
        'label': 'Juegos Terapeuticos',
        'type': 'phaser',
    },
}


def get_game_info(game_type):
    return GAMES.get(game_type, GAMES['platformer'])
