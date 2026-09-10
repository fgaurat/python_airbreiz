"""Conteneur générique (DockerContainer) : parler à Redis sans bibliothèque cliente.

On envoie une commande au format RESP (le protocole texte de Redis) via un
simple socket : le but est de montrer le conteneur, pas Redis.
"""

import socket

import pytest


def _commande_redis(adresse, *mots: str) -> str:
    requete = f"*{len(mots)}\r\n" + "".join(f"${len(m)}\r\n{m}\r\n" for m in mots)
    with socket.create_connection(adresse, timeout=5) as s:
        s.sendall(requete.encode())
        return s.recv(1024).decode()


def test_ping(redis_adresse):
    assert _commande_redis(redis_adresse, "PING") == "+PONG\r\n"


def test_set_get(redis_adresse):
    assert _commande_redis(redis_adresse, "SET", "formation", "pytest") == "+OK\r\n"
    assert _commande_redis(redis_adresse, "GET", "formation") == "$6\r\npytest\r\n"


@pytest.mark.parametrize("cle", ["a", "b"])
def test_cle_absente(redis_adresse, cle):
    assert _commande_redis(redis_adresse, "GET", f"inexistante-{cle}") == "$-1\r\n"
