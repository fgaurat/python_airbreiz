"""conftest.py du TP03 : fixtures partagées par tous les tests du répertoire.

Un conftest.py est découvert automatiquement (pas d'import à écrire).
Ses fixtures sont visibles dans le répertoire et ses sous-répertoires.
"""

import pytest
from tp03_fixtures.banque import Banque, Journal, Compte
from typing import Callable

# ---------------------------------------------------------------------------
# Fixture "function" (scope par défaut) : recréée pour CHAQUE test
# ---------------------------------------------------------------------------


@pytest.fixture
def banque():
    return Banque("Crédit Pytest")


# ---------------------------------------------------------------------------
# Fixtures qui dépendent d'autres fixtures : pytest résout le graphe
# ---------------------------------------------------------------------------


@pytest.fixture
def compte_alice(banque):
    return banque.ouvrir_compte("alice", solde=100)


@pytest.fixture
def compte_bob(banque):
    return banque.ouvrir_compte("bob", solde=50)


# ---------------------------------------------------------------------------
# Fixture "factory" : renvoie une FONCTION pour créer autant d'objets qu'on veut
# ---------------------------------------------------------------------------


@pytest.fixture
def creer_compte(banque: Banque):
    """Fixture factory pour créer des comptes."""
    l = []

    def _creer(titulaire: str, solde: float = 0) -> "Compte":

        compte = banque.ouvrir_compte(titulaire, solde)
        l.append(compte)
        return compte

    return _creer


def nouveau_compte(creer_compte: Callable[[str, float], Compte], titulaire: str, solde: float = 0) -> "Compte":
    return creer_compte(titulaire, solde)


# ---------------------------------------------------------------------------
# Fixture avec `yield` : tout ce qui suit le yield est le TEARDOWN
# ---------------------------------------------------------------------------


@pytest.fixture
def journal(tmp_path):
    # tmp_path est une fixture INTÉGRÉE : répertoire temporaire unique par test
    j = Journal(tmp_path / "journal.txt")
    yield j  # <- le test s'exécute ici
    j.fermer()  # <- exécuté même si le test échoue


# ---------------------------------------------------------------------------
# Scopes plus larges : module / session
# Lancer avec `--setup-show -s` pour voir l'ordre des SETUP / TEARDOWN
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def parametres():
    print("\n[SETUP session] chargement des paramètres")
    yield {"devise": "EUR", "plafond_retrait": 1000}
    print("\n[TEARDOWN session] paramètres libérés")


@pytest.fixture(scope="module")
def connexion_bdd():
    """Simule une connexion coûteuse, ouverte une fois par module de test."""
    print("\n[SETUP module] ouverture de la connexion")
    connexion = {"ouverte": True, "requetes": []}
    yield connexion
    connexion["ouverte"] = False
    print("\n[TEARDOWN module] fermeture de la connexion")
