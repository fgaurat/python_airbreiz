"""Fixtures du kit TDD.

Au départ, une seule chose : le garde-fou réseau (vu au TP06 / TP11).
Les autres fixtures (depot, service, client_taux...) apparaîtront au fil des
histoires, quand un test en aura BESOIN, pas avant.
"""

import socket

import pytest


@pytest.fixture(autouse=True)
def _pas_de_reseau(monkeypatch):
    def interdit(*args, **kwargs):
        raise RuntimeError("accès réseau interdit pendant les tests")

    monkeypatch.setattr(socket, "getaddrinfo", interdit)
    monkeypatch.setattr(socket, "socket", interdit)
