# TP09 – Configuration, organisation et exécution

## En une phrase

Ce TP quitte le code des tests pour regarder ce qui les entoure : le fichier
de configuration, la structure du projet, les options de la ligne de commande
et les outils qui font passer une suite de tests du poste du développeur à
l'intégration continue.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- écrire et lire une section `[tool.pytest.ini_options]` et connaître les
  clés les plus utiles ;
- expliquer ce qu'est le `rootdir`, comment pytest le détermine et pourquoi
  cela compte ;
- organiser les tests d'un projet (à côté du code ou dans `tests/`, `src`
  layout) et éviter l'erreur `import file mismatch` ;
- sélectionner, arrêter, reprendre et déboguer une exécution avec les
  options de la ligne de commande ;
- exécuter les doctests, mesurer la couverture, paralléliser ;
- écrire une commande pytest adaptée à une intégration continue et lire son
  code de sortie.

## Prérequis

- TP01 (options de base `-v`, `-k`, `-x`, `--lf`).
- TP03 (`conftest.py`) et TP05 (marqueurs, `--strict-markers`), car le
  `pyproject.toml` les configure.
- TP08 pour `pytestconfig` et le `cache`.

## Fichiers

| Fichier | Rôle |
|---|---|
| `../pyproject.toml` | La configuration **active** du projet (section `[tool.pytest.ini_options]`) |
| `../conftest.py` | Options `--env` / `--lent`, fixture `env`, en-tête de rapport |
| `exemples_config/` | La même configuration écrite dans les cinq formats reconnus : `pytest.ini`, `pytest.toml`, `pyproject.toml`, `tox.ini`, `setup.cfg`. Fichiers de référence, **non actifs** (voir leur README) |
| `mini_projet/` | Mini-projet avec son propre `pytest.ini` : démontre que le fichier de configuration le plus proche des arguments gagne, et ce que change le `rootdir` |
| `outils.py` | Fonctions avec **doctests** |
| `test_configuration.py` | Tests de support pour les démos (`--durations`, `--lf`, `--sw`, `--env`) |

## Mise en route

```bash
uv run pytest tp09_configuration -v
```

Sortie attendue : `12 passed` en 0,3 s environ (deux tests contiennent un
`time.sleep` volontaire). En haut du rapport, faire lire l'en-tête :

```
platform darwin -- Python 3.13.0, pytest-9.1.1, pluggy-1.6.0
Formation pytest -- environnement : dev
rootdir: /Users/fgaurat/local_dev/formations/prep/formation-pytest
configfile: pyproject.toml
plugins: mock-3.15.1, cov-7.1.0, xdist-3.8.0, hypothesis-6.167.1
collected 12 items
```

Chaque ligne sera expliquée dans le déroulé : la ligne "Formation pytest"
vient du conftest racine, `rootdir` et `configfile` de la découverte de la
configuration, `plugins` des paquets installés.

## Déroulé de la présentation

### Thème 1 : le fichier de configuration

**Ce que montre le code.** Ouvrir `pyproject.toml` et lire la section
`[tool.pytest.ini_options]` clé par clé :

```toml
[tool.pytest.ini_options]
minversion = "8.0"
pythonpath = ["."]
addopts = "-ra --strict-markers"
markers = [
    "lent: test long a executer (desactivable avec -m 'not lent')",
    "integration: test necessitant une ressource externe (BDD, API...)",
    ...
]
testpaths = ["tp01_bases", "tp02_classes", ...]
log_format = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
log_date_format = "%H:%M:%S"
```

| Clé | Effet dans ce projet |
|---|---|
| `minversion` | pytest refuse de démarrer avec une version plus ancienne que 8.0 : évite les surprises entre postes |
| `pythonpath` | ajoute la racine du projet à `sys.path` avant la collecte ; c'est ce qui rend `from tp01_bases.calculatrice import ...` possible |
| `addopts` | options ajoutées à chaque exécution : `-ra` affiche le résumé des tests non passés, `--strict-markers` refuse tout marqueur non déclaré |
| `markers` | déclaration des marqueurs personnalisés, une ligne `nom: description` chacun ; `donnees(fichier)` documente un marqueur à argument |
| `testpaths` | répertoires explorés quand on lance `pytest` sans argument ; sans cette clé, pytest explore le répertoire courant en entier |
| `log_format`, `log_date_format` | format des logs capturés par `caplog` et affichés par `--log-cli-level` |

