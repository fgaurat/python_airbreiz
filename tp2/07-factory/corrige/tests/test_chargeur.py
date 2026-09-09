import pytest

from geo.chargeur import charger
from geo.erreurs import FormeInconnue
from geo.fabrique import FabriqueFormes, fabrique_par_defaut
from geo.rectangle import Rectangle


def test_charger_avec_la_fabrique_par_defaut():
    formes = charger(["rectangle;2;3", "carre;4"], fabrique_par_defaut())
    assert formes == [Rectangle(2, 3), Rectangle(4, 4)]


def test_charger_tolere_les_espaces():
    assert charger([" rectangle ; 2 ; 3 "], fabrique_par_defaut()) == [Rectangle(2, 3)]


def test_charger_refuse_une_forme_inconnue():
    with pytest.raises(FormeInconnue):
        charger(["triangle;3;4;5"], fabrique_par_defaut())


def test_charger_delegue_a_la_fabrique_recue():
    # Une fabrique de test avec une seule forme bidon : on vérifie le découpage
    # des lignes, pas la géométrie.
    fabrique = FabriqueFormes()
    fabrique.enregistrer("point", lambda x, y: (x, y))
    assert charger(["point;1;2"], fabrique) == [(1.0, 2.0)]


def test_charger_liste_vide():
    assert charger([], fabrique_par_defaut()) == []
