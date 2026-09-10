"""Tests unitaires purs : dataclass, validations, calculs (TP01, TP04)."""

from datetime import date

import pytest

from tp11_projet.stock.modeles import Produit


class TestValidation:
    @pytest.mark.parametrize(
        "kwargs, message",
        [
            ({"reference": ""}, "référence"),
            ({"prix_ht": -1}, "prix"),
            ({"quantite": -1}, "quantité"),
        ],
        ids=["reference-vide", "prix-negatif", "quantite-negative"],
    )
    def test_valeurs_invalides(self, kwargs, message):
        base = {"reference": "X", "nom": "x", "prix_ht": 1.0}
        with pytest.raises(ValueError, match=message):
            Produit(**{**base, **kwargs})


@pytest.mark.parametrize(
    "prix_ht, taux, ttc",
    [(100, 0.20, 120.0), (10, 0.055, 10.55), (0, 0.20, 0.0), (19.99, 0.20, 23.99)],
)
def test_prix_ttc(prix_ht, taux, ttc):
    assert Produit("R", "n", prix_ht).prix_ttc(taux) == pytest.approx(ttc)


@pytest.mark.parametrize("quantite, seuil, rupture", [(0, 5, True), (5, 5, True), (6, 5, False), (100, 5, False)])
def test_en_rupture(quantite, seuil, rupture):
    assert Produit("R", "n", 1.0, quantite, seuil).en_rupture is rupture


def test_aller_retour_dict(produit_stylo):
    d = produit_stylo.to_dict()
    assert d["date_creation"] == date.today().isoformat()
    assert Produit.from_dict(d) == produit_stylo
