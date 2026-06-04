from typing import Optional, List

from src.domain.entities import (
    Role, User, Patient, Game, GameSession, FingerEvent,
    SensitivityPreset, PatientSensitivity, SensitivityHistory,
    PlayerGameConfig, Sprite,
)
from src.domain.interfaces.repositories import (
    IUserRepository, IPatientRepository, IGameRepository,
    ISessionRepository, IFingerEventRepository,
    ISensitivityPresetRepository, IPatientSensitivityRepository,
    ISensitivityHistoryRepository, IPlayerGameConfigRepository,
    ISpriteRepository,
)
from .models import (
    db, UserModel, RoleModel, PatientModel, GameModel, GameSessionModel,
    FingerEventModel, SensitivityPresetModel, PatientSensitivityModel,
    SensitivityHistoryModel, PlayerGameConfigModel, SpriteModel,
)


class RoleRepository:
    def find_all(self) -> List[Role]:
        models = RoleModel.query.order_by(RoleModel.id).all()
        return [self._to_entity(m) for m in models]

    def find_by_name(self, name: str) -> Optional[Role]:
        m = RoleModel.query.filter_by(name=name).first()
        return self._to_entity(m) if m else None

    @staticmethod
    def _to_entity(m: RoleModel) -> Role:
        return Role(id=m.id, name=m.name, description=m.description)


class UserRepository(IUserRepository):
    def find_by_id(self, user_id: int) -> Optional[User]:
        m = UserModel.query.get(user_id)
        return self._to_entity(m) if m else None

    def find_by_email(self, email: str) -> Optional[User]:
        m = UserModel.query.filter_by(email=email).first()
        return self._to_entity(m) if m else None

    def save(self, user: User) -> User:
        if user.id:
            m = UserModel.query.get(user.id)
        else:
            m = UserModel()
            db.session.add(m)
        m.email = user.email
        m.password_hash = user.password_hash
        m.name = user.name
        m.lastname = user.lastname
        if user.role_id:
            m.role_id = user.role_id
        db.session.commit()
        return self._to_entity(m)

    @staticmethod
    def _to_entity(m: UserModel) -> User:
        return User(
            id=m.id, email=m.email, password_hash=m.password_hash,
            name=m.name, role_id=m.role_id,
            created_at=m.created_at,
        )


