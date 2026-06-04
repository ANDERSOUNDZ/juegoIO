from abc import ABC, abstractmethod
from typing import Optional, List

from ..entities import (
    User, Patient, Game, GameSession, FingerEvent,
    SensitivityPreset, PatientSensitivity, SensitivityHistory,
    PlayerGameConfig, Sprite,
)

class IUserRepository(ABC):
    @abstractmethod
    def find_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    def find_by_email(self, email: str) -> Optional[User]: ...

    @abstractmethod
    def save(self, user: User) -> User: ...


class IPatientRepository(ABC):
    @abstractmethod
    def find_by_id(self, patient_id: int) -> Optional[Patient]: ...

    @abstractmethod
    def find_by_user_id(self, user_id: int, user_role: str = 'therapist') -> List[Patient]: ...

    @abstractmethod
    def find_by_user_id_paginated(self, therapist_id: int, page: int, per_page: int, user_role: str = 'therapist') -> dict: ...

    @abstractmethod
    def save(self, patient: Patient) -> Patient: ...

    @abstractmethod
    def delete(self, patient_id: int) -> None: ...


class IGameRepository(ABC):
    @abstractmethod
    def find_by_id(self, game_id: int) -> Optional[Game]: ...

    @abstractmethod
    def find_all(self) -> List[Game]: ...

    @abstractmethod
    def save(self, game: Game) -> Game: ...

    @abstractmethod
    def delete(self, game_id: int) -> None: ...


class ISessionRepository(ABC):
    @abstractmethod
    def find_by_id(self, session_id: int) -> Optional[GameSession]: ...

    @abstractmethod
    def find_by_user_id(
        self, user_id: int,
        patient_id: Optional[int] = None,
        game_id: Optional[int] = None,
        limit: int = 100,
        user_role: str = 'therapist',
    ) -> List[GameSession]: ...

    @abstractmethod
    def save(self, session: GameSession) -> GameSession: ...


class IFingerEventRepository(ABC):
    @abstractmethod
    def find_by_session_id(self, session_id: int) -> List[FingerEvent]: ...

    @abstractmethod
    def save_batch(self, events: List[FingerEvent]) -> None: ...


class ISensitivityPresetRepository(ABC):
    @abstractmethod
    def find_all(self) -> List[SensitivityPreset]: ...

    @abstractmethod
    def save(self, preset: SensitivityPreset) -> SensitivityPreset: ...


class IPatientSensitivityRepository(ABC):
    @abstractmethod
    def find_by_patient_id(self, patient_id: int) -> Optional[PatientSensitivity]: ...

    @abstractmethod
    def save(self, sensitivity: PatientSensitivity) -> PatientSensitivity: ...


class ISensitivityHistoryRepository(ABC):
    @abstractmethod
    def find_by_patient_id(self, patient_id: int) -> List[SensitivityHistory]: ...

    @abstractmethod
    def save(self, history: SensitivityHistory) -> SensitivityHistory: ...


class IPlayerGameConfigRepository(ABC):
    @abstractmethod
    def find_by_patient_and_game(self, patient_id: int, game_id: int) -> Optional[PlayerGameConfig]: ...

    @abstractmethod
    def save(self, config: PlayerGameConfig) -> PlayerGameConfig: ...


class ISpriteRepository(ABC):
    @abstractmethod
    def find_by_id(self, sprite_id: int) -> Optional[Sprite]: ...

    @abstractmethod
    def find_by_ids(self, sprite_ids: list) -> List[Sprite]: ...

    @abstractmethod
    def find_all(self, category: Optional[str] = None) -> List[Sprite]: ...

    @abstractmethod
    def save(self, sprite: Sprite) -> Sprite: ...

    @abstractmethod
    def delete(self, sprite_id: int) -> None: ...
