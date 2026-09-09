"""Démonstration de l'introspection des assertions (assertion rewriting).

Ce fichier ne respecte PAS le motif `test_*.py` : il n'est donc pas collecté
par un `pytest` global. Pour voir les échecs, lancez-le explicitement :

    uv run pytest tp01_bases/demo_echecs.py
    uv run pytest tp01_bases/demo_echecs.py --tb=short
    uv run pytest tp01_bases/demo_echecs.py --tb=line
    uv run pytest tp01_bases/demo_echecs.py -x        # s'arrête au 1er échec

Tous les tests ci-dessous ÉCHOUENT volontairement.
"""

import pytest

from calculatrice import additionner, diviser, moyenne


def test_echec_entiers():
    assert additionner(2, 2) == 5


def test_echec_flottants_sans_approx():
    assert additionner(0.1, 0.2) == 0.3


def test_echec_liste():
    assert [1, 2, 3, 4] == [1, 2, 4, 3]


def test_echec_dictionnaire():
    attendu = {"nom": "Alice", "age": 30, "ville": "Paris"}
    obtenu = {"nom": "Alice", "age": 31, "pays": "France"}
    assert obtenu == attendu


def test_echec_chaine_longue():
    texte = "Le rapide renard brun saute par-dessus le chien paresseux"
    assert texte == "Le rapide renard roux saute par-dessus le chien paresseux"


def test_echec_ensemble():
    assert {1, 2, 3} == {2, 3, 4}


def test_echec_exception_non_levee():
    with pytest.raises(ZeroDivisionError):
        diviser(10, 2)  # ne lève rien -> "DID NOT RAISE"


def test_echec_mauvaise_exception():
    with pytest.raises(ValueError):
        diviser(10, 0)  # lève ZeroDivisionError, pas ValueError


def test_echec_approx():
    assert moyenne([1, 2, 3]) == pytest.approx(2.5, abs=0.1)


def test_erreur_hors_assert():
    # Une exception non attendue = ERREUR (pas seulement un échec d'assert)
    moyenne([])
