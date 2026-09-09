import pytest

from geo.carre import Carre
from geo.cercle import Cercle
from geo.erreurs import DimensionInvalide, FormeInconnue
from geo.fabrique import FabriqueFormes, fabrique_par_defaut
from geo.rectangle import Rectangle


@pytest.fixture
def fabrique():
    return fabrique_par_defaut()


def test_creer_un_rectangle(fabrique):
    assert fabrique.creer("rectangle", 2, 3) == Rectangle(2, 3)


def test_creer_un_carre(fabrique):
    assert fabrique.creer("carre", 4) == Carre(4)


def test_creer_un_cercle(fabrique):
    cercle = fabrique.creer("cercle", 2)
    assert isinstance(cercle, Cercle)
    assert cercle.rayon == 2


def test_valeurs_en_chaines_sont_converties(fabrique):
    assert fabrique.creer("rectangle", "2", "3") == Rectangle(2, 3)


def test_nom_insensible_a_la_casse_et_aux_espaces(fabrique):
    assert fabrique.creer(" Rectangle ", 2, 3) == Rectangle(2, 3)


def test_synonyme_disque(fabrique):
    assert isinstance(fabrique.creer("disque", 1), Cercle)


def test_forme_inconnue_cite_les_formes_connues(fabrique):
    with pytest.raises(FormeInconnue, match="rectangle"):
        fabrique.creer("triangle", 3, 4, 5)


@pytest.mark.parametrize(
    ("nom", "valeurs"),
    [
        pytest.param("rectangle", (2,), id="pas_assez"),
        pytest.param("cercle", (1, 2), id="trop"),
        pytest.param("rectangle", ("a", "b"), id="non_numerique"),
    ],
)
def test_valeurs_incorrectes(fabrique, nom, valeurs):
    with pytest.raises(DimensionInvalide):
        fabrique.creer(nom, *valeurs)


def test_enregistrer_une_nouvelle_forme_sans_modifier_geo():
    # Le principe ouvert / fermé, prouvé par un test : Triangle n'existe
    # que dans ce fichier, et la fabrique sait le construire.
    class Triangle:
        def __init__(self, base, hauteur):
            self.surface = base * hauteur / 2

    fabrique = FabriqueFormes()
    fabrique.enregistrer("triangle", Triangle)
    assert fabrique.creer("triangle", 4, 3).surface == 6
    assert fabrique.noms() == ["triangle"]
