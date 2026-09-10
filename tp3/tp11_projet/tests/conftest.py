"""Fixtures du projet fil rouge."""

import socket

import pytest

from tp11_projet.stock.depot import DepotJSON, DepotMemoire
from tp11_projet.stock.modeles import Produit
from tp11_projet.stock.service import ServiceStock

# ---------------------------------------------------------------------------
# Garde-fou : AUCUN test ne doit toucher au réseau. Si l'un d'eux oublie de
# mocker le client de taux, il échoue immédiatement au lieu de faire un vrai
# appel (lent, non reproductible, et possiblement facturé...).
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _pas_de_reseau(monkeypatch):
    def interdit(*args, **kwargs):
        raise RuntimeError("accès réseau interdit pendant les tests")

    # getaddrinfo (résolution DNS) est appelé AVANT la création du socket :
    # sans lui, une machine hors ligne échouerait en OSError "gentille"
    # (rattrapée par le code) au lieu de notre RuntimeError explicite.
    monkeypatch.setattr(socket, "getaddrinfo", interdit)
    monkeypatch.setattr(socket, "socket", interdit)


# ---------------------------------------------------------------------------
# Données de test
# ---------------------------------------------------------------------------


@pytest.fixture
def produit_stylo():
    return Produit("STY-01", "Stylo bleu", prix_ht=1.50, quantite=100)


@pytest.fixture
def produit_cahier():
    return Produit("CAH-01", "Cahier A4", prix_ht=3.20, quantite=4)  # sous le seuil


# ---------------------------------------------------------------------------
# Dépôts : mémoire (rapide) et JSON (tmp_path). La fixture `depot` est
# paramétrée : chaque test qui l'utilise tourne contre LES DEUX implémentations.
# ---------------------------------------------------------------------------


@pytest.fixture
def depot_memoire():
    return DepotMemoire()


@pytest.fixture
def depot_json(tmp_path):
    return DepotJSON(tmp_path / "stock.json")


@pytest.fixture(params=["memoire", "json"])
def depot(request):
    return request.getfixturevalue(f"depot_{request.param}")


# ---------------------------------------------------------------------------
# Service avec client de taux mocké
# ---------------------------------------------------------------------------


@pytest.fixture
def client_taux(mocker):
    client = mocker.Mock()
    client.taux.return_value = 1.0
    return client


@pytest.fixture
def service(depot_memoire, client_taux, produit_stylo, produit_cahier):
    depot_memoire.sauvegarder(produit_stylo)
    depot_memoire.sauvegarder(produit_cahier)
    return ServiceStock(depot_memoire, client_taux)
