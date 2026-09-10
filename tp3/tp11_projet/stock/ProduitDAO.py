"""produit_dao.py — accès SQLite pour la dataclass Produit."""

import sqlite3
from typing import Iterator, Optional

from produit import Produit


class ProduitDAO:
    _COLONNES = "ref, nom, prix_ht, quantite"

    def __init__(self, db_path: str = "produits.db"):
        self._conn = sqlite3.connect(db_path)
        self.create_table()

    # --- schéma -----------------------------------------------------------

    def create_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS produits (
                ref      TEXT PRIMARY KEY,
                nom      TEXT NOT NULL,
                prix_ht  REAL NOT NULL CHECK (prix_ht >= 0),
                quantite INTEGER NOT NULL DEFAULT 0 CHECK (quantite >= 0)
            )
            """
        )
        self._conn.commit()

    # --- lecture ----------------------------------------------------------

    @staticmethod
    def _row_to_produit(row) -> Produit:
        ref, nom, prix_ht, quantite = row
        return Produit(ref=ref, nom=nom, prix_ht=prix_ht, quantite=quantite)

    def find_all(self) -> Iterator[Produit]:
        cursor = self._conn.cursor()
        cursor.execute(f"SELECT {self._COLONNES} FROM produits ORDER BY ref")
        for row in cursor.fetchall():
            yield self._row_to_produit(row)

    def find_by_ref(self, ref: str) -> Optional[Produit]:
        cursor = self._conn.cursor()
        cursor.execute(
            f"SELECT {self._COLONNES} FROM produits WHERE ref = ?", (ref,))
        row = cursor.fetchone()
        return self._row_to_produit(row) if row else None

    def exists(self, ref: str) -> bool:
        cursor = self._conn.cursor()
        cursor.execute("SELECT 1 FROM produits WHERE ref = ?", (ref,))
        return cursor.fetchone() is not None

    # --- écriture ---------------------------------------------------------

    def save(self, produit: Produit) -> Produit:
        cursor = self._conn.cursor()
        if self.exists(produit.ref):
            cursor.execute(
                "UPDATE produits SET nom = ?, prix_ht = ?, quantite = ? WHERE ref = ?",
                (produit.nom, produit.prix_ht, produit.quantite, produit.ref),
            )
        else:
            cursor.execute(
                f"INSERT INTO produits ({self._COLONNES}) VALUES (?, ?, ?, ?)",
                (produit.ref, produit.nom, produit.prix_ht, produit.quantite),
            )
        self._conn.commit()
        return produit

    def delete(self, ref: str) -> bool:
        cursor = self._conn.cursor()
        cursor.execute("DELETE FROM produits WHERE ref = ?", (ref,))
        self._conn.commit()
        return cursor.rowcount > 0

    # --- cycle de vie -----------------------------------------------------

    def close(self) -> None:
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
