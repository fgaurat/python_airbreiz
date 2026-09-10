"""Tests des dépôts : même suite pour les deux implémentations (TP03, TP04, TP08)."""

import json

import pytest

from tp11_projet.stock.depot import DepotJSON, ProduitInconnu
from tp11_projet.stock.modeles import Produit


class TestContratDepot:
    """Ces tests tournent 2 fois : depot[memoire] et depot[json]."""

    def test_vide_au_depart(self, depot):
        assert depot.tous() == []

    def test_sauvegarder_et_charger(self, depot, produit_stylo):
        depot.sauvegarder(produit_stylo)
        assert depot.charger("STY-01") == produit_stylo

    def test_charger_inconnu(self, depot):
        with pytest.raises(ProduitInconnu):
            depot.charger("NOPE")

    def test_sauvegarder_ecrase(self, depot, produit_stylo):
        depot.sauvegarder(produit_stylo)
        produit_stylo.quantite = 1
        depot.sauvegarder(produit_stylo)
        assert depot.charger("STY-01").quantite == 1
        assert len(depot.tous()) == 1

    def test_tous_trie_par_reference(self, depot, produit_stylo, produit_cahier):
        depot.sauvegarder(produit_stylo)
        depot.sauvegarder(produit_cahier)
        assert [p.reference for p in depot.tous()] == ["CAH-01", "STY-01"]

    def test_supprimer(self, depot, produit_stylo):
        depot.sauvegarder(produit_stylo)
        depot.supprimer("STY-01")
        assert depot.tous() == []
        with pytest.raises(ProduitInconnu):
            depot.supprimer("STY-01")


class TestDepotJSON:
    """Spécifique au fichier : format, persistance réelle."""

    def test_fichier_cree_au_premier_enregistrement(self, depot_json, produit_stylo):
        assert not depot_json.chemin.exists()
        depot_json.sauvegarder(produit_stylo)
        assert depot_json.chemin.exists()

    def test_format_json_lisible(self, depot_json, produit_stylo):
        depot_json.sauvegarder(produit_stylo)
        contenu = json.loads(depot_json.chemin.read_text(encoding="utf-8"))
        assert contenu["STY-01"]["nom"] == "Stylo bleu"

    def test_persistance_entre_deux_instances(self, tmp_path, produit_stylo):
        chemin = tmp_path / "s.json"
        DepotJSON(chemin).sauvegarder(produit_stylo)
        assert DepotJSON(chemin).charger("STY-01") == produit_stylo
