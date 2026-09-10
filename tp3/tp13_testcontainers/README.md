# TP13 – Testcontainers : tester contre de vraies dépendances

## En une phrase

Une fixture de scope session démarre un vrai PostgreSQL (et un vrai Redis)
dans un conteneur Docker jetable ; les tests de contrat écrits au TP11
s'exécutent contre cette base sans qu'une ligne soit réécrite, puis le
conteneur est détruit.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- expliquer ce que fait Testcontainers : client Docker, ports aléatoires,
  attente de disponibilité, nettoyage par Ryuk ;
- écrire une fixture session qui démarre un conteneur et une fixture
  function qui isole les tests par les données ;
- réutiliser une suite de tests de contrat pour une nouvelle
  implémentation ;
- faire échouer proprement (skip) quand Docker est absent, et exclure ces
  tests avec un marqueur ;
- utiliser un module dédié (`PostgresContainer`) et le conteneur générique
  (`DockerContainer`) avec une stratégie d'attente ;
- situer Testcontainers par rapport aux mocks et aux fakes, et l'intégrer
  en CI.

## Prérequis

- TP03 (scopes de fixtures, `yield`), TP04 (fixture paramétrée), TP05
  (marqueurs), TP10 (hook `pytest_collection_modifyitems`), TP11 (le
  protocole `Depot` et `TestContratDepot`).
- Un démon Docker accessible : Docker Desktop, Colima, Rancher Desktop ou
  Podman (avec `DOCKER_HOST` pointé sur son socket). Vérifier la veille
  avec `docker info`.
- Les images `postgres:16-alpine` (environ 100 Mo) et `redis:7-alpine`
  (environ 15 Mo) : les télécharger avant la session en lançant une fois
  les tests.
- Les paquets `testcontainers[postgres]` et `psycopg[binary]`, déjà dans
  les dépendances de développement.

## Fichiers

| Fichier | Rôle |
|---|---|
| `depot_postgres.py` | `DepotPostgres` : implémentation SQL du protocole `Depot` du TP11, avec psycopg 3 |
| `conftest.py` | hook de marquage, fixtures `docker`, `postgres_url`, `depot_postgres_session`, `depot_postgres`, `depot`, produits, `redis_adresse` |
| `test_depot_postgres.py` | `TestContratDepot` importée du TP11 + cinq tests spécifiques SQL |
| `test_redis_generique.py` | conteneur générique, dialogue avec Redis par socket |

## Mise en route

```bash
uv run pytest tp13_testcontainers -v
```

Sortie attendue : `15 passed` en 3 à 5 secondes quand les images sont déjà
présentes (la première exécution prend jusqu'à une minute pour les
télécharger). Décompte : 6 tests de contrat `[postgres]`, 5 tests SQL, 4
tests Redis.

Commandes à préparer :

```bash
uv run pytest tp13_testcontainers --setup-show          # cycle de vie des fixtures
uv run pytest tp13_testcontainers --durations=3         # où passe le temps
uv run pytest -m "not docker"                           # toute la formation sans ce TP
uv run pytest -m docker                                 # seulement ce TP
DOCKER_HOST=unix:///nonexistent.sock uv run pytest tp13_testcontainers -ra   # simuler l'absence de Docker
docker ps                                               # à lancer pendant les tests, dans un second terminal
```

## Déroulé de la présentation

Ordre conseillé : cinq minutes sur le fonctionnement de Testcontainers,
puis `depot_postgres.py`, puis `conftest.py` fixture par fixture, puis les
deux fichiers de tests, puis les démonstrations (sans Docker, `docker ps`,
`--setup-show`). Compter 30 minutes plus 15 minutes d'exercices.

### Comment fonctionne Testcontainers

- **À dire aux stagiaires** : Testcontainers est une bibliothèque, pas un
  outil en ligne de commande. Depuis le processus pytest, elle parle au
  démon Docker par son API (socket Unix ou TCP, via le paquet `docker`),
  demande le démarrage d'un conteneur à partir d'une image, attend qu'il
  soit prêt, expose ses ports sur des **ports aléatoires** de la machine
  hôte, et le supprime à la fin. Trois conséquences :
  - pas de conflit de port entre deux exécutions parallèles ;
  - le test lit l'adresse réelle (`get_connection_url()`,
    `get_exposed_port(6379)`) au lieu de la coder en dur ;
  - la base est neuve à chaque session, identique en local et en CI.