**À dire aux stagiaires.** pytest cherche son fichier de configuration en
remontant depuis les chemins passés en argument (ou le répertoire courant).
Le premier trouvé parmi `pytest.toml`, `pytest.ini`, `pyproject.toml`
(seulement s'il contient la section), `tox.ini`, `setup.cfg` fixe la
configuration. Un `pytest.ini` gagne toujours, même vide : c'est un moyen de
forcer la racine. Les autres formats sont équivalents ; `pyproject.toml` est
le choix moderne parce que tout l'outillage Python y est déjà.

Priorité des sources d'options, de la plus forte à la plus faible : la ligne
de commande, la variable d'environnement `PYTEST_ADDOPTS`, la clé `addopts`.
Trois options pour intervenir ponctuellement : `-o cle=valeur` surcharge une
clé ini, `-c fichier` impose un fichier de configuration, `--rootdir=chemin`
impose la racine.

**À montrer en direct.**

```bash
uv run pytest --help | grep -A 40 "configuration options"
```

La fin de `--help` liste toutes les clés ini reconnues, avec leur type. Puis
faire une faute de frappe volontaire :

```bash
uv run pytest tp09_configuration -o inconnue=1 --strict-config
```

```
ERROR: Unknown config option: inconnue
```

Sans `--strict-config`, la même commande n'émet qu'un avertissement
`PytestConfigWarning`. Recommander `--strict-config` en CI.

Ensuite ouvrir `exemples_config/` : la même configuration dans les cinq
formats. Les faire défiler côte à côte, en insistant sur les différences de
syntaxe (listes INI sur plusieurs lignes contre listes TOML, section
`[tool:pytest]` avec deux-points dans `setup.cfg`, `addopts` obligatoirement
une liste dans les formats TOML natifs). Puis prouver qu'ils sont
interchangeables en imposant l'un d'eux avec `-c` :

```bash
uv run pytest -c tp09_configuration/exemples_config/pytest.ini --rootdir=. tp01_bases
```

```
rootdir: /Users/.../formation-pytest
configfile: tp09_configuration/exemples_config/pytest.ini
16 passed in 0.09s
```

Même chose avec `pytest.toml` : 16 passed. Expliquer `--rootdir=.` : sans
lui, la racine deviendrait le dossier du fichier imposé et `pythonpath = .`
pointerait au mauvais endroit.

**Pièges et erreurs fréquentes.**
- Section `[tool.pytest]` au lieu de `[tool.pytest.ini_options]` : ignorée
  silencieusement par pytest 8. pytest 9 l'accepte, ainsi qu'un fichier
  `pytest.toml` avec une table `[pytest]`, mais avec des types TOML natifs :
  `addopts = "-v"` y provoque l'erreur réelle
  `config option 'addopts' expects a list for type 'args', got str: '-v'`.
  Il faut écrire `addopts = ["-v"]`. La section `ini_options` garde la
  syntaxe historique (chaînes), c'est celle utilisée dans ce projet.
- Deux fichiers de configuration dans le dépôt (un `pytest.ini` oublié et un
  `pyproject.toml`) : seul le premier trouvé compte.
- `addopts` contenant `--cov` : la couverture s'active à chaque lancement et
  ralentit tout, et le débogueur `--pdb` devient inutilisable. Laisser la
  couverture à la CI.

### Thème 2 : rootdir et conftest racine

**Ce que montre le code.** Le `conftest.py` racine, ligne par ligne :

```python
pytest_plugins = ["tp10_hooks_plugins.plugin_chrono"]
```
Charge un plugin local (détaillé au TP10). Cette variable n'est autorisée que
dans le conftest racine.

```python
def pytest_addoption(parser):
    parser.addoption("--env", action="store", default="dev", choices=["dev", "staging", "prod"], ...)
    parser.addoption("--lent", action="store_true", default=False, ...)
```
Déclare deux options de ligne de commande. `parser.addoption` a la même
signature que `argparse.add_argument`. Les options sont visibles dans
`pytest --help`, section "Custom options".

```python
def pytest_report_header(config):
    return f"Formation pytest -- environnement : {config.getoption('--env')}"
```
Ajoute une ligne à l'en-tête du rapport.

```python
@pytest.fixture(scope="session")
def env(pytestconfig):
    return pytestconfig.getoption("--env")
```
Expose l'option sous forme de fixture : les tests demandent `env` plutôt que
d'aller lire la configuration.

**À dire aux stagiaires.** Le `rootdir` est le répertoire du fichier de
configuration trouvé, ou à défaut l'ancêtre commun des arguments. Il sert de
base aux node ids (`tp09_configuration/test_configuration.py::test_slugifier`),
au cache, et à la résolution de `pythonpath` et `testpaths`. Il ne dépend pas
du répertoire courant : lancer pytest depuis `tp09_configuration/` donne le
même `rootdir`, on peut le vérifier. Le conftest racine est chargé au
démarrage, avant l'analyse des options, ce qui explique pourquoi
`pytest_addoption` doit y vivre.

**À montrer en direct.**

```bash
cd tp09_configuration && uv run pytest -q && cd ..
uv run pytest tp09_configuration --env staging
uv run pytest --help | grep -A 6 "Custom options"
```

Sortie réelle de `--help` :

```
Custom options:
  --env={dev,staging,prod}
                        Environnement cible des tests (dev par défaut)
  --lent                Exécute aussi les tests marqués @pytest.mark.lent du
                        TP10
```

Puis montrer l'effet de `--env prod` sur `test_skip_selon_env`, dont la
fixture `base_url` appelle `pytest.skip` :

```bash
uv run pytest tp09_configuration --env prod -ra
```

```
SKIPPED [1] tp09_configuration/test_configuration.py:54: on ne lance pas ce test contre la prod
11 passed, 1 skipped
```

**Pièges et erreurs fréquentes.** `pytest --env staging` sans chemin ni
`testpaths` fonctionne ; mais `pytest --env=truc` échoue avec
`invalid choice: 'truc'` grâce à `choices`. Un `pytest_addoption` placé dans
un conftest de sous-dossier fonctionne seulement si ce dossier est passé en
argument, et casse dès qu'on lance depuis la racine.

### Le mini-projet : voir le rootdir changer

**Ce que montre le code.** `mini_projet/` contient un `pytest.ini` qui
diffère de la configuration racine sur deux points : `addopts = -v` et
`python_files = test_*.py verif_*.py`. Il contient deux fichiers de test :
`test_mini.py` (motif standard) et `verif_regles.py` (motif reconnu
seulement par ce `pytest.ini`, avec un marqueur `regle` déclaré là
uniquement).

**À montrer en direct.** Lancer le même dossier de deux façons.

```bash
uv run pytest tp09_configuration/mini_projet
```

```
rootdir: /Users/.../formation-pytest/tp09_configuration/mini_projet
configfile: pytest.ini
collected 2 items
tp09_configuration/mini_projet/test_mini.py::test_toujours_collecte PASSED
tp09_configuration/mini_projet/verif_regles.py::test_regle_metier PASSED
2 passed
```

Les arguments sont dans `mini_projet`, pytest y trouve un `pytest.ini`,
qui devient la configuration et fixe le `rootdir`. Les deux fichiers sont
collectés, en mode verbeux.

```bash
uv run pytest --collect-only -q tp09_configuration | grep mini
```

```
tp09_configuration/mini_projet/test_mini.py::test_toujours_collecte
```

Ici l'argument est `tp09_configuration` : pytest remonte jusqu'au
`pyproject.toml` racine. Le `pytest.ini` du sous-dossier est ignoré,
`verif_regles.py` n'existe pas aux yeux de pytest, et son marqueur non
déclaré ne gêne pas `--strict-markers` puisque le fichier n'est jamais lu.

Puis la conséquence la plus surprenante du changement de `rootdir` :

```bash
uv run pytest tp09_configuration/mini_projet --env prod
```

```
pytest: error: unrecognized arguments: --env prod
```

Le `conftest.py` racine, qui déclare `--env`, est **en dehors** du nouveau
`rootdir` : il n'est pas chargé. Ni l'option, ni la fixture `env`, ni le
plugin `plugin_chrono` du TP10 n'existent dans cette session. C'est
l'illustration concrète de « les conftest sont chargés du répertoire des
arguments jusqu'au rootdir, pas au-delà ».

**À dire aux stagiaires.** Un `pytest.ini` oublié dans un sous-dossier
(souvent copié avec un exemple) change silencieusement la configuration
dès qu'on lance les tests de ce sous-dossier. Toujours lire les deux
lignes `rootdir` et `configfile` de l'en-tête quand un comportement
surprend.

**Pièges et erreurs fréquentes.** Lancer `pytest` depuis le sous-dossier
avec `cd` produit le même effet que de le passer en argument : c'est le
répertoire des arguments (ou le répertoire courant) qui compte, pas
l'endroit où se trouve l'environnement virtuel.

### Thème 3 : organisation des tests et modes d'import

**Ce que montre le code.** Ce dépôt place les tests à côté du code, dans des
paquets (`__init__.py` dans chaque `tpXX_*`). Le TP11 illustre la variante
courante avec un sous-répertoire `tests/`.

```
projet/                          projet/
├── pyproject.toml               ├── pyproject.toml
├── conftest.py                  ├── src/monpaquet/...       (src layout)
├── monpaquet/                   └── tests/
│   ├── module.py                    ├── conftest.py
│   └── test_module.py               ├── unit/test_module.py
└── ...                              └── integration/test_api.py
```

**À dire aux stagiaires.** Trois façons de rendre le code importable depuis
les tests : `pythonpath = ["src"]` dans la configuration (simple, ce qu'on
fait ici avec `"."`), l'installation éditable du paquet (`uv pip install -e .`
ou `uv sync` avec un projet packagé, la méthode la plus fidèle à la
production), ou les modes d'import de pytest. Le mode par défaut, `prepend`,
insère dans `sys.path` le premier répertoire sans `__init__.py` au-dessus de
chaque fichier de test, et nomme le module d'après son chemin de paquet. Deux
fichiers `test_m.py` dans deux dossiers sans `__init__.py` reçoivent donc le
même nom de module, et le second ne peut pas être importé. `append` fait la
même chose en fin de `sys.path`. `importlib` n'ajoute rien à `sys.path` et
donne des noms uniques, mais les modules de test ne peuvent plus s'importer
entre eux.

