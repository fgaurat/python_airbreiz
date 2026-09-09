"""Présentation des CINQ scopes de fixtures, du plus court au plus long.

Chaque fixture affiche son SETUP et son TEARDOWN : lancer avec `-s` pour
voir les messages, ou avec `--setup-show` pour la vue de pytest (lettres
F / C / M / P / S devant chaque fixture).

    uv run pytest tp03_fixtures/scopes -s -q
    uv run pytest tp03_fixtures/scopes --setup-show -q
    uv run pytest tp03_fixtures/scopes --setup-show --env staging -q   # scope dynamique
"""

import pytest

# Compteurs de créations, vérifiés par le dernier test (test_2_module_b.py::test_bilan)
CREATIONS = {"function": 0, "class": 0, "module": 0, "package": 0, "session": 0, "dynamique": 0}


def _fabrique(scope):
    """Construit une fixture de scope donné qui trace son cycle de vie."""

    @pytest.fixture(scope=scope, name=f"fx_{scope}")
    def fixture(request):
        CREATIONS[scope] += 1
        # request.node : le test (function), la classe, le module, le package ou la session
        noeud = request.node.name or "la session"
        print(f"\n  [SETUP    {scope:8s}] #{CREATIONS[scope]}  pour {noeud}")
        yield f"{scope}-{CREATIONS[scope]}"
        print(f"\n  [TEARDOWN {scope:8s}] #{CREATIONS[scope]}  après {noeud}")

    return fixture


# Une fixture par scope : fx_function, fx_class, fx_module, fx_package, fx_session
fx_function = _fabrique("function")
fx_class = _fabrique("class")
fx_module = _fabrique("module")
fx_package = _fabrique("package")  # "package" = le paquet où la fixture est DÉFINIE : tp03_fixtures/scopes
fx_session = _fabrique("session")


# ---------------------------------------------------------------------------
# Scope DYNAMIQUE : décidé à l'exécution par une fonction (fixture_name, config)
# Ici : partagée pour toute la session hors "dev", recréée à chaque test en "dev"
# ---------------------------------------------------------------------------


def _scope_selon_env(fixture_name, config):
    return "function" if config.getoption("--env") == "dev" else "session"


@pytest.fixture(scope=_scope_selon_env)
def fx_dynamique(request):
    CREATIONS["dynamique"] += 1
    print(f"\n  [SETUP    dynamique] scope réel = {request.scope}")
    yield request.scope
    print(f"\n  [TEARDOWN dynamique] scope réel = {request.scope}")