- **Ryuk** : Testcontainers démarre aussi un petit conteneur auxiliaire,
  `testcontainers/ryuk`, qui surveille le processus de test. Si pytest est
  tué (Ctrl-C, crash, OOM), Ryuk supprime les conteneurs orphelins. C'est
  pour cela que `docker ps` montre deux conteneurs pendant les tests.
- **À montrer en direct**, dans un second terminal pendant que les tests
  tournent :

  ```
  $ docker ps --format '{{.Image}}  {{.Ports}}'
  postgres:16-alpine         0.0.0.0:59875->5432/tcp
  testcontainers/ryuk:0.8.1  0.0.0.0:59873->8080/tcp
  ```

  Puis, une fois les tests terminés, `docker ps -a` : plus rien. Le port
  59875 change à chaque exécution.

### depot_postgres.py : la troisième implémentation

- **Ce que montre le code** : `DepotPostgres(url)` crée la table au
  démarrage avec `CREATE TABLE IF NOT EXISTS`. La table porte des
  contraintes `CHECK (prix_ht >= 0)` et `CHECK (quantite >= 0)`, un
  `PRIMARY KEY` sur la référence, un `NUMERIC(10, 2)` pour le prix.
  Chaque méthode ouvre une connexion avec `with self._connexion() as conn`
  (psycopg 3 valide la transaction à la sortie du bloc, ou l'annule en cas
  d'exception).

  ```python
  INSERT INTO produits (...) VALUES (%s, %s, %s, %s, %s, %s)
  ON CONFLICT (reference) DO UPDATE SET
      nom = EXCLUDED.nom, prix_ht = EXCLUDED.prix_ht, quantite = EXCLUDED.quantite, ...
  ```

- **À dire aux stagiaires** : `sauvegarder` fait un *upsert* : insertion,
  ou mise à jour si la référence existe déjà. C'est exactement le contrat
  de `DepotMemoire` (un `dict`) et de `DepotJSON`, exprimé en SQL.
  `supprimer` utilise `curseur.rowcount == 0` pour lever `ProduitInconnu`.
  La méthode `vider()` n'existe que pour les tests : c'est un compromis
  assumé, documenté dans sa docstring.
- **Conversions de types** : psycopg renvoie un `NUMERIC` sous forme de
  `decimal.Decimal`, que `_vers_produit` convertit en `float` pour rester
  compatible avec `Produit`. Une `DATE` revient déjà en `datetime.date`.
  C'est le genre de détail qu'un fake ne révèle jamais.
- **Pièges** : les paramètres de requête utilisent `%s` (style psycopg),
  pas `?` (style sqlite3) ni des f-strings (injection SQL). Ne jamais
  formater une valeur dans la chaîne SQL.

### conftest.py, bloc 1 : marquer tout le répertoire

```python
def pytest_collection_modifyitems(items):
    for item in items:
        if ICI in item.path.parents:
            item.add_marker(pytest.mark.docker)
            item.add_marker(pytest.mark.integration)
```

- **Ce que montre le code** : un hook de collecte (vu au TP10) qui ajoute
  deux marqueurs à chaque test dont le chemin est sous ce répertoire.
- **À dire aux stagiaires** : la première version de ce fichier contenait
  `pytestmark = [pytest.mark.docker, pytest.mark.integration]`, et
  `-m "not docker"` n'excluait rien. `pytestmark` n'a d'effet que dans un
  module de test ; dans un `conftest.py`, il est ignoré sans avertissement.
  Le hook est la seule façon de marquer un répertoire entier. Comme le hook
  reçoit tous les items de la session, il faut filtrer par chemin, sinon
  les tests des autres TP seraient marqués aussi.
- **À montrer en direct** : `uv run pytest -m "not docker" -q` affiche
  `15 deselected` ; `uv run pytest -m docker -q` affiche `15 passed, 296 deselected`.

### conftest.py, bloc 2 : la fixture `docker`

```python
@pytest.fixture(scope="session")
def docker():
    if not _docker_disponible():
        pytest.skip("démon Docker injoignable : démarrez Docker Desktop / Colima / Podman")
```

- **Ce que montre le code** : `_docker_disponible()` crée un
  `DockerClient` et appelle `ping()` ; toute exception signifie « pas de
  démon ». La fixture ne renvoie rien : elle sert de garde.
- **À dire aux stagiaires** : `pytest.skip()` dans une fixture de scope
  session marque **tous** les tests qui en dépendent comme `SKIPPED`, avec
  la raison, et la suite continue. C'est ce qui permet à un stagiaire sans
  Docker de lancer `uv run pytest` à la racine et d'avoir un résultat vert.
  Les fixtures `postgres_url` et `redis_adresse` dépendent de `docker`, donc
  tout le TP est protégé par cette seule fixture.
- **À montrer en direct** :

  ```
  $ DOCKER_HOST=unix:///nonexistent.sock uv run pytest tp13_testcontainers -ra
  SKIPPED [1] tp11_projet/tests/test_depot.py:14: démon Docker injoignable : démarrez Docker Desktop / Colima / Podman
  SKIPPED [1] tp11_projet/tests/test_depot.py:17: démon Docker injoignable : ...
  ...
  15 skipped in 0.15s
  ```

  Remarquer que les tests de contrat sont rapportés avec le chemin de
  `tp11_projet/tests/test_depot.py` : c'est là que le code de la classe est
  écrit, même s'il est collecté ici.
- **Pièges** : la détection par `ping()` prend quelques dizaines de
  millisecondes. Une alternative est une option `--docker` explicite
  (comme `--lent` au TP10), mais le skip automatique est plus confortable
  en formation.

### conftest.py, bloc 3 : PostgreSQL

```python
@pytest.fixture(scope="session")
def postgres_url(docker):
    from testcontainers.community.postgres import PostgresContainer
    with PostgresContainer("postgres:16-alpine", driver=None) as conteneur:
        yield conteneur.get_connection_url()
```

- **Ce que montre le code** : `PostgresContainer` est un module dédié :
  il connaît l'image, le port 5432, crée un utilisateur `test` avec le mot
  de passe `test` et une base `test`, et surtout **attend** que la base
  accepte les connexions avant de rendre la main. `driver=None` produit
  une URL `postgresql://test:test@localhost:PORT/test` que psycopg 3
  comprend directement (par défaut, l'URL contient `+psycopg2` pour
  SQLAlchemy). Le `yield` à l'intérieur du `with` fait que la sortie du
  bloc, donc l'arrêt et la suppression du conteneur, se produit au
  teardown de la session.
- **`depot_postgres_session`** construit un seul `DepotPostgres`, donc
  crée le schéma une seule fois. **`depot_postgres`** (scope function)
  vide la table avant et après chaque test : c'est l'isolation par les
  **données**, pas par le conteneur.
- **À dire aux stagiaires** : démarrer un conteneur coûte une à deux
  secondes, `TRUNCATE` coûte une milliseconde. On paie le démarrage une
  fois par session et on isole chaque test à bas coût. Vider avant **et**
  après : avant, pour ne pas dépendre du test précédent (qui a pu être
  interrompu) ; après, pour laisser la table propre au test suivant d'un
  autre fichier.
- **À montrer en direct** :

  ```
  $ uv run pytest tp13_testcontainers --setup-show -q
  SETUP    S docker
  SETUP    S postgres_url (fixtures used: docker)
  SETUP    S depot_postgres_session (fixtures used: postgres_url)
          SETUP    F depot_postgres (fixtures used: depot_postgres_session)
          SETUP    F depot['postgres']
          TEARDOWN F depot['postgres']
          TEARDOWN F depot_postgres
  ...
  SETUP    S redis_adresse (fixtures used: docker)
  ...
  TEARDOWN S redis_adresse
  TEARDOWN S depot_postgres_session
  TEARDOWN S postgres_url
  TEARDOWN S docker
  ```

  Et `--durations=3` : le premier test porte 1,5 s de `setup` (démarrage
  du conteneur), tous les autres sont en millisecondes.
- **Pièges** : l'import de `PostgresContainer` est fait dans la fixture,
  pas en tête de fichier, pour que le `conftest.py` reste importable sur
  une machine où `testcontainers` ne serait pas installé. Le module
  `testcontainers.postgres` (sans `community`) fonctionne encore mais
  émet un `DeprecationWarning` depuis la version 4.15 ; avec
  `filterwarnings = ["error"]` il ferait échouer la suite.

### conftest.py, bloc 4 : rejouer le contrat

```python
@pytest.fixture(params=["postgres"])
def depot(request):
    return request.getfixturevalue(f"depot_{request.param}")
```

- **Ce que montre le code** : une fixture `depot` de même nom et de même
  forme que celle du TP11, mais avec un seul paramètre. Les fixtures
  `produit_stylo` et `produit_cahier` sont recopiées à l'identique parce
  que le `conftest.py` du TP11 n'est pas visible depuis ce répertoire.
- **À dire aux stagiaires** : c'est le prix de la réutilisation entre deux
  arborescences. Dans un vrai projet, ces fixtures seraient dans un
  `conftest.py` commun ou dans un plugin local. L'alternative, plus simple
  quand tout est dans le même projet, est d'ajouter `"postgres"` aux
  `params` de la fixture du TP11 et de définir `depot_postgres` à côté.

### conftest.py, bloc 5 : Redis avec le conteneur générique

```python
conteneur = (
    DockerContainer("redis:7-alpine")
    .with_exposed_ports(6379)
    .waiting_for(LogMessageWaitStrategy("Ready to accept connections"))
)
with conteneur:
    yield conteneur.get_container_host_ip(), int(conteneur.get_exposed_port(6379))
```

- **Ce que montre le code** : `DockerContainer` accepte n'importe quelle
  image. On déclare le port à exposer et une **stratégie d'attente** : ici,
  attendre la ligne de log que Redis écrit quand il est prêt. La fixture
  renvoie un tuple `(hôte, port)`.
- **À dire aux stagiaires** : avec un module dédié, l'attente est
  intégrée. Avec le générique, il faut la choisir soi-même, et c'est
  indispensable : le port TCP est ouvert par Docker avant que le service
  soit réellement prêt, et un test lancé trop tôt échoue de façon
  intermittente. Stratégies disponibles dans
  `testcontainers.core.wait_strategies` : `LogMessageWaitStrategy`,
  `HttpWaitStrategy` (un GET qui répond 200), `PortWaitStrategy`, ou une
  fonction personnalisée. L'ancienne fonction `wait_for_logs(...)` est
  dépréciée.
- **Pièges** : `get_exposed_port` renvoie une chaîne ; d'où le `int(...)`.
  `get_container_host_ip()` renvoie `localhost` en général, mais peut être
  différent avec Docker distant ou certaines configurations de Podman :
  ne pas coder `localhost` en dur.

### test_depot_postgres.py : le contrat, puis le spécifique

```python
from tp11_projet.tests.test_depot import TestContratDepot  # noqa: F401
```

- **Ce que montre le code** : une seule ligne d'import, et six tests
  apparaissent dans ce module avec l'id `[postgres]`.
- **À dire aux stagiaires** : pytest collecte les classes `Test*` présentes
  dans l'espace de noms du module, qu'elles y soient définies ou importées.
  Les fixtures sont résolues **à l'emplacement du test collecté**, donc
  `depot` est celle de ce `conftest.py`. Le `# noqa: F401` empêche le
  linter de supprimer un import qui semble inutilisé. Ce mécanisme a un
  revers : si l'on importe une classe de test par erreur (par exemple pour
  en réutiliser une méthode utilitaire), ses tests sont exécutés deux
  fois. Certains préfèrent une classe de base sans préfixe `Test`, héritée
  dans chaque module : `class TestPostgres(ContratDepot): pass`.
