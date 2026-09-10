"""Persistance : deux implémentations de la même interface.

DepotMemoire est un FAKE utilisable dans les tests du service ;
DepotJSON est testé pour lui-même avec tmp_path.
"""

import json
from pathlib import Path
from typing import Protocol

from tp11_projet.stock.modeles import Produit


class ProduitInconnu(KeyError):
    pass


class Depot(Protocol):
    def sauvegarder(self, produit: Produit) -> None: ...
    def charger(self, reference: str) -> Produit: ...
    def tous(self) -> list[Produit]: ...
    def supprimer(self, reference: str) -> None: ...


class DepotMemoire:
    def __init__(self):
        self._produits: dict[str, Produit] = {}

    def sauvegarder(self, produit: Produit) -> None:
        self._produits[produit.reference] = produit

    def charger(self, reference: str) -> Produit:
        try:
            return self._produits[reference]
        except KeyError:
            raise ProduitInconnu(reference) from None

    def tous(self) -> list[Produit]:
        return sorted(self._produits.values(), key=lambda p: p.reference)

    def supprimer(self, reference: str) -> None:
        if reference not in self._produits:
            raise ProduitInconnu(reference)
        del self._produits[reference]


class DepotJSON:
    def __init__(self, chemin: Path):
        self.chemin = Path(chemin)

    def _lire(self) -> dict[str, dict]:
        if not self.chemin.exists():
            return {}
        return json.loads(self.chemin.read_text(encoding="utf-8"))

    def _ecrire(self, donnees: dict[str, dict]) -> None:
        self.chemin.write_text(json.dumps(donnees, indent=2, ensure_ascii=False), encoding="utf-8")

    def sauvegarder(self, produit: Produit) -> None:
        donnees = self._lire()
        donnees[produit.reference] = produit.to_dict()
        self._ecrire(donnees)

    def charger(self, reference: str) -> Produit:
        donnees = self._lire()
        if reference not in donnees:
            raise ProduitInconnu(reference)
        return Produit.from_dict(donnees[reference])

    def tous(self) -> list[Produit]:
        return sorted((Produit.from_dict(d) for d in self._lire().values()), key=lambda p: p.reference)

    def supprimer(self, reference: str) -> None:
        donnees = self._lire()
        if reference not in donnees:
            raise ProduitInconnu(reference)
        del donnees[reference]
        self._ecrire(donnees)
