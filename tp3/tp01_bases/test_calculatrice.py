"""TP01 - Les bases : tests sous forme de fonctions.

Règles de découverte (par défaut) :
  - fichiers   : test_*.py ou *_test.py
  - fonctions  : préfixées par `test`
  - classes    : préfixées par `Test` (sans méthode __init__) -> voir TP02
"""

import pytest

from tp01_bases.calculatrice import (
    additionner,
    diviser,
    est_pair,
    factorielle,
    moyenne,
    multiplier,
    soustraire,
)

# ---------------------------------------------------------------------------
# 1. Un test = une fonction + des `assert` standards Python
# ---------------------------------------------------------------------------


def test_additionner():
    assert additionner(2, 3) == 5


def test_soustraire():
    assert soustraire(10, 4) == 6


def test_multiplier():
    assert multiplier(3, 4) == 12


def test_diviser():
    assert diviser(10, 4) == 2.5


def test_est_pair():
    assert est_pair(4)
    assert not est_pair(7)


def test_assert_avec_message():
    # Le message n'est affiché qu'en cas d'échec, en plus de l'introspection
    resultat = additionner(1, 1)
    assert resultat == 2, f"1 + 1 devrait valoir 2, obtenu {resultat}"


# ---------------------------------------------------------------------------
# 2. Toutes les formes d'assert fonctionnent : pas de assertEqual / assertIn...
# ---------------------------------------------------------------------------


def test_assertions_variees():
    valeurs = [3, 1, 2]
    assert sorted(valeurs) == [1, 2, 3]
    assert 2 in valeurs
    assert len(valeurs) == 3
    assert isinstance(moyenne(valeurs), float)
    assert factorielle(0) is not None
    assert {"a": 1} == {"a": 1}


# ---------------------------------------------------------------------------
# 3. Tester qu'une exception est levée : pytest.raises
# ---------------------------------------------------------------------------


def test_diviser_par_zero_leve_une_exception():
    with pytest.raises(ZeroDivisionError):
        diviser(1, 0)


def test_diviser_par_zero_message():
    # `match` est une expression régulière appliquée à str(exception)
    with pytest.raises(ZeroDivisionError, match="division par zéro"):
        diviser(1, 0)


def test_moyenne_liste_vide_excinfo():
    # `as excinfo` donne accès à l'exception capturée après le bloc `with`
    with pytest.raises(ValueError) as excinfo:
        moyenne([])

    assert "liste vide" in str(excinfo.value)
    assert excinfo.type is ValueError


def test_factorielle_negative():
    with pytest.raises(ValueError, match=r"positif ou nul"):
        factorielle(-1)


# ---------------------------------------------------------------------------
# 4. Comparer des flottants : pytest.approx
# ---------------------------------------------------------------------------


def test_flottants_sans_approx():
    # Piège classique : 0.1 + 0.2 != 0.3 en flottants IEEE 754
    assert additionner(0.1, 0.2) != 0.3


def test_flottants_avec_approx():
    assert additionner(0.1, 0.2) == pytest.approx(0.3)
    assert moyenne([0.1, 0.2, 0.3]) == pytest.approx(0.2)


def test_approx_tolerance_explicite():
    # rel = tolérance relative, abs = tolérance absolue
    assert diviser(22, 7) == pytest.approx(3.14, rel=1e-3)
    assert diviser(1, 3) == pytest.approx(0.33, abs=0.01)


def test_approx_sur_une_collection():
    assert [0.1 + 0.2, 0.3 + 0.6] == pytest.approx([0.3, 0.9])


# ---------------------------------------------------------------------------
# 5. Ce qui n'est PAS collecté
# ---------------------------------------------------------------------------


def _outil_interne():
    """Pas de préfixe `test` : pytest ignore cette fonction (utilitaire)."""
    return 42


def verifie_quelque_chose():
    """Idem : pas collectée. Utile pour des helpers partagés."""
    return _outil_interne() == 42


def test_utilise_un_helper():
    assert verifie_quelque_chose()
