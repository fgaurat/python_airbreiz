import math
from calcGeo import CalcGeo

class Cercle(CalcGeo):
    
    def __init__(self, rayon: int = 1) -> None:
        self.__rayon = rayon

    @property
    def rayon(self):
        return self.__rayon

    @rayon.setter
    def rayon(self,c):
        self.__rayon = c

    def __str__(self):
        return f"{__class__.__name__} {self.__rayon=}"

    @property
    def surface(self)->float | None:
        return math.pi*self.__rayon**2