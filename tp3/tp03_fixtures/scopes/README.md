# TP03 bis – Les scopes de fixtures, en une trace

## En une phrase

Une fixture est créée une fois par « portée » (scope) puis mise en cache :
ce paquet fait défiler les cinq scopes dans une seule trace pour voir quand
chaque fixture naît, combien de tests la partagent, et quand elle meurt.

## Objectifs pédagogiques

À la fin de cette présentation, le stagiaire sait :

- citer les cinq scopes (`function`, `class`, `module`, `package`, `session`)
  et dire pour chacun quand la fixture est créée et détruite ;
- lire une trace `--setup-show` (lettres `F C M P S`, indentation) ;
- prédire, pour un fichier de tests donné, combien de fois une fixture sera
  instanciée ;
- expliquer l'ordre de SETUP (du plus large au plus étroit) et de TEARDOWN
  (ordre inverse) ;
- reconnaître et corriger un `ScopeMismatch` ;
- utiliser un scope **dynamique** (`scope=` fonction) ;
- choisir le bon scope : rapidité contre isolation.

## Prérequis

TP03 sections 1 à 3 : savoir écrire une fixture, la consommer par son nom,
utiliser `yield` pour le teardown. Savoir que `conftest.py` partage des
fixtures avec tout un répertoire.

## Fichiers

| Fichier | Rôle |
|---|---|
| `conftest.py` | Fabrique cinq fixtures identiques sauf leur scope (`fx_function` ... `fx_session`), chacune imprime son SETUP / TEARDOWN et compte ses créations ; plus `fx_dynamique` |
| `test_1_module_a.py` | Deux classes (`TestClasseA`, `TestClasseB`) et une fonction hors classe ; chaque test demande les cinq fixtures et vérifie **quelle instance** il reçoit |
| `test_2_module_b.py` | Second module : nouvelle instance de `fx_module`, tests du scope dynamique, `test_bilan` qui vérifie les compteurs |
| `demo_scope_mismatch.py` | Erreur volontaire, non collectée par défaut (pas de préfixe `test_`) |

Le préfixe numérique `test_1_` / `test_2_` fixe l'ordre alphabétique de
collecte : la démonstration compte sur le fait que le module A passe avant
le module B.

## Mise en route

```bash
uv run pytest tp03_fixtures/scopes -q             # 8 passed, ~0.1 s
uv run pytest tp03_fixtures/scopes -s -q          # la trace lisible (print des fixtures)
uv run pytest tp03_fixtures/scopes --setup-show -q  # la vue pytest
uv run pytest tp03_fixtures/scopes/demo_scope_mismatch.py   # 1 error, volontaire
```

## Déroulé de la présentation

### Le `conftest.py` : une fabrique de fixtures

**Ce que montre le code.** Les cinq fixtures sont strictement identiques,
seule la valeur de `scope=` change. Pour ne pas écrire cinq fois le même
code, une fonction `_fabrique(scope)` construit la fixture et lui donne son
nom via le paramètre `name=` du décorateur :

```python
def _fabrique(scope):
    @pytest.fixture(scope=scope, name=f"fx_{scope}")
    def fixture(request):
        CREATIONS[scope] += 1
        noeud = request.node.name or "la session"
        print(f"\n  [SETUP    {scope:8s}] #{CREATIONS[scope]}  pour {noeud}")
        yield f"{scope}-{CREATIONS[scope]}"
        print(f"\n  [TEARDOWN {scope:8s}] #{CREATIONS[scope]}  après {noeud}")
    return fixture

fx_function = _fabrique("function")
fx_class = _fabrique("class")
fx_module = _fabrique("module")
fx_package = _fabrique("package")
fx_session = _fabrique("session")
```

Chaque fixture renvoie une chaîne `scope-numéro` : `"module-2"` signifie
« deuxième instance de la fixture de scope module ». Les tests comparent ces
chaînes : ce que la trace montre à l'écran, les `assert` le prouvent.

**À dire aux stagiaires.**

- `name=` permet de donner à la fixture un nom différent de celui de la
  fonction Python. Utile ici pour la fabrique, utile en général pour éviter
  qu'un nom de fixture masque une variable.
