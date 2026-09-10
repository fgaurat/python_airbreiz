"""Petite classe pour illustrer pytest_assertrepr_compare."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Vecteur:
    x: float
    y: float

    def __add__(self, autre: "Vecteur") -> "Vecteur":
        return Vecteur(self.x + autre.x, self.y + autre.y)
