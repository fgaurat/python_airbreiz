"""TP12 (bonus) - Tests par propriétés avec Hypothesis.

Au lieu de choisir des exemples à la main, on décrit la FORME des entrées
(stratégies) et une PROPRIÉTÉ qui doit toujours être vraie. Hypothesis
génère des centaines de cas, cherche un contre-exemple, puis le SIMPLIFIE
(shrinking) pour présenter le plus petit cas qui échoue.
"""

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st

from tp12_bonus_hypothesis.algos import decoder_rle, encoder_rle, mediane, tri_insertion

# ---------------------------------------------------------------------------
# 1. Propriétés d'un tri
# ---------------------------------------------------------------------------


@given(st.lists(st.integers()))
def test_tri_est_ordonne(valeurs):
    resultat = tri_insertion(valeurs)
    assert all(a <= b for a, b in zip(resultat, resultat[1:]))


@given(st.lists(st.integers()))
def test_tri_conserve_les_elements(valeurs):
    assert sorted(tri_insertion(valeurs)) == sorted(valeurs)


@given(st.lists(st.integers()))
def test_tri_est_idempotent(valeurs):
    une_fois = tri_insertion(valeurs)
    assert tri_insertion(une_fois) == une_fois


@given(st.lists(st.integers()))
def test_tri_equivalent_a_sorted(valeurs):
    # Comparer à une implémentation de référence : "oracle"
    assert tri_insertion(valeurs) == sorted(valeurs)


# ---------------------------------------------------------------------------
# 2. Aller-retour (round-trip) : decoder(encoder(x)) == x
# ---------------------------------------------------------------------------


@given(st.text())
@example("")  # cas explicite toujours testé en plus des cas générés
@example("aaaaaaaaaaaaaaaa")
def test_rle_aller_retour(texte):
    assert decoder_rle(encoder_rle(texte)) == texte


@given(st.text(min_size=1))
def test_rle_pas_deux_paires_consecutives_identiques(texte):
    paires = encoder_rle(texte)
    assert all(a[0] != b[0] for a, b in zip(paires, paires[1:]))
    assert all(n >= 1 for _, n in paires)


# ---------------------------------------------------------------------------
# 3. assume : écarter les entrées non pertinentes
# ---------------------------------------------------------------------------


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False)))
def test_mediane_entre_min_et_max(valeurs):
    assume(valeurs)  # on ignore la liste vide (testée à part)
    m = mediane(valeurs)
    assert min(valeurs) <= m <= max(valeurs)


def test_mediane_vide():
    with pytest.raises(ValueError):
        mediane([])


# ---------------------------------------------------------------------------
# 4. Stratégies composées et settings
# ---------------------------------------------------------------------------


@settings(max_examples=300)
@given(
    st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=50),
    st.integers(min_value=1, max_value=10),
)
def test_mediane_invariante_par_ajout_symetrique(valeurs, k):
    # Ajouter k valeurs sous le min et k valeurs au-dessus du max ne change pas la médiane
    m = mediane(valeurs)
    etendue = [min(valeurs) - 1] * k + valeurs + [max(valeurs) + 1] * k
    assert mediane(etendue) == m


@given(st.dictionaries(st.text(min_size=1), st.integers(min_value=0)))
def test_strategie_dictionnaire(stock):
    total = sum(stock.values())
    assert total >= 0
    assert total == sum(v for v in stock.values())