- `request.node` n'est pas toujours le test : pour une fixture `class`,
  c'est la classe ; pour `module`, le module ; pour `package`, le paquet ;
  pour `session`, la session (dont le nom est vide, d'où le
  `or "la session"`). C'est ce qui apparaît après « pour » dans la trace.
- Le dictionnaire `CREATIONS` est un état global **volontaire** : il sert de
  preuve dans `test_bilan`. Dans de vrais tests, on évite ce genre d'état.

**Pièges.** Sans `name=`, les cinq fixtures s'appelleraient toutes
`fixture` et la dernière écraserait les autres.

### La trace complète avec `-s`

**À montrer en direct.**

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
8 passed
```

**Lecture guidée, ligne par ligne.**

1. **Cinq SETUP en cascade** avant le tout premier test, du plus large
   (`session`) au plus étroit (`function`). Rien n'a été créé au lancement
   de pytest : tout démarre parce que `test_a1` demande les cinq fixtures.
2. **`function` fait l'aller-retour à chaque test** : SETUP juste avant,
   TEARDOWN juste après. Cinq tests demandent `fx_function`, donc cinq
   instances (`#1` à `#5`).
3. **`class` change à chaque classe** : `#1` pour `TestClasseA` (partagée
   par `test_a1` et `test_a2`), `#2` pour `TestClasseB`. Son TEARDOWN arrive
   après le dernier test de la classe.
4. **Fonction hors classe** : `test_hors_classe` obtient quand même une
   instance `class` (`#3`), détruite juste après lui. Pour une fonction hors
   classe, le scope `class` se comporte donc comme `function`.
5. **`module` change au changement de fichier** : TEARDOWN de `#1` après le
   dernier test de `test_1_module_a.py`, SETUP de `#2` au premier test de
   `test_2_module_b.py`.
6. **`package` et `session` ne bougent pas** : une seule instance chacune,
   détruites tout à la fin, dans l'ordre inverse de leur création
   (module, puis package, puis session).
7. **`dynamique`** apparaît deux fois avec « scope réel = function » : en
   environnement `dev` (le défaut), elle est recréée à chaque test. Voir
   plus bas.

**À dire aux stagiaires.** Les scopes sont emboîtés comme des poupées
russes. Le teardown suit la règle « dernier créé, premier détruit ». Une
fixture large n'est jamais créée « au cas où » : seulement quand un test la
demande. Et une fois créée, elle est **mise en cache** jusqu'à la fin de sa
portée : c'est ce cache qui fait gagner du temps, et c'est ce cache qui
partage l'état entre tests.

### La même trace vue par pytest : `--setup-show`

**À montrer en direct.**

```bash
uv run pytest tp03_fixtures/scopes --setup-show -q
```

```
SETUP    S fx_session
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
TEARDOWN S fx_session
```

**À dire aux stagiaires.** La lettre indique le scope : `S` session,
`P` package, `M` module, `C` class, `F` function. L'indentation reflète
l'emboîtement : une fixture `F` est toujours plus indentée qu'une `M`.
`--setup-show` est l'outil à sortir dès qu'on ne comprend pas « pourquoi ma
fixture est recréée » ou « pourquoi elle ne l'est pas ». Il fonctionne
avec n'importe quelle suite, sans modifier le code.

### `test_1_module_a.py` : les assertions qui prouvent la trace

**Ce que montre le code.**

```python
class TestClasseA:
    def test_a1(self, fx_function, fx_class, fx_module, fx_package, fx_session):
        assert (fx_session, fx_package, fx_module, fx_class, fx_function) == (
            "session-1", "package-1", "module-1", "class-1", "function-1",
        )

    def test_a2(self, fx_function, fx_class, fx_module, fx_package, fx_session):
        assert fx_class == "class-1"        # même classe : même instance
        assert fx_function == "function-2"  # nouveau test : nouvelle instance
```

