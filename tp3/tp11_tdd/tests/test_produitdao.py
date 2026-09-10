from unittest.mock import MagicMock

from modeles import Produit
from produit_dao import ProduitDAO
import sqlite3
import pytest


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.executed = []

    def execute(self, sql, params=()):
        self.executed.append((sql, params))
        return self  # comme sqlite3 : execute() renvoie le curseur

    def fetchall(self):
        return self.rows


FAKE_ROWS = [
    ("P001", "Clavier", 100.0, 5),
    ("P002", "Souris", 25.0, 12),
]


class FakeConn:
    def __init__(self, rows):
        self.cursor_obj = FakeCursor(rows)

    def cursor(self):
        return self.cursor_obj


def test_find_all(monkeypatch):
    dao = ProduitDAO(conn=None)              # conn réel remplacé juste après
    monkeypatch.setattr(dao, "_conn", FakeConn(FAKE_ROWS))
    assert len(list(dao.find_all())) == 2


@pytest.mark.skip
def test_find_all_old():
    fake_rows = [
        ("P001", "Clavier", 100.0, 5),
        ("P002", "Souris", 25.0, 12),
        ("P003", "Écran", 200.0, 7),
    ]

    cursor = MagicMock()
    cursor.fetchall.return_value = fake_rows
    conn = MagicMock()
    conn.cursor.return_value = cursor
    dao = ProduitDAO(conn)

    produits = list(dao.find_all())

    assert len(produits) == 3


def test_find_all_vraie_base_fetchall_patche(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE produits_tbl (ref TEXT, nom TEXT, prix_ht REAL, quantite INTEGER)"
    )
    dao = ProduitDAO(conn)

    # sqlite3.Connection/Cursor sont des types C : on ne peut pas patcher
    # leurs instances, mais on peut patcher la classe.
    monkeypatch.setattr(sqlite3.Cursor, "fetchall", lambda self: FAKE_ROWS)

    assert list(dao.find_all())[1] == Produit("P002", "Souris", 25.0, 12)