**À montrer en direct.** Reproduire l'erreur dans un dossier temporaire hors
du projet :

```bash
mkdir -p /tmp/demo/a /tmp/demo/b && cd /tmp/demo
printf 'def test_x():\n    pass\n' > a/test_m.py && cp a/test_m.py b/test_m.py && touch pytest.ini
uv run --project ~/local_dev/formations/prep/formation-pytest pytest -q
```

```
import file mismatch:
  /tmp/demo/a/test_m.py
which is not the same as the test file we want to collect:
  /tmp/demo/b/test_m.py
HINT: remove __pycache__ / .pyc files and/or use a unique basename for your test file modules
```

Puis `--import-mode=importlib` : `2 passed`. Ou ajouter un `__init__.py` dans
`a/` et `b/`.

**Pièges et erreurs fréquentes.** Un `__init__.py` oublié dans un seul des
dossiers de test ; un `conftest.py` dupliqué ; un module de test qui porte le
même nom qu'un module du code (`test_utils.py` et `utils.py` ne posent pas
problème, mais `logging.py` dans le dossier de tests masque la bibliothèque
standard).

### Thème 4 : sélectionner les tests

**À dire aux stagiaires.** Du plus large au plus précis : un répertoire, un
fichier, un node id `fichier::Classe::test`, un cas paramétré
`test_serie[3]` (entre guillemets à cause des crochets dans le shell). `-k`
filtre sur les noms avec une expression booléenne, `-m` sur les marqueurs,
`--deselect` retire un node id, `--collect-only -q` liste sans exécuter.

