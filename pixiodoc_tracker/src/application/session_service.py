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
                     game_id: Optional[int] = None, user_role: str = 'therapist') -> list:
        return self._session_repo.find_by_user_id(user_id, patient_id, game_id, user_role=user_role)

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

    @staticmethod
    def _aggregate_finger_events(events):
        raw = {}
        for e in events:
            if e.finger_index not in raw:
                raw[e.finger_index] = {'total': 0, 'active': 0, 'min_x': None, 'max_x': None, 'min_y': None, 'max_y': None}
            raw[e.finger_index]['total'] += 1
            raw[e.finger_index]['active'] += e.state
            if e.landmark_x is not None:
                fi = raw[e.finger_index]
                fi['min_x'] = min(fi['min_x'], e.landmark_x) if fi['min_x'] is not None else e.landmark_x
                fi['max_x'] = max(fi['max_x'], e.landmark_x) if fi['max_x'] is not None else e.landmark_x
                fi['min_y'] = min(fi['min_y'], e.landmark_y) if fi['min_y'] is not None else e.landmark_y
                fi['max_y'] = max(fi['max_y'], e.landmark_y) if fi['max_y'] is not None else e.landmark_y
        return raw

    @staticmethod
    def _build_finger_stats(raw):
        finger_names = ['Pulgar', 'Indice', 'Medio', 'Anular', 'Menique']
        return [
            {'finger_index': fi, 'name': finger_names[fi] if fi < 5 else f'Dedo {fi}',
             'total_events': st['total'], 'active_count': st['active']}
            for fi, st in sorted(raw.items())
        ]

    @staticmethod
    def _build_movement_stats(raw):
        return [
            {'finger_index': fi, 'range_x': round((st['max_x'] or 0) - (st['min_x'] or 0), 4),
             'range_y': round((st['max_y'] or 0) - (st['min_y'] or 0), 4)}
            for fi, st in sorted(raw.items())
        ]

    def _build_session_dict(self, s, game):
        return {
            'id': s.id, 'patient_id': s.patient_id, 'game_id': s.game_id,
            'user_id': s.user_id, 'score': s.score, 'metadata': s.metadata_,
            'started_at': s.started_at.isoformat() if s.started_at else None,
            'ended_at': s.ended_at.isoformat() if s.ended_at else None,
            'game_name': game.name if game else None,
        }

    def get_analytics(self, session_id: int) -> dict:
        s = self.get_by_id(session_id)
        events = self._event_repo.find_by_session_id(session_id)

        finger_names = ['Pulgar', 'Indice', 'Medio', 'Anular', 'Menique']

        by_finger = {}
        for e in events:
            by_finger.setdefault(e.finger_index, []).append(e)

        ts_list = [e.timestamp for e in events if e.timestamp]
        if ts_list:
            t_start = min(ts_list).timestamp()
            t_end = max(ts_list).timestamp()
            duration = t_end - t_start
        else:
            t_start = t_end = duration = 0.0

        metrics = {}
        total_functional = 0.0
        active_count = 0
        issues = []

        for i in range(5):
            fevents = by_finger.get(i, [])
            has_data = len(fevents) > 0

            if has_data:
                ys = [e.landmark_y for e in fevents if e.landmark_y is not None]
                rom = round(max(ys) - min(ys), 4) if ys else 0.0

                if duration > 0:
                    mid_t = t_start + duration / 2
                    first_half = sum(1 for e in fevents if e.state == 1 and e.timestamp and e.timestamp.timestamp() <= mid_t)
                    second_half = sum(1 for e in fevents if e.state == 1 and e.timestamp and e.timestamp.timestamp() > mid_t)
                    fatigue_pct = max(0, round((first_half - second_half) / max(first_half, 1) * 100)) if first_half > 0 else 0
                else:
                    fatigue_pct = 0

                pressed_xs = [e.landmark_x for e in fevents if e.state == 1 and e.landmark_x is not None]
                if len(pressed_xs) > 1:
                    mean_x = sum(pressed_xs) / len(pressed_xs)
                    tremor = round((sum((x - mean_x) ** 2 for x in pressed_xs) / len(pressed_xs)) ** 0.5, 4)
                else:
                    tremor = 0.0

                active_count += 1
                total_functional += rom * 1000
                if rom < 0.05:
                    issues.append(f'{finger_names[i]}: ROM reducido')
                if fatigue_pct > 25:
                    issues.append(f'{finger_names[i]}: señal de fatiga')
            else:
                rom = fatigue_pct = tremor = 0.0

            metrics[str(i)] = {
                'name': finger_names[i],
                'rom': rom,
                'reaction_time': None,
                'fatigue': fatigue_pct,
                'tremor': tremor,
                'has_data': has_data,
            }

        avg_rom_score = min((total_functional / max(active_count, 1)) / 10, 60)
        total_activations = sum(sum(1 for e in evs if e.state == 1) for evs in by_finger.values())
        act_score = min(total_activations / 2, 40)
        functional_score = round(avg_rom_score + act_score)

        indep_score = round(active_count / 5 * 100)
        if indep_score >= 80:
            status = 'Alta independencia digital'
        elif indep_score >= 40:
            status = 'Independencia parcial'
        else:
            status = 'Baja independencia digital'

        metrics['independence'] = {'score': indep_score, 'issues': issues, 'status': status}

        # Compare with previous session
        previous_session_data = None
        if s.patient_id and s.id:
            prev = self._session_repo.find_previous_for_patient(s.patient_id, s.id)
            if prev:
                prev_events = self._event_repo.find_by_session_id(prev.id)
                prev_raw = self._aggregate_finger_events(prev_events)
                prev_activations = sum(st['active'] for st in prev_raw.values()) if prev_raw else 0
                prev_active = sum(1 for st in prev_raw.values() if st['total'] > 0) if prev_raw else 0
                prev_ys_total = sum(
                    (st['max_y'] or 0) - (st['min_y'] or 0)
                    for st in prev_raw.values() if st['max_y'] is not None
                )
                prev_rom_score = min((prev_ys_total / max(prev_active, 1)) * 1000 / 10, 60)
                prev_act_score = min(prev_activations / 2, 40)
                prev_score = round(prev_rom_score + prev_act_score)
                if prev_score > 0:
                    change_pct = round((functional_score - prev_score) / prev_score * 100)
                else:
                    change_pct = 100 if functional_score > 0 else 0
                previous_session_data = {
                    'change_pct': change_pct,
                    'improving': change_pct >= 0,
                    'previous_score': prev_score,
                }

        # ── Interpretación clínica (profesionales) ──────────────────────
        if functional_score >= 80:
            score_desc = 'Excelente funcionalidad'
            recom = 'Considerar reducción de frecuencia de sesiones o avance a ejercicios de mayor complejidad.'
        elif functional_score >= 65:
            score_desc = 'Buena funcionalidad'
            recom = 'Mantener el programa actual con seguimiento regular.'
        elif functional_score >= 45:
            score_desc = 'Funcionalidad moderada'
            recom = 'Continuar el programa de rehabilitación con atención a los dedos con menor actividad.'
        elif functional_score >= 25:
            score_desc = 'Funcionalidad reducida'
            recom = 'Revisar ajuste de sensibilidad del dispositivo y la frecuencia de sesiones.'
        else:
            score_desc = 'Actividad muy limitada'
            recom = 'Se recomienda evaluación clínica presencial para ajustar el plan terapéutico.'

        trend = ''
        if previous_session_data:
            cp = previous_session_data['change_pct']
            ps = previous_session_data['previous_score']
            if cp >= 15:
                trend = f' Mejora significativa de +{cp}% respecto a la sesión anterior (score previo: {ps}/100).'
            elif cp >= 5:
                trend = f' Progreso moderado de +{cp}% respecto a la sesión anterior (score previo: {ps}/100).'
            elif cp >= -5:
                trend = f' Rendimiento estable — variacion de {cp}% respecto a la sesion anterior ({ps}/100).'
            elif cp >= -15:
                trend = f' Leve descenso de {abs(cp)}% respecto a la sesión anterior ({ps}/100).'
            else:
                trend = f' Descenso notable de {abs(cp)}% respecto a la sesión anterior ({ps}/100) — revisar condición clínica del paciente.'

        active_detail = f'{active_count}/5 dedos con actividad registrada.'
        issues_detail = (' Alertas clínicas: ' + '; '.join(issues[:4]) + '.') if issues else ' Sin alertas clínicas detectadas.'
        interp = f'{score_desc} ({functional_score}/100).{trend} {active_detail}{issues_detail} {recom}'

        # ── Interpretación para el paciente (lenguaje accesible) ────────
        if previous_session_data:
            cp = previous_session_data['change_pct']
            if cp >= 15:
                pat_trend = f'Mejoraste un {cp}% respecto a tu sesión anterior.'
            elif cp >= 5:
                pat_trend = f'Progresaste un {cp}% respecto a tu sesión anterior.'
            elif cp >= -5:
                pat_trend = 'Mantuviste tu nivel de la sesión anterior.'
            else:
                pat_trend = 'Esta sesión fue más difícil que la anterior — la constancia es lo que genera resultados a largo plazo.'
        else:
            pat_trend = ''

        if functional_score >= 65:
            pat_base = 'Tus dedos mostraron muy buena actividad en esta sesión.'
        elif functional_score >= 45:
            pat_base = 'Tus dedos mostraron actividad moderada en esta sesión.'
        else:
            pat_base = 'Tus dedos registraron actividad limitada en esta sesión.'

        pat_fingers = f'{active_count} de 5 dedos registraron movimiento.'
        if issues:
            pat_detail = f'Dedos que requieren mas practica: {", ".join(iss.split(":")[0].strip() for iss in issues[:3])}.'
        else:
            pat_detail = 'Todos tus dedos respondieron correctamente en la sesión.'

        patient_interp = ' '.join(p for p in [pat_base, pat_trend, pat_fingers, pat_detail] if p)

        return {
            'functional_score': functional_score,
            'previous_session': previous_session_data,
            'metrics': metrics,
            'interpretation': interp,
            'patient_interpretation': patient_interp,
        }

    def get_report(self, session_id):
        s = self.get_by_id(session_id)
        events = self._event_repo.find_by_session_id(session_id)
        raw = self._aggregate_finger_events(events)

        duration = None
        if s.started_at and s.ended_at:
            duration = (s.ended_at - s.started_at).total_seconds()

        game = self._game_repo.find_by_id(s.game_id)
        return {
            'session': self._build_session_dict(s, game),
            'duration_seconds': duration,
            'finger_stats': self._build_finger_stats(raw),
            'movement_stats': self._build_movement_stats(raw),
        }
