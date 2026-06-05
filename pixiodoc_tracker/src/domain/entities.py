from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class Role:
    id: Optional[int] = None
    name: str = ''
    description: Optional[str] = None

@dataclass
class User:
    id: Optional[int] = None
    email: str = ''
    password_hash: str = ''
    name: str = ''
    lastname: str = ''
    role_id: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class Patient:
    id: Optional[int] = None
    therapist_id: Optional[int] = None
    user_id: Optional[int] = None
    name: str = ''
    lastname: str = ''
    document: str = ''
    birth_date: Optional[str] = None
    age: Optional[int] = None
    diagnosis: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    patient_user: Optional[User] = None


@dataclass
class Game:
    id: Optional[int] = None
    name: str = ''
    description: Optional[str] = None
    game_type: str = ''
    thumbnail_url: Optional[str] = None
    config: dict = field(default_factory=dict)
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class GameSession:
    id: Optional[int] = None
    patient_id: Optional[int] = None
    game_id: Optional[int] = None
    user_id: Optional[int] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    score: int = 0
    metadata_: Optional[dict] = None


@dataclass
class FingerEvent:
    id: Optional[int] = None
    session_id: Optional[int] = None
    timestamp: Optional[datetime] = None
    finger_index: int = 0
    state: int = 0
    landmark_x: Optional[float] = None
    landmark_y: Optional[float] = None
    landmark_z: Optional[float] = None
    confidence: Optional[float] = None


@dataclass
class SensitivityPreset:
    id: Optional[int] = None
    name: str = ''
    description: Optional[str] = None
    difficulty_level: Optional[str] = None
    sensitivities: list = field(default_factory=lambda: [50, 50, 50, 50, 50])
    is_default: bool = False
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass
class PatientSensitivity:
    id: Optional[int] = None
    patient_id: Optional[int] = None
    sensitivities: list = field(default_factory=lambda: [50, 50, 50, 50, 50])
    based_on_preset: Optional[int] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[int] = None


@dataclass
class SensitivityHistory:
    id: Optional[int] = None
    patient_id: Optional[int] = None
    old_sensitivities: Optional[list] = None
    new_sensitivities: list = field(default_factory=lambda: [50, 50, 50, 50, 50])
    reason: Optional[str] = None
    changed_by: Optional[int] = None
    changed_at: Optional[datetime] = None


@dataclass
class PlayerGameConfig:
    id: Optional[int] = None
    patient_id: Optional[int] = None
    game_id: Optional[int] = None
    sensitivities: list = field(default_factory=lambda: [50, 50, 50, 50, 50])
    finger_map: dict = field(default_factory=lambda: {'0': 'jump', '1': 'right', '2': 'left', '3': 'none', '4': 'none'})
    updated_at: Optional[datetime] = None


@dataclass
class Sprite:
    id: Optional[int] = None
    name: str = ''
    category: str = ''
    type: str = 'pixelmap'
    width: int = 0
    height: int = 0
    data: Optional[dict] = None
    image_url: Optional[str] = None
    frame_count: int = 1
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