**À dire aux stagiaires.** Chaque test affirme quelle instance il reçoit.
Si un stagiaire doute de la trace, ces `assert` sont la preuve formelle.
Exercice mental à faire faire avant de montrer `TestClasseB` : « quelle
valeur `fx_class` aura-t-elle dans `test_b1` ? ». Réponse `class-2`.

**Pièges.** Ces tests **dépendent de l'ordre d'exécution** (le numéro
d'instance croît au fil de la session). C'est acceptable pour une
démonstration, mais c'est exactement ce qu'il ne faut pas faire dans une
vraie suite : avec `pytest-randomly` ou `-n auto` (xdist), ils cassent.

### `test_2_module_b.py` : second module et bilan

**Ce que montre le code.**

```python
def test_nouveau_module(fx_function, fx_class, fx_module, fx_package, fx_session):
    assert fx_module == "module-2"     # nouveau fichier : nouvelle instance
    assert fx_package == "package-1"   # même paquet : conservée
    assert fx_session == "session-1"   # même session : conservée

def test_bilan(fx_session):
    assert CREATIONS["function"] == 5
    assert CREATIONS["class"] == 4
    assert CREATIONS["module"] == 2
    assert CREATIONS["package"] == 1
    assert CREATIONS["session"] == 1
```

**À dire aux stagiaires.** Le bilan est le résumé chiffré de la trace :
5 tests ont demandé `fx_function`, 4 « classes » (2 vraies classes + 2
fonctions hors classe), 2 modules, 1 paquet, 1 session.

**Pièges.** Le scope `package` est celui du paquet où la fixture est
**définie** (ici `tp03_fixtures/scopes/`, à cause du `conftest.py` qui s'y
trouve), pas celui du test qui l'utilise. Si la même fixture était définie
dans `tp03_fixtures/conftest.py`, son scope `package` engloberait tout le
TP03.

### Le scope dynamique

**Ce que montre le code.** Le paramètre `scope=` accepte, au lieu d'une
chaîne, une fonction `(fixture_name, config)` qui renvoie le nom du scope :

```python
def _scope_selon_env(fixture_name, config):
    return "function" if config.getoption("--env") == "dev" else "session"

@pytest.fixture(scope=_scope_selon_env)
def fx_dynamique(request):
    CREATIONS["dynamique"] += 1
    yield request.scope       # la fixture peut connaître son propre scope réel
```

L'option `--env` est définie dans le `conftest.py` racine du projet (TP09).

**À dire aux stagiaires.** Cas d'usage réel : un serveur ou une base que
l'on veut partager pour toute la session en intégration continue (rapide),
mais recréer à chaque test en local pour déboguer un test isolé (propre).
La décision est prise **à la collecte**, une fois pour toutes ; elle peut
s'appuyer sur une option, une variable d'environnement, une valeur `ini`.

**À montrer en direct.** Comparer les deux exécutions :

```bash
uv run pytest tp03_fixtures/scopes --setup-show -q -k dynamique
```

```
        SETUP    F fx_dynamique
        test_2_module_b.py::test_scope_dynamique .
        TEARDOWN F fx_dynamique
        SETUP    F fx_dynamique
        test_2_module_b.py::test_scope_dynamique_bis .
        TEARDOWN F fx_dynamique
```

```bash
uv run pytest tp03_fixtures/scopes --setup-show -q -k dynamique --env staging
```

```
SETUP    S fx_dynamique
        test_2_module_b.py::test_scope_dynamique .
        test_2_module_b.py::test_scope_dynamique_bis .
TEARDOWN S fx_dynamique
```

Même fixture, même tests : `F` recréée deux fois en `dev`, `S` créée une
seule fois en `staging`. `test_scope_dynamique_bis` vérifie le compteur dans
les deux cas.

**Pièges.** La fonction de scope reçoit `config`, pas `request` : elle ne
peut pas dépendre d'un test particulier. Elle ne peut pas non plus renvoyer
un scope qui dépend des fixtures demandées.

### `demo_scope_mismatch.py` : l'erreur à connaître

**Ce que montre le code.** Une fixture `session` qui demande une fixture
`function` :

```python
@pytest.fixture(scope="session")
def config_partagee(fx_function):   # session -> function : interdit
    return {"base": fx_function}
```

**À montrer en direct.**

```bash
uv run pytest tp03_fixtures/scopes/demo_scope_mismatch.py
```

```
ScopeMismatch: You tried to access the function scoped fixture fx_function
with a session scoped request object. Requesting fixture stack:
tp03_fixtures/scopes/demo_scope_mismatch.py:11:  def config_partagee(fx_function)
Requested fixture:
tp03_fixtures/scopes/conftest.py:21:  def fixture(request)
```

**À dire aux stagiaires.** Règle : une fixture ne peut dépendre que d'une
fixture de scope **égal ou plus large**. Logique : si `config_partagee` vit
toute la session, quelle instance de `fx_function` (recréée à chaque test)
devrait-elle garder ? Le message donne les deux fichiers et lignes en cause.
Le cas concret le plus fréquent : une fixture `session` qui demande
`tmp_path` (scope `function`) ; la solution est `tmp_path_factory`, de scope
session (TP08).

**Modification en direct suggérée.** Dans `conftest.py`, passer `fx_module`
en `scope="session"` et relancer le paquet : `test_nouveau_module` échoue
(`module-1` au lieu de `module-2`) ainsi que `test_bilan`. Remettre
`"module"`. Cela montre que les tests documentent le comportement attendu.

## Questions fréquentes des stagiaires

**Quel scope choisir par défaut ?** `function`. C'est le seul qui garantit
l'isolation : chaque test reçoit un objet neuf. On n'élargit que pour une
ressource coûteuse à créer (connexion, serveur, conteneur, gros jeu de
données), et de préférence utilisée en lecture seule.

**Une fixture `session` est-elle créée au démarrage de pytest ?** Non.
Elle est créée au premier test qui la demande (directement ou via une
autre fixture) et détruite à la fin de la session. Si aucun test ne la
demande, elle n'est jamais créée.

**Si un test modifie un objet fourni par une fixture `module`, les tests
suivants voient-ils la modification ?** Oui. C'est le principal danger des
scopes larges : un test qui laisse des traces contamine les suivants, et
l'échec dépend alors de l'ordre. Solutions : ne partager que de
l'immuable, ou remettre l'objet à zéro dans une fixture `function` qui
dépend de la fixture large (pattern du TP13 avec `TRUNCATE`).

**Peut-on avoir une fixture `class` utilisée par une fonction hors classe ?**
Oui, elle se comporte alors comme `function` : recréée pour chaque fonction
hors classe. La trace le montre avec `test_hors_classe`.

**Le scope `package`, c'est le paquet du test ou de la fixture ?** Celui où
la fixture est définie. Une fixture `package` dans `tp03_fixtures/conftest.py`
serait partagée par tout le TP03, y compris `scopes/`.

**Que se passe-t-il si une fixture `session` échoue ?** Tous les tests qui
en dépendent sont en ERROR. pytest ne réessaie pas : l'exception est mise en
cache avec la fixture pour toute sa portée.

**Et avec `pytest-xdist` ?** Chaque worker est un processus séparé : une
fixture `session` est créée une fois **par worker**. Pour n'avoir qu'une
seule instance (un seul conteneur, par exemple), il faut un mécanisme
externe (verrou fichier, `--dist loadfile` avec scope module, ou lancer ces
tests sans `-n`).

**Peut-on changer le scope de `tmp_path` ou `monkeypatch` ?** Non, ce sont
des fixtures `function`. Pour un scope large : `tmp_path_factory`, et pour
`monkeypatch` on crée soi-même un `pytest.MonkeyPatch()` dans une fixture
`session` avec `with MonkeyPatch.context() as mp: yield mp`.

**Dans quel ordre pytest exécute-t-il les fixtures d'un même test ?** D'abord
par scope décroissant (session, package, module, class, function), puis dans
l'ordre des dépendances, puis dans l'ordre des paramètres de la fonction.
Les `autouse` d'un scope passent avant les autres du même scope.

## Ce qu'il faut retenir

| Scope | Une instance par | Détruite après | Usage typique |
|---|---|---|---|
| `function` (défaut) | test | le test | tout ce qui est mutable |
| `class` | classe de test (ou fonction hors classe) | le dernier test de la classe | setup partagé par un groupe |
| `module` | fichier de test | le dernier test du fichier | connexion, jeu de données |
| `package` | paquet où la fixture est définie | le dernier test du paquet | idem, à plus grande échelle |
| `session` | exécution de pytest | le dernier test de la session | serveur, conteneur, configuration |
| fonction `(name, config)` | décidé à la collecte | selon le scope renvoyé | local vs CI |

- SETUP du plus large au plus étroit, TEARDOWN dans l'ordre inverse.
- Créée au premier test qui la demande, jamais avant ; mise en cache ensuite.
- Dépendance uniquement vers un scope égal ou plus large, sinon `ScopeMismatch`.
- Gain de temps contre isolation : élargir le scope, c'est accepter le partage d'état.
- `--setup-show` pour voir, `-s` pour lire vos propres `print`.

## Exercices

1. **Prédire avant de lancer.** Ajouter une classe `TestClasseC` avec un
   test dans `test_1_module_a.py` qui demande les cinq fixtures. Avant de
   lancer, écrire sur papier les valeurs attendues, puis les nouveaux
   compteurs de `test_bilan`. Lancer et corriger.

   *Indice / corrigé* : `class-3` pour `TestClasseC`, `function-4` ;
   `test_hors_classe` passe à `class-4` / `function-5`,
   `test_nouveau_module` à `class-5` / `function-6`. Dans `test_bilan` :
   function 6, class 5. Le reste ne change pas.

2. **Déplacer le scope `package`.** Copier la définition de `fx_package`
   dans `tp03_fixtures/conftest.py` (en la renommant `fx_package_tp03`) et
   la demander depuis un test de `tp03_fixtures/test_fixtures.py` et un
   test de `scopes/`. Vérifier avec `--setup-show` qu'une seule instance
   sert aux deux.

   *Indice* : lancer `uv run pytest tp03_fixtures --setup-show -q | grep fx_package_tp03`
   doit montrer un seul `SETUP P` et un seul `TEARDOWN P`.

3. **Isoler malgré un scope large.** Écrire une fixture `session`
   `registre` qui renvoie un `dict` vide, et une fixture `function`
   `registre_propre` qui dépend de `registre`, le vide (`clear()`) avant de
   le renvoyer, et le vide encore en teardown. Écrire deux tests qui
   écrivent dans `registre_propre` et vérifient qu'ils ne se voient pas.

   *Corrigé* :

   ```python
   @pytest.fixture(scope="session")
   def registre():
       return {}

   @pytest.fixture
   def registre_propre(registre):
       registre.clear()
       yield registre
       registre.clear()

   def test_ecrit_a(registre_propre):
       registre_propre["a"] = 1
       assert registre_propre == {"a": 1}

   def test_ecrit_b(registre_propre):
       assert "a" not in registre_propre
       registre_propre["b"] = 2
   ```

4. **Scope dynamique par variable d'environnement.** Remplacer la fonction
   `_scope_selon_env` par une version qui lit `os.environ.get("CI")` :
   `session` si la variable existe, `function` sinon. Tester les deux cas
   avec `CI=1 uv run pytest tp03_fixtures/scopes -k dynamique --setup-show`.

   *Indice* : la fonction reçoit `config` mais rien n'oblige à l'utiliser ;
   `import os` en tête du conftest suffit. Les deux tests du scope dynamique
   devront être adaptés puisqu'ils lisent `--env`.

5. **Provoquer puis corriger un `ScopeMismatch` réaliste.** Écrire une
   fixture `session` `dossier_donnees` qui utilise `tmp_path`, constater
   l'erreur, puis la corriger avec `tmp_path_factory.mktemp("donnees")`.

## Transition vers le TP suivant

Les scopes répondent à « combien de fois cette fixture est-elle créée ».
Le TP04 répond à la question voisine « combien de fois ce test est-il
exécuté » avec le paramétrage, et montre qu'une fixture peut elle-même être
paramétrée (`params=`), ce qui multiplie les tests qui l'utilisent.
