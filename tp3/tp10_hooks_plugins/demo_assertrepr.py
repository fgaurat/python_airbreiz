"""Échec volontaire : montre le message produit par pytest_assertrepr_compare.

    uv run pytest tp10_hooks_plugins/demo_assertrepr.py
"""

from tp10_hooks_plugins.geometrie import Vecteur


def test_vecteurs_differents():
    assert Vecteur(1, 2) + Vecteur(1, 1) == Vecteur(2, 4)
