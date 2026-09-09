from geo.calc_geo import CalcGeo
from geo.erreurs import DimensionInvalide


class Rectangle(CalcGeo):

    _cpt: int = 0

    __slots__ = ["_longueur", "_largeur"]

    def __init__(self, longueur: float, largeur: float) -> None:
        # On passe par les setters : la validation est écrite une seule fois.
        self.longueur = longueur
        self.largeur = largeur
        Rectangle._cpt += 1

    @classmethod
    def build_from_str(cls, init_str: str):
        parts = [p.strip() for p in init_str.split(";")]
        if len(parts) != 2:
            raise DimensionInvalide(
                f"attendu 'longueur;largeur', reçu {init_str!r}"
            )
        try:
            longueur, largeur = (float(p) for p in parts)
        except ValueError:
            raise DimensionInvalide(f"dimensions non numériques : {init_str!r}") from None
        return cls(longueur, largeur)

    @staticmethod
    def get_cpt():
        return Rectangle._cpt

    @staticmethod
    def _verifier(nom: str, value: float) -> None:
        # 0 est accepté : un rectangle dégénéré a une surface nulle, ce n'est pas une erreur.
        if value < 0:
            raise DimensionInvalide(f"{nom} négative : {value}")

    @property
    def longueur(self):
        return self._longueur

    @longueur.setter
    def longueur(self, value):
        self._verifier("longueur", value)
        self._longueur = value

    @property
    def largeur(self):
        return self._largeur

    @largeur.setter
    def largeur(self, value):
        self._verifier("largeur", value)
        self._largeur = value

    @property
    def surface(self):
        return self._longueur * self._largeur

    def __repr__(self) -> str:
        return f"{type(self).__name__}(longueur={self._longueur!r}, largeur={self._largeur!r})"

    def __str__(self) -> str:
        return f"{__class__.__name__} {self._longueur=}, {self._largeur=}"

    def __eq__(self, value: object) -> bool:
        # Choix documenté par test_carre_egal_rectangle_de_memes_dimensions :
        # l'égalité porte sur les dimensions, pas sur la classe.
        # Un Carre(2) est donc égal à un Rectangle(2, 2).
        # Pour l'inverse, remplacer isinstance par `type(value) is type(self)`.
        if not isinstance(value, Rectangle):
            return NotImplemented
        return self.longueur == value.longueur and self.largeur == value.largeur

    # Définir __eq__ met __hash__ à None : un Rectangle est mutable, il ne
    # peut pas aller dans un set ni servir de clé de dict. C'est voulu.
