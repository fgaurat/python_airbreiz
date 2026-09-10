from modeles import Produit


class ProduitDAO:

    def __init__(self, conn):
        self._conn = conn

    def find_all(self):
        cur = self._conn.cursor()
        res = cur.execute("SELECT * FROM produits_tbl")
        produits = res.fetchall()
        for p in produits:
            produit = Produit(*p)  # Todo(id=t[0],title=t[1],completed=t[2])
            yield produit
