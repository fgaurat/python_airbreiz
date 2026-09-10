"""Tests d'intégration : tout le circuit, fichier JSON réel, seul le réseau est simulé."""

import pytest

from tp11_projet.stock.depot import DepotJSON
from tp11_projet.stock.service import ServiceStock

pytestmark = pytest.mark.integration


@pytest.fixture
def client_taux_fixe(mocker):
    client = mocker.Mock()
    client.taux.side_effect = lambda devise: {"EUR": 1.0, "USD": 1.10, "GBP": 0.85}[devise]
    return client


def test_scenario_complet(tmp_path, client_taux_fixe, caplog):
    chemin = tmp_path / "stock.json"
    service = ServiceStock(DepotJSON(chemin), client_taux_fixe)

    service.ajouter_produit("STY-01", "Stylo", 1.50, quantite=100)
    service.ajouter_produit("CAH-01", "Cahier", 3.20, quantite=20)
    service.sortir_stock("CAH-01", 17)
    service.entrer_stock("STY-01", 50)

    # Nouvelle instance sur le même fichier : l'état est bien persisté
    service2 = ServiceStock(DepotJSON(chemin), client_taux_fixe)
    assert [p.reference for p in service2.produits_en_rupture()] == ["CAH-01"]
    assert service2.valeur_stock("USD") == pytest.approx((150 * 1.50 + 3 * 3.20) * 1.10)
    assert "CAH-01 sous le seuil" in caplog.text


@pytest.mark.skipif("config.getoption('--env') == 'prod'", reason="jamais contre la prod")
def test_skip_conditionnel_par_env(env):
    assert env != "prod"
