# TP10 – Hooks et plugins

## En une phrase

pytest est un petit noyau entouré de plugins qui communiquent par des
fonctions nommées `pytest_xxx`, les hooks ; ce TP montre comment un
`conftest.py` ou un module maison peut se brancher sur ces mêmes hooks pour
ajouter des options, réordonner la collecte, réagir au résultat d'un test,
enrichir le rapport et personnaliser les messages d'échec.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- expliquer le modèle pluggy : une spécification de hook, plusieurs
  implémentations, toutes appelées ;
- déclarer une option de ligne de commande avec `pytest_addoption` et la
  lire depuis un test ou une fixture ;
- filtrer, marquer et réordonner les tests avec `pytest_collection_modifyitems` ;
- écrire un hook wrapper et l'utiliser pour connaître le résultat d'un test
  dans une fixture (`pytest_runtest_makereport`) ;
- ajouter une section au rapport (`pytest_terminal_summary`) et une ligne
  d'en-tête (`pytest_report_header`) ;
- personnaliser l'affichage d'une assertion sur ses propres classes
  (`pytest_assertrepr_compare`) ;
- écrire un plugin local, le charger de trois façons, et savoir ce qu'il faut
  pour le distribuer.

## Prérequis

- TP03 (fixtures, `conftest.py`, `yield`), TP05 (marqueurs, `--strict-markers`).
- TP09 (conftest racine, `pyproject.toml`, `pytestconfig`).
- Le TP04 a déjà montré un hook, `pytest_generate_tests`.

## Fichiers

| Fichier | Rôle |
|---|---|
| `../conftest.py` (racine) | `pytest_plugins`, `pytest_addoption` (`--env`, `--lent`), `pytest_report_header`, fixture `env` |
| `conftest.py` | Hooks limités à ce répertoire : `pytest_configure`, `pytest_collection_modifyitems`, `pytest_runtest_makereport`, `pytest_sessionstart`, `pytest_terminal_summary`, `pytest_assertrepr_compare`, fixture `resultat_du_test` |
| `plugin_chrono.py` | Plugin local : chronomètre chaque test, affiche les trois plus lents, fournit la fixture `horloge` |
| `geometrie.py` | Classe `Vecteur` pour la démonstration de `pytest_assertrepr_compare` |
| `test_hooks.py` | Huit tests qui observent les effets des hooks |
| `demo_assertrepr.py` | Échec volontaire avec message personnalisé, à lancer explicitement |

## Mise en route

```bash
uv run pytest tp10_hooks_plugins -v
```

Sortie attendue, à lire ligne par ligne avec les stagiaires :

```
Formation pytest -- environnement : dev                 <- pytest_report_header (conftest racine)
...
collected 8 items
tp10_hooks_plugins/test_hooks.py::test_prioritaire PASSED           <- réordonné en premier
tp10_hooks_plugins/test_hooks.py::test_normal_1 PASSED
tp10_hooks_plugins/test_hooks.py::test_normal_2 PASSED
tp10_hooks_plugins/test_hooks.py::test_tres_lent SKIPPED (test lent ...)   <- skip ajouté par le hook
tp10_hooks_plugins/test_hooks.py::test_marqueur_programmatique PASSED
tp10_hooks_plugins/test_hooks.py::test_option_env PASSED
tp10_hooks_plugins/test_hooks.py::test_avec_resultat PASSED
tp10_hooks_plugins/test_hooks.py::test_avec_resultat_bis PASSED
============= TP10 : résultats vus par la fixture resultat_du_test =============
passed   test_avec_resultat
passed   test_avec_resultat_bis
==================== plugin_chrono : 3 tests les plus lents ====================
    55.1 ms  tp10_hooks_plugins/test_hooks.py::test_marqueur_programmatique
     0.1 ms  tp10_hooks_plugins/test_hooks.py::test_option_env
     0.1 ms  tp10_hooks_plugins/test_hooks.py::test_avec_resultat
=========================== short test summary info ============================
SKIPPED [1] tp10_hooks_plugins/test_hooks.py:41: test lent : ajoutez --lent pour l'exécuter
========================= 7 passed, 1 skipped in 0.13s =========================
```

Tout ce qui n'est pas standard dans cette sortie vient d'un hook de ce TP.

## Déroulé de la présentation

### Introduction : l'architecture pluggy

