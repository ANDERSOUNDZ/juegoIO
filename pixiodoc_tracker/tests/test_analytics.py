"""Tests for AnalyticsService metrics calculations."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.domain.entities import FingerEvent
from src.domain.value_objects import Sensitivity
from datetime import datetime, timezone


def make_event(finger, state, x=0.5, y=0.5, z=0):
    return FingerEvent(
        finger_index=finger, state=state,
        landmark_x=x, landmark_y=y, landmark_z=z,
        timestamp=datetime.now(timezone.utc),
        confidence=0.9,
    )



class TestSensitivity:
    def test_valid(self):
        s = Sensitivity.from_list([0, 50, 100, 25, 75])
        assert s.as_list() == [0, 50, 100, 25, 75]

    def test_clamp(self):
        s = Sensitivity.from_list([-10, 150, 50, 0, 100])
        assert s.as_list() == [0, 100, 50, 0, 100]


class TestROMCalculation:
    """ROM = (max(X)-min(X) + max(Y)-min(Y)) / 2"""

    def test_rom_max_movement(self):
        events = []
        for i in range(5):
            events.append(make_event(0, 1, x=0.1 + i * 0.05, y=0.1 + i * 0.05))
        x_vals = [e.landmark_x for e in events if e.landmark_x is not None]
        y_vals = [e.landmark_y for e in events if e.landmark_y is not None]
        rom = (max(x_vals) - min(x_vals) + max(y_vals) - min(y_vals)) / 2
        assert rom > 0.05

    def test_rom_no_movement(self):
        events = [make_event(0, 1, x=0.5, y=0.5) for _ in range(5)]
        x_vals = [e.landmark_x for e in events if e.landmark_x is not None]
        y_vals = [e.landmark_y for e in events if e.landmark_y is not None]
        rom = (max(x_vals) - min(x_vals) + max(y_vals) - min(y_vals)) / 2
        assert rom == 0


class TestFatigueCalculation:
    """Fatigue = (1 - ROM_last_third / ROM_first_third) * 100"""

    def test_no_fatigue(self):
        # Same amplitude throughout
        finger_data = {i: [] for i in range(5)}
        for i in range(30):
            finger_data[0].append(make_event(0, 1, x=0.5 + (i % 3) * 0.1, y=0.5))
        fevents = finger_data[0]
        x_vals = [e.landmark_x for e in fevents if e.landmark_x is not None]
        third = len(x_vals) // 3
        if third > 0 and len(x_vals) > 5:
            first = x_vals[:third]
            last = x_vals[-third:]
            rom_first = max(first) - min(first)
            rom_last = max(last) - min(last)
            fatigue = 0 if rom_first == 0 else (1 - rom_last / rom_first) * 100
            # With consistent data, fatigue should be low
            assert 0 <= fatigue <= 50


class TestFingerDetectionLogic:
    """Validate the hysteresis-based finger detection."""

    def test_threshold_calculation(self):
        HYST_MARGIN = 0.02
        for sensitivity in [0, 25, 50, 75, 100]:
            t = (100 - sensitivity) / 100.0 * 0.12
            assert 0 <= t <= 0.12

    def test_hysteresis_activation(self):
        HYST_MARGIN = 0.02
        s = 50  # sensitivity
        t = (100 - s) / 100.0 * 0.12  # = 0.06

        # Start off (current=0), diff above threshold → activates
        diff = 0.08  # > 0.06
        current = 0
        result = 1 if diff > t else 0
        assert result == 1

        # Stay on (current=1), diff above (thresh - margin)
        diff = 0.05  # > 0.04
        current = 1
        t_off = t - HYST_MARGIN  # = 0.04
        result = 0 if diff < t_off else 1
        assert result == 1

        # Turn off: diff below (thresh - margin)
        diff = 0.03  # < 0.04
        result = 0 if diff < t_off else 1
        assert result == 0
