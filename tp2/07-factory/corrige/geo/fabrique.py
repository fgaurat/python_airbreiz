from typing import Callable

from geo.calc_geo import CalcGeo
from geo.carre import Carre
from geo.cercle import Cercle
from geo.erreurs import DimensionInvalide, FormeInconnue
from geo.rectangle import Rectangle

Constructeur = Callable[..., CalcGeo]


class FabriqueFormes:
    """La table nom -> constructeur, écrite une seule fois."""

    def __init__(self):
        self._constructeurs: dict[str, Constructeur] = {}

    def enregistrer(self, nom: str, constructeur: Constructeur) -> None:
        self._constructeurs[nom.lower()] = constructeur

    def noms(self) -> list[str]:
        return sorted(self._constructeurs)

    def creer(self, nom: str, *valeurs) -> CalcGeo:
        try:
            constructeur = self._constructeurs[nom.strip().lower()]
        except KeyError:
            raise FormeInconnue(
                f"forme inconnue : {nom!r} (connues : {', '.join(self.noms())})"
            ) from None
        try:
            nombres = [float(v) for v in valeurs]
        except ValueError:
            raise DimensionInvalide(f"valeurs non numériques : {valeurs}") from None
        try:
            return constructeur(*nombres)
        except TypeError:
            raise DimensionInvalide(
                f"{nom} : nombre de valeurs incorrect ({len(nombres)} reçues)"
            ) from None


def fabrique_par_defaut() -> FabriqueFormes:
    fabrique = FabriqueFormes()
    fabrique.enregistrer("rectangle", Rectangle)
    fabrique.enregistrer("carre", Carre)
    fabrique.enregistrer("cercle", Cercle)
    fabrique.enregistrer("disque", Cercle)  # un synonyme : une ligne
    return fabrique