**Ce que montre le code.** Rien encore ; commencer au tableau. pytest repose
sur la bibliothèque `pluggy` (visible dans l'en-tête : `pluggy-1.6.0`). Un
hook est défini une fois par pytest sous forme de spécification (nom,
paramètres). N'importe quel plugin, y compris un `conftest.py`, peut fournir
une implémentation : une fonction du même nom, qui ne déclare que les
paramètres dont elle a besoin. Quand pytest appelle le hook, toutes les
implémentations enregistrées sont exécutées, en général de la dernière
enregistrée à la première ; les résultats sont collectés dans une liste,
sauf pour les hooks marqués `firstresult` où la première implémentation qui
renvoie autre chose que `None` arrête la chaîne (`pytest_assertrepr_compare`
et `pytest_collect_file` en sont).

**À dire aux stagiaires.** Trois conséquences pratiques : une implémentation
ne remplace jamais les autres, elle s'ajoute (sauf `firstresult`) ; un hook
d'un `conftest.py` de sous-répertoire reçoit des données globales, comme la
liste complète des tests collectés, et doit filtrer lui-même ; enfin les
plugins standard de pytest (capture, marqueurs, cache, terminal) sont écrits
exactement comme ce que l'on va lire, on peut ouvrir
`.venv/lib/python3.13/site-packages/_pytest/` pour s'en convaincre.

Ordre entre implémentations : `@pytest.hookimpl(tryfirst=True)` place la
sienne avant les autres, `trylast=True` après, `wrapper=True` l'enroule
autour de toutes les autres avec un `yield` au milieu.

**À montrer en direct.** Lister les hooks disponibles :

```bash
uv run python -c "import _pytest.hookspec as h; print([n for n in dir(h) if n.startswith('pytest_')])"
```

Une cinquantaine de noms, organisés par phase : démarrage (`pytest_addoption`,
`pytest_configure`), collecte (`pytest_collect_file`,
`pytest_collection_modifyitems`), exécution (`pytest_runtest_setup`,
`pytest_runtest_call`, `pytest_runtest_makereport`), rapport
(`pytest_report_header`, `pytest_terminal_summary`), fin
(`pytest_sessionfinish`).

**Pièges et erreurs fréquentes.** Une faute de frappe dans un nom de hook
(`pytest_collection_modifyitem` sans `s`) donne une erreur explicite au
démarrage : `PluginValidationError: unknown hook 'pytest_collection_modifyitem'`.
Un paramètre inconnu dans la signature donne aussi une erreur au démarrage.

### Fichier 1 : le `conftest.py` racine

**Ce que montre le code.** Quatre éléments, déjà entrevus au TP09.

```python
pytest_plugins = ["tp10_hooks_plugins.plugin_chrono"]
```
Charge un module comme plugin. Le nom est un chemin d'import Python, résolu
grâce à `pythonpath = ["."]`.

```python
def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", choices=["dev", "staging", "prod"], help=...)
    parser.addoption("--lent", action="store_true", default=False, help=...)
```
Deux options. `parser.addini("cle", help=..., default=...)` ajouterait de la
même façon une clé de configuration lisible par `config.getini`.

```python
def pytest_report_header(config):
    return f"Formation pytest -- environnement : {config.getoption('--env')}"
```
Renvoie une chaîne ou une liste de chaînes, insérées dans l'en-tête.

```python
@pytest.fixture(scope="session")
def env(pytestconfig):
    return pytestconfig.getoption("--env")
```
Une fixture dans un conftest est visible partout sous ce conftest, donc dans
tout le projet.

**À dire aux stagiaires.** Deux choses sont réservées au conftest racine
(ou aux plugins) : `pytest_addoption` et `pytest_plugins`. La raison est
l'ordre de démarrage. pytest lit les arguments, charge les conftest des
répertoires passés en argument, enregistre leurs options, puis analyse la
ligne de commande. Un conftest de sous-dossier non passé en argument n'est
chargé qu'à la collecte, trop tard pour déclarer une option. Le conftest
racine, lui, est toujours chargé au démarrage.

**À montrer en direct.** Créer, en dehors du projet, un sous-dossier avec un
`conftest.py` contenant `pytest_plugins = ["xyz"]` et lancer pytest depuis
le dossier parent :

```bash
mkdir -p /tmp/demo_plugins/sub && cd /tmp/demo_plugins && touch pytest.ini
printf 'pytest_plugins = ["xyz"]\n' > sub/conftest.py
printf 'def test_a():\n    pass\n' > sub/test_a.py
uv run --project ~/local_dev/formations/prep/formation-pytest pytest -q
```

Erreur réelle :

```
Defining 'pytest_plugins' in a non-top-level conftest is no longer supported:
  https://docs.pytest.org/en/stable/deprecations.html#pytest-plugins-in-non-top-level-conftest-files
ERROR sub - Failed: Defining 'pytest_plugins' in a non-top-level conftest is ...
```

Puis `uv run pytest --help | grep -A 6 "Custom options"` pour voir `--env`
et `--lent` documentées comme n'importe quelle option.

**Pièges et erreurs fréquentes.** `config.getoption("--lent")` sur une option
jamais déclarée lève `ValueError: no option named '--lent'` ; cela arrive
quand on déplace un `pytest_addoption` dans un sous-dossier. Le paramètre
`choices` fait le contrôle de valeur à la place du code.

### Fichier 2 : `conftest.py` du TP, hook par hook

#### `_est_dans_ce_tp` et le filtrage

```python
ICI = Path(__file__).parent

def _est_dans_ce_tp(item) -> bool:
    return ICI in item.path.parents
```

**À dire aux stagiaires.** Chaque test collecté est un `item` ; `item.path`
est le chemin de son fichier. Ce petit utilitaire limite l'effet des hooks à
ce répertoire. Sans lui, le hook de skip ci-dessous affecterait aussi les
tests `lent` du TP05 et du TP09 dès que le TP10 est collecté, ce qui serait
très déroutant. Le TP13 réutilise ce motif pour marquer tout un répertoire.

#### `pytest_configure`

```python
def pytest_configure(config):
    config.addinivalue_line("markers", "chrono: test dont on vérifie la durée")
```

**Ce que montre le code.** Appelé une fois, après lecture de la
configuration et chargement des plugins initiaux. Ici, on déclare un
marqueur par programme au lieu de l'écrire dans `pyproject.toml`.

**À montrer en direct.** `uv run pytest --markers | grep chrono` affiche
`@pytest.mark.chrono: test dont on vérifie la durée`. Retirer la ligne du hook
et relancer le TP : `--strict-markers` fait échouer
`test_marqueur_programmatique` avec `'chrono' not found in markers configuration option`.

**Pièges.** `pytest_configure` d'un conftest de sous-dossier n'est appelé
que si ce conftest est chargé au démarrage, c'est-à-dire si le dossier est
passé en argument ou listé dans `testpaths`. C'est le cas ici grâce à
`testpaths`. Pour un plugin destiné à être partagé, préférer le conftest
racine ou un module plugin.

#### `pytest_collection_modifyitems`

```python
def pytest_collection_modifyitems(config, items):
    lancer_lents = config.getoption("--lent")
    skip_lent = pytest.mark.skip(reason="test lent : ajoutez --lent pour l'exécuter")

    prioritaires, autres = [], []
    for item in items:
        if not _est_dans_ce_tp(item):
            autres.append(item)
            continue
        if "lent" in item.keywords and not lancer_lents:
            item.add_marker(skip_lent)
        (prioritaires if item.get_closest_marker("prioritaire") else autres).append(item)

    items[:] = prioritaires + autres
```

**Ce que montre le code.** Appelé une fois après la collecte, avec la liste
complète des tests. Deux actions : ajouter un marqueur `skip` aux tests
`lent` si `--lent` est absent, et remonter en tête les tests `prioritaire`.
La liste est modifiée en place avec `items[:] = ...` ; réaffecter `items =`
ne changerait rien, la variable locale serait perdue.

**À dire aux stagiaires.** `item.keywords` contient les noms de marqueurs et
de fixtures, `item.get_closest_marker("nom")` renvoie le marqueur le plus
proche ou `None`, `item.add_marker` ajoute un marqueur à la volée. On peut
aussi retirer des éléments (`items.remove`) pour désélectionner, ou les
trier par nom pour rendre l'ordre déterministe. C'est le hook qu'utilisent
`pytest-randomly` (ordre aléatoire) et `pytest-ordering`.

**À montrer en direct.**

```bash
uv run pytest tp10_hooks_plugins --collect-only -q
```

```
tp10_hooks_plugins/test_hooks.py::test_prioritaire
tp10_hooks_plugins/test_hooks.py::test_normal_1
tp10_hooks_plugins/test_hooks.py::test_normal_2
...
```

`test_prioritaire` est déclaré après `test_normal_1` dans le fichier mais
collecté avant. Puis `uv run pytest tp10_hooks_plugins -v --lent` : le test
lent passe de `SKIPPED` à `PASSED` et prend 300 ms dans la section du plugin
chrono.

**Pièges et erreurs fréquentes.** Oublier `items[:]`. Oublier de filtrer par
répertoire. Faire dépendre un test de cet ordre : `test_normal_2` vérifie
`ORDRE_EXECUTION[0] == "prioritaire"`, ce qui casse dès qu'on parallélise :

```bash
uv run pytest tp10_hooks_plugins -n 2
```

```
>       assert ORDRE_EXECUTION[0] == "prioritaire"
E       AssertionError: assert 'normal_2' == 'prioritaire'
1 failed, 6 passed, 1 skipped
```

Avec deux workers, `test_normal_2` tourne dans un processus où
`test_prioritaire` n'a jamais tourné ; la liste globale ne contient que lui.
Le commentaire dans le test le dit : c'est une démonstration, pas une
pratique à suivre. Les tests doivent être indépendants de l'ordre.

#### `pytest_runtest_makereport` et la fixture `resultat_du_test`

```python
@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    rapport = yield
    setattr(item, f"rapport_{rapport.when}", rapport)
    return rapport


@pytest.fixture
def resultat_du_test(request):
    yield
    rapport = getattr(request.node, "rapport_call", None)
    if rapport is not None:
        request.config._resultats_tp10.append((request.node.name, rapport.outcome))
```

**Ce que montre le code.** Ce hook est appelé trois fois par test, une par
phase (`setup`, `call`, `teardown`), et fabrique l'objet `TestReport`. En
mode wrapper, le `yield` renvoie le rapport produit par pytest ; on
l'accroche à l'item sous le nom `rapport_setup`, `rapport_call` ou
`rapport_teardown`. La fixture, elle, ne fait rien avant le test ; après le
`yield`, c'est-à-dire pendant le teardown, elle lit `rapport_call.outcome`
(`passed`, `failed` ou `skipped`) et le range dans une liste stockée sur la
configuration.

**À dire aux stagiaires.** C'est le motif officiel, documenté dans pytest,
pour "faire quelque chose seulement si le test a échoué" : capture d'écran
Selenium, sauvegarde des logs d'un conteneur, conservation d'un `tmp_path`.
Une fixture seule ne sait pas si le test a réussi ; il faut ce relais par le
hook. Le `wrapper=True` moderne remplace l'ancien `hookwrapper=True` avec
`outcome = yield` puis `outcome.get_result()`.

**À montrer en direct.** Faire échouer `test_avec_resultat_bis`
(`assert False`) et relancer : la section de résumé affiche
`failed   test_avec_resultat_bis`. Pour un skip, remplacer par
`pytest.skip("démo")` : `skipped`. Remettre le test en état.

**Pièges et erreurs fréquentes.** Lire `rapport_call` dans une fixture de
scope plus large que `function` n'a pas de sens. Un échec dans le `setup`
d'une fixture donne `rapport_setup.failed` et pas de `rapport_call`. Stocker
sur `config` un attribut préfixé par `_` est une convention, pas une API.

#### `pytest_sessionstart` et `pytest_terminal_summary`

```python
def pytest_sessionstart(session):
    session.config._resultats_tp10 = []


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    resultats = getattr(config, "_resultats_tp10", [])
    if resultats:
        terminalreporter.section("TP10 : résultats vus par la fixture resultat_du_test")
        for nom, outcome in resultats:
            terminalreporter.write_line(f"{outcome:8s} {nom}")
```

**Ce que montre le code.** `pytest_sessionstart` initialise la liste avant
tout test. `pytest_terminal_summary` écrit une section dans le rapport
final, après les tests et avant la ligne de résumé. `terminalreporter`
propose `section`, `write_line`, `write_sep`, et l'accès aux rapports par
catégorie via `terminalreporter.stats["failed"]`.

**À dire aux stagiaires.** `exitstatus` est le code de sortie (TP09), on
peut le lire ici pour adapter le message. `pytest_sessionfinish(session,
exitstatus)` est l'équivalent pour un traitement sans affichage (écrire un
fichier, envoyer une notification) ; il permet aussi de modifier
`session.exitstatus`.

