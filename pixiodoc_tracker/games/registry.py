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
    'platformer': {
        'dir': 'therapeutic',
        'label': 'Juegos Terapeuticos',
        'type': 'phaser',
    },
}


def get_game_info(game_type):
    return GAMES.get(game_type, GAMES['platformer'])
