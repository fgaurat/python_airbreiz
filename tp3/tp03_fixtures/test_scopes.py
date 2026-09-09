"""Démonstration des scopes : combien de fois une fixture est-elle créée ?

Lancer :  uv run pytest tp03_fixtures/test_scopes.py --setup-show
"""

import pytest

COMPTEURS = {"function": 0, "class": 0, "module": 0}


@pytest.fixture
def fx_function():
    COMPTEURS["function"] += 1
    return object()


@pytest.fixture(scope="class")
def fx_class():
    COMPTEURS["class"] += 1
    return object()


@pytest.fixture(scope="module")
def fx_module():
    COMPTEURS["module"] += 1
    return object()


class TestScopesA:
    def test_1(self, fx_function, fx_class, fx_module):
        self.__class__.objets = (fx_class, fx_module)

    def test_2(self, fx_function, fx_class, fx_module):
        # class et module : mêmes objets que dans test_1 ; function : nouvel objet
        assert fx_class is self.objets[0]
        assert fx_module is self.objets[1]


class TestScopesB:
    def test_3(self, fx_function, fx_class, fx_module):
        pass


def test_bilan(fx_module):
    assert COMPTEURS["function"] == 3  # une par test qui la demande
    assert COMPTEURS["class"] == 2  # une par classe (A et B)
    assert COMPTEURS["module"] == 1  # une seule pour tout le fichier
