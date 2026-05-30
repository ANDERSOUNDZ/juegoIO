from datetime import datetime, timezone
from typing import Optional

from src.domain.entities import GameSession
from src.domain.exceptions import NotFoundError
from src.domain.interfaces.repositories import (
    ISessionRepository, IFingerEventRepository,
    IGameRepository, IPatientRepository,
)


class SessionService:
    def __init__(
        self,
        session_repo: ISessionRepository,
        event_repo: IFingerEventRepository,
        game_repo: IGameRepository,
        patient_repo: IPatientRepository,
    ):
        self._session_repo = session_repo
        self._event_repo = event_repo
        self._game_repo = game_repo
        self._patient_repo = patient_repo

    def list_by_user(self, user_id: int, patient_id: Optional[int] = None,
                     game_id: Optional[int] = None) -> list:
        return self._session_repo.find_by_user_id(user_id, patient_id, game_id)

    def get_by_id(self, session_id: int) -> GameSession:
        s = self._session_repo.find_by_id(session_id)
        if not s:
            raise NotFoundError('Sesión', session_id)
        return s

    def create(self, patient_id: int, game_id: int, user_id: int,
               metadata: Optional[dict] = None) -> GameSession:
        if not self._patient_repo.find_by_id(patient_id):
            raise NotFoundError('Paciente', patient_id)
        if not self._game_repo.find_by_id(game_id):
            raise NotFoundError('Juego', game_id)

        session = GameSession(
            patient_id=patient_id, game_id=game_id,
            user_id=user_id, metadata_=metadata,
        )
        return self._session_repo.save(session)

    def end(self, session_id: int, score: Optional[int] = None,
            metadata: Optional[dict] = None) -> GameSession:
        s = self.get_by_id(session_id)
        s.ended_at = datetime.now(timezone.utc)
        if score is not None:
            s.score = score
        if metadata is not None:
            s.metadata_ = metadata
        return self._session_repo.save(s)

    def get_events(self, session_id: int) -> list:
        self.get_by_id(session_id)
        return self._event_repo.find_by_session_id(session_id)

    def get_report(self, session_id: int) -> dict:
        s = self.get_by_id(session_id)
        events = self._event_repo.find_by_session_id(session_id)

        finger_stats_raw = {}
        for e in events:
            if e.finger_index not in finger_stats_raw:
                finger_stats_raw[e.finger_index] = {'total': 0, 'active': 0, 'min_x': None, 'max_x': None, 'min_y': None, 'max_y': None}
            finger_stats_raw[e.finger_index]['total'] += 1
            finger_stats_raw[e.finger_index]['active'] += e.state
            if e.landmark_x is not None:
                fi = finger_stats_raw[e.finger_index]
                fi['min_x'] = min(fi['min_x'], e.landmark_x) if fi['min_x'] is not None else e.landmark_x
                fi['max_x'] = max(fi['max_x'], e.landmark_x) if fi['max_x'] is not None else e.landmark_x
                fi['min_y'] = min(fi['min_y'], e.landmark_y) if fi['min_y'] is not None else e.landmark_y
                fi['max_y'] = max(fi['max_y'], e.landmark_y) if fi['max_y'] is not None else e.landmark_y

        finger_names = ['Pulgar', 'Índice', 'Medio', 'Anular', 'Meñique']
        finger_stats = [
            {
                'finger_index': fi,
                'name': finger_names[fi] if fi < 5 else f'Dedo {fi}',
                'total_events': st['total'],
                'active_count': st['active'],
            }
            for fi, st in sorted(finger_stats_raw.items())
        ]
        movement_stats = [
            {
                'finger_index': fi,
                'range_x': round((st['max_x'] or 0) - (st['min_x'] or 0), 4),
                'range_y': round((st['max_y'] or 0) - (st['min_y'] or 0), 4),
            }
            for fi, st in sorted(finger_stats_raw.items())
        ]
        duration = None
        if s.started_at and s.ended_at:
            duration = (s.ended_at - s.started_at).total_seconds()

        game = self._game_repo.find_by_id(s.game_id)

        return {
            'session': {
                'id': s.id,
                'patient_id': s.patient_id,
                'game_id': s.game_id,
                'user_id': s.user_id,
                'started_at': s.started_at.isoformat() if s.started_at else None,
                'ended_at': s.ended_at.isoformat() if s.ended_at else None,
                'score': s.score,
                'metadata': s.metadata_,
                'game_name': game.name if game else None,
            },
            'duration_seconds': duration,
            'finger_stats': finger_stats,
            'movement_stats': movement_stats,
        }