class PatientRepository(IPatientRepository):
    def find_by_id(self, patient_id: int) -> Optional[Patient]:
        m = PatientModel.query.get(patient_id)
        return self._to_entity(m) if m else None

    def find_by_user_id(self, user_id: int, user_role: str = 'therapist') -> List[Patient]:
        q = PatientModel.query
        if user_role != 'admin':
            q = q.filter_by(user_id=user_id)
        models = q.order_by(PatientModel.name).all()
        return [self._to_entity(m) for m in models]

    def find_by_user_id_paginated(self, user_id: int, page: int, per_page: int, user_role: str = 'therapist') -> dict:
        q = PatientModel.query
        if user_role != 'admin':
            q = q.filter_by(user_id=user_id)
        pagination = (q
                      .order_by(PatientModel.name)
                      .paginate(page=page, per_page=per_page, error_out=False))
        return {
            'items': [self._to_entity(m) for m in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
        }

    def save(self, patient: Patient) -> Patient:
        if patient.id:
            m = PatientModel.query.get(patient.id)
        else:
            m = PatientModel()
            db.session.add(m)
        m.user_id = patient.user_id
        m.name = patient.name
        m.lastname = patient.lastname
        m.document = patient.document
        m.birth_date = patient.birth_date
        m.age = patient.age
        m.diagnosis = patient.diagnosis
        m.notes = patient.notes
        db.session.commit()
        return self._to_entity(m)

    def delete(self, patient_id: int) -> None:
        PatientModel.query.filter_by(id=patient_id).delete()
        db.session.commit()

    @staticmethod
    def _to_entity(m: PatientModel) -> Patient:
        return Patient(
            id=m.id,
            user_id=m.user_id,
            name=m.name,
            lastname=m.lastname,
            document=m.document,
            birth_date=m.birth_date,
            age=m.age,
            diagnosis=m.diagnosis,
            notes=m.notes,
            created_at=m.created_at,
        )


class GameRepository(IGameRepository):
    def find_by_id(self, game_id: int) -> Optional[Game]:
        m = GameModel.query.get(game_id)
        return self._to_entity(m) if m else None

    def find_all(self) -> List[Game]:
        models = GameModel.query.order_by(GameModel.created_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def save(self, game: Game) -> Game:
        if game.id:
            m = GameModel.query.get(game.id)
        else:
            m = GameModel()
            db.session.add(m)
        m.name = game.name
        m.description = game.description
        m.game_type = game.game_type
        m.thumbnail_url = game.thumbnail_url
        m.config = game.config
        m.created_by = game.created_by
        db.session.commit()
        return self._to_entity(m)

    def delete(self, game_id: int) -> None:
        GameModel.query.filter_by(id=game_id).delete()
        db.session.commit()

    @staticmethod
    def _to_entity(m: GameModel) -> Game:
        return Game(
            id=m.id, name=m.name, description=m.description,
            game_type=m.game_type, thumbnail_url=m.thumbnail_url,
            config=m.config, created_by=m.created_by, created_at=m.created_at,
        )


class SessionRepository(ISessionRepository):
    def find_by_id(self, session_id: int) -> Optional[GameSession]:
        m = GameSessionModel.query.get(session_id)
        return self._to_entity(m) if m else None

    def find_by_user_id(self, user_id: int, patient_id: Optional[int] = None,
                        game_id: Optional[int] = None, limit: int = 100,
                        user_role: str = 'therapist') -> List[GameSession]:
        q = GameSessionModel.query
        if user_role != 'admin':
            q = q.filter_by(user_id=user_id)
        if patient_id:
            q = q.filter_by(patient_id=patient_id)
        if game_id:
            q = q.filter_by(game_id=game_id)
        models = q.order_by(GameSessionModel.started_at.desc()).limit(limit).all()
        return [self._to_entity(m) for m in models]

    def save(self, session: GameSession) -> GameSession:
        if session.id:
            m = GameSessionModel.query.get(session.id)
        else:
            m = GameSessionModel()
            db.session.add(m)
        m.patient_id = session.patient_id
        m.game_id = session.game_id
        m.user_id = session.user_id
        m.started_at = session.started_at
        m.ended_at = session.ended_at
        m.score = session.score
        m.metadata_ = session.metadata_
        db.session.commit()
        return self._to_entity(m)

    @staticmethod
    def _to_entity(m: GameSessionModel) -> GameSession:
        return GameSession(
            id=m.id, patient_id=m.patient_id, game_id=m.game_id,
            user_id=m.user_id, started_at=m.started_at, ended_at=m.ended_at,
            score=m.score, metadata_=m.metadata_,
        )


class FingerEventRepository(IFingerEventRepository):
    def find_by_session_id(self, session_id: int) -> List[FingerEvent]:
        models = FingerEventModel.query.filter_by(session_id=session_id).order_by(FingerEventModel.timestamp).all()
        return [self._to_entity(m) for m in models]

    def save_batch(self, events: List[FingerEvent]) -> None:
        for e in events:
            m = FingerEventModel(
                session_id=e.session_id, finger_index=e.finger_index,
                state=e.state, landmark_x=e.landmark_x,
                landmark_y=e.landmark_y, landmark_z=e.landmark_z,
                confidence=e.confidence,
            )
            db.session.add(m)
        db.session.commit()

    @staticmethod
    def _to_entity(m: FingerEventModel) -> FingerEvent:
        return FingerEvent(
            id=m.id, session_id=m.session_id, timestamp=m.timestamp,
            finger_index=m.finger_index, state=m.state,
            landmark_x=m.landmark_x, landmark_y=m.landmark_y,
            landmark_z=m.landmark_z, confidence=m.confidence,
        )


class SensitivityPresetRepository(ISensitivityPresetRepository):
    def find_all(self) -> List[SensitivityPreset]:
        models = SensitivityPresetModel.query.order_by(SensitivityPresetModel.difficulty_level).all()
        return [self._to_entity(m) for m in models]

    def save(self, preset: SensitivityPreset) -> SensitivityPreset:
        if preset.id:
            m = SensitivityPresetModel.query.get(preset.id)
        else:
            m = SensitivityPresetModel()
            db.session.add(m)
        m.name = preset.name
        m.description = preset.description
        m.difficulty_level = preset.difficulty_level
        m.sensitivities = preset.sensitivities
        m.is_default = preset.is_default
        m.created_by = preset.created_by
        db.session.commit()
        return self._to_entity(m)

    @staticmethod
    def _to_entity(m: SensitivityPresetModel) -> SensitivityPreset:
        return SensitivityPreset(
            id=m.id, name=m.name, description=m.description,
            difficulty_level=m.difficulty_level,
            sensitivities=m.sensitivities, is_default=m.is_default,
            created_by=m.created_by, created_at=m.created_at,
        )


class PatientSensitivityRepository(IPatientSensitivityRepository):
    def find_by_patient_id(self, patient_id: int) -> Optional[PatientSensitivity]:
        m = PatientSensitivityModel.query.filter_by(patient_id=patient_id).first()
        return self._to_entity(m) if m else None

    def save(self, sensitivity: PatientSensitivity) -> PatientSensitivity:
        if sensitivity.id:
            m = PatientSensitivityModel.query.get(sensitivity.id)
        else:
            m = PatientSensitivityModel()
            db.session.add(m)
        m.patient_id = sensitivity.patient_id
        m.sensitivities = sensitivity.sensitivities
        m.based_on_preset = sensitivity.based_on_preset
        m.updated_at = sensitivity.updated_at
        m.updated_by = sensitivity.updated_by
        db.session.commit()
        return self._to_entity(m)

    @staticmethod
    def _to_entity(m: PatientSensitivityModel) -> PatientSensitivity:
        return PatientSensitivity(
            id=m.id, patient_id=m.patient_id,
            sensitivities=m.sensitivities,
            based_on_preset=m.based_on_preset,
            updated_at=m.updated_at, updated_by=m.updated_by,
        )


class SensitivityHistoryRepository(ISensitivityHistoryRepository):
    def find_by_patient_id(self, patient_id: int) -> List[SensitivityHistory]:
        models = SensitivityHistoryModel.query.filter_by(patient_id=patient_id).order_by(
            SensitivityHistoryModel.changed_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def save(self, history: SensitivityHistory) -> SensitivityHistory:
        m = SensitivityHistoryModel(
            patient_id=history.patient_id,
            old_sensitivities=history.old_sensitivities,
            new_sensitivities=history.new_sensitivities,
            reason=history.reason,
            changed_by=history.changed_by,
        )
        db.session.add(m)
        db.session.commit()
        return self._to_entity(m)

    @staticmethod
    def _to_entity(m: SensitivityHistoryModel) -> SensitivityHistory:
        return SensitivityHistory(
            id=m.id, patient_id=m.patient_id,
            old_sensitivities=m.old_sensitivities,
            new_sensitivities=m.new_sensitivities,
            reason=m.reason, changed_by=m.changed_by,
            changed_at=m.changed_at,
        )


class PlayerGameConfigRepository(IPlayerGameConfigRepository):
    def find_by_patient_and_game(self, patient_id: int, game_id: int) -> Optional[PlayerGameConfig]:
        m = PlayerGameConfigModel.query.filter_by(patient_id=patient_id, game_id=game_id).first()
        return self._to_entity(m) if m else None

    def save(self, config: PlayerGameConfig) -> PlayerGameConfig:
        if config.id:
            m = PlayerGameConfigModel.query.get(config.id)
        else:
            m = PlayerGameConfigModel()
            db.session.add(m)
        m.patient_id = config.patient_id
        m.game_id = config.game_id
        m.sensitivities = config.sensitivities
        m.finger_map = config.finger_map
        m.updated_at = config.updated_at
        db.session.commit()
        return self._to_entity(m)

    @staticmethod
    def _to_entity(m: PlayerGameConfigModel) -> PlayerGameConfig:
        return PlayerGameConfig(
            id=m.id, patient_id=m.patient_id, game_id=m.game_id,
            sensitivities=m.sensitivities, finger_map=m.finger_map,
            updated_at=m.updated_at,
        )


class SpriteRepository(ISpriteRepository):
    def find_by_id(self, sprite_id: int) -> Optional[Sprite]:
        m = SpriteModel.query.get(sprite_id)
        return self._to_entity(m) if m else None

    def find_by_ids(self, sprite_ids: list) -> List[Sprite]:
        models = SpriteModel.query.filter(SpriteModel.id.in_(sprite_ids)).all()
        return [self._to_entity(m) for m in models]

    def find_all(self, category: Optional[str] = None) -> List[Sprite]:
        q = SpriteModel.query
        if category:
            q = q.filter_by(category=category)
        models = q.order_by(SpriteModel.created_at.desc()).all()
        return [self._to_entity(m) for m in models]

    def save(self, sprite: Sprite) -> Sprite:
        if sprite.id:
            m = SpriteModel.query.get(sprite.id)
        else:
            m = SpriteModel()
            db.session.add(m)
        m.name = sprite.name
        m.category = sprite.category
        m.type = sprite.type
        m.width = sprite.width
        m.height = sprite.height
        m.data = sprite.data
        m.image_url = sprite.image_url
        m.frame_count = sprite.frame_count
        m.created_by = sprite.created_by
        db.session.commit()
        return self._to_entity(m)

    def delete(self, sprite_id: int) -> None:
        SpriteModel.query.filter_by(id=sprite_id).delete()
        db.session.commit()

    @staticmethod
    def _to_entity(m: SpriteModel) -> Sprite:
        return Sprite(
            id=m.id, name=m.name, category=m.category, type=m.type,
            width=m.width, height=m.height, data=m.data,
            image_url=m.image_url, frame_count=m.frame_count,
            created_by=m.created_by, created_at=m.created_at,
        )