**À montrer en direct.**

```bash
uv run pytest tp09_configuration --collect-only -q
uv run pytest "tp09_configuration/test_configuration.py::test_serie[3]" -v
uv run pytest tp09_configuration -k "serie and not 3" -v
uv run pytest tp09_configuration -m "not lent" -v
uv run pytest tp09_configuration --deselect tp09_configuration/test_configuration.py::test_moyen -q
```

Sortie de `--collect-only -q` :

```
tp09_configuration/test_configuration.py::test_slugifier
tp09_configuration/test_configuration.py::test_tranche
tp09_configuration/test_configuration.py::test_rapide
...
tp09_configuration/test_configuration.py::test_serie[0]
```

**Pièges et erreurs fréquentes.** `-k` est insensible à la casse et
correspond aussi aux noms de fichiers et de classes : `-k config` sélectionne
tout le fichier `test_configuration.py`. Les crochets dans `-k "serie[3]"` ne
fonctionnent pas comme on l'attend ; utiliser `-k "serie and 3"` ou le node
id complet.

### Thème 5 : arrêter et reprendre

**À dire aux stagiaires.** `-x` s'arrête au premier échec, `--maxfail=N`
après N. `--lf` relance uniquement les derniers échecs, `--ff` les joue en
premier puis le reste. `--sw` (stepwise) s'arrête au premier échec et, au
lancement suivant, reprend à ce test en sautant ceux qui ont déjà réussi :
c'est le mode idéal pour corriger une longue série d'échecs un par un. Tout
cela repose sur le cache du TP08.

