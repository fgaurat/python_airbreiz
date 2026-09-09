# TP03 – Les fixtures

## En une phrase

Une fixture est une fonction de préparation que pytest appelle pour vous
quand un test la nomme en paramètre ; elle peut dépendre d'autres fixtures,
nettoyer après le test, et être créée une fois par test, par classe, par
module ou par session.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- écrire une fixture avec `@pytest.fixture` et la consommer par son nom ;
- composer des fixtures (une fixture qui en demande une autre) et expliquer
  l'ordre d'instanciation ;
- écrire un nettoyage avec `yield` ou `request.addfinalizer`, et savoir
  qu'il s'exécute même si le test échoue ;
- choisir un scope (`function`, `class`, `module`, `package`, `session`) et
  comprendre le cache associé ;
- partager des fixtures via `conftest.py` et les surcharger localement ;
- écrire une fixture *factory*, une fixture `autouse`, utiliser
  `@pytest.mark.usefixtures` et l'objet `request` ;
- lire la sortie de `--setup-show` et de `--fixtures` ;
- reconnaître les messages d'erreur classiques (`fixture 'x' not found`,
  `called directly`, `ScopeMismatch`, ERROR at setup).

## Prérequis

TP01 (assert, `pytest.raises`) et TP02 (classes de test, cycle de vie
xunit, à comparer avec les fixtures). Notion de générateur Python (`yield`)
utile mais non indispensable : on l'explique.

## Fichiers

| Fichier | Rôle |
|---|---|
| `banque.py` | Code métier : `Compte`, `Banque`, `Journal` (fichier texte), exception `SoldeInsuffisant` |
| `conftest.py` | Fixtures partagées : `banque`, `compte_alice`, `compte_bob`, `creer_compte`, `journal`, `parametres` (session), `connexion_bdd` (module) |
| `test_fixtures.py` | 19 tests, 8 sections numérotées couvrant chaque forme de fixture |
| `test_scopes.py` | 4 tests qui **comptent** le nombre de créations selon le scope |
| `scopes/` | Sous-paquet de démonstration des cinq scopes + scope dynamique + `demo_scope_mismatch.py` ; possède son propre [README](scopes/README.md) détaillé |

## Mise en route

```bash
uv run pytest tp03_fixtures
```

Sortie attendue : `23 passed` en moins de 0,2 s.

Les deux commandes à avoir sous la main pendant tout le TP :

```bash
uv run pytest tp03_fixtures --setup-show     # affiche SETUP / TEARDOWN de chaque fixture
uv run pytest tp03_fixtures -s               # laisse passer les print() des fixtures
```

## Déroulé de la présentation

### Le code métier : `banque.py`

`Compte` a un titulaire et un solde, avec `deposer`, `retirer` (lève
`SoldeInsuffisant`) et `virer_vers`. `Banque` ouvre des comptes
(`ouvrir_compte`, refuse les doublons), les retrouve (`trouver`) et les
compte (`nb_comptes`). `Journal` écrit des lignes dans un fichier ouvert en
mode ajout, avec `enregistrer`, `lire` et `fermer`.

```python
class Journal:
    def __init__(self, chemin):
        self.chemin = Path(chemin)
        self._fichier = self.chemin.open("a", encoding="utf-8")
    def fermer(self):
        self._fichier.close()
```

Pourquoi ce choix : `Banque` et `Compte` forment un petit **graphe
d'objets** (un compte appartient à une banque), idéal pour montrer des
fixtures qui dépendent les unes des autres. `Journal` tient un fichier
ouvert : il a besoin d'un **nettoyage**, ce qui motive `yield`.

### Le `conftest.py` : lecture guidée avant les tests

- **Ce que montre le code** : sept fixtures, présentées dans un ordre
  progressif. `banque` renvoie un objet neuf. `compte_alice` et `compte_bob`
  **demandent** `banque` en paramètre. `creer_compte` renvoie une fonction.
  `journal` utilise `yield`. `parametres` et `connexion_bdd` ont un scope
  large et impriment leurs étapes.

  ```python
  @pytest.fixture
  def banque():
      return Banque("Crédit Pytest")

  @pytest.fixture
  def compte_alice(banque):
      return banque.ouvrir_compte("alice", solde=100)
  ```

- **À dire aux stagiaires** : un `conftest.py` n'est **jamais importé**
  explicitement. pytest le charge automatiquement et rend ses fixtures
  disponibles dans son répertoire et tous les sous-répertoires. Il peut y en
  avoir un par niveau (celui de la racine du projet définit la fixture `env`
  visible partout). Le nom de la fixture est celui de la fonction ; on la
  demande en écrivant ce nom comme paramètre du test.
