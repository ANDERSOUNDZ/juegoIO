from abc import ABC, abstractmethod
from typing import Optional

from ..value_objects import HandLandmarks


class IHandTracker(ABC):
    @abstractmethod
    def detect_landmarks(self, frame_bytes: bytes, timestamp_ms: int) -> Optional[HandLandmarks]: ...

    @abstractmethod
    def close(self) -> None: ...