**À montrer en direct.** Casser `test_serie` (par exemple `assert n != 3`)
puis enchaîner :

```bash
uv run pytest tp09_configuration -q            # 1 failed
uv run pytest tp09_configuration --lf -v       # ne rejoue que test_serie[3]
uv run pytest tp09_configuration --sw -v       # s'arrête à test_serie[3]
```

Sortie réelle de `--sw` sur un échec :

```
!!!!!!!! Interrupted: Test failed, continuing from this test next run. !!!!!!!!!
```

Corriger, relancer `--sw` :

```
stepwise: skipping 1 already passed items (cache from 0:00:05 ago, use --sw-reset to discard).
```

**Pièges et erreurs fréquentes.** `--lf` après avoir renommé un test rejoue
tout (le node id n'existe plus). `--sw-reset` pour repartir de zéro.

### Thème 6 : affichage et diagnostic

**À dire aux stagiaires.** `-v` un test par ligne, `-vv` diff complet des
assertions, `-q` sortie minimale. `-ra` résumé des non-passés, `-rA` tout.
`--tb=short|long|line|native|no` règle la longueur des tracebacks.
`--durations=N` liste les N tests les plus lents, `--durations-min` filtre
sous un seuil. `--setup-show` montre les fixtures (TP03). `-s` désactive la
capture, `--log-cli-level=INFO` affiche les logs en direct (TP08).

**À montrer en direct.**

```bash
uv run pytest tp09_configuration --durations=3
```

```
============================= slowest 3 durations ==============================
0.16s call     tp09_configuration/test_configuration.py::test_plus_lent
0.06s call     tp09_configuration/test_configuration.py::test_moyen

(1 durations < 0.005s hidden.  Use -vv to show these durations.)
```

Chaque durée est ventilée par phase : `setup`, `call`, `teardown`. Une fixture
lente apparaît en `setup`.

**Pièges et erreurs fréquentes.** `--tb=no` cache aussi la raison d'un
`ERROR` de fixture ; garder au moins `--tb=line`.

### Thème 7 : déboguer

**À dire aux stagiaires.** `--pdb` ouvre le débogueur au premier échec, sur
la ligne fautive, avec les variables locales. `--trace` l'ouvre au début de
chaque test. `breakpoint()` dans un test fonctionne aussi : pytest désactive
la capture automatiquement. `-W error::DeprecationWarning` transforme une
catégorie d'avertissements en erreurs, `-p no:nom` désactive un plugin
(`-p no:cacheprovider`, `-p no:randomly`).

**À montrer en direct.** Avec `test_serie` cassé :

```bash
uv run pytest tp09_configuration --lf --pdb
```

Dans le débogueur : `p n`, `l`, `q`. Puis `--lf -x --pdb` combiné, qui est la
commande de travail quotidienne de beaucoup de développeurs.

**Pièges et erreurs fréquentes.** `--pdb` avec `-n` (xdist) ne fonctionne
pas : les tests tournent dans d'autres processus.

### Thème 8 : doctests

**Ce que montre le code.** `outils.py` contient deux fonctions dont les
docstrings incluent des exemples, y compris une exception attendue :

```python
>>> tranche([1], 0)
Traceback (most recent call last):
    ...
ValueError: taille doit être > 0
```

**À dire aux stagiaires.** `--doctest-modules` importe chaque module Python
et exécute ses exemples comme des tests. Bon pour garantir que la
documentation reste vraie ; mauvais comme suite de tests principale
(assertions limitées, fragiles aux détails d'affichage). Clés utiles :
`doctest_optionflags = ["NORMALIZE_WHITESPACE", "ELLIPSIS"]`, et la fixture
`doctest_namespace` pour injecter des objets dans les exemples.

**À montrer en direct.**

```bash
uv run pytest --doctest-modules tp09_configuration/outils.py -v
```

```
tp09_configuration/outils.py::tp09_configuration.outils.slugifier PASSED
tp09_configuration/outils.py::tp09_configuration.outils.tranche PASSED
```

Modifier `'formation-pytest-2024'` en `'formation-pytest'` dans la docstring
et relancer pour voir le rapport `Expected` / `Got`.

**Pièges et erreurs fréquentes.** `--doctest-modules` à la racine importe
aussi `conftest.py` et tous les modules, y compris ceux qui ont des effets de
bord à l'import. Le limiter à un dossier, ou l'activer dans `addopts` avec
`testpaths` bien délimité.

### Thème 9 : couverture (pytest-cov)

**À dire aux stagiaires.** `--cov=chemin_ou_paquet` mesure les lignes
exécutées, `--cov-report=term-missing` liste les lignes manquantes,
`--cov-report=html` génère `htmlcov/index.html`, `--cov-fail-under=N` fait
échouer sous N %. La couverture dit ce qui n'est pas testé ; elle ne dit pas
que ce qui est couvert est bien testé. La couverture de branches
(`[tool.coverage.run] branch = true`) est plus exigeante que la couverture de
lignes.

**À montrer en direct.**

```bash
uv run pytest tp11_projet --cov=tp11_projet/stock --cov-report=term-missing -q
```

```
Name                                Stmts   Miss  Cover   Missing
-----------------------------------------------------------------
tp11_projet/stock/cli.py               36      0   100%
tp11_projet/stock/depot.py             49      0   100%
tp11_projet/stock/modeles.py           27      0   100%
tp11_projet/stock/service.py           49      0   100%
tp11_projet/stock/tarification.py      21      0   100%
-----------------------------------------------------------------
TOTAL                                 182      0   100%
```

Commenter un test de `test_cli.py` pour voir apparaître des numéros de lignes
dans la colonne `Missing`. La ligne `if __name__ == "__main__":  # pragma: no cover`
de `cli.py` montre comment exclure une ligne.

**Pièges et erreurs fréquentes.** `--cov` sans argument mesure tout, y compris
les tests. `--cov=tp11_projet` inclut les tests dans le total et gonfle le
pourcentage. Toujours viser le paquet de code.

### Thème 10 : parallélisation (pytest-xdist)

**À dire aux stagiaires.** `-n auto` crée un processus par cœur, `-n 4`
quatre. `--dist loadfile` regroupe les tests d'un même fichier sur un même
worker (utile pour les fixtures de scope module), `--dist loadgroup` avec
`@pytest.mark.xdist_group("nom")`. Conditions : tests indépendants de
l'ordre, pas d'état partagé sur disque ou sur un port, et fixtures `session`
exécutées une fois par worker, pas une fois au total.

**À montrer en direct.**

```bash
uv run pytest tp11_projet -n 2 -v | head
```

```
created: 2/2 workers
2 workers [63 items]
[gw1] [  1%] PASSED tp11_projet/tests/test_depot.py::TestContratDepot::test_vide_au_depart[json]
[gw0] [  4%] PASSED tp11_projet/tests/test_cli.py::test_ajouter_puis_lister
```

Les préfixes `gw0`, `gw1` identifient les workers. Sur une suite de 63 tests
rapides, la parallélisation ne fait rien gagner : le démarrage des workers
coûte plus que les tests. Le gain apparaît au-delà de quelques secondes de
suite.

**Pièges et erreurs fréquentes.** Le TP10 contient un test dépendant de
l'ordre : le lancer avec `-n 2` le fait échouer (vu au TP10). `-s` et `--pdb`
ne fonctionnent pas avec xdist.

### Thème 11 : intégration continue

**À dire aux stagiaires.** Une commande de CI type :

```bash
uv run pytest -ra -q --strict-markers --strict-config \
    -W error::DeprecationWarning \
    --cov=monpaquet --cov-report=xml --cov-fail-under=80 \
    --junitxml=rapport.xml -n auto
```

`--junitxml` produit un fichier XML lu par GitLab, Jenkins, GitHub et les
tableaux de bord de tests. Extrait réel :

```xml
<testsuite name="pytest" errors="0" failures="0" skipped="0" tests="12" time="0.229" ...>
  <testcase classname="tp09_configuration.test_configuration" name="test_slugifier" time="0.000" />
```

Codes de sortie, vérifiés dans ce projet :

| Code | Signification | Exemple |
|---|---|---|
| 0 | tout est passé | `pytest tp09_configuration` |
| 1 | au moins un échec | `pytest tp01_bases/demo_echecs.py` |
| 2 | interrompu (Ctrl+C, `-x`, `--sw`) | |
| 3 | erreur interne de pytest | |
| 4 | mauvais usage | `pytest dossier_inexistant` |
| 5 | aucun test collecté | `pytest -k nexistepas` |

Le code 5 surprend souvent : un filtre `-k` ou `-m` qui ne sélectionne rien
fait échouer le job.

Exemple GitHub Actions :

```yaml
name: tests
on: [push, pull_request]
jobs:
  pytest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync
      - run: uv run pytest -ra --strict-markers --strict-config --junitxml=rapport.xml --cov=tp11_projet/stock --cov-report=xml
      - uses: actions/upload-artifact@v4
        if: always()
        with: { name: rapports, path: "rapport.xml" }
```

Exemple GitLab CI :

```yaml
tests:
  image: ghcr.io/astral-sh/uv:python3.13-bookworm-slim
  script:
    - uv sync
    - uv run pytest -ra --strict-markers --junitxml=rapport.xml --cov=tp11_projet/stock --cov-report=xml
  artifacts:
    when: always
    reports:
      junit: rapport.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

**Pièges et erreurs fréquentes.** Un `addopts` de développement (`-x`,
`--pdb`) commité par erreur casse la CI. Les tests marqués `integration` ou
`docker` (TP13) doivent être filtrés ou avoir leurs services disponibles.

## Questions fréquentes des stagiaires

**`pytest.ini`, `pyproject.toml` ou `tox.ini` ?**
Même contenu, syntaxe différente. `pyproject.toml` pour un projet moderne ;
`pytest.ini` si on veut forcer la racine ou séparer la configuration.

**Comment savoir quel fichier de configuration pytest a utilisé ?**
Ligne `configfile:` de l'en-tête. `rootdir:` juste au-dessus.

**Faut-il des `__init__.py` dans les dossiers de tests ?**
Avec le mode `prepend` par défaut : oui dès qu'un nom de fichier est
dupliqué, ou choisir `--import-mode=importlib`. Avec des noms uniques, on
peut s'en passer.

**Pourquoi mes options `addopts` ne s'appliquent pas ?**
Vérifier `configfile:` dans l'en-tête ; un autre fichier a peut-être été
trouvé avant. `PYTEST_ADDOPTS` peut aussi être défini dans l'environnement.

**Comment lancer un seul cas paramétré ?**
Node id complet entre guillemets : `"fichier::test_serie[3]"`. Ou
`-k "serie and 3"`.

**La couverture à 100 % veut dire que tout est testé ?**
Non. Elle signifie que chaque ligne a été exécutée au moins une fois. Une
ligne peut être exécutée sans qu'aucune assertion ne vérifie son effet.

**Pourquoi `-n auto` est plus lent que sans ?**
Le démarrage des workers et la collecte dans chaque worker coûtent un temps
fixe. Le gain apparaît sur des suites de plusieurs dizaines de secondes.

**Comment ignorer un dossier ?**
`norecursedirs` dans la configuration, `--ignore=chemin` sur la ligne de
commande, ou `collect_ignore = [...]` dans un `conftest.py`.

**Quelle est la différence entre `--lf` et `--sw` ?**
`--lf` rejoue tous les derniers échecs. `--sw` s'arrête au premier échec et
reprend là au prochain lancement, sans rejouer ce qui a réussi.

## Ce qu'il faut retenir

| Besoin | Outil |
|---|---|
| Configurer une fois pour tous | `[tool.pytest.ini_options]` : `addopts`, `testpaths`, `pythonpath`, `markers`, `filterwarnings` |
| Savoir où on est | en-tête : `rootdir`, `configfile`, `plugins` |
| Rendre le code importable | `pythonpath`, ou installation éditable |
| Éviter `import file mismatch` | noms uniques, `__init__.py`, ou `--import-mode=importlib` |
| Sélectionner | chemin, node id, `-k`, `-m`, `--deselect`, `--collect-only` |
| Boucler sur les échecs | `-x`, `--lf`, `--ff`, `--sw` |
| Comprendre un échec | `-vv`, `--tb=`, `--durations`, `--setup-show`, `--pdb` |
| Documentation exécutable | `--doctest-modules` |
| Mesurer | `--cov=paquet --cov-report=term-missing --cov-fail-under=N` |
| Accélérer | `-n auto`, à condition d'avoir des tests indépendants |
| CI | `--strict-markers --strict-config -W error --junitxml`, lire le code de sortie |

## Exercices

1. **Test le plus lent.** Lancer `--durations=3` sur ce TP et identifier le
   test le plus lent et sa phase.

   Indice / corrigé : `test_plus_lent`, phase `call`, 0,16 s. Ajouter une
   fixture avec `time.sleep(0.2)` pour voir apparaître une ligne `setup`.

2. **Cycle `--lf` / `--sw`.** Faire échouer `test_serie[3]`, puis enchaîner
   `pytest`, `pytest --lf`, `pytest --sw`, corriger, `pytest --sw`.

   Indice / corrigé : remplacer `assert n < 5` par `assert n != 3`. Le
   deuxième `--sw` affiche `stepwise: skipping N already passed items`. Ne pas
   oublier de remettre l'assertion d'origine.

3. **`xfail_strict = true`.** Ajouter la clé dans `pyproject.toml` et lancer
   le TP05.

   Indice / corrigé : `test_xfail_conditionnel` (marqué `strict=False`
   explicitement) n'est pas affecté, mais tout `xfail` qui passerait
   deviendrait `FAILED [XPASS(strict)]`. Dans le TP05 tous les xfail échouent
   réellement, donc rien ne change ; corriger `fonction_buggee` pour voir la
   différence. Retirer la clé ensuite.

4. **Rapport HTML de couverture.** Générer le rapport du TP11 et repérer ce
   qui est exclu.

   Indice / corrigé : `uv run pytest tp11_projet --cov=tp11_projet/stock --cov-report=html`
   puis ouvrir `htmlcov/index.html`. La ligne `if __name__ == "__main__"` de
   `cli.py` est grisée par le `# pragma: no cover`.

5. **Doctest faux.** Ajouter un exemple incorrect dans `outils.py` et le
   voir échouer.

   Indice / corrigé : ajouter `>>> slugifier("A B")` suivi de `'a_b'` ;
   `--doctest-modules` affiche `Expected: 'a_b'` et `Got: 'a-b'`.

6. **Code de sortie 5.** Écrire une commande qui ne collecte rien et afficher
   son code de sortie ; puis trouver l'option qui rend ce cas non bloquant.

   Indice / corrigé : `uv run pytest -k nexistepas; echo $?` affiche 5. Il
   n'existe pas d'option intégrée pour le neutraliser : soit le script de CI
   accepte ce code (`uv run pytest ... || [ $? -eq 5 ]`), soit un hook
   `pytest_sessionfinish` remplace `session.exitstatus` 5 par 0 (TP10).

## Transition vers le TP suivant

Le conftest racine de ce projet contient déjà deux hooks, `pytest_addoption`
et `pytest_report_header`, et charge un plugin. Le TP10 explique ce mécanisme
d'extension et montre comment modifier la collecte, le rapport et les
messages d'échec.