**Pièges.** Écrire avec `print` dans ces hooks fonctionne mais passe à côté
de la mise en forme ; utiliser `terminalreporter`.

#### `pytest_assertrepr_compare`

```python
def pytest_assertrepr_compare(config, op, left, right):
    from tp10_hooks_plugins.geometrie import Vecteur

    if isinstance(left, Vecteur) and isinstance(right, Vecteur) and op == "==":
        return [
            "Comparaison de Vecteur :",
            f"   x : {left.x} {'==' if left.x == right.x else '!='} {right.x}",
            f"   y : {left.y} {'==' if left.y == right.y else '!='} {right.y}",
        ]
    return None
```

**Ce que montre le code.** Appelé quand un `assert a op b` échoue. Si le
hook renvoie une liste de lignes, elle remplace l'explication standard ;
`None` laisse pytest faire. C'est un hook `firstresult`.

**À montrer en direct.**

```bash
uv run pytest tp10_hooks_plugins/demo_assertrepr.py
```

```
    def test_vecteurs_differents():
>       assert Vecteur(1, 2) + Vecteur(1, 1) == Vecteur(2, 4)
E       assert Comparaison de Vecteur :
E            x : 2 == 2
E            y : 3 != 4
```

Commenter le corps du hook (ou renvoyer `None`) et relancer : pytest affiche
`assert Vecteur(x=2, y=3) == Vecteur(x=2, y=4)` avec sa comparaison
d'attributs de dataclass, déjà correcte mais moins parlante pour un objet
métier complexe (matrices, documents, réponses HTTP).

