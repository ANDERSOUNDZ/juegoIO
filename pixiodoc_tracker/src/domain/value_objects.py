from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class FingerState:
    values: tuple = (0, 0, 0, 0, 0)

    def __post_init__(self):
        if len(self.values) != 5:
            raise ValueError('FingerState requires exactly 5 values')
        if not all(v in (0, 1) for v in self.values):
            raise ValueError('FingerState values must be 0 or 1')

    def as_list(self) -> List[int]:
        return list(self.values)

    def changed_from(self, other: 'FingerState') -> bool:
        return self.values != other.values


@dataclass(frozen=True)
class Sensitivity:
    values: tuple = (50, 50, 50, 50, 50)

    def __post_init__(self):
        if len(self.values) != 5:
            raise ValueError('Sensitivity requires exactly 5 values')
        if not all(0 <= v <= 100 for v in self.values):
            raise ValueError('Sensitivity values must be 0-100')

    @classmethod
    def from_list(cls, items: list) -> 'Sensitivity':
        clamped = [max(0, min(100, int(v))) for v in items]
        return cls(tuple(clamped))

    def as_list(self) -> List[int]:
        return list(self.values)


@dataclass(frozen=True)
class HandLandmark:
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class HandLandmarks:
    landmarks: tuple

    @classmethod
    def from_list(cls, items: list) -> 'HandLandmarks':
        return cls(tuple(HandLandmark(x=l[0], y=l[1], z=l[2]) for l in items))