- **À montrer en direct** :

  ```bash
  uv run pytest tp03_fixtures --fixtures
  ```

  ```
  banque -- tp03_fixtures/conftest.py:17
      no docstring available
  compte_alice -- tp03_fixtures/conftest.py:27
  ...
  parametres [session scope] -- tp03_fixtures/conftest.py:69
  ```

  La liste montre aussi les fixtures intégrées (`tmp_path`, `capsys`,
  `monkeypatch`...) qui feront l'objet des TP06 et TP08. La mention
  `no docstring available` incite à documenter ses fixtures : la docstring
  s'affiche ici.
- **Pièges et erreurs fréquentes** : importer une fixture depuis
  `conftest.py` avec `from conftest import banque` fonctionne parfois mais
  crée des doublons et des comportements étranges ; ne jamais le faire.
  Mettre du code métier dans `conftest.py`.

### Section 1 : utilisation de base et composition

- **Ce que montre le code** : `test_banque_vide(banque)`,
  `test_compte_alice(compte_alice)`, puis
  `test_plusieurs_fixtures(banque, compte_alice, compte_bob)` qui vérifie
  que `banque.trouver("alice") is compte_alice`. `test_isolation_des_fixtures`
  revérifie `nb_comptes == 0`.
- **À dire aux stagiaires** : quand un test demande `compte_alice`, pytest
  construit le **graphe de dépendances** : `compte_alice` a besoin de
  `banque`, donc `banque` est créée d'abord. Si le même test demande aussi
  `banque` et `compte_bob`, la fixture `banque` n'est instanciée qu'**une
  seule fois** pour ce test : c'est le cache par scope. Tous les paramètres
  reçoivent le même objet, c'est ce que prouve `is`. Au test suivant, tout
  est recréé (scope `function`, le défaut) : `test_isolation_des_fixtures`
  ne voit pas les comptes ouverts avant.
- **À montrer en direct** :

  ```bash
  uv run pytest tp03_fixtures/test_fixtures.py --setup-show -k test_plusieurs_fixtures
  ```

  ```
  SETUP    F banque
  SETUP    F compte_alice (fixtures used: banque)
  SETUP    F compte_bob (fixtures used: banque)
  tp03_fixtures/test_fixtures.py::test_plusieurs_fixtures (fixtures used: banque, compte_alice, compte_bob) .
  TEARDOWN F compte_bob
  TEARDOWN F compte_alice
  TEARDOWN F banque
  ```

  Lecture : `F` est le scope (function), l'indentation reflète la
  hiérarchie, les teardowns sont dans l'ordre **inverse** des setups.
  Comparer avec le TP02 : ici, le test choisit ce qu'il reçoit.
- **Pièges et erreurs fréquentes** : faute de frappe dans le nom du
  paramètre. Le message est explicite et donne la liste disponible :

  ```
  E       fixture 'banqe' not found
  >       available fixtures: banque, capfd, caplog, capsys, compte_alice, ...
  >       use 'pytest --fixtures [testpath]' for help on them.
  ```

  Le test est en **ERROR** (pas FAILED) : il n'a pas pu démarrer.

### Section 2 : fixture factory

- **Ce que montre le code** : `creer_compte` renvoie une fonction interne
  `_creer(titulaire, solde=0)` qui appelle `banque.ouvrir_compte`.
  `test_factory` crée deux comptes et vérifie `nb_comptes == 2`.

  ```python
  @pytest.fixture
  def creer_compte(banque):
      def _creer(titulaire, solde=0):
          return banque.ouvrir_compte(titulaire, solde)
      return _creer
  ```

- **À dire aux stagiaires** : une fixture renvoie une valeur, une seule.
  Quand le test a besoin de **plusieurs** objets ou de **paramètres** choisis
  par le test lui-même, la fixture renvoie une fonction de fabrication. La
  factory capture `banque` par fermeture : tous les comptes créés
  appartiennent à la même banque que celle du test.