**Pièges.** L'import de `Vecteur` est fait dans la fonction, pas en tête de
fichier, pour éviter que le conftest importe du code métier au chargement.
Le hook n'est appelé que pour les assertions réécrites, donc dans les
modules de test, pas dans les helpers importés (sauf
`pytest.register_assert_rewrite`).

### Fichier 3 : `plugin_chrono.py`

```python
@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    debut = time.perf_counter()
    try:
        return (yield)
    finally:
        _DUREES[item.nodeid] = time.perf_counter() - debut


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    plus_lents = sorted(_DUREES.items(), key=lambda kv: kv[1], reverse=True)[:3]
    terminalreporter.section("plugin_chrono : 3 tests les plus lents")
    ...


@pytest.fixture
def horloge():
    ...
```

**Ce que montre le code.** Un plugin est un module ordinaire : des hooks,
des fixtures, un peu d'état de module. `pytest_runtest_call` enroule l'appel
du test lui-même (pas les fixtures) ; le `try/finally` garantit la mesure
même si le test échoue. Le second `pytest_terminal_summary` du projet
s'ajoute à celui du conftest : les deux sections apparaissent, ce qui
illustre "toutes les implémentations sont appelées". La fixture `horloge` est
disponible dans tout le projet, comme le montre `test_marqueur_programmatique`.

