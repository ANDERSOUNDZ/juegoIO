from typing import Optional

from src.domain.entities import Sprite
from src.domain.exceptions import NotFoundError, ValidationError
from src.domain.interfaces.repositories import ISpriteRepository


class SpriteService:
    def __init__(self, sprite_repo: ISpriteRepository):
        self._sprite_repo = sprite_repo

    def list_all(self, category: Optional[str] = None) -> list:
        return self._sprite_repo.find_all(category)

    def get_by_id(self, sprite_id: int) -> Sprite:
        s = self._sprite_repo.find_by_id(sprite_id)
        if not s:
            raise NotFoundError('Sprite', sprite_id)
        return s

    def create(self, name: str, category: str, type: str, width: int, height: int,
               data: Optional[dict] = None, image_url: Optional[str] = None,
               frame_count: int = 1, created_by: Optional[int] = None) -> Sprite:
        if not all([name, category, type, width, height]):
            raise ValidationError('name, category, type, width y height son requeridos')
        if type == 'pixelmap' and not data:
            raise ValidationError('data es requerido para tipo pixelmap')
        if type == 'image' and not image_url:
            raise ValidationError('image_url es requerido para tipo image')
        sprite = Sprite(
            name=name, category=category, type=type,
            width=width, height=height,
            data=data, image_url=image_url,
            frame_count=frame_count, created_by=created_by,
        )
        return self._sprite_repo.save(sprite)

    def update(self, sprite_id: int, data: dict) -> Sprite:
        s = self.get_by_id(sprite_id)
        for field in ('name', 'category', 'type', 'width', 'height', 'data', 'image_url', 'frame_count'):
            if field in data:
                setattr(s, field, data[field])
        return self._sprite_repo.save(s)

    def delete(self, sprite_id: int) -> None:
        self.get_by_id(sprite_id)
        self._sprite_repo.delete(sprite_id)

    def get_batch(self, ids: list) -> list:
        if not ids:
            return []
        return self._sprite_repo.find_by_ids(ids)