- **Les cinq tests spécifiques** :
  - `test_contraintes_sql` : un `UPDATE` direct qui viole `CHECK (quantite
    >= 0)` lève `psycopg.errors.CheckViolation`. La base protège même
    contre du code qui contournerait `Produit.__post_init__`.
  - `test_upsert_ne_cree_pas_de_doublon` : deux `sauvegarder` de la même
    référence, puis `SELECT count(*)` qui doit valoir 1 et le nom mis à jour.
  - `test_arrondi_numeric` : un prix de 1.999 est stocké en `NUMERIC(10,2)`
    et relu à 2.0. C'est une différence de comportement avec `DepotMemoire`
    et `DepotJSON`, qui conservent 1.999 : le contrat commun ne teste pas
    ce point, chaque implémentation a ses propres règles d'arrondi.
  - `test_isolation_entre_tests` : la table est vide malgré les tests
    précédents.
  - `test_service_complet_sur_postgres` : `ServiceStock` avec ce dépôt et un
    client de taux mocké ; toute la logique métier tourne contre la vraie
    base.
- **À montrer en direct** : `uv run pytest tp13_testcontainers/test_depot_postgres.py -v`
  pour voir les six ids `[postgres]` suivis des cinq tests nommés.
- **Pièges** : `test_contraintes_sql` combine deux gestionnaires de
  contexte sur une ligne : `with psycopg.connect(...) as conn,
  pytest.raises(...)`. L'ordre compte : la connexion est ouverte avant
  `raises`, et fermée après.

