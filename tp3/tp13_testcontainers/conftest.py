"""conftest.py du TP13 : conteneurs Docker jetables via Testcontainers.

Principe : une fixture de scope SESSION démarre le conteneur une seule fois
(quelques secondes), tous les tests l'utilisent, et il est détruit à la fin.
L'isolation entre tests se fait au niveau des DONNÉES (TRUNCATE), pas en
redémarrant le conteneur.
"""

from pathlib import Path

import pytest

from tp11_projet.stock.modeles import Produit
from tp13_testcontainers.depot_postgres import DepotPostgres

ICI = Path(__file__).parent


def pytest_collection_modifyitems(items):
    """Marque `docker` + `integration` tous les tests de ce répertoire.

    Piège : `pytestmark = ...` n'a AUCUN effet dans un conftest.py (il ne
    fonctionne que dans un module de test). Pour marquer tout un répertoire,
    on passe par ce hook (voir TP10). Permet `pytest -m "not docker"`.
    """
    for item in items:
        if ICI in item.path.parents:
            item.add_marker(pytest.mark.docker)
            item.add_marker(pytest.mark.integration)


def _docker_disponible() -> bool:
    try:
        from testcontainers.core.docker_client import DockerClient

        DockerClient().client.ping()
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def docker():
    """Skippe TOUS les tests dépendants si le démon Docker est injoignable.

    pytest.skip() dans une fixture session -> chaque test qui en dépend est
    marqué SKIPPED avec cette raison, la suite continue normalement.
    """
    if not _docker_disponible():
        pytest.skip("démon Docker injoignable : démarrez Docker Desktop / Colima / Podman")


# ---------------------------------------------------------------------------
# PostgreSQL : module dédié, prêt à l'emploi (attend que la base accepte les connexions)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_url(docker):
    from testcontainers.community.postgres import PostgresContainer

    # driver=None -> URL "postgresql://user:pass@host:port/db" utilisable par psycopg 3
    with PostgresContainer("postgres:16-alpine", driver=None) as conteneur:
        yield conteneur.get_connection_url()
    # sortie du `with` -> conteneur arrêté et supprimé


@pytest.fixture(scope="session")
def depot_postgres_session(postgres_url):
    return DepotPostgres(postgres_url)  # crée le schéma une fois


@pytest.fixture
def depot_postgres(depot_postgres_session):
    """Version function-scope : table vidée avant ET après chaque test."""
    depot_postgres_session.vider()
    yield depot_postgres_session
    depot_postgres_session.vider()


# ---------------------------------------------------------------------------
# Fixtures nécessaires pour rejouer les tests de contrat du TP11 tels quels
# ---------------------------------------------------------------------------


@pytest.fixture(params=["postgres"])
def depot(request):
    # Même nom, même forme que dans tp11_projet/tests/conftest.py :
    # les tests de contrat ne voient pas la différence.
    return request.getfixturevalue(f"depot_{request.param}")


@pytest.fixture
def produit_stylo():
    return Produit("STY-01", "Stylo bleu", prix_ht=1.50, quantite=100)


@pytest.fixture
def produit_cahier():
    return Produit("CAH-01", "Cahier A4", prix_ht=3.20, quantite=4)


# ---------------------------------------------------------------------------
# Conteneur générique : n'importe quelle image, ici Redis
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def redis_adresse(docker):
    from testcontainers.core.container import DockerContainer
    from testcontainers.core.wait_strategies import LogMessageWaitStrategy

    # Stratégie d'attente : le port est ouvert avant que Redis soit prêt ;
    # on attend donc la ligne de log qui signale la disponibilité.
    conteneur = (
        DockerContainer("redis:7-alpine")
        .with_exposed_ports(6379)
        .waiting_for(LogMessageWaitStrategy("Ready to accept connections"))
    )
    with conteneur:
        yield conteneur.get_container_host_ip(), int(conteneur.get_exposed_port(6379))
