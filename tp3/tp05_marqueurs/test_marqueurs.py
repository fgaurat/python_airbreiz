"""TP05 - Les marqueurs : skip, xfail, marqueurs personnalisés, sélection.

Un marqueur est une étiquette posée sur un test (ou une classe, un module).
Certains ont un effet intégré (skip, xfail, parametrize, usefixtures) ;
les autres servent à SÉLECTIONNER (-m) ou à transporter des données.

Avec --strict-markers (activé dans pyproject.toml), tout marqueur doit être
déclaré dans la section `markers` : cela évite les fautes de frappe silencieuses.
"""

import sys

import pytest

from tp05_marqueurs.traitement import (
    calcul_lourd,
    charger_donnees,
    fonction_buggee,
    telecharger,
)

# ---------------------------------------------------------------------------
# 1. skip / skipif : ne pas exécuter
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="fonctionnalité pas encore implémentée")
def test_skip_inconditionnel():
    raise AssertionError("ne doit jamais s'exécuter")


@pytest.mark.skipif(sys.platform == "win32", reason="chemins POSIX uniquement")
def test_skipif_plateforme():
    assert "/" in "/tmp/x"


@pytest.mark.skipif(sys.version_info < (3, 14), reason="nécessite Python 3.14+")
def test_skipif_version_python():
    pass


def test_skip_dynamique():
    # Décision prise PENDANT le test, avec des infos qu'on n'a qu'à l'exécution
    if not hasattr(sys, "getandroidapilevel"):
        pytest.skip("uniquement sur Android")
    raise AssertionError


def test_importorskip():
    # Skippe proprement si une dépendance optionnelle est absente
    pytest.importorskip("module_qui_n_existe_pas")


# ---------------------------------------------------------------------------
# 2. xfail : échec attendu (bug connu, fonctionnalité en cours)
# ---------------------------------------------------------------------------


@pytest.mark.xfail(reason="bug #42 : les négatifs ne sont pas doublés")
def test_xfail_bug_connu():
    assert fonction_buggee(-3) == -6  # échoue -> XFAIL (pas d'erreur)


@pytest.mark.xfail(reason="on s'attend à un échec", strict=True)
def test_xfail_strict():
    # strict=True : si le test PASSE, c'est une ERREUR (XPASS strict).
    # Utile pour être prévenu quand le bug est corrigé et retirer le marqueur.
    assert fonction_buggee(-1) == -2


@pytest.mark.xfail(raises=ConnectionError, reason="pas de réseau en formation")
def test_xfail_raises():
    # `raises=` : seul ConnectionError compte comme échec attendu ;
    # une autre exception serait un vrai FAILED.
    telecharger("https://example.com")


@pytest.mark.xfail(run=False, reason="fait planter l'interpréteur, ne pas exécuter")
def test_xfail_run_false():
    import os

    os._exit(1)


@pytest.mark.xfail(sys.platform == "darwin", reason="xfail conditionnel", strict=False)
def test_xfail_conditionnel():
    assert sys.platform != "darwin"


def test_xfail_dynamique():
    if fonction_buggee(-1) != -2:
        pytest.xfail("bug encore présent")


# ---------------------------------------------------------------------------
# 3. Marqueurs personnalisés : sélection avec -m
# ---------------------------------------------------------------------------


@pytest.mark.lent
def test_calcul_lourd():
    assert calcul_lourd(1000) == 332_833_500


@pytest.mark.lent
@pytest.mark.integration
def test_lent_et_integration():
    assert calcul_lourd(10) == 285


@pytest.mark.integration
def test_integration_seule():
    assert True


@pytest.mark.reseau
@pytest.mark.xfail(raises=ConnectionError)
def test_reseau():
    telecharger("https://example.com")


def test_sans_marqueur():
    assert True


# ---------------------------------------------------------------------------
# 4. Marqueur sur une classe ou tout un module
# ---------------------------------------------------------------------------


@pytest.mark.bdd
class TestAvecBdd:
    def test_requete_1(self):
        pass

    def test_requete_2(self):
        pass


# Pour marquer TOUT le module : `pytestmark = pytest.mark.xxx`
# (ou une liste : pytestmark = [pytest.mark.a, pytest.mark.b])
# Voir test_module_marque.py


# ---------------------------------------------------------------------------
# 5. Marqueur avec arguments : transporter des données vers une fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def donnees(request):
    """Lit le marqueur @pytest.mark.donnees("fichier") posé sur le test."""
    marqueur = request.node.get_closest_marker("donnees")
    if marqueur is None:
        pytest.fail("ce test doit être décoré avec @pytest.mark.donnees(...)")
    return charger_donnees(marqueur.args[0])


@pytest.mark.donnees("clients.csv")
def test_marqueur_avec_argument(donnees):
    assert donnees[0] == "clients.csv:ligne0"


@pytest.mark.donnees("produits.csv")
def test_marqueur_avec_autre_argument(donnees):
    assert all(ligne.startswith("produits.csv") for ligne in donnees)


# ---------------------------------------------------------------------------
# 6. Lire ses propres marqueurs depuis un test
# ---------------------------------------------------------------------------


@pytest.mark.lent
@pytest.mark.bdd
def test_lister_ses_marqueurs(request):
    noms = {m.name for m in request.node.iter_markers()}
    assert {"lent", "bdd"} <= noms
