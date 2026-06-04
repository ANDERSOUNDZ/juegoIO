from dataclasses import dataclass
from typing import List


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


