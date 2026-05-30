from src.domain.entities import SensitivityPreset
from src.domain.exceptions import ValidationError
from src.domain.interfaces.repositories import ISensitivityPresetRepository
from src.domain.value_objects import Sensitivity


class SensitivityService:
    def __init__(self, preset_repo: ISensitivityPresetRepository):
        self._preset_repo = preset_repo

    def list_presets(self) -> list:
        return self._preset_repo.find_all()

    def create_preset(self, name: str, sensitivities: list,
                      description: str = None,
                      difficulty_level: str = 'custom',
                      created_by: int = None) -> SensitivityPreset:
        if not name:
            raise ValidationError('name es requerido')
        Sensitivity.from_list(sensitivities)

        preset = SensitivityPreset(
            name=name, description=description,
            difficulty_level=difficulty_level,
            sensitivities=sensitivities,
            created_by=created_by,
        )
        return self._preset_repo.save(preset)