**À dire aux stagiaires.** Trois façons de charger un plugin :

| Méthode | Où | Quand l'utiliser |
|---|---|---|
| `pytest_plugins = ["module"]` | conftest racine uniquement | plugin interne au projet |
| `-p module` sur la ligne de commande, ou dans `addopts` | partout | essai, activation ponctuelle |
| entry point `pytest11` dans `pyproject.toml` | paquet installé | plugin distribué, chargé automatiquement |

Pour distribuer :

```toml
[project.entry-points.pytest11]
chrono = "monpaquet.plugin_chrono"
```

Après `pip install`, le plugin apparaît dans la ligne `plugins:` de l'en-tête
et se désactive avec `-p no:chrono`. Le nom de la clé (`chrono`) est celui
utilisé par `-p no:`. Les plugins installés dans ce projet, `mock`, `cov`,
`xdist`, `hypothesis`, sont chargés exactement ainsi.

**À montrer en direct.** Retirer la ligne `pytest_plugins` du conftest
racine, relancer : `fixture 'horloge' not found` sur
`test_marqueur_programmatique`, et la section du chrono disparaît. La
remettre, ou obtenir le même effet avec
`uv run pytest tp10_hooks_plugins -p tp10_hooks_plugins.plugin_chrono`.
Montrer `-p no:cacheprovider` pour la désactivation d'un plugin intégré
(TP08).