### test_redis_generique.py : parler RESP

- **Ce que montre le code** : `_commande_redis(adresse, *mots)` encode une
  commande au format RESP, le protocole texte de Redis : `*N` pour le
  nombre d'arguments, puis `$longueur` et la valeur pour chacun, chaque
  ligne terminée par `\r\n`. `PING` donne `*1\r\n$4\r\nPING\r\n` et Redis
  répond `+PONG\r\n`. `GET` d'une clé absente répond `$-1\r\n`.
- **À dire aux stagiaires** : on n'installe pas de bibliothèque cliente
  pour garder l'exemple minimal ; le point est le conteneur, pas Redis.
  Dans un vrai projet, `uv add redis` et
  `redis.Redis(host, port).ping()`. Ce fichier montre aussi que le
  garde-fou réseau du TP11 ne s'applique pas ici : il est limité au
  répertoire `tp11_projet/tests`.
- **Pièges** : `test_set_get` laisse la clé `formation` dans Redis. Les
  autres tests utilisent des clés différentes, donc pas d'interférence,
  mais un `FLUSHALL` en fixture function serait la version rigoureuse.

## Questions fréquentes des stagiaires

**Quelle différence avec un `docker compose up` avant les tests ?**
Compose démarre une infrastructure fixe, sur des ports fixes, que l'on
oublie d'arrêter, et que chaque développeur configure différemment.
Testcontainers démarre depuis le code de test, sur des ports aléatoires,
avec attente de disponibilité et nettoyage garanti ; la configuration est
versionnée avec les tests. Compose reste utile pour faire tourner
l'application en développement.

