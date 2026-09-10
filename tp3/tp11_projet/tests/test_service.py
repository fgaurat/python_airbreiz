"""Tests du service : fakes, mocks, logs (TP03, TP06, TP07, TP08)."""

import logging

import pytest

from tp11_projet.stock.depot import ProduitInconnu
from tp11_projet.stock.service import ServiceStock, StockInsuffisant
from tp11_projet.stock.tarification import ServiceTauxIndisponible


class TestAjouterProduit:
    def test_ajout(self, service):
        p = service.ajouter_produit("GOM-01", "Gomme", 0.80, quantite=10)
        assert service.depot.charger("GOM-01") is p

    def test_doublon(self, service):
        with pytest.raises(ValueError, match="existe déjà"):
            service.ajouter_produit("STY-01", "Autre stylo", 2.0)

    def test_journalise(self, service, caplog):
        with caplog.at_level(logging.INFO, logger="stock"):
            service.ajouter_produit("GOM-01", "Gomme", 0.80, quantite=10)
        assert "produit GOM-01 ajouté (10 unités)" in caplog.messages


class TestMouvements:
    def test_entrer(self, service):
        assert service.entrer_stock("STY-01", 50).quantite == 150

    def test_sortir(self, service):
        assert service.sortir_stock("STY-01", 30).quantite == 70

    @pytest.mark.parametrize("methode", ["entrer_stock", "sortir_stock"])
    @pytest.mark.parametrize("quantite", [0, -5])
    def test_quantite_invalide(self, service, methode, quantite):
        with pytest.raises(ValueError, match="positive"):
            getattr(service, methode)("STY-01", quantite)

    def test_sortir_trop(self, service):
        with pytest.raises(StockInsuffisant, match="100 disponible"):
            service.sortir_stock("STY-01", 101)
        assert service.depot.charger("STY-01").quantite == 100  # inchangé

    def test_produit_inconnu(self, service):
        with pytest.raises(ProduitInconnu):
            service.sortir_stock("NOPE", 1)

    def test_alerte_seuil(self, service, caplog):
        service.sortir_stock("STY-01", 96)  # reste 4 <= seuil 5
        assert any(r.levelno == logging.WARNING and "STY-01" in r.getMessage() for r in caplog.records)

    def test_pas_d_alerte_au_dessus_du_seuil(self, service, caplog):
        service.sortir_stock("STY-01", 10)
        assert not [r for r in caplog.records if r.levelno >= logging.WARNING]


class TestRupture:
    def test_produits_en_rupture(self, service):
        assert [p.reference for p in service.produits_en_rupture()] == ["CAH-01"]

    def test_apres_reapprovisionnement(self, service):
        service.entrer_stock("CAH-01", 20)
        assert service.produits_en_rupture() == []


class TestValeurStock:
    # stylo : 100 x 1.50 = 150 ; cahier : 4 x 3.20 = 12.80 ; total 162.80 EUR

    def test_en_euros(self, service, client_taux):
        assert service.valeur_stock() == 162.80
        client_taux.taux.assert_called_once_with("EUR")

    def test_en_dollars(self, service, client_taux):
        client_taux.taux.return_value = 1.10
        assert service.valeur_stock("USD") == pytest.approx(179.08)
        client_taux.taux.assert_called_once_with("USD")

    def test_service_taux_indisponible(self, service, client_taux, caplog):
        client_taux.taux.side_effect = ServiceTauxIndisponible("timeout")
        assert service.valeur_stock("USD") == 162.80  # repli en EUR
        assert "taux USD indisponible" in caplog.text

    def test_stock_vide(self, depot_memoire, client_taux):
        assert ServiceStock(depot_memoire, client_taux).valeur_stock() == 0.0


def test_le_garde_fou_reseau_fonctionne(depot_memoire):
    """Sans client mocké, ServiceStock utilise le vrai ClientTaux : le conftest
    doit bloquer l'appel. valeur_stock() attrape ServiceTauxIndisponible...
    mais notre garde-fou lève RuntimeError, qui n'est PAS un OSError -> il remonte."""
    service = ServiceStock(depot_memoire)
    with pytest.raises(RuntimeError, match="réseau interdit"):
        service.valeur_stock("USD")
