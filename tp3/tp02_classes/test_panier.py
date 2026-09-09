"""TP02 - Regrouper les tests dans des classes.

Une classe de test :
  - commence par `Test` (configurable via `python_classes`) ;
  - n'a PAS de méthode __init__ (pytest l'ignorerait avec un avertissement) ;
  - ses méthodes de test commencent par `test` ;
  - une NOUVELLE instance de la classe est créée pour CHAQUE test
    -> pas d'état partagé via `self` entre deux tests.
"""

import pytest

from panier import Article, Panier, PanierVide

# ---------------------------------------------------------------------------
# 1. Classe simple : regroupement logique, sans état partagé
# ---------------------------------------------------------------------------


class TestArticle:
    def test_sous_total_quantite_1(self):
        assert Article("stylo", 2.5).sous_total == 2.5

    def test_sous_total_quantite_multiple(self):
        assert Article("stylo", 2.5, quantite=4).sous_total == 10.0


# ---------------------------------------------------------------------------
# 2. setup_method / teardown_method : exécutés avant/après CHAQUE test
# ---------------------------------------------------------------------------


class TestPanier:
    def setup_method(self, method):
        # `method` est la fonction de test qui va s'exécuter (rarement utile)
        self.panier = Panier()
        self.panier.ajouter("stylo", 2.0, quantite=3)
        self.panier.ajouter("cahier", 5.0)

    def teardown_method(self, method):
        # Ici : rien à libérer, mais c'est l'endroit pour fermer un fichier, etc.
        self.panier = None

    def test_nombre_articles(self):
        assert len(self.panier) == 2

    def test_total(self):
        assert self.panier.total() == 11.0

    def test_ajouter_meme_article_cumule_la_quantite(self):
        self.panier.ajouter("stylo", 2.0, quantite=2)
        assert self.panier.quantite_de("stylo") == 5
        assert len(self.panier) == 2

    def test_retirer(self):
        self.panier.retirer("cahier")
        assert len(self.panier) == 1
        assert self.panier.quantite_de("cahier") == 0

    def test_retirer_article_inconnu(self):
        with pytest.raises(KeyError, match="inconnu"):
            self.panier.retirer("gomme")

    def test_isolation_entre_tests(self):
        # Preuve que setup_method a bien recréé un panier neuf :
        # les modifications des tests précédents ne sont pas visibles ici.
        assert self.panier.quantite_de("stylo") == 3
        assert len(self.panier) == 2


# ---------------------------------------------------------------------------
# 3. setup_class / teardown_class : une seule fois pour toute la classe
# ---------------------------------------------------------------------------


class TestPanierRemise:
    compteur_setup_class = 0
    compteur_setup_method = 0

    @classmethod
    def setup_class(cls):
        # Ressource coûteuse partagée par tous les tests de la classe
        cls.compteur_setup_class += 1
        cls.catalogue = {"stylo": 2.0, "cahier": 5.0, "sac": 30.0}

    @classmethod
    def teardown_class(cls):
        cls.catalogue = None

    def setup_method(self):
        type(self).compteur_setup_method += 1
        self.panier = Panier()
        for nom, prix in self.catalogue.items():
            self.panier.ajouter(nom, prix)

    def test_sans_remise(self):
        assert self.panier.total() == 37.0

    def test_remise_10_pourcent(self):
        self.panier.appliquer_remise(10)
        assert self.panier.total() == 33.3

    def test_remise_100_pourcent(self):
        self.panier.appliquer_remise(100)
        assert self.panier.total() == 0

    @pytest.mark.parametrize("remise", [-1, 101, 250])
    def test_remise_invalide(self, remise):
        with pytest.raises(ValueError):
            self.panier.appliquer_remise(remise)

    def test_setup_class_appele_une_seule_fois(self):
        assert self.compteur_setup_class == 1
        # setup_method a été appelé au moins pour ce test
        assert self.compteur_setup_method >= 1


# ---------------------------------------------------------------------------
# 4. Classes + fixtures : la combinaison la plus courante (détails au TP03)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
@pytest.fixture(scope="function")  # par défaut
def panier_rempli():
    panier = Panier()
    panier.ajouter("stylo", 2.0, quantite=3)
    panier.ajouter("cahier", 5.0)
    return panier


class TestValidation:
    def test_valider_panier_rempli(self, panier_rempli):
        assert panier_rempli.valider() == 11.0

    def test_valider_panier_vide(self):
        with pytest.raises(PanierVide):
            Panier().valider()

    def test_est_vide(self, panier_rempli):
        assert not panier_rempli.est_vide()
        assert Panier().est_vide()


# ---------------------------------------------------------------------------
# 5. Classes imbriquées : sous-regroupements
# ---------------------------------------------------------------------------


class TestAjouter:
    # region Cas nominaux
    class TestCasNominaux:
        def test_ajout_simple(self):
            p = Panier()
            p.ajouter("stylo", 1.0)
            assert p.quantite_de("stylo") == 1
    # endregion Cas nominaux

    # region Cas erreurs
    class TestCasErreurs:

        @pytest.mark.parametrize("quantite", [0, -1])
        def test_quantite_invalide(self, quantite):
            with pytest.raises(ValueError, match="quantité"):
                Panier().ajouter("stylo", 1.0, quantite=quantite)

        def test_prix_negatif(self):
            with pytest.raises(ValueError, match="prix"):
                Panier().ajouter("stylo", -1.0)

    # endregion Cas erreurs
# ---------------------------------------------------------------------------
# 6. Ce qui n'est PAS collecté
# ---------------------------------------------------------------------------


class OutilsPanier:
    """Pas de préfixe `Test` : ignorée par pytest, utilisable comme helper."""

    @staticmethod
    def panier_avec(*noms):
        p = Panier()
        for nom in noms:
            p.ajouter(nom, 1.0)
        return p


def test_helper_classe():
    assert len(OutilsPanier.panier_avec("a", "b", "c")) == 3