**Pourquoi ne pas utiliser SQLite en mémoire ?**
Parce que ce n'est pas la même base : types, contraintes, transactions,
fonctions SQL, comportement de `ON CONFLICT`, tout diffère. Un test qui
passe sur SQLite peut échouer sur PostgreSQL. SQLite reste un bon fake
pour la logique métier (exercice 3 du TP11) ; Testcontainers vérifie le
vrai SQL.

**Combien de temps ça prend en CI ?**
Environ 2 secondes de démarrage pour PostgreSQL une fois l'image en cache,
plus le téléchargement la première fois. Les runners CI mettent les images
en cache. Pour des dizaines de tests d'intégration, le coût est
négligeable devant celui d'un pipeline complet.

**Peut-on garder le conteneur entre deux exécutions pour aller plus vite ?**
Oui, avec `TESTCONTAINERS_REUSE_ENABLE=true` et `.with_kwargs(...)` ou
`with_name` selon les versions, mais on perd la garantie d'une base neuve.
À réserver au développement local.

**Et avec xdist ?**
Une fixture session est créée **une fois par worker** : `-n 4` démarre
quatre PostgreSQL. C'est correct (chaque worker a sa base isolée) mais
plus lent au démarrage. Pour n'en démarrer qu'un, il faut un verrou fichier
et le partage de l'URL entre workers, ou lancer ces tests sans `-n` et le
reste avec.

**Comment charger un schéma ou des données initiales ?**
Trois options : `DepotPostgres.__init__` exécute le DDL (choix de ce TP) ;
`PostgresContainer(...).with_volume_mapping("./init.sql",
"/docker-entrypoint-initdb.d/init.sql")` pour laisser l'image exécuter le
script au démarrage ; ou lancer l'outil de migration du projet (Alembic,
Django `migrate`) dans la fixture session.

