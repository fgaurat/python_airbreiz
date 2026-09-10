"""Tests pytest — ProduitDAO (fixture in-memory + mock)."""

from unittest.mock import MagicMock

from produit import Produit
from produit_dao import ProduitDAO


def make_dao_with_conn(conn) -> ProduitDAO:
    dao = ProduitDAO.__new__(ProduitDAO)
    dao._conn = conn
    return dao


def test_find_all_avec_memory_db(memory_db):
    dao = make_dao_with_conn(memory_db)
    produits = list(dao.find_all())
    assert len(produits) == 3
    assert produits[0] == Produit("P001", "Clavier", 100.0, 5)


def test_find_all_avec_mock():
    fake_rows = [
        ("P001", "Clavier", 100.0, 5),
        ("P002", "Souris", 25.0, 12),
    ]
    cursor = MagicMock()
    cursor.fetchall.return_value = fake_rows
    conn = MagicMock()
    conn.cursor.return_value = cursor

    dao = make_dao_with_conn(conn)
    produits = list(dao.find_all())

    assert len(produits) == 2
    assert produits[0] == Produit("P001", "Clavier", 100.0, 5)
    conn.cursor.assert_called_once()
    cursor.execute.assert_called_once()


def test_find_by_ref_avec_memory_db(memory_db):
    dao = make_dao_with_conn(memory_db)
    assert dao.find_by_ref("P002") == Produit("P002", "Souris", 25.0, 12)


def test_find_by_ref_renvoie_none_si_absent(memory_db):
    dao = make_dao_with_conn(memory_db)
    assert dao.find_by_ref("P999") is None


def test_save_insere_un_nouveau_produit(memory_db):
    dao = make_dao_with_conn(memory_db)
    nouveau = Produit(ref="P004", nom="Casque", prix_ht=80.0, quantite=3)

    saved = dao.save(nouveau)

    assert saved == nouveau
    assert dao.find_by_ref("P004") == nouveau
    assert len(list(dao.find_all())) == 4


def test_save_met_a_jour_un_produit_existant(memory_db):
    dao = make_dao_with_conn(memory_db)
    produit = dao.find_by_ref("P001")
    assert produit is not None
    produit.prix_ht = 90.0
    produit.quantite = 7

    saved = dao.save(produit)

    assert dao.find_by_ref("P001") == saved
    assert len(list(dao.find_all())) == 3


def test_delete_supprime_un_produit(memory_db):
    dao = make_dao_with_conn(memory_db)
    assert dao.delete("P003") is True
    assert dao.find_by_ref("P003") is None


def test_delete_renvoie_false_si_absent(memory_db):
    dao = make_dao_with_conn(memory_db)
    assert dao.delete("P404") is False
