"""conftest.py du TP10 : hooks de personnalisation.

Un hook est une fonction nommée `pytest_xxx` avec une signature précise.
pytest l'appelle au bon moment. Liste complète :
    https://docs.pytest.org/en/stable/reference/reference.html#hooks

IMPORTANT : les hooks d'un conftest de sous-répertoire reçoivent souvent des
données GLOBALES (ex. tous les items collectés). Il faut filtrer soi-même si
on veut limiter l'effet au répertoire (voir `_est_dans_ce_tp`).
"""

from pathlib import Path

import pytest

ICI = Path(__file__).parent


def _est_dans_ce_tp(item) -> bool:
    return ICI in item.path.parents


# ---------------------------------------------------------------------------
# pytest_configure : appelé après la lecture de la configuration
# ---------------------------------------------------------------------------


def pytest_configure(config):
    # Déclaration programmatique d'un marqueur (alternative au pyproject.toml)
    config.addinivalue_line("markers", "chrono: test dont on vérifie la durée")


# ---------------------------------------------------------------------------
# pytest_collection_modifyitems : réordonner, filtrer, marquer les tests
# ---------------------------------------------------------------------------


def pytest_collection_modifyitems(config, items):
    lancer_lents = config.getoption("--lent")
    skip_lent = pytest.mark.skip(reason="test lent : ajoutez --lent pour l'exécuter")

    prioritaires, autres = [], []
    for item in items:
        if not _est_dans_ce_tp(item):
            autres.append(item)
            continue
        # 1. Ajouter dynamiquement un marqueur skip
        if "lent" in item.keywords and not lancer_lents:
            item.add_marker(skip_lent)
        # 2. Réordonner : les tests @pytest.mark.prioritaire d'abord
        (prioritaires if item.get_closest_marker("prioritaire") else autres).append(item)

    items[:] = prioritaires + autres  # modification EN PLACE obligatoire


# ---------------------------------------------------------------------------
# pytest_runtest_makereport : connaître le résultat d'un test dans une fixture
# ---------------------------------------------------------------------------


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    """Stocke le rapport de chaque phase (setup / call / teardown) sur l'item."""
    rapport = yield
    setattr(item, f"rapport_{rapport.when}", rapport)
    return rapport


@pytest.fixture
def resultat_du_test(request):
    """Fixture qui, en teardown, sait si le test a réussi ou échoué.

    Cas d'usage classique : faire une capture d'écran Selenium uniquement si
    le test a échoué, conserver des logs, etc.
    """
    yield
    rapport = getattr(request.node, "rapport_call", None)
    if rapport is not None:
        request.config._resultats_tp10.append((request.node.name, rapport.outcome))


def pytest_sessionstart(session):
    session.config._resultats_tp10 = []


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    resultats = getattr(config, "_resultats_tp10", [])
    if resultats:
        terminalreporter.section("TP10 : résultats vus par la fixture resultat_du_test")
        for nom, outcome in resultats:
            terminalreporter.write_line(f"{outcome:8s} {nom}")


# ---------------------------------------------------------------------------
# pytest_assertrepr_compare : message d'échec personnalisé pour vos classes
# ---------------------------------------------------------------------------


def pytest_assertrepr_compare(config, op, left, right):
    from tp10_hooks_plugins.geometrie import Vecteur

    if isinstance(left, Vecteur) and isinstance(right, Vecteur) and op == "==":
        return [
            "Comparaison de Vecteur :",
            f"   x : {left.x} {'==' if left.x == right.x else '!='} {right.x}",
            f"   y : {left.y} {'==' if left.y == right.y else '!='} {right.y}",
        ]
    return None
