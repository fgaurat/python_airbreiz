"""TP10 - Hooks et plugins : observer leurs effets.

Lancer :
    uv run pytest tp10_hooks_plugins -v            # test lent SKIPPED, prioritaires en premier
    uv run pytest tp10_hooks_plugins -v --lent     # test lent exécuté
    uv run pytest tp10_hooks_plugins -v --env prod
"""

import time

import pytest

from tp10_hooks_plugins.geometrie import Vecteur

ORDRE_EXECUTION: list[str] = []


# --- Réordonnancement par pytest_collection_modifyitems --------------------


def test_normal_1():
    ORDRE_EXECUTION.append("normal_1")


@pytest.mark.prioritaire
def test_prioritaire():
    # Déclaré APRÈS test_normal_1 dans le fichier, mais exécuté AVANT grâce au hook
    ORDRE_EXECUTION.append("prioritaire")


def test_normal_2():
    ORDRE_EXECUTION.append("normal_2")
    assert ORDRE_EXECUTION[0] == "prioritaire"
    # NB : ce test dépend de l'ordre d'exécution -> incompatible avec
    # pytest-xdist (-n) ou pytest-randomly. C'est une démo, pas une bonne pratique.


# --- Skip dynamique via option --lent ---------------------------------------


@pytest.mark.lent
def test_tres_lent():
    time.sleep(0.3)


# --- Marqueur enregistré dans pytest_configure ------------------------------


@pytest.mark.chrono
def test_marqueur_programmatique(horloge):
    # `horloge` vient du plugin plugin_chrono
    time.sleep(0.05)
    assert horloge.ecoule() >= 0.05


# --- Option personnalisée (--env, définie dans le conftest racine) ---------


def test_option_env(env, pytestconfig):
    assert env in {"dev", "staging", "prod"}
    assert env == pytestconfig.getoption("--env")


# --- Fixture qui connaît le résultat du test -------------------------------


def test_avec_resultat(resultat_du_test):
    assert Vecteur(1, 2) + Vecteur(3, 4) == Vecteur(4, 6)


def test_avec_resultat_bis(resultat_du_test):
    assert True