**Docker n'est pas autorisé sur les postes de l'entreprise, que faire ?**
Podman en mode sans démon est souvent accepté ; Testcontainers le
supporte via `DOCKER_HOST=unix://$XDG_RUNTIME_DIR/podman/podman.sock` et
`TESTCONTAINERS_RYUK_DISABLED=true` si Ryuk pose problème. Sinon, garder
ces tests pour la CI uniquement et les exclure en local avec `-m "not
docker"`.

**Faut-il un test Testcontainers pour chaque méthode du dépôt ?**
Non : le contrat commun suffit pour le comportement fonctionnel. Ajouter
seulement ce qui est spécifique à la base : contraintes, types, arrondis,
concurrence, migrations.

## Ce qu'il faut retenir

| Question | Mock (TP07) | Fake (`DepotMemoire`, TP11) | Testcontainers (TP13) |
|---|---|---|---|
| Vitesse | microsecondes | microsecondes | secondes au démarrage, puis millisecondes |
| Ce qui est vérifié | que le code appelant fait les bons appels | la logique métier sur une implémentation simplifiée | le vrai SQL, les types, les contraintes, la configuration |
| Ce qui n'est pas vérifié | tout le comportement réel de la dépendance | les différences entre le fake et la vraie base | rien de moins que la production, hors volumétrie et réseau |
| Dépendance | aucune | aucune | Docker |
| Niveau de la pyramide | unitaire | unitaire / composant | intégration |
| Quand l'utiliser | collaboration à vérifier, dépendance non injectable | logique métier | implémentation d'accès aux données, migrations |

Le pattern à mémoriser :

```python
@pytest.fixture(scope="session")
def postgres_url(docker):
    with PostgresContainer("postgres:16-alpine", driver=None) as c:
        yield c.get_connection_url()

@pytest.fixture
def depot_postgres(depot_postgres_session):
    depot_postgres_session.vider()
    yield depot_postgres_session
    depot_postgres_session.vider()
```

Session pour le conteneur, function pour l'isolation, skip si Docker est
absent, marqueur pour pouvoir exclure.

Intégration continue, deux exemples :

```yaml
# GitHub Actions : Docker est disponible sur ubuntu-latest, rien à configurer
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run pytest -ra --junitxml=rapport.xml
```

```yaml
# GitLab CI : Docker-in-Docker
tests:
  image: ghcr.io/astral-sh/uv:python3.13-bookworm
  services:
    - docker:dind
  variables:
    DOCKER_HOST: tcp://docker:2375
    DOCKER_TLS_CERTDIR: ""
    TESTCONTAINERS_HOST_OVERRIDE: docker
  script:
    - uv sync
    - uv run pytest -ra --junitxml=rapport.xml
```

`TESTCONTAINERS_HOST_OVERRIDE` indique à Testcontainers que les ports
exposés sont joignables sur l'hôte `docker` (le service) et non sur
`localhost`. Fixer les tags d'image (`postgres:16-alpine`, jamais
`latest`) pour la reproductibilité.

## Exercices

### 1. Persistance entre deux instances

Écrire l'équivalent de `test_persistance_entre_deux_instances` du TP11 :
deux `DepotPostgres` sur la même URL voient les mêmes données.

**Corrigé** :

```python
def test_deux_instances_partagent_la_base(depot_postgres, postgres_url, produit_stylo):
    depot_postgres.sauvegarder(produit_stylo)
    autre = DepotPostgres(postgres_url)  # CREATE TABLE IF NOT EXISTS : sans effet
    assert autre.charger("STY-01") == produit_stylo
```

Utiliser `depot_postgres` (et non `depot_postgres_session`) pour bénéficier
du `TRUNCATE` avant et après.

### 2. Isolation par transaction annulée

Remplacer l'isolation par `TRUNCATE` par une transaction annulée en
teardown. Quelles modifications dans `DepotPostgres` ?

**Corrigé** : `DepotPostgres` ouvre une connexion par opération et valide à
chaque sortie de `with`. Pour annuler, il faut une seule connexion
partagée, sans validation. Une sous-classe suffit :

