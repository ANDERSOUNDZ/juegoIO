GAMES = {
    'platformer': {
        'dir': 'therapeutic',
        'label': 'Juegos Terapeuticos',
        'type': 'phaser',
    },
}


def get_game_info(game_type):
    return GAMES.get(game_type, GAMES['platformer'])
