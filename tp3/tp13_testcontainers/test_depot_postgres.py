"""TP13 - Testcontainers : le dépôt PostgreSQL passe les mêmes tests que les autres.

Lancer :
    uv run pytest tp13_testcontainers -v          # ~5 s au premier démarrage du conteneur
    uv run pytest tp13_testcontainers -m "not docker"   # -> rien à exécuter
"""

import psycopg
import pytest

from tp11_projet.stock.depot import ProduitInconnu
from tp11_projet.stock.service import ServiceStock

# Importer la classe suffit : pytest la collecte dans CE module, avec NOS fixtures
# (`depot` -> postgres). Zéro test réécrit pour la nouvelle implémentation.
from tp11_projet.tests.test_depot import TestContratDepot  # noqa: F401

# ---------------------------------------------------------------------------
# Tests spécifiques à PostgreSQL : ce qu'un mock ou SQLite ne vérifierait pas
# ---------------------------------------------------------------------------


def test_contraintes_sql(depot_postgres, postgres_url, produit_stylo):
    """Les CHECK de la table protègent même du code qui contournerait le modèle."""
    depot_postgres.sauvegarder(produit_stylo)
    with psycopg.connect(postgres_url) as conn, pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("UPDATE produits SET quantite = -1 WHERE reference = 'STY-01'")


def test_upsert_ne_cree_pas_de_doublon(depot_postgres, postgres_url, produit_stylo):
    depot_postgres.sauvegarder(produit_stylo)
    produit_stylo.nom = "Stylo noir"
    depot_postgres.sauvegarder(produit_stylo)
    with psycopg.connect(postgres_url) as conn:
        assert conn.execute("SELECT count(*) FROM produits").fetchone() == (1,)
        assert conn.execute("SELECT nom FROM produits").fetchone() == ("Stylo noir",)


def test_arrondi_numeric(depot_postgres, produit_stylo):
    """NUMERIC(10,2) : le prix est stocké avec 2 décimales et relu en float."""
    produit_stylo.prix_ht = 1.999
    depot_postgres.sauvegarder(produit_stylo)
    assert depot_postgres.charger("STY-01").prix_ht == 2.0


def test_isolation_entre_tests(depot_postgres):
    # Le conteneur est partagé, mais la table a été vidée par la fixture
    assert depot_postgres.tous() == []


def test_service_complet_sur_postgres(depot_postgres, mocker):
    client_taux = mocker.Mock()
    client_taux.taux.return_value = 1.0
    service = ServiceStock(depot_postgres, client_taux)

    service.ajouter_produit("STY-01", "Stylo", 1.50, quantite=100)
    service.sortir_stock("STY-01", 96)

    assert [p.reference for p in service.produits_en_rupture()] == ["STY-01"]
    assert service.valeur_stock() == 6.0
    with pytest.raises(ProduitInconnu):
        service.sortir_stock("NOPE", 1)
