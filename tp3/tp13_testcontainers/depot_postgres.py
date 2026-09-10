"""Troisième implémentation du dépôt du TP11, sur PostgreSQL (psycopg 3).

Elle respecte le même protocole `Depot` que DepotMemoire et DepotJSON :
les tests de contrat du TP11 doivent passer sans modification.
"""

from datetime import date

import psycopg

from tp11_projet.stock.depot import ProduitInconnu
from tp11_projet.stock.modeles import Produit

SCHEMA = """
CREATE TABLE IF NOT EXISTS produits (
    reference     TEXT PRIMARY KEY,
    nom           TEXT NOT NULL,
    prix_ht       NUMERIC(10, 2) NOT NULL CHECK (prix_ht >= 0),
    quantite      INTEGER NOT NULL CHECK (quantite >= 0),
    seuil_alerte  INTEGER NOT NULL,
    date_creation DATE NOT NULL
)
"""


class DepotPostgres:
    def __init__(self, url: str):
        self.url = url
        with self._connexion() as conn:
            conn.execute(SCHEMA)

    def _connexion(self) -> psycopg.Connection:
        return psycopg.connect(self.url)

    def sauvegarder(self, produit: Produit) -> None:
        with self._connexion() as conn:
            conn.execute(
                """
                INSERT INTO produits (reference, nom, prix_ht, quantite, seuil_alerte, date_creation)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (reference) DO UPDATE SET
                    nom = EXCLUDED.nom, prix_ht = EXCLUDED.prix_ht, quantite = EXCLUDED.quantite,
                    seuil_alerte = EXCLUDED.seuil_alerte, date_creation = EXCLUDED.date_creation
                """,
                (
                    produit.reference,
                    produit.nom,
                    produit.prix_ht,
                    produit.quantite,
                    produit.seuil_alerte,
                    produit.date_creation,
                ),
            )

    def charger(self, reference: str) -> Produit:
        with self._connexion() as conn:
            ligne = conn.execute("SELECT * FROM produits WHERE reference = %s", (reference,)).fetchone()
        if ligne is None:
            raise ProduitInconnu(reference)
        return self._vers_produit(ligne)

    def tous(self) -> list[Produit]:
        with self._connexion() as conn:
            lignes = conn.execute("SELECT * FROM produits ORDER BY reference").fetchall()
        return [self._vers_produit(l) for l in lignes]

    def supprimer(self, reference: str) -> None:
        with self._connexion() as conn:
            curseur = conn.execute("DELETE FROM produits WHERE reference = %s", (reference,))
            if curseur.rowcount == 0:
                raise ProduitInconnu(reference)

    def vider(self) -> None:
        """Utilisé par les tests pour repartir d'une table vide."""
        with self._connexion() as conn:
            conn.execute("TRUNCATE produits")

    @staticmethod
    def _vers_produit(ligne: tuple) -> Produit:
        reference, nom, prix_ht, quantite, seuil_alerte, date_creation = ligne
        return Produit(
            reference=reference,
            nom=nom,
            prix_ht=float(prix_ht),  # NUMERIC -> Decimal côté psycopg
            quantite=quantite,
            seuil_alerte=seuil_alerte,
            date_creation=date_creation if isinstance(date_creation, date) else date.fromisoformat(date_creation),
        )
