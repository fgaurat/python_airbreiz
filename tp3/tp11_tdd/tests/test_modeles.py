from modeles import Produit
import pytest


@pytest.mark.parametrize("ref, nom, prix_ht, quantite", [
    ("12345", "Produit Test", 100.0, 0)
])
def test_init_produit(ref, nom, prix_ht, quantite):
    p = Produit(ref=ref, nom=nom, prix_ht=prix_ht, quantite=quantite)
    assert p.ref == ref
    assert p.nom == nom
    assert p.prix_ht == prix_ht
    assert p.quantite == quantite


@pytest.mark.parametrize("ref, nom, prix_ht, quantite, message", [
    ("", "Produit Test", 100.0, 0, "[R | r]éférence"),
    ("Produit 1", "Produit Test", -100.0, 0, ""),
    ("Produit 2", "Produit Test", 100.0, -12, ""),
])
def test_init_produit_erreur(ref, nom, prix_ht, quantite, message):
    with pytest.raises(ValueError, match=message):
        p = Produit(ref=ref, nom=nom, prix_ht=prix_ht, quantite=quantite)
        assert p.ref == ref
        assert p.nom == nom
        assert p.prix_ht == prix_ht
        assert p.quantite == quantite


def test_prix_ttc():
    p = Produit(ref="12345", nom="Produit Test", prix_ht=100.0, quantite=1)
    assert p.prix_ttc() == 120.0  # Assuming a 20% VAT rate
