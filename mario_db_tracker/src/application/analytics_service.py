import statistics
from typing import Optional

from src.domain.exceptions import NotFoundError
from src.domain.interfaces.repositories import (
    IFingerEventRepository, ISessionRepository,
    IPatientRepository, IGameRepository,
)

FINGER_NAMES = ['Pulgar', 'Índice', 'Medio', 'Anular', 'Meñique']


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

    def get_analytics(self, session_id: int, previous_session_id: Optional[int] = None) -> dict:
        session = self._session_repo.find_by_id(session_id)
        if not session:
            raise NotFoundError('Sesión', session_id)

        events = self._event_repo.find_by_session_id(session_id)

        patient = self._patient_repo.find_by_id(session.patient_id)
        game = self._game_repo.find_by_id(session.game_id)

        # Group events by finger
        finger_data = {i: [] for i in range(5)}
        for e in events:
            if e.finger_index in finger_data:
                finger_data[e.finger_index].append(e)

        # Previous session data for comparison
        prev_report = None
        if previous_session_id:
            prev_events = self._event_repo.find_by_session_id(previous_session_id)
            prev_finger_data = {i: [] for i in range(5)}
            for e in prev_events:
                if e.finger_index in prev_finger_data:
                    prev_finger_data[e.finger_index].append(e)
            prev_metrics = self._compute_all_metrics(prev_finger_data, prev_events)

        metrics = self._compute_all_metrics(finger_data, events)

        # Functional score
        score = self._compute_functional_score(metrics)
        prev_score = self._compute_functional_score(prev_metrics) if previous_session_id else None

        # Previous session comparison
        comparison = None
        if prev_score is not None:
            diff = score - prev_score
            comparison = {
                'previous_score': prev_score,
                'change': round(diff, 1),
                'change_pct': round((diff / prev_score) * 100 if prev_score > 0 else 0, 1),
                'improving': diff > 0,
            }

        duration = None
        if session.started_at and session.ended_at:
            duration = (session.ended_at - session.started_at).total_seconds()

        # Clinical interpretation
        interpretation = self._generate_interpretation(metrics, score, comparison)

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

    def _compute_all_metrics(self, finger_data: dict, all_events: list) -> dict:
        result = {}
        for fi in range(5):
            fevents = finger_data[fi]
            if not fevents:
                result[str(fi)] = {
                    'name': FINGER_NAMES[fi],
                    'rom': 0,
                    'reaction_time': None,
                    'fatigue': 0,
                    'tremor': 0,
                    'activations': 0,
                    'has_data': False,
                }
                continue

            # ROM (Range of Motion) — normalized X+Y range
            x_vals = [e.landmark_x for e in fevents if e.landmark_x is not None]
            y_vals = [e.landmark_y for e in fevents if e.landmark_y is not None]
            rom_x = max(x_vals) - min(x_vals) if len(x_vals) > 1 else 0
            rom_y = max(y_vals) - min(y_vals) if len(y_vals) > 1 else 0
            rom = round((rom_x + rom_y) / 2, 4)

            # Reaction time — first transition 0→1
            reaction_time = None
            for e in fevents:
                if e.state == 1:
                    reaction_time = round((e.timestamp - fevents[0].timestamp).total_seconds(), 2) if e.timestamp and fevents[0].timestamp else None
                    break

            # Fatigue — ROM first third vs last third
            third = len(fevents) // 3
            if third > 1 and len(x_vals) > 5:
                first_x = x_vals[:third]
                last_x = x_vals[-third:]
                rom_first = max(first_x) - min(first_x) if first_x else 0
                rom_last = max(last_x) - min(last_x) if last_x else 0
                fatigue = round((1 - (rom_last / rom_first)) * 100, 1) if rom_first > 0 else 0
            else:
                fatigue = 0

            # Tremor — std deviation of landmark positions when state=1
            active_events = [e for e in fevents if e.state == 1 and e.landmark_x is not None]
            tremor = 0
            if len(active_events) > 5:
                ax = [e.landmark_x for e in active_events]
                ay = [e.landmark_y for e in active_events]
                tremor_x = statistics.stdev(ax) if len(ax) > 1 else 0
                tremor_y = statistics.stdev(ay) if len(ay) > 1 else 0
                tremor = round((tremor_x + tremor_y) / 2, 4)

            activations = sum(1 for e in fevents if e.state == 1)

            result[str(fi)] = {
                'name': FINGER_NAMES[fi],
                'rom': rom,
                'reaction_time': reaction_time,
                'fatigue': fatigue,
                'tremor': tremor,
                'activations': activations,
                'has_data': True,
            }

        # Finger independence — co-occurrence analysis
        result['independence'] = self._compute_independence(all_events)

        return result

    def _compute_independence(self, events: list) -> dict:
        """Checks if fingers move independently or together (synergy)."""
        by_timestamp = {}
        for e in events:
            ts = e.timestamp.isoformat() if e.timestamp else ''
            if ts not in by_timestamp:
                by_timestamp[ts] = {}
            if e.state == 1:
                by_timestamp[ts][e.finger_index] = True

        # Count how many times each pair activates together
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

        independence_score = 100
        issues = []
        for (f1, f2), count in pair_count.items():
            total = max(single_count[f1], 1)
            ratio = count / total
            if ratio > 0.5:
                independence_score -= 15
                issues.append(f'{FINGER_NAMES[f1]} y {FINGER_NAMES[f2]} se activan juntos el {int(ratio*100)}% del tiempo')

        independence_score = max(0, independence_score)

        return {
            'score': independence_score,
            'status': 'Normal' if independence_score >= 70 else 'Leve sinergia' if independence_score >= 40 else 'Sinergia significativa',
            'issues': issues,
        }

    def _compute_functional_score(self, metrics: dict) -> float:
        """Score 0-100 combining all metrics."""
        finger_scores = []
        for fi in range(5):
            m = metrics.get(str(fi), {})
            if not m.get('has_data'):
                continue

            s = 0
            # ROM: 0.3+ = 100pts, 0.15 = 50pts, 0 = 0pts
            s += min(100, m.get('rom', 0) / 0.003) * 0.35

            # Fatigue: 0% = 100pts, 30%+ = 0pts
            s += max(0, 100 - m.get('fatigue', 0) * 3.3) * 0.25

            # Tremor: 0 = 100pts, 0.02+ = 0pts
            s += max(0, 100 - m.get('tremor', 0) * 5000) * 0.20

            # Activations
            s += min(100, m.get('activations', 0) * 5) * 0.20

            finger_scores.append(s)

        if not finger_scores:
            return 0

        base = sum(finger_scores) / len(finger_scores)
        indep = metrics.get('independence', {}).get('score', 100)

        return base * 0.7 + indep * 0.3

    def _generate_interpretation(self, metrics: dict, score: float, comparison: Optional[dict]) -> str:
        parts = []

        if score >= 80:
            parts.append('El paciente presenta buena funcionalidad motriz general.')
        elif score >= 50:
            parts.append('El paciente presenta funcionalidad motriz moderada. Hay áreas que requieren atención.')
        else:
            parts.append('El paciente presenta funcionalidad motriz reducida. Se recomienda evaluación especializada.')

        if comparison:
            if comparison.get('improving'):
                parts.append(f'Comparado con la sesión anterior, hay una mejora del {comparison["change_pct"]}% en el score funcional ({comparison["previous_score"]} → {score}).')
            else:
                parts.append(f'Comparado con la sesión anterior, el score funcional disminuyó un {abs(comparison["change_pct"])}% ({comparison["previous_score"]} → {score}).')

        # Per-finger analysis
        weak_fingers = []
        for fi in range(5):
            m = metrics.get(str(fi), {})
            if not m.get('has_data'):
                continue
            if m.get('tremor', 0) > 0.015:
                parts.append(f'{m["name"]}: Se detecta temblor significativo ({m["tremor"]}).')
            if m.get('fatigue', 0) > 25:
                parts.append(f'{m["name"]}: Fatiga elevada ({m["fatigue"]}%). Posible debilidad muscular.')
            if m.get('rom', 0) < 0.05 and m.get('has_data'):
                parts.append(f'{m["name"]}: Rango articular reducido ({m["rom"]}). Limitación de movimiento.')

        indep = metrics.get('independence', {})
        if indep.get('issues'):
            parts.append(f'Independencia digital: {indep["status"]}. {" ".join(indep["issues"][:2])}')

        if not parts:
            parts.append('No se detectaron anomalías significativas en esta sesión.')

        return ' '.join(parts)

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