- **À montrer en direct** : ajouter dans `test_factory` un troisième appel
  `creer_compte("carol")` et observer l'erreur `ValueError: carol a déjà un
  compte` venue du code métier, preuve que tout passe par la même banque.
  Retirer.
- **Pièges et erreurs fréquentes** : vouloir passer des arguments à une
  fixture directement (`def test(banque("nom"))`) : impossible. Les
  solutions sont la factory, ou le paramétrage indirect du TP04.

### Section 3 : `yield` et teardown, avec `tmp_path`

- **Ce que montre le code** : la fixture `journal` du `conftest.py`.

  ```python
  @pytest.fixture
  def journal(tmp_path):
      j = Journal(tmp_path / "journal.txt")
      yield j          # le test s'exécute ici
      j.fermer()       # exécuté même si le test échoue
  ```

  `test_journal` écrit deux lignes et relit le fichier.
- **À dire aux stagiaires** : tout ce qui précède `yield` est le setup, tout
  ce qui suit est le teardown. pytest reprend l'exécution de la fixture après
  le test, **même si le test a échoué ou levé une exception**. C'est
  l'équivalent de `try/finally` sans l'écrire. `tmp_path` est une fixture
  intégrée : un répertoire temporaire vide, unique par test, détaillé au
  TP08. `journal` en dépend, ce qui montre qu'une fixture maison peut
  s'appuyer sur une fixture intégrée.
- **À montrer en direct** :

  ```bash
  uv run pytest tp03_fixtures/test_fixtures.py --setup-show -k test_journal
  ```

  ```
  SETUP    S tmp_path_factory
      SETUP    F tmp_path (fixtures used: tmp_path_factory)
      SETUP    F journal (fixtures used: tmp_path)
      tp03_fixtures/test_fixtures.py::test_journal (fixtures used: journal, request, tmp_path, tmp_path_factory) .
      TEARDOWN F journal
      TEARDOWN F tmp_path
  TEARDOWN S tmp_path_factory
  ```

  Puis faire échouer `test_journal` (`assert journal.lire() == []`), ajouter
  un `print("fermeture")` après le `yield`, lancer avec `-s` : le mot
  `fermeture` apparaît malgré l'échec. Remettre.
- **Pièges et erreurs fréquentes** : deux `yield` dans une fixture (erreur
  `yield_fixture function has more than one 'yield'`). Écrire `return` avant
  le teardown au lieu de `yield` : le nettoyage n'est jamais exécuté.
  Mettre une assertion après le `yield` : elle transforme un test réussi en
  ERROR at teardown, à réserver aux vérifications d'invariants.

### Section 4 : fixtures locales et surcharge

- **Ce que montre le code** : `compte_riche` est définie dans le module de
  test. `TestSurcharge` redéfinit `compte_alice` avec un solde de 5000 ;
  `test_alice_est_riche_ici` voit 5000, `test_alice_normale_ailleurs`
  (hors de la classe) voit toujours 100.

  ```python
  class TestSurcharge:
      @pytest.fixture
      def compte_alice(self, banque):
          return banque.ouvrir_compte("alice", solde=5000)
  ```

- **À dire aux stagiaires** : une fixture peut être définie dans un
  `conftest.py`, un module de test, ou une classe. En cas de nom identique,
  **la plus proche du test gagne** : classe > module > `conftest.py` du
  répertoire > `conftest.py` parent > plugins. Une fixture dans une classe
  reçoit `self` en premier paramètre. On peut même surcharger en réutilisant
  l'originale : `def compte_alice(self, compte_alice): compte_alice.deposer(4900); return compte_alice`
  (pytest résout le nom vers le niveau supérieur).
- **À montrer en direct** : `-v -k alice` pour voir les deux tests passer
  côte à côte avec des soldes différents.
- **Pièges et erreurs fréquentes** : surcharger sans le savoir, parce qu'on
  a choisi un nom générique (`client`, `data`) déjà pris dans un
  `conftest.py` parent. `--fixtures-per-test` montre laquelle est utilisée
  par chaque test.

### Section 5 : l'objet `request`

- **Ce que montre le code** : `compte_nomme(request)` crée un compte dont le
  titulaire est `request.node.name`, et enregistre un teardown avec
  `request.addfinalizer(...)`. `info_fixture` expose `request.fixturename`,
  `request.scope`, `request.module`.
- **À dire aux stagiaires** : `request` est une fixture intégrée qui décrit
  **le contexte de la demande** : quel test (`request.node`), quel scope,
  quel module, quelle configuration (`request.config`, pour lire les
  options), et au TP04 `request.param`. `addfinalizer` est l'alternative à
  `yield` : elle permet d'enregistrer **plusieurs** fonctions de nettoyage,
  exécutées dans l'ordre inverse d'enregistrement, et fonctionne aussi si
  la fixture échoue après en avoir enregistré une (avec `yield`, une
  exception avant le `yield` empêche tout teardown).
- **À montrer en direct** :

  ```bash
  uv run pytest tp03_fixtures/test_fixtures.py -s -k test_request_node_name
  ```

  ```
  [teardown] compte test_request_node_name
  ```

- **Pièges et erreurs fréquentes** : confondre `request.node` (le test) et
  `request.module`. Utiliser `request` pour accéder à des attributs d'un
  autre test : signe de couplage à corriger.

### Section 6 : `autouse`

- **Ce que montre le code** : dans `TestAutouse`, la fixture `_preparer` est
  déclarée `autouse=True`. Elle ouvre un compte `auto` et stocke `banque`
  sur `self`. Les deux tests ne la nomment pas mais en bénéficient.
- **À dire aux stagiaires** : `autouse=True` applique la fixture à tous les
  tests de sa portée (classe ici ; module si définie dans le module ;
  répertoire si dans `conftest.py`). C'est l'équivalent de `setup_method`
  du TP02, en composable. À réserver aux préparations **invisibles** et
  systématiques : nettoyer une base, fixer une variable d'environnement,
  couper le réseau (TP11). Une autouse qui fournit une valeur que les tests
  utilisent rend le code implicite ; préférer une fixture nommée.
- **À montrer en direct** : `--setup-show -k TestAutouse` montre `_preparer`
  dans les fixtures utilisées alors que les tests ne la déclarent pas.
- **Pièges et erreurs fréquentes** : une autouse de scope session dans le
  `conftest.py` racine qui fait un travail coûteux ralentit toute la suite,
  y compris les tests qui n'en ont pas besoin. Le préfixe `_` dans le nom
  est une convention pour signaler « pas destinée à être demandée ».

### Section 7 : `@pytest.mark.usefixtures`

- **Ce que montre le code** : `journal_initialise` enrichit `journal` d'une
  ligne. `test_usefixtures` est décoré `@pytest.mark.usefixtures("journal_initialise")`
  et n'a aucun paramètre.
- **À dire aux stagiaires** : on veut l'**effet** de la fixture sans sa
  valeur. Le décorateur accepte plusieurs noms, s'applique à une fonction ou
  à une classe entière (`@pytest.mark.usefixtures("bdd_vide")` sur une
  classe). Différence avec `autouse` : ici c'est le test qui choisit, pas
  la fixture qui s'impose.
- **À montrer en direct** : `--setup-show -k test_usefixtures` montre la
  chaîne `tmp_path` > `journal` > `journal_initialise`.
- **Pièges et erreurs fréquentes** : `usefixtures` ne donne pas accès à la
  valeur ; si on en a besoin, la mettre en paramètre. Le nom est une
  chaîne : une faute de frappe donne `fixture 'x' not found`.

### Section 8 : scopes `module` et `session`

- **Ce que montre le code** : `parametres` (session) et `connexion_bdd`
  (module) impriment leurs setup et teardown. `test_connexion_partagee_1`
  ajoute une requête dans le dictionnaire, `test_connexion_partagee_2` la
  retrouve.
- **À dire aux stagiaires** : les scopes disponibles sont `function`
  (défaut), `class`, `module`, `package`, `session`. Une fixture de scope
  large est créée à la première demande et **mise en cache** jusqu'à la fin
  de sa portée. Elle sert à amortir un coût (connexion, serveur, conteneur
  Docker au TP13, gros jeu de données). Contrepartie : les tests partagent
  l'objet. `test_connexion_partagee_2` dépend du fait que
  `test_connexion_partagee_1` a tourné avant : c'est volontairement un
  contre-exemple. Règle : ne partager que des ressources en lecture seule,
  ou nettoyer entre les tests avec une fixture `function` qui dépend de la
  fixture large (modèle `depot_postgres` du TP13). Règle de compatibilité :
  une fixture ne peut demander qu'une fixture de scope **égal ou plus
  large**. Sinon :

  ```
  ScopeMismatch: You tried to access the function scoped fixture banque
  with a session scoped request object.
  ```

- **À montrer en direct** :

  ```bash
  uv run pytest tp03_fixtures/test_fixtures.py -s -k "connexion or parametres"
  ```

  ```
  [SETUP session] chargement des paramètres
  [SETUP module] ouverture de la connexion
  [TEARDOWN module] fermeture de la connexion
  [TEARDOWN session] paramètres libérés
  ```

  Puis modification en direct : passer `connexion_bdd` en `scope="function"`
  et relancer : `test_connexion_partagee_2` échoue (`[] == ['SELECT 1']`),
  ce qui montre à la fois le rôle du scope et la fragilité du test.
  Remettre `module`.
- **Pièges et erreurs fréquentes** : `ScopeMismatch` quand on ajoute
  `tmp_path` (function) à une fixture session ; utiliser `tmp_path_factory`
  (TP08). Croire que `session` signifie « une fois pour toutes les
  exécutions » : c'est une fois par **lancement** de pytest (et une fois par
  worker avec xdist).

### `test_scopes.py` : compter les créations

- **Ce que montre le code** : trois fixtures `fx_function`, `fx_class`,
  `fx_module` incrémentent un dictionnaire `COMPTEURS`. Deux classes de
  tests les demandent, puis `test_bilan` vérifie les compteurs : 3, 2, 1.
  `TestScopesA.test_2` vérifie avec `is` que `fx_class` et `fx_module` sont
  les mêmes objets qu'au test précédent.
- **À dire aux stagiaires** : c'est la preuve chiffrée de la section 8.
  Trois tests demandent `fx_function` : trois créations. Deux classes :
  deux créations de `fx_class`. Un fichier : une création de `fx_module`.
- **À montrer en direct** :

  ```bash
  uv run pytest tp03_fixtures/test_scopes.py --setup-show
  ```

  ```
  SETUP    M fx_module
    SETUP    C fx_class
      SETUP    F fx_function
      tp03_fixtures/test_scopes.py::TestScopesA::test_1 (fixtures used: fx_class, fx_function, fx_module) .
      TEARDOWN F fx_function
      SETUP    F fx_function
      tp03_fixtures/test_scopes.py::TestScopesA::test_2 (...) .
      TEARDOWN F fx_function
    TEARDOWN C fx_class
    SETUP    C fx_class
      SETUP    F fx_function
      tp03_fixtures/test_scopes.py::TestScopesB::test_3 (...) .
      TEARDOWN F fx_function
    TEARDOWN C fx_class
      tp03_fixtures/test_scopes.py::test_bilan (fixtures used: fx_module) .
  TEARDOWN M fx_module
  ```

  Les lettres `F`, `C`, `M`, `S` (et `P` pour package) indiquent le scope.
  L'indentation montre l'imbrication des durées de vie.
- **Pièges et erreurs fréquentes** : ce fichier utilise un état global
  (`COMPTEURS`) et une écriture sur `self.__class__` pour les besoins de la
  démonstration ; ne pas y voir un modèle.

### Présentation dédiée des scopes : le paquet `scopes/`

Le sous-paquet `tp03_fixtures/scopes/` est conçu pour être projeté tel quel :
il fait défiler les **cinq scopes** dans une seule trace, ajoute le scope
**dynamique**, et fournit un fichier d'erreur volontaire pour `ScopeMismatch`.

| Fichier | Rôle |
|---|---|
| `scopes/conftest.py` | Une fixture par scope (`fx_function`, `fx_class`, `fx_module`, `fx_package`, `fx_session`) fabriquées par `_fabrique`, chacune imprime son SETUP / TEARDOWN ; plus `fx_dynamique` |
| `scopes/test_1_module_a.py` | Deux classes et une fonction hors classe, qui demandent les 5 fixtures et vérifient quelle instance elles reçoivent |
| `scopes/test_2_module_b.py` | Second module (nouvelle `fx_module`), tests du scope dynamique, `test_bilan` qui vérifie les compteurs |
| `scopes/demo_scope_mismatch.py` | Échec volontaire, non collecté par défaut |

**Ce que montre le code.** Chaque fixture renvoie une chaîne `scope-numéro`
(`"module-2"` = deuxième instance de la fixture module). Les tests comparent
ces chaînes : c'est la preuve, en `assert`, de ce que la trace montre
visuellement. Le compteur `CREATIONS` est vérifié par le dernier test.

```python
def _fabrique(scope):
    @pytest.fixture(scope=scope, name=f"fx_{scope}")
    def fixture(request):
        CREATIONS[scope] += 1
        print(f"[SETUP    {scope}] #{CREATIONS[scope]}  pour {request.node.name}")
        yield f"{scope}-{CREATIONS[scope]}"
        print(f"[TEARDOWN {scope}] #{CREATIONS[scope]}  après {request.node.name}")
    return fixture