```python
from contextlib import nullcontext
import psycopg
from tp13_testcontainers.depot_postgres import SCHEMA, DepotPostgres


class DepotPostgresTransactionnel(DepotPostgres):
    """Toutes les opérations passent par UNE connexion fournie, jamais validée."""

    def __init__(self, conn: psycopg.Connection):
        self._conn = conn
        conn.execute(SCHEMA)

    def _connexion(self):
        return nullcontext(self._conn)  # ne ferme ni ne valide rien


@pytest.fixture
def depot_transactionnel(postgres_url):
    with psycopg.connect(postgres_url) as conn:
        yield DepotPostgresTransactionnel(conn)
        conn.rollback()  # tout ce que le test a écrit disparaît


def test_ecriture_annulee(depot_transactionnel):
    depot_transactionnel.sauvegarder(Produit("TX-01", "x", 1.0))
    assert depot_transactionnel.charger("TX-01").nom == "x"


def test_table_vide_apres_rollback(depot_transactionnel):
    assert depot_transactionnel.tous() == []
```

`nullcontext(obj)` est un gestionnaire de contexte qui renvoie `obj` sans
rien faire à la sortie : `with self._connexion() as conn` continue de
fonctionner dans le code hérité. Avantages : plus rapide que `TRUNCATE`,
aucune méthode `vider()` dans le code de production. Inconvénients : le
code testé ne doit pas faire de `commit` lui-même, et les tests de
concurrence (deux connexions) deviennent impossibles.

### 3. `RedisContainer` contre `DockerContainer`

Utiliser le module dédié `testcontainers.community.redis.RedisContainer`
et comparer avec la version générique.

**Corrigé** : le module dédié importe la bibliothèque cliente `redis`, il
faut donc `uv add --dev "testcontainers[redis]"`, qui installe `redis`.

```python
@pytest.fixture(scope="session")
def redis_client(docker):
    from testcontainers.community.redis import RedisContainer

    with RedisContainer("redis:7-alpine") as conteneur:
        yield conteneur.get_client()  # redis.Redis déjà connecté


def test_ping_module_dedie(redis_client):
    assert redis_client.ping() is True


def test_set_get_module_dedie(redis_client):
    redis_client.set("formation", "pytest")
    assert redis_client.get("formation") == b"pytest"
```

Comparaison : le module dédié connaît le port, attend la disponibilité et
fournit un client prêt ; le générique demande de tout écrire mais
fonctionne avec n'importe quelle image, y compris une image interne à
l'entreprise.

### 4. Cache devant le dépôt, mesuré avec `--durations` et `mocker.spy`

Mesurer le coût du démarrage, puis introduire un cache mémoire devant
`DepotPostgres` et tester qu'il évite les requêtes.

**Indice** : `--durations=3` montre 1,5 s de `setup` sur le premier test.
Pour le cache, une classe `DepotAvecCache(depot)` qui mémorise les
résultats de `charger` dans un `dict` et l'invalide dans `sauvegarder` et
`supprimer`. Test avec `mocker.spy(depot_postgres, "charger")` (TP07) :
deux `charger` de la même référence, `spy.call_count == 1`. Puis un
`sauvegarder` suivi d'un `charger`, `spy.call_count == 2`.

## Transition / conclusion

Ce TP clôt la formation en fermant la boucle ouverte au TP11 : la même
suite de tests de contrat a validé un dictionnaire, un fichier JSON et
une base PostgreSQL, parce que le code a été conçu autour d'une interface
et de l'injection de dépendances.

Message final sur la pyramide des tests. En bas, beaucoup de tests
unitaires purs (TP01 à TP05) : rapides, précis, sans dépendance. Au
milieu, des tests avec doublures (TP06, TP07) qui vérifient les
collaborations sans payer le prix des vraies dépendances. En haut, peu de
tests d'intégration (TP11, TP13) qui vérifient que l'assemblage
fonctionne contre les vraies technologies. Hypothesis (TP12) élargit la
base en cherchant les entrées auxquelles on n'a pas pensé. La
configuration, les marqueurs et les hooks (TP05, TP09, TP10) servent à
faire tourner la bonne partie de la pyramide au bon moment : les tests
unitaires à chaque sauvegarde, tout le reste en intégration continue.
