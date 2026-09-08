
class Rectangle:    

    _cpt:int = 0

    __slots__= ["_longueur","_largeur"]

    def __init__(self, longueur:int, largeur:int) -> None:
        self._longueur = longueur  # _Rectangle__longueur
        self._largeur = largeur
        Rectangle._cpt+=1


    @classmethod
    def build_from_str(cls,init_str:str):
        values = [int(v) for v in init_str.split(";")]
        o = cls(*values)
        return o

    @staticmethod
    def get_cpt():
        return Rectangle._cpt

    
    @property
    def longueur(self):
        return self._longueur

    @longueur.setter
    def longueur(self, value):
        if value<0:
            raise Exception("Hooooo!")
        self._longueur = value

    @property
    def largeur(self):
        return self._largeur

    @largeur.setter
    def largeur(self, value):
        self._largeur = value

    @property
    def surface(self):
        return self._longueur *  self._largeur

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"longueur={self._longueur!r}, largeur={self._largeur!r})"
        )

    def __str__(self) -> str:
        return f"{__class__.__name__} {self._longueur=}, {self._largeur=}"

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Rectangle):
            return NotImplemented
        return self.longueur == value.longueur and self.largeur == value.largeur