```

`request.node` change de nature selon le scope : la fonction de test, la
classe, le module, le paquet ou la session. C'est ce qui apparaît après
« pour » dans la trace.

**À dire aux stagiaires.**

- Les scopes sont **emboîtés** comme des poupées russes : session contient
  package, qui contient module, qui contient class, qui contient function.
- Le SETUP se fait du plus large au plus étroit, le TEARDOWN dans l'ordre
  inverse (dernier créé, premier détruit).
- Une fixture n'est créée que **quand un test la demande**, et jamais avant :
  la session ne démarre pas ses fixtures au lancement de pytest mais au
  premier test qui en a besoin.
- Le scope `package` est celui du paquet où la fixture est **définie** (ici
  `tp03_fixtures/scopes/`, à cause du `conftest.py` qui s'y trouve), pas
  celui du test qui l'utilise.
- Pour une fonction hors classe, le scope `class` se comporte comme
  `function` : voir `test_hors_classe` (`class-3`) puis
  `test_nouveau_module` (`class-4`).
- Le scope dynamique : `scope=` accepte une fonction `(fixture_name, config)`
  qui renvoie le nom du scope. Cas d'usage réel : partager un serveur en CI
  mais le recréer à chaque test en local pour déboguer. Ici la décision
  dépend de l'option `--env` du conftest racine.

**À montrer en direct.** D'abord la trace lisible, en désactivant la capture :

```bash
uv run pytest tp03_fixtures/scopes -s -q
```

```
  [SETUP    session ] #1  pour la session
  [SETUP    package ] #1  pour scopes
  [SETUP    module  ] #1  pour test_1_module_a.py
  [SETUP    class   ] #1  pour TestClasseA
  [SETUP    function] #1  pour test_a1
  [TEARDOWN function] #1  après test_a1
  [SETUP    function] #2  pour test_a2
  [TEARDOWN function] #2  après test_a2
  [TEARDOWN class   ] #1  après TestClasseA
  [SETUP    class   ] #2  pour TestClasseB
  [SETUP    function] #3  pour test_b1
  [TEARDOWN function] #3  après test_b1
  [TEARDOWN class   ] #2  après TestClasseB
  [SETUP    class   ] #3  pour test_hors_classe
  [SETUP    function] #4  pour test_hors_classe
  [TEARDOWN function] #4  après test_hors_classe
  [TEARDOWN class   ] #3  après test_hors_classe
  [TEARDOWN module  ] #1  après test_1_module_a.py
  [SETUP    module  ] #2  pour test_2_module_b.py
  [SETUP    class   ] #4  pour test_nouveau_module
  [SETUP    function] #5  pour test_nouveau_module
  [TEARDOWN function] #5  après test_nouveau_module
  [TEARDOWN class   ] #4  après test_nouveau_module
  [SETUP    dynamique] scope réel = function
  [TEARDOWN dynamique] scope réel = function
  [SETUP    dynamique] scope réel = function
  [TEARDOWN dynamique] scope réel = function
  [TEARDOWN module  ] #2  après test_2_module_b.py
  [TEARDOWN package ] #1  après scopes
  [TEARDOWN session ] #1  après la session
8 passed in 0.61s
```

Lecture guidée : montrer du doigt les cinq SETUP en cascade au début, le
`function` qui va et vient à chaque test, le `class` recréé à chaque classe,
le `module` recréé au passage à `test_2_module_b.py`, et les trois derniers
TEARDOWN (module, package, session) tout à la fin, dans l'ordre inverse.

Ensuite la même chose vue par pytest, avec les lettres de scope :

```bash
uv run pytest tp03_fixtures/scopes --setup-show -q
```

```
  SETUP    P fx_package
    SETUP    M fx_module
      SETUP    C fx_class
        SETUP    F fx_function
        test_1_module_a.py::TestClasseA::test_a1 .
        TEARDOWN F fx_function
        SETUP    F fx_function
        test_1_module_a.py::TestClasseA::test_a2 .
        TEARDOWN F fx_function
      TEARDOWN C fx_class
      SETUP    C fx_class
        SETUP    F fx_function
        test_1_module_a.py::TestClasseB::test_b1 .
        TEARDOWN F fx_function
      TEARDOWN C fx_class
      SETUP    C fx_class
        SETUP    F fx_function
        test_1_module_a.py::test_hors_classe .
        TEARDOWN F fx_function
      TEARDOWN C fx_class
    TEARDOWN M fx_module
    SETUP    M fx_module
      SETUP    C fx_class
        SETUP    F fx_function
        test_2_module_b.py::test_nouveau_module .
        TEARDOWN F fx_function
      TEARDOWN C fx_class
        SETUP    F fx_dynamique
        test_2_module_b.py::test_scope_dynamique .
        TEARDOWN F fx_dynamique
        SETUP    F fx_dynamique
        test_2_module_b.py::test_scope_dynamique_bis .
        TEARDOWN F fx_dynamique
        test_2_module_b.py::test_bilan .
    TEARDOWN M fx_module
  TEARDOWN P fx_package
     0.7 ms  test_2_module_b.py::test_scope_dynamique_bis
     0.6 ms  test_2_module_b.py::test_scope_dynamique
     0.2 ms  test_1_module_a.py::test_hors_classe
