import statistics
from typing import Optional

from src.domain.exceptions import NotFoundError
from src.domain.interfaces.repositories import (
    IFingerEventRepository, ISessionRepository,
    IPatientRepository, IGameRepository,
)

FINGER_NAMES = ['Pulgar', 'Índice', 'Medio', 'Anular', 'Meñique']

# Scoring weights
ROM_WEIGHT = 0.35
FATIGUE_WEIGHT = 0.25
TREMOR_WEIGHT = 0.20
ACTIVATIONS_WEIGHT = 0.20
BASE_SCORE_WEIGHT = 0.7
INDEPENDENCE_WEIGHT = 0.3

# Scoring divisors
ROM_SCORE_DIVISOR = 0.003
FATIGUE_SCORE_DIVISOR = 3.3
TREMOR_SCORE_DIVISOR = 5000
ACTIVATIONS_MULTIPLIER = 5

# Alert thresholds
TREMOR_WARNING = 0.015
FATIGUE_WARNING = 25
ROM_WARNING = 0.05

# Independence thresholds
INDEPENDENCE_NORMAL = 70
INDEPENDENCE_MILD = 40
INDEPENDENCE_PENALTY = 15
INDEPENDENCE_RATIO = 0.5


def _group_events(events):
    finger_data = {i: [] for i in range(5)}
    for e in events:
        if e.finger_index in finger_data:
            finger_data[e.finger_index].append(e)
    return finger_data


def _compute_rom(fevents):
    x_vals = [e.landmark_x for e in fevents if e.landmark_x is not None]
    y_vals = [e.landmark_y for e in fevents if e.landmark_y is not None]
    rom_x = max(x_vals) - min(x_vals) if len(x_vals) > 1 else 0
    rom_y = max(y_vals) - min(y_vals) if len(y_vals) > 1 else 0
    return round((rom_x + rom_y) / 2, 4)


def _compute_reaction_time(fevents):
    for e in fevents:
        if e.state == 1:
            if e.timestamp and fevents[0].timestamp:
                return round((e.timestamp - fevents[0].timestamp).total_seconds(), 2)
            return None
    return None


def _compute_fatigue(fevents, x_vals):
    third = len(fevents) // 3
    if third <= 1 or len(x_vals) <= 5:
        return 0
    first_x = x_vals[:third]
    last_x = x_vals[-third:]
    rom_first = max(first_x) - min(first_x) if first_x else 0
    rom_last = max(last_x) - min(last_x) if last_x else 0
    if rom_first <= 0:
        return 0
    return round((1 - (rom_last / rom_first)) * 100, 1)


def _compute_tremor(fevents):
    active = [e for e in fevents if e.state == 1 and e.landmark_x is not None]
    if len(active) <= 5:
        return 0
    ax = [e.landmark_x for e in active]
    ay = [e.landmark_y for e in active]
    tx = statistics.stdev(ax) if len(ax) > 1 else 0
    ty = statistics.stdev(ay) if len(ay) > 1 else 0
    return round((tx + ty) / 2, 4)


class AnalyticsService:
    def __init__(
        self,
        event_repo: IFingerEventRepository,
        session_repo: ISessionRepository,
        patient_repo: IPatientRepository,
        game_repo: IGameRepository,
    ):
        self._event_repo = event_repo
        self._session_repo = session_repo
        self._patient_repo = patient_repo
        self._game_repo = game_repo

    def _get_session_data(self, session_id):
        session = self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError('Sesion', session_id)
        events = self._event_repo.find_by_session_id(session_id)
        patient = self._patient_repo.find_by_id(session.patient_id)
        game = self._game_repo.find_by_id(session.game_id)
        return session, events, patient, game

    def _compute_prev_metrics(self, previous_session_id):
        prev_events = self._event_repo.find_by_session_id(previous_session_id)
        prev_finger_data = _group_events(prev_events)
        return self._compute_all_metrics(prev_finger_data, prev_events)

    def _build_comparison(self, score, prev_score):
        if prev_score is None:
            return None
        diff = score - prev_score
        return {
            'previous_score': prev_score,
            'change': round(diff, 1),
            'change_pct': round((diff / prev_score) * 100 if prev_score > 0 else 0, 1),
            'improving': diff > 0,
        }

    def _build_result(self, session, patient, game, duration, score, comparison, metrics, interpretation):
        return {
            'session_id': session.id,
            'patient_id': session.patient_id,
            'patient_name': patient.name if patient else 'Desconocido',
            'patient_age': patient.age,
            'patient_diagnosis': patient.diagnosis,
            'game_name': game.name if game else 'Desconocido',
            'date': session.started_at.isoformat() if session.started_at else None,
            'duration_seconds': duration,
            'functional_score': round(score, 1),
            'previous_session': comparison,
            'metrics': metrics,
            'interpretation': interpretation,
        }

    def get_analytics(self, session_id, previous_session_id=None):
        session, events, patient, game = self._get_session_data(session_id)
        finger_data = _group_events(events)

        prev_metrics = None
        if previous_session_id:
            prev_metrics = self._compute_prev_metrics(previous_session_id)

        metrics = self._compute_all_metrics(finger_data, events)
        score = self._compute_functional_score(metrics)
        prev_score = self._compute_functional_score(prev_metrics) if prev_metrics else None

        comparison = self._build_comparison(score, prev_score)
        duration = None
        if session.started_at and session.ended_at:
            duration = (session.ended_at - session.started_at).total_seconds()

        interpretation = self._generate_interpretation(metrics, score, comparison)
        return self._build_result(session, patient, game, duration, score, comparison, metrics, interpretation)

    def _compute_single_metrics(self, fi, fevents):
        if not fevents:
            return {'name': FINGER_NAMES[fi], 'rom': 0, 'reaction_time': None,
                    'fatigue': 0, 'tremor': 0, 'activations': 0, 'has_data': False}

        x_vals = [e.landmark_x for e in fevents if e.landmark_x is not None]
        rom = _compute_rom(fevents)
        reaction_time = _compute_reaction_time(fevents)
        fatigue = _compute_fatigue(fevents, x_vals)
        tremor = _compute_tremor(fevents)
        activations = sum(1 for e in fevents if e.state == 1)

        return {'name': FINGER_NAMES[fi], 'rom': rom, 'reaction_time': reaction_time,
                'fatigue': fatigue, 'tremor': tremor, 'activations': activations, 'has_data': True}

    def _compute_all_metrics(self, finger_data, all_events):
        result = {}
        for fi in range(5):
            result[str(fi)] = self._compute_single_metrics(fi, finger_data[fi])
        result['independence'] = self._compute_independence(all_events)
        return result

    def _compute_independence(self, events):
        by_timestamp = {}
        for e in events:
            ts = e.timestamp.isoformat() if e.timestamp else ''
            if ts not in by_timestamp:
                by_timestamp[ts] = {}
            if e.state == 1:
                by_timestamp[ts][e.finger_index] = True

        pair_count = {}
        single_count = {i: 0 for i in range(5)}
        for ts, fingers in by_timestamp.items():
            active = list(fingers.keys())
            for f in active:
                single_count[f] += 1
                for other in active:
                    if other != f:
                        key = tuple(sorted((f, other)))
                        pair_count[key] = pair_count.get(key, 0) + 1

        score = 100
        issues = []
        for (f1, f2), count in pair_count.items():
            ratio = count / max(single_count[f1], 1)
            if ratio > INDEPENDENCE_RATIO:
                score -= INDEPENDENCE_PENALTY
                issues.append(f'{FINGER_NAMES[f1]} y {FINGER_NAMES[f2]} se activan juntos el {int(ratio*100)}% del tiempo')

        score = max(0, score)
        status = 'Normal' if score >= INDEPENDENCE_NORMAL else 'Leve sinergia' if score >= INDEPENDENCE_MILD else 'Sinergia significativa'
        return {'score': score, 'status': status, 'issues': issues}

    def _compute_functional_score(self, metrics):
        finger_scores = []
        for fi in range(5):
            m = metrics.get(str(fi), {})
            if not m.get('has_data'):
                continue

            s = 0
            s += min(100, m.get('rom', 0) / ROM_SCORE_DIVISOR) * ROM_WEIGHT
            s += max(0, 100 - m.get('fatigue', 0) * FATIGUE_SCORE_DIVISOR) * FATIGUE_WEIGHT
            s += max(0, 100 - m.get('tremor', 0) * TREMOR_SCORE_DIVISOR) * TREMOR_WEIGHT
            s += min(100, m.get('activations', 0) * ACTIVATIONS_MULTIPLIER) * ACTIVATIONS_WEIGHT
            finger_scores.append(s)

        if not finger_scores:
            return 0

        base = sum(finger_scores) / len(finger_scores)
        indep = metrics.get('independence', {}).get('score', 100)
        return base * BASE_SCORE_WEIGHT + indep * INDEPENDENCE_WEIGHT

    def _generate_interpretation(self, metrics, score, comparison=None):
        parts = []
        self._add_score_summary(parts, score)
        self._add_comparison(parts, comparison, score)
        self._add_finger_alerts(parts, metrics)
        self._add_independence_note(parts, metrics)
        if not parts:
            parts.append('No se detectaron anomalias significativas en esta sesion.')
        return ' '.join(parts)

    def _add_score_summary(self, parts, score):
        if score >= 80:
            parts.append('El paciente presenta buena funcionalidad motriz general.')
        elif score >= 50:
            parts.append('El paciente presenta funcionalidad motriz moderada. Hay areas que requieren atencion.')
        else:
            parts.append('El paciente presenta funcionalidad motriz reducida. Se recomienda evaluacion especializada.')

    def _add_comparison(self, parts, comparison, score):
        if not comparison:
            return
        key = 'mejora' if comparison.get('improving') else 'disminuyo'
        pct = comparison['change_pct']
        prev = comparison['previous_score']
        parts.append(f'Comparado con la sesion anterior, hay una {key} del {pct}% en el score funcional ({prev} la {score}).')

    def _add_finger_alerts(self, parts, metrics):
        for fi in range(5):
            m = metrics.get(str(fi), {})
            if not m.get('has_data'):
                continue
            if m.get('tremor', 0) > TREMOR_WARNING:
                parts.append(f'{m["name"]}: Se detecta temblor significativo ({m["tremor"]}).')
            if m.get('fatigue', 0) > FATIGUE_WARNING:
                parts.append(f'{m["name"]}: Fatiga elevada ({m["fatigue"]}%). Posible debilidad muscular.')
            if m.get('rom', 0) < ROM_WARNING and m.get('has_data'):
                parts.append(f'{m["name"]}: Rango articular reducido ({m["rom"]}). Limitacion de movimiento.')

    def _add_independence_note(self, parts, metrics):
        indep = metrics.get('independence', {})
        if indep.get('issues'):
            parts.append(f'Independencia digital: {indep["status"]}. {" ".join(indep["issues"][:2])}')

    def get_pdf_data(self, session_id: int) -> dict:
        """Returns data structured for PDF template."""
        analytics = self.get_analytics(session_id)

        # Build finger table rows
        finger_rows = []
        for fi in range(5):
            m = analytics['metrics'].get(str(fi), {})
            row = {
                'name': FINGER_NAMES[fi],
                'rom': m.get('rom', '-'),
                'reaction': f'{m["reaction_time"]}s' if m.get('reaction_time') is not None else '-',
                'fatigue': f'{m["fatigue"]}%' if m.get('has_data') else '-',
                'tremor': m.get('tremor', '-'),
                'activations': m.get('activations', '-'),
            }
            # Color coding
            alert = False
            if m.get('rom', 0) < 0.05 and m.get('has_data'):
                alert = True
            if m.get('fatigue', 0) > 25:
                alert = True
            if m.get('tremor', 0) > 0.015:
                alert = True
            row['alert'] = alert
            finger_rows.append(row)

        return {
            'session_id': analytics['session_id'],
            'patient_name': analytics['patient_name'],
            'patient_age': analytics['patient_age'] or '-',
            'patient_diagnosis': analytics['patient_diagnosis'] or '-',
            'game_name': analytics['game_name'],
            'date': analytics['date'],
            'duration': analytics['duration_seconds'],
            'functional_score': analytics['functional_score'],
            'previous_session': analytics['previous_session'],
            'finger_rows': finger_rows,
            'independence': analytics['metrics'].get('independence', {}),
            'interpretation': analytics['interpretation'],
        }
