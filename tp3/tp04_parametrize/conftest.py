"""conftest.py du TP04 : paramétrage avancé via fixtures et hook."""

import pytest

# ---------------------------------------------------------------------------
# Fixture paramétrée : chaque test qui la demande s'exécute pour CHAQUE param
# ---------------------------------------------------------------------------


@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def moteur_bdd(request):
    # request.param contient la valeur courante
    return {"moteur": request.param, "connecte": True}


# Avec des ids lisibles
@pytest.fixture(params=[(1, "un"), (2, "deux")], ids=["premier", "second"])
def nombre_et_libelle(request):
    return request.param


# ---------------------------------------------------------------------------
# Hook pytest_generate_tests : paramétrage dynamique (calculé, lu d'un fichier...)
# ---------------------------------------------------------------------------


def pytest_generate_tests(metafunc):
    if "nombre_premier" in metafunc.fixturenames:
        premiers = [2, 3, 5, 7, 11, 13]
        metafunc.parametrize("nombre_premier", premiers, ids=[f"p{p}" for p in premiers])