**Pièges et erreurs fréquentes.** L'état de module `_DUREES` est partagé par
tout le processus ; avec xdist, chaque worker a le sien et le résumé du
processus principal est vide. Charger le même module par `pytest_plugins`
et par `-p` ne provoque pas d'erreur : pytest reconnaît le module déjà
enregistré et l'ignore (vérifié : une seule section chrono dans le rapport).
En revanche, enregistrer deux plugins distincts sous le même nom avec
`config.pluginmanager.register(obj, name="chrono")` lève
`ValueError: Plugin name already registered`.

### Fichier 4 : `test_hooks.py`

**Ce que montre le code.** Chaque test observe un hook : `test_prioritaire`
et `test_normal_2` l'ordre, `test_tres_lent` le skip conditionnel,
`test_marqueur_programmatique` le marqueur déclaré par `pytest_configure` et
la fixture du plugin, `test_option_env` l'option maison via la fixture `env`
et via `pytestconfig`, `test_avec_resultat` et `test_avec_resultat_bis` la
fixture de résultat.

**À montrer en direct.** Les trois variantes du docstring :

```bash
uv run pytest tp10_hooks_plugins -v
uv run pytest tp10_hooks_plugins -v --lent
uv run pytest tp10_hooks_plugins -v --env prod
```

### Hooks fréquents non illustrés

| Hook | Usage typique |
|---|---|
| `pytest_runtest_setup(item)` | skipper selon une condition d'environnement : `if item.get_closest_marker("bdd") and not bdd_dispo: pytest.skip(...)` |
| `pytest_runtest_teardown(item)` | nettoyage après chaque test |
| `pytest_sessionfinish(session, exitstatus)` | écrire un fichier de synthèse, changer le code de sortie |
| `pytest_ignore_collect(collection_path, config)` | exclure des chemins de la collecte |
| `pytest_collect_file(file_path, parent)` | collecter des tests non Python (fichiers YAML, `.feature` de pytest-bdd) |
| `pytest_generate_tests(metafunc)` | paramétrage dynamique (TP04) |
| `pytest_exception_interact(node, call, report)` | réagir à une exception avant le débogueur |
| `pytest_load_initial_conftests` | très tôt au démarrage, réservé aux plugins |

## Questions fréquentes des stagiaires

**Où dois-je mettre mon hook ?**
Dans le conftest racine s'il concerne tout le projet ou déclare une option.
Dans un conftest de sous-dossier s'il ne concerne que ce dossier, en
filtrant par chemin. Dans un module plugin s'il doit être partagé entre
projets.

**Pourquoi mon `pytest_addoption` provoque `no option named` ?**
Il est dans un conftest de sous-dossier, chargé après l'analyse des options.
Le déplacer dans le conftest racine.

**Comment savoir si un test a échoué dans une fixture ?**
Avec le motif `pytest_runtest_makereport` en wrapper qui stocke le rapport
sur `item`, puis `request.node.rapport_call.outcome` après le `yield` de la
fixture.

**Quelle est la différence entre `tryfirst`, `trylast` et `wrapper` ?**
`tryfirst` et `trylast` changent la position dans la liste des
implémentations ordinaires. `wrapper` fait de l'implémentation une enveloppe
qui s'exécute avant et après toutes les autres, avec accès au résultat.

**Peut-on modifier les arguments d'un hook ?**
Pour `pytest_collection_modifyitems`, oui, en place. Pour la plupart des
autres, non : on renvoie une valeur ou on agit par effet de bord.

**Comment tester un plugin ?**
Avec la fixture `pytester` (`-p pytester` ou `pytest_plugins = ["pytester"]`),
qui crée un projet temporaire, y écrit des tests et lance pytest dedans, puis
permet d'inspecter le résultat (`result.assert_outcomes(passed=2)`).

**`pytest_plugins` fonctionne dans un conftest de sous-dossier ?**
Non, erreur `Defining 'pytest_plugins' in a non-top-level conftest is no longer supported`.

**Pourquoi le résumé du plugin chrono est vide avec `-n auto` ?**
Les tests tournent dans des workers, chacun avec son propre dictionnaire
`_DUREES` ; le processus principal, qui écrit le résumé, n'a rien mesuré.
Un plugin compatible xdist doit remonter ses données au contrôleur, par
exemple via `config.workeroutput` et le hook `pytest_testnodedown`.

