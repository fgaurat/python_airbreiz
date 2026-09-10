"""Plugin pytest local : chronomètre chaque test et affiche les plus lents.

Un plugin est simplement un module qui définit des hooks et/ou des fixtures.
Il est chargé :
  - via `pytest_plugins = ["tp10_hooks_plugins.plugin_chrono"]` dans le conftest RACINE, ou
  - via la ligne de commande : `pytest -p tp10_hooks_plugins.plugin_chrono`, ou
  - via un entry point `pytest11` s'il est distribué comme package pip.
"""

import time

import pytest

_DUREES: dict[str, float] = {}


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    """Hook "wrapper" : s'exécute AUTOUR de l'appel du test.

    Tout ce qui précède `yield` se passe avant le test, tout ce qui suit
    après (même si le test échoue). `wrapper=True` remplace l'ancien
    `hookwrapper=True` + `outcome = yield`.
    """
    debut = time.perf_counter()
    try:
        return (yield)
    finally:
        _DUREES[item.nodeid] = time.perf_counter() - debut


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Ajoute une section au rapport final."""
    if not _DUREES:
        return
    plus_lents = sorted(_DUREES.items(), key=lambda kv: kv[1], reverse=True)[:3]
    terminalreporter.section("plugin_chrono : 3 tests les plus lents")
    for nodeid, duree in plus_lents:
        terminalreporter.write_line(f"{duree * 1000:8.1f} ms  {nodeid}")


@pytest.fixture
def horloge():
    """Fixture fournie par le plugin : mesure une durée dans un test."""

    class Horloge:
        def __init__(self):
            self._debut = time.perf_counter()

        def ecoule(self) -> float:
            return time.perf_counter() - self._debut

    return Horloge()
