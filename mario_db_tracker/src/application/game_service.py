from datetime import datetime, timezone
from typing import Optional

from src.domain.entities import Game, PlayerGameConfig
from src.domain.exceptions import NotFoundError, ValidationError
from src.domain.interfaces.repositories import IGameRepository, IPlayerGameConfigRepository


class GameService:
    def __init__(
        self,
        game_repo: IGameRepository,
        config_repo: IPlayerGameConfigRepository,
    ):
        self._game_repo = game_repo
        self._config_repo = config_repo

    def list_all(self) -> list:
        return self._game_repo.find_all()

    def get_by_id(self, game_id: int) -> Game:
        g = self._game_repo.find_by_id(game_id)
        if not g:
            raise NotFoundError('Juego', game_id)
        return g

    def create(self, name: str, game_type: str, config: dict,
               description: Optional[str] = None,
               thumbnail_url: Optional[str] = None,
               created_by: Optional[int] = None) -> Game:
        if not name or not game_type or not config:
            raise ValidationError('name, game_type y config son requeridos')
        game = Game(
            name=name, game_type=game_type, config=config,
            description=description, thumbnail_url=thumbnail_url,
            created_by=created_by,
        )
        return self._game_repo.save(game)

    def update(self, game_id: int, data: dict) -> Game:
        g = self.get_by_id(game_id)
        for field in ('name', 'description', 'game_type', 'thumbnail_url', 'config'):
            if field in data:
                setattr(g, field, data[field])
        return self._game_repo.save(g)

    def delete(self, game_id: int) -> None:
        self.get_by_id(game_id)
        self._game_repo.delete(game_id)

    def get_config(self, game_id: int) -> dict:
        g = self.get_by_id(game_id)
        return g.config

    def get_player_config(self, game_id: int, patient_id: int) -> dict:
        self.get_by_id(game_id)
        pgc = self._config_repo.find_by_patient_and_game(patient_id, game_id)
        if pgc:
            return {
                'sensitivities': pgc.sensitivities,
                'finger_map': pgc.finger_map,
                'is_custom': True,
            }
        game = self._game_repo.find_by_id(game_id)
        controls = game.config.get('controls', {})
        return {
            'sensitivities': [50, 50, 50, 50, 50],
            'finger_map': controls.get('fingerMap', {}),
            'is_custom': False,
        }

    def save_player_config(self, game_id: int, patient_id: int, data: dict) -> dict:
        self.get_by_id(game_id)
        pgc = self._config_repo.find_by_patient_and_game(patient_id, game_id)
        if pgc:
            if 'sensitivities' in data:
                pgc.sensitivities = data['sensitivities']
            if 'finger_map' in data:
                pgc.finger_map = data['finger_map']
            pgc.updated_at = datetime.now(timezone.utc)
        else:
            pgc = PlayerGameConfig(
                patient_id=patient_id,
                game_id=game_id,
                sensitivities=data.get('sensitivities', [50, 50, 50, 50, 50]),
                finger_map=data.get('finger_map', {'0': 'jump', '1': 'right', '2': 'left', '3': 'none', '4': 'none'}),
            )
        saved = self._config_repo.save(pgc)
        return {'sensitivities': saved.sensitivities, 'finger_map': saved.finger_map}
