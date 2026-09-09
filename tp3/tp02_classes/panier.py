"""Code métier du TP02 : un panier d'achats."""

from dataclasses import dataclass


class PanierVide(Exception):
    """Levée quand on tente de valider un panier vide."""


@dataclass
class Article:
    nom: str
    prix: float
    quantite: int = 1

    @property
    def sous_total(self) -> float:
        return self.prix * self.quantite


class Panier:
    def __init__(self):
        self._articles: dict[str, Article] = {}
        self._remise = 0.0

    def ajouter(self, nom: str, prix: float, quantite: int = 1) -> None:
        if quantite <= 0:
            raise ValueError("la quantité doit être strictement positive")
        if prix < 0:
            raise ValueError("le prix ne peut pas être négatif")
        if nom in self._articles:
            self._articles[nom].quantite += quantite
        else:
            self._articles[nom] = Article(nom, prix, quantite)

    def retirer(self, nom: str) -> None:
        if nom not in self._articles:
            raise KeyError(f"article inconnu : {nom}")
        del self._articles[nom]

    def quantite_de(self, nom: str) -> int:
        return self._articles[nom].quantite if nom in self._articles else 0

    def appliquer_remise(self, pourcentage: float) -> None:
        if not 0 <= pourcentage <= 100:
            raise ValueError("la remise doit être comprise entre 0 et 100")
        self._remise = pourcentage

    def total(self) -> float:
        brut = sum(a.sous_total for a in self._articles.values())
        return round(brut * (1 - self._remise / 100), 2)

    def est_vide(self) -> bool:
        return not self._articles

    def valider(self) -> float:
        if self.est_vide():
            raise PanierVide("impossible de valider un panier vide")
        return self.total()

    def __len__(self) -> int:
        return len(self._articles)
