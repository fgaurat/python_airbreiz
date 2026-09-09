"""Erreur volontaire : une fixture large qui dépend d'une fixture plus courte.

Non collecté par défaut (pas de préfixe test_). Lancer :

    uv run pytest tp03_fixtures/scopes/demo_scope_mismatch.py
"""

import pytest


@pytest.fixture(scope="session")
def config_partagee(fx_function):  # session -> function : INTERDIT
    return {"base": fx_function}


def test_provoque_scope_mismatch(config_partagee):
    pass
