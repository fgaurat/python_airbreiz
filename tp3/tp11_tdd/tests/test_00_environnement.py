"""Test de fumée : vérifie que l'environnement est prêt avant le premier cycle.

Il restera vert pendant tout le TP. Les vrais tests commencent dans
test_01_produit.py, que VOUS allez créer (voir README.md, histoire 1).
"""


def test_environnement_pret():
    import tp11_tdd.stock  # le paquet existe, il est vide : c'est normal

    assert tp11_tdd.stock is not None
