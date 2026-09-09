import math

from geo.calc_geo import CalcGeo


class Cercle(CalcGeo):

    def __init__(self, rayon: int = 1) -> None:
        self.__rayon = rayon

    @property
    def rayon(self):
        return self.__rayon

    @rayon.setter
    def rayon(self, r):
        self.__rayon = r

    def __repr__(self) -> str:
        return f"{type(self).__name__}(rayon={self.__rayon!r})"

    def __str__(self):
        return f"{__class__.__name__} {self.__rayon=}"

    @property
    def surface(self) -> float:
        return math.pi * self.__rayon ** 2
