"""conftest.py RACINE du projet : ses options et fixtures s'appliquent à tous les TP.

Déclare l'option `--env` (dev par défaut) utilisée par le scope dynamique
de tp03_fixtures/scopes/conftest.py.

    uv run pytest tp03_fixtures/scopes --setup-show -q                  # env = dev
    uv run pytest tp03_fixtures/scopes --setup-show -q --env staging    # env = staging
"""

import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        default="dev",
        choices=("dev", "staging", "prod"),
        help="Environnement cible : dev (défaut), staging ou prod",
    )


@pytest.fixture(scope="session")
def env(request):
    """Nom de l'environnement passé avec --env."""
    return request.config.getoption("--env")