## Ce qu'il faut retenir

| Besoin | Hook | Emplacement |
|---|---|---|
| Option de ligne de commande, clé ini | `pytest_addoption(parser)` | conftest racine, plugin |
| Enregistrer un marqueur, initialiser | `pytest_configure(config)` | conftest, plugin |
| Ligne d'en-tête | `pytest_report_header(config)` | conftest, plugin |
| Paramétrage calculé | `pytest_generate_tests(metafunc)` | conftest |
| Trier, filtrer, marquer les tests | `pytest_collection_modifyitems(config, items)` | conftest (filtrer par chemin) |
| Skipper selon l'environnement | `pytest_runtest_setup(item)` | conftest |
| Chronométrer, envelopper le test | `pytest_runtest_call(item)` en wrapper | plugin |
| Connaître le résultat dans une fixture | `pytest_runtest_makereport(item, call)` en wrapper | conftest |
| Message d'échec personnalisé | `pytest_assertrepr_compare(config, op, left, right)` | conftest |
| Section de rapport | `pytest_terminal_summary(terminalreporter, exitstatus, config)` | conftest, plugin |
| Traitement de fin | `pytest_sessionfinish(session, exitstatus)` | conftest, plugin |

Charger un plugin : `pytest_plugins` (conftest racine), `-p module`, entry
point `pytest11`. Désactiver : `-p no:nom`.

## Exercices

1. **Skip `bdd` en prod.** Ajouter un hook `pytest_runtest_setup(item)` dans
   `conftest.py` qui skippe tout test marqué `bdd` quand `--env prod`.

   Indice / corrigé :
   ```python
   def pytest_runtest_setup(item):
       if item.get_closest_marker("bdd") and item.config.getoption("--env") == "prod":
           pytest.skip("pas d'accès à la base en prod")
   ```
   Tester avec un test marqué `@pytest.mark.bdd` dans `test_hooks.py` et
   `uv run pytest tp10_hooks_plugins --env prod -ra`.

2. **Durées dans un fichier JSON.** Faire écrire `_DUREES` dans `durees.json`
   à la fin de la session.

   Indice / corrigé : dans `plugin_chrono.py`,
   ```python
   def pytest_sessionfinish(session, exitstatus):
       chemin = session.config.rootpath / "durees.json"
       chemin.write_text(json.dumps(_DUREES, indent=2), encoding="utf-8")
   ```
   Penser à ajouter `durees.json` au `.gitignore`.

3. **Opérateur `!=` dans `pytest_assertrepr_compare`.** Étendre le hook.

   Indice / corrigé : accepter `op in ("==", "!=")` et adapter la première
   ligne : `f"Comparaison de Vecteur ({op}) :"`. Vérifier avec un test
   `assert Vecteur(1, 1) != Vecteur(1, 1)` dans `demo_assertrepr.py`.

4. **Ordre déterministe.** Remplacer le réordonnancement "prioritaires
   d'abord" par un tri alphabétique des tests de ce répertoire, et constater
   avec `--collect-only -q`.

   Indice / corrigé : `items[:] = sorted(items, key=lambda i: i.nodeid)` sur
   la partie filtrée. `test_normal_2` échoue alors : le supprimer ou le
   corriger, c'est justement le but.

5. **Plugin testé avec `pytester`.** Écrire un test qui vérifie que la fixture
   `horloge` du plugin fonctionne dans un projet vierge.

   Indice / corrigé : dans un nouveau fichier `test_plugin_chrono.py`,
   ```python
   pytest_plugins = ["pytester"]  # à mettre dans le conftest racine en réalité

   def test_horloge_disponible(pytester):
       pytester.makepyfile("def test_x(horloge):\n    assert horloge.ecoule() >= 0\n")
       result = pytester.runpytest("-p", "tp10_hooks_plugins.plugin_chrono")
       result.assert_outcomes(passed=1)
   ```
   Le `pytest_plugins = ["pytester"]` doit aller dans le conftest racine
   (règle vue plus haut) ; ou lancer avec `-p pytester`.

## Transition vers le TP suivant

Tous les mécanismes des TP01 à TP10 sont maintenant connus. Le TP11 les
assemble sur une application complète, organisée comme un vrai projet, où
chaque technique apparaît à l'endroit où elle est utile.
