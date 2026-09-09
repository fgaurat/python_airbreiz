"""TP03 - Les fixtures : injection de dépendances pour les tests.

Une fixture est une fonction décorée par @pytest.fixture. Un test la reçoit
en la nommant comme PARAMÈTRE. pytest s'occupe de l'appeler, de mettre en
cache sa valeur selon son scope, et d'exécuter son teardown.
"""

import pytest

from tp03_fixtures.banque import Compte, SoldeInsuffisant

# ---------------------------------------------------------------------------
# 1. Utilisation de base (fixtures définies dans conftest.py)
# ---------------------------------------------------------------------------


def test_banque_vide(banque):
    assert banque.nb_comptes == 0


def test_compte_alice(compte_alice):
    assert compte_alice.titulaire == "alice"
    assert compte_alice.solde == 100


def test_plusieurs_fixtures(banque, compte_alice, compte_bob):
    # `banque` est la MÊME instance que celle utilisée par compte_alice/compte_bob :
    # une fixture n'est instanciée qu'une fois par test, même si demandée plusieurs fois.
    assert banque.nb_comptes == 2
    assert banque.trouver("alice") is compte_alice


def test_virement(compte_alice, compte_bob):
    compte_alice.virer_vers(compte_bob, 30)
    assert compte_alice.solde == 70
    assert compte_bob.solde == 80


def test_virement_solde_insuffisant(compte_alice, compte_bob):
    with pytest.raises(SoldeInsuffisant):
        compte_alice.virer_vers(compte_bob, 500)
    # Le retrait a échoué avant le dépôt : rien n'a bougé
    assert compte_alice.solde == 100
    assert compte_bob.solde == 50


def test_isolation_des_fixtures(banque):
    # Chaque test reçoit une banque NEUVE (scope function) :
    # les comptes ouverts par les tests précédents n'existent plus.
    assert banque.nb_comptes == 0


# ---------------------------------------------------------------------------
# 2. Fixture factory
# ---------------------------------------------------------------------------


def test_factory(creer_compte, banque):
    c1 = creer_compte("carol", 10)
    c2 = creer_compte("dave")
    assert banque.nb_comptes == 2
    assert c1.solde == 10 and c2.solde == 0


# ---------------------------------------------------------------------------
# 3. Fixture avec yield (teardown) + fixture intégrée tmp_path
# ---------------------------------------------------------------------------


def test_journal(journal):
    journal.enregistrer("dépôt 100")
    journal.enregistrer("retrait 20")
    assert journal.lire() == ["dépôt 100", "retrait 20"]


# ---------------------------------------------------------------------------
# 4. Fixtures locales au module et surcharge (override)
# ---------------------------------------------------------------------------


@pytest.fixture
def compte_riche():
    return Compte("crésus", solde=1_000_000)


def test_fixture_locale(compte_riche):
    compte_riche.retirer(999_999)
    assert compte_riche.solde == 1


class TestSurcharge:
    # Une fixture définie dans une classe (ou un module) SURCHARGE celle du
    # conftest pour les tests de cette classe (ou de ce module) uniquement.
    @pytest.fixture
    def compte_alice(self, banque):
        return banque.ouvrir_compte("alice", solde=5000)

    def test_alice_est_riche_ici(self, compte_alice):
        assert compte_alice.solde == 5000


def test_alice_normale_ailleurs(compte_alice):
    assert compte_alice.solde == 100


# ---------------------------------------------------------------------------
# 5. L'objet `request` : introspection du test en cours
# ---------------------------------------------------------------------------


@pytest.fixture
def compte_nomme(request):
    """Crée un compte dont le titulaire est le nom du test qui le demande."""
    compte = Compte(titulaire=request.node.name)
    # Alternative au yield pour enregistrer un teardown :
    request.addfinalizer(lambda: print(
        f"\n[teardown] compte {compte.titulaire}"))
    return compte


def test_request_node_name(compte_nomme):
    assert compte_nomme.titulaire == "test_request_node_name"


@pytest.fixture
def info_fixture(request):
    return {
        "nom_fixture": request.fixturename,
        "scope": request.scope,
        "module": request.module.__name__,
    }


def test_request_infos(info_fixture):
    assert info_fixture["nom_fixture"] == "info_fixture"
    assert info_fixture["scope"] == "function"
    assert info_fixture["module"].endswith("test_fixtures")


# ---------------------------------------------------------------------------
# 6. autouse : appliquée automatiquement sans être demandée
# ---------------------------------------------------------------------------


class TestAutouse:
    @pytest.fixture(autouse=True)
    def _preparer(self, banque):
        # S'exécute avant chaque test de la classe, sans être listée en paramètre
        banque.ouvrir_compte("auto", solde=1)
        self.banque = banque

    def test_compte_auto_existe(self):
        assert self.banque.trouver("auto").solde == 1

    def test_toujours_une_banque_neuve(self):
        assert self.banque.nb_comptes == 1


# ---------------------------------------------------------------------------
# 7. usefixtures : demander une fixture sans utiliser sa valeur
# ---------------------------------------------------------------------------


@pytest.fixture
def journal_initialise(journal):
    journal.enregistrer("ouverture")
    return journal


@pytest.mark.usefixtures("journal_initialise")
def test_usefixtures():
    # On veut l'effet de bord (le journal existe) sans manipuler l'objet
    assert True


# ---------------------------------------------------------------------------
# 8. Scopes module / session : partagés entre plusieurs tests
# ---------------------------------------------------------------------------


def test_parametres_session(parametres):
    assert parametres["devise"] == "EUR"


def test_connexion_partagee_1(connexion_bdd):
    connexion_bdd["requetes"].append("SELECT 1")
    assert connexion_bdd["ouverte"]


def test_connexion_partagee_2(connexion_bdd):
    # Même objet que dans le test précédent : la requête est encore là.
    # ATTENTION : c'est exactement le genre de couplage entre tests à éviter
    # avec des scopes larges. Ne partager que des ressources en lecture seule
    # ou coûteuses à créer (connexion, serveur, gros jeu de données).
    assert connexion_bdd["requetes"] == ["SELECT 1"]
