import math
import os
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Hand skeleton connections for drawing
CONEXIONES = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
]

HYST_MARGIN = 0.02


def ensure_model(model_url, model_path):
    if not os.path.exists(model_path):
        print("[SERVER] Descargando modelo...")
        urllib.request.urlretrieve(model_url, model_path)
        print("[SERVER] Descargado")


def create_detector(model_path, num_hands=1):
    base_opts = python.BaseOptions(model_asset_path=model_path)
    opts = vision.HandLandmarkerOptions(
        base_options=base_opts,
        num_hands=num_hands,
        min_hand_detection_confidence=0.7,
        min_tracking_confidence=0.7,
        running_mode=vision.RunningMode.VIDEO,
    )
    return vision.HandLandmarker.create_from_options(opts)


def calc_threshold(sensitivity):
    """Map sensitivity (0-100) to threshold (0.12-0.00)."""
    return (100 - sensitivity) / 100.0 * 0.12


def check_finger_hyst(diff, sensitivity, current_state):
    """Check finger state with hysteresis to prevent jitter."""
    thresh = calc_threshold(sensitivity)
    if current_state == 0:
        return 1 if diff > thresh else 0
    else:
        return 0 if diff < (thresh - HYST_MARGIN) else 1


def compute_finger_diffs(landmarks):
    """Compute bend differences for all 5 fingers from landmarks."""
    lm = landmarks
    diffs = [
        0,  # thumb handled separately
        lm[8].y - lm[6].y,    # index
        lm[12].y - lm[10].y,  # middle
        lm[16].y - lm[14].y,  # ring
        lm[20].y - lm[18].y,  # pinky
    ]

    # Thumb: distance from tip(4) to index MCP(5), normalized by hand size
    thumb_dist = math.sqrt((lm[4].x - lm[5].x) ** 2 + (lm[4].y - lm[5].y) ** 2)
    hand_size = math.sqrt((lm[0].x - lm[9].x) ** 2 + (lm[0].y - lm[9].y) ** 2)
    if hand_size > 0.01:
        norm_dist = thumb_dist / hand_size
        diffs[0] = 0.4 - norm_dist
    else:
        diffs[0] = 0

    return diffs


def detect_fingers(diffs, sensitivities, finger_state):
    """Detect finger states using hysteresis. Returns new state list."""
    return [check_finger_hyst(diffs[i], sensitivities[i], finger_state[i]) for i in range(5)]


def draw_landmarks(frame, landmarks):
    """Draw hand skeleton and landmarks on frame."""
    h, w, _ = frame.shape
    coords = [(int(l.x * w), int(l.y * h)) for l in landmarks]
    for a, b in CONEXIONES:
        cv2.line(frame, coords[a], coords[b], (255, 0, 0), 2)
    for pt in coords:
        cv2.circle(frame, pt, 4, (0, 255, 0), -1)
    return coords


def draw_hud(frame, nivel, finger_states):
    """Draw HUD overlay with level and finger states."""
    labels = ["Pulgar", "Indice", "Medio", "Anular", "Menique"]
    cv2.rectangle(frame, (10, 10), (280, 150), (0, 0, 0), -1)
    cv2.putText(frame, f"NIVEL: {nivel}", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    for j, (nom, val) in enumerate(zip(labels, finger_states)):
        color = (0, 255, 0) if val else (0, 0, 255)
        cv2.putText(frame, f"{nom}: {val}", (20, 60 + j * 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
