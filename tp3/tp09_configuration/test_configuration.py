"""TP09 - Configuration et exécution.

Ce fichier contient peu de tests : l'essentiel du TP est dans le README et
dans les commandes à essayer. Les tests ici servent de support aux démos
(--durations, --lf, -x, --env, doctests...).
"""

import time

import pytest

from tp09_configuration.outils import slugifier, tranche


def test_slugifier():
    assert slugifier("Hello World") == "hello-world"


def test_tranche():
    assert tranche([1, 2, 3], 2) == [[1, 2], [3]]


# --- Support pour --durations ------------------------------------------------


def test_rapide():
    pass


def test_moyen():
    time.sleep(0.05)


@pytest.mark.lent
def test_plus_lent():
    time.sleep(0.15)


# --- Support pour --env (option définie dans le conftest racine) ------------


def test_comportement_selon_env(env):
    urls = {"dev": "http://localhost", "staging": "https://staging.example", "prod": "https://example.com"}
    assert urls[env].startswith("http")


@pytest.fixture
def base_url(env):
    if env == "prod":
        pytest.skip("on ne lance pas ce test contre la prod")
    return "http://localhost" if env == "dev" else "https://staging.example"


def test_skip_selon_env(base_url):
    assert base_url.startswith("http")


# --- Support pour -p no:cacheprovider, --sw etc. ---------------------------


@pytest.mark.parametrize("n", range(5))
def test_serie(n):
    assert n < 5