```

`S` session, `P` package, `M` module, `C` class, `F` function.
L'indentation reflète l'emboîtement.

Puis le scope dynamique : relancer avec `--env staging`. `fx_dynamique`
passe de `F` à `S` dans `--setup-show`, et n'est plus créée qu'une fois.

```bash
uv run pytest tp03_fixtures/scopes --setup-show --env staging -q -k dynamique
```

Enfin l'erreur à connaître, avec le fichier d'échec volontaire :

```bash
uv run pytest tp03_fixtures/scopes/demo_scope_mismatch.py
```

```
ScopeMismatch: You tried to access the function scoped fixture fx_function with a session scoped request object. Requesting fixture stack:
tp03_fixtures/scopes/demo_scope_mismatch.py:11:  def config_partagee(fx_function)
Requested fixture:
tp03_fixtures/scopes/conftest.py:21:  def fixture(request)
```

Modification en direct suggérée : dans `scopes/conftest.py`, passer
`fx_module` en `scope="session"` et relancer. `test_nouveau_module` échoue
(`module-1` au lieu de `module-2`) et `test_bilan` aussi : les tests
documentent le comportement attendu.

**Pièges et erreurs fréquentes.**

- Croire que `session` veut dire « au démarrage de pytest » : non, c'est
  « au premier test qui la demande, jusqu'à la fin ».
- Oublier que l'état d'une fixture large est **partagé** : un test qui
  modifie l'objet contamine les suivants. C'est le prix du gain de temps.
  Réserver les scopes larges aux ressources coûteuses et immuables
  (connexion, serveur, jeu de données en lecture seule).
- `ScopeMismatch` en ajoutant `tmp_path` (function) à une fixture `session` :
  utiliser `tmp_path_factory` (TP08).
- Avec `pytest-xdist`, une fixture `session` est créée **une fois par
  worker** (TP09).

### Les trois messages d'erreur à connaître

À montrer en fin de TP avec un fichier jetable, ou à commenter à partir des
extraits ci-dessous.

1. Appeler une fixture directement :

   ```python
   def test_appel_direct():
       b = banque()
   ```

   ```
   Failed: Fixture "banque" called directly. Fixtures are not meant to be
   called directly, but are created automatically when test functions
   request them as parameters.
   ```

2. Nom inconnu : `fixture 'banqe' not found` avec la liste des fixtures
   disponibles (voir section 1). Statut ERROR.

3. Exception dans une fixture :

   ```
   ERROR at setup of test_erreur_fixture
   E   RuntimeError: boum dans la fixture
   ```

   Le test n'a pas tourné, il est en ERROR. Distinguer de FAILED permet de
   chercher le bug au bon endroit : dans la préparation, pas dans le test.

## Questions fréquentes des stagiaires

**Quelle différence entre `setup_method` et une fixture `autouse` ?**
Le résultat est le même pour une classe. La fixture peut en plus être
partagée via `conftest.py`, dépendre d'autres fixtures, avoir un scope,
et être désactivée test par test en la surchargeant. `setup_method` reste
acceptable pour du code hérité.

**Dans quel ordre pytest instancie-t-il les fixtures d'un test ?**
D'abord par scope décroissant (session, puis package, module, class,
function), puis selon les dépendances (une fixture est créée après celles
qu'elle demande), puis les `autouse` avant les autres, et enfin dans l'ordre
des paramètres du test. On ne doit jamais compter sur l'ordre entre deux
fixtures indépendantes : si un ordre importe, exprimer une dépendance.

**Une fixture peut-elle renvoyer plusieurs valeurs ?**
Elle renvoie un seul objet ; ce peut être un tuple, un dictionnaire, une
dataclass, ou une factory. Le TP07 montre une fixture qui renvoie
`(service, email_client)`.

**Le teardown s'exécute-t-il si le test échoue ? Et si une autre fixture
échoue ?**
Oui si le test échoue. Si une fixture échoue dans son setup, les fixtures
déjà créées avant elle sont bien nettoyées ; celle qui a échoué n'a pas de
teardown à exécuter (le `yield` n'a pas été atteint), sauf finalizers déjà
enregistrés avec `addfinalizer`.

**Comment passer un argument à une fixture ?**
Impossible directement. Trois solutions : une factory (section 2), le
paramétrage `params=` ou `indirect=True` (TP04), ou un marqueur lu via
`request.node.get_closest_marker` (TP05).

**Pourquoi `tmp_path` dans une fixture `session` provoque-t-elle une
erreur ?**
`tmp_path` a le scope `function`. Une fixture `session` ne peut pas dépendre
d'une fixture plus courte qu'elle (`ScopeMismatch`). Utiliser
`tmp_path_factory`, de scope session.

**Peut-on avoir plusieurs `conftest.py` ?**
Oui, un par répertoire si nécessaire. Celui de la racine du projet s'applique
partout ; celui d'un sous-répertoire uniquement en dessous. Ce projet en a un
à la racine (options `--env`, fixture `env`) et un par TP.

**Une fixture peut-elle être asynchrone ?**
Pas nativement ; il faut le plugin `pytest-asyncio` ou `anyio`, qui
fournissent des fixtures `async def`.

**Comment savoir quelles fixtures un test utilise réellement ?**
`--setup-show` pendant l'exécution, ou `--fixtures-per-test` sans exécuter.

## Ce qu'il faut retenir

| Sujet | À retenir |
|---|---|
| Déclarer | `@pytest.fixture` sur une fonction ; le nom de la fonction est le nom de la fixture |
| Consommer | nommer la fixture en paramètre du test (ou d'une autre fixture) |
| Composer | une fixture demande une autre fixture ; pytest résout le graphe ; une instance par scope |
| Nettoyer | `yield` (setup avant, teardown après, même en cas d'échec) ou `request.addfinalizer` |
| Scopes | `function` (défaut), `class`, `module`, `package`, `session` ; dépendance seulement vers un scope égal ou plus large |
| Partager | `conftest.py`, jamais importé ; le plus proche du test gagne en cas de surcharge |
| Formes | factory (renvoie une fonction), `autouse=True`, `@pytest.mark.usefixtures("nom")` |
| `request` | `.node`, `.fixturename`, `.scope`, `.config`, `.param` (TP04), `.addfinalizer` |
| Diagnostic | `--setup-show`, `--fixtures`, `--fixtures-per-test` |
| Erreurs | `fixture 'x' not found`, `called directly`, `ScopeMismatch`, ERROR at setup |

## Exercices

1. **Créer une fixture `compte_vide`** et un test vérifiant qu'un retrait
   lève `SoldeInsuffisant`.

   Indice / corrigé :

   ```python
   @pytest.fixture
   def compte_vide():
       return Compte("vide")

   def test_retrait_sur_compte_vide(compte_vide):
       with pytest.raises(SoldeInsuffisant):
           compte_vide.retirer(1)
   ```

2. **Passer `parametres` en scope `module`** et observer la différence avec
   `--setup-show`.

   Indice / corrigé : la ligne `SETUP    S parametres` devient
   `SETUP    M parametres`, indentée d'un niveau de plus, et le teardown a
   lieu à la fin de `test_fixtures.py` au lieu de la fin de la session. Avec
   un seul module qui l'utilise, le comportement observable est identique :
   le scope ne se voit que quand plusieurs modules partagent la fixture.

3. **Écrire `banque_peuplee`** qui ouvre trois comptes via `creer_compte`.

   Indice / corrigé :

   ```python
   @pytest.fixture
   def banque_peuplee(banque, creer_compte):
       for nom, solde in [("a", 10), ("b", 20), ("c", 30)]:
           creer_compte(nom, solde)
       return banque

   def test_banque_peuplee(banque_peuplee):
       assert banque_peuplee.nb_comptes == 3
   ```

   Faire remarquer que `banque` et `creer_compte` partagent la même
   instance de `Banque` grâce au cache par test.

4. **Ajouter un `print` dans le teardown de `journal`** et le faire
   apparaître avec `-s`.

   Indice / corrigé : `print("\n[teardown] journal fermé")` après
   `j.fermer()`, puis `uv run pytest tp03_fixtures -s -k journal`. Sans
   `-s`, pytest capture la sortie ; elle n'est affichée que pour les tests
   en échec, dans une section `Captured stdout teardown`.

5. **Exercice supplémentaire : provoquer un `ScopeMismatch`.** Écrire une
   fixture `scope="session"` qui demande `banque`, l'utiliser dans un test,
   et lire le message.

   Indice / corrigé : le message nomme les deux fixtures et leurs scopes,
   avec la pile de demande (`Requesting fixture stack`). Correction : passer
   `banque` en session (mauvaise idée, état partagé) ou la nouvelle fixture
   en function.

6. **Exercice supplémentaire : deux finalizers.** Réécrire `journal` avec
   `request.addfinalizer` pour fermer le fichier ET afficher un message,
   dans deux finalizers séparés. Dans quel ordre s'exécutent-ils ?

   Indice / corrigé :

   ```python
   @pytest.fixture
   def journal(tmp_path, request):
       j = Journal(tmp_path / "journal.txt")
       request.addfinalizer(j.fermer)
       request.addfinalizer(lambda: print("\n[teardown] journal"))
       return j
   ```

   Ordre inverse d'enregistrement : le message s'affiche avant la fermeture.

## Transition vers le TP suivant

Toutes les fixtures de ce TP renvoient une seule configuration. Le TP04
montre comment exécuter un même test avec **plusieurs jeux de données**
(`@pytest.mark.parametrize`), et comment paramétrer une fixture elle-même
(`params=`) pour faire tourner une suite entière contre plusieurs
implémentations.
