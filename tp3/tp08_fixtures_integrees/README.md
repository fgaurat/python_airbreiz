# TP08 – Fixtures intégrées

## En une phrase

pytest livre en standard une dizaine de fixtures prêtes à l'emploi pour les
besoins récurrents des tests : fichiers temporaires, capture de la sortie
standard, capture des logs, avertissements, cache persistant et accès à la
configuration. Ce TP les passe en revue une par une sur du code réaliste.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- créer des fichiers de test dans un répertoire jetable avec `tmp_path`, et
  dans un scope plus large avec `tmp_path_factory` ;
- vérifier ce qu'un programme affiche avec `capsys`, et choisir `capfd` quand
  la sortie ne passe pas par Python ;
- vérifier ce qu'un programme journalise avec `caplog`, en réglant le niveau
  capturé ;
- exiger ou compter des avertissements avec `pytest.warns` et `recwarn` ;
- persister une valeur entre deux exécutions avec `cache` ;
- lire les options et la configuration avec `pytestconfig` ;
- retrouver la liste et la documentation de toutes les fixtures avec
  `pytest --fixtures`.

## Prérequis

- TP03 (fixtures : injection par nom, `yield`, scopes, `conftest.py`).
- TP06 (`monkeypatch`) et TP07 (`mocker`) sont eux aussi des fixtures
  intégrées ; ils ne sont pas repris ici.
- Notions de base de `logging` et de `warnings` de la bibliothèque standard.

## Fichiers

| Fichier | Rôle |
|---|---|
| `fichiers.py` | Code métier : écriture et lecture CSV, affichage avec `print`, journalisation avec `logging`, fonction obsolète qui émet un `DeprecationWarning` |
| `conftest.py` | Fixture `gros_fichier` de scope session, construite avec `tmp_path_factory` |
| `test_fixtures_integrees.py` | Huit sections, une par fixture |

## Mise en route

```bash
uv run pytest tp08_fixtures_integrees -v
```

Sortie attendue : `19 passed` en moins de 0,2 s.

Avant d'ouvrir le code, lancer la commande qui liste les fixtures :

```bash
uv run pytest tp08_fixtures_integrees --fixtures -q
```

Extrait réel (noms et fichiers d'origine) :

```
cache -- .venv/lib/python3.13/site-packages/_pytest/cacheprovider.py:560
capsys -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1007
capsysbinary -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1070
capfd -- .venv/lib/python3.13/site-packages/_pytest/capture.py:1098
doctest_namespace [session scope] -- .venv/lib/python3.13/site-packages/_pytest/doctest.py:721
pytestconfig [session scope] -- .venv/lib/python3.13/site-packages/_pytest/fixtures.py:1564
record_property -- .venv/lib/python3.13/site-packages/_pytest/junitxml.py:275
tmpdir -- .venv/lib/python3.13/site-packages/_pytest/legacypath.py:305
caplog -- .venv/lib/python3.13/site-packages/_pytest/logging.py:611
monkeypatch -- .venv/lib/python3.13/site-packages/_pytest/monkeypatch.py:36
recwarn -- .venv/lib/python3.13/site-packages/_pytest/recwarn.py:37
tmp_path_factory [session scope] -- .venv/lib/python3.13/site-packages/_pytest/tmpdir.py:276
tmp_path -- .venv/lib/python3.13/site-packages/_pytest/tmpdir.py:291
mocker -- .venv/lib/python3.13/site-packages/pytest_mock/plugin.py:463
env [session scope] -- conftest.py:37
gros_fichier [session scope] -- tp08_fixtures_integrees/conftest.py:5
```

À faire remarquer : les fixtures intégrées, celles des plugins (`mocker`) et
celles du projet (`env`, `gros_fichier`) apparaissent dans la même liste. Il
n'y a pas de différence de nature : une fixture intégrée est une fixture
définie par un plugin livré avec pytest. Sans `-q`, la commande affiche aussi
la docstring de chaque fixture.

## Déroulé de la présentation

Commencer par `fichiers.py`, deux minutes suffisent : `ecrire_csv` et
`lire_csv` manipulent des fichiers, `afficher_rapport` écrit sur `stdout` et
`stderr`, `traiter` journalise à trois niveaux différents, `ancienne_fonction`
émet un avertissement de dépréciation. Chaque fonction a été écrite pour
donner du travail à une fixture précise.

### Section 1 : `tmp_path`, un répertoire temporaire par test

**Ce que montre le code.** `test_tmp_path_est_vide_et_unique` vérifie trois
propriétés : c'est un répertoire, il est vide, et son chemin contient le nom
du test. `test_aller_retour_csv` fait le cas d'usage typique : construire un
chemin avec l'opérateur `/`, écrire, relire.

```python
def test_aller_retour_csv(tmp_path):
    fichier = tmp_path / "personnes.csv"
    ecrire_csv(fichier, LIGNES)
    assert lire_csv(fichier) == LIGNES
```

**À dire aux stagiaires.** `tmp_path` est un `pathlib.Path`, pas une chaîne.
Il est de scope `function` : chaque test reçoit son propre répertoire, il n'y
a donc jamais de collision entre tests ni besoin de nettoyer. Le code testé
reçoit un chemin ordinaire et ne sait pas qu'il est en test.

**À montrer en direct.** Faire afficher le chemin en ajoutant `print(tmp_path)`
et en lançant avec `-s`. Sur macOS il ressemble à
`/var/folders/.../T/pytest-of-fgaurat/pytest-44/test_tmp_path_est_vide_et0`,
sur Linux à `/tmp/pytest-of-<user>/pytest-N/...`. Puis lister le dossier
parent :

```bash
ls -la $TMPDIR/pytest-of-$(whoami)/        # macOS
ls -la /tmp/pytest-of-$(whoami)/           # Linux
```

On voit `pytest-42`, `pytest-43`, `pytest-44` et un lien symbolique
`pytest-current` vers le dernier. pytest conserve les trois dernières
exécutions et supprime les plus anciennes : après un échec, on peut aller
regarder les fichiers produits.

**Pièges et erreurs fréquentes.**
- Écrire dans le répertoire courant ou dans `/tmp` à la main : les tests
  deviennent dépendants de l'ordre et laissent des déchets.
- Concaténer avec `+` au lieu de `/` : `tmp_path + "x"` lève `TypeError`.
- Passer `tmp_path` à une API qui exige une chaîne : `str(tmp_path)`.
- Option `--basetemp=chemin` pour imposer l'emplacement (attention, ce
  répertoire est vidé au démarrage).

### Section 2 : `tmp_path_factory`, pour les scopes larges

**Ce que montre le code.** Dans `conftest.py`, `gros_fichier` est de scope
`session` : elle ne peut pas dépendre de `tmp_path` qui est de scope
`function` (règle du TP03 : une fixture dépend d'un scope égal ou plus
large). Elle passe donc par la fabrique :

```python
@pytest.fixture(scope="session")
def gros_fichier(tmp_path_factory):
    dossier = tmp_path_factory.mktemp("donnees")
    chemin = dossier / "gros.txt"
    chemin.write_text("\n".join(f"ligne {i}" for i in range(1500)), encoding="utf-8")
    return chemin
```

`test_gros_fichier` et `test_gros_fichier_partage` reçoivent le même chemin.

**À dire aux stagiaires.** `mktemp("donnees")` crée `donnees0`, puis
`donnees1` au second appel, dans le même répertoire de session que les
`tmp_path`. C'est l'outil pour un jeu de données coûteux à générer, ou un
fichier partagé par toute une classe de tests. En contrepartie, si un test
modifie le fichier, les suivants le voient : réserver cet usage aux données
en lecture seule.

**À montrer en direct.** Demander `tmp_path` dans une fixture `session` pour
provoquer l'erreur :

```
ScopeMismatch: You tried to access the function scoped fixture tmp_path
with a session scoped request object
```

**Pièges et erreurs fréquentes.** `tmp_path_factory.getbasetemp()` renvoie
la racine de la session ; ne pas y écrire directement, utiliser `mktemp`.

### Section 3 : `capsys` et `capfd`, capturer la sortie standard

**Ce que montre le code.** `test_capsys` appelle `afficher_rapport` puis lit
la capture :

```python
capture = capsys.readouterr()
assert capture.out.splitlines() == ["Rapport : 2 enregistrement(s)", ...]
assert capture.err == ""
```

`test_capsys_stderr` vérifie qu'un message part bien sur `stderr` et pas sur
`stdout`. `test_capsys_lecture_incrementale` montre que `readouterr()` vide le
tampon : la seconde lecture ne contient que ce qui a été écrit depuis la
première. `test_capfd` écrit directement sur le descripteur 1 avec
`os.write` : `capsys` ne le verrait pas, `capfd` oui.

**À dire aux stagiaires.** `readouterr()` renvoie un tuple nommé `(out, err)`.
Il faut le stocker dans une variable si on veut vérifier les deux champs,
sinon le second appel renvoie du vide. `capsys` remplace `sys.stdout` et
`sys.stderr` par des objets Python : il voit tout ce qui passe par `print` ou
`sys.stdout.write`. `capfd` remplace les descripteurs de fichier 1 et 2 au
niveau du système : il voit en plus les sous-processus et les bibliothèques C.
Il existe aussi `capsysbinary` et `capfdbinary` qui renvoient des `bytes`.

Nuance à ne pas rater : l'option `-s` désactive la capture globale de pytest,
celle qui masque les `print` des tests qui passent. `capsys` installe sa propre
capture pour le test qui la demande et continue de fonctionner avec `-s` : on
peut le vérifier avec `uv run pytest tp08_fixtures_integrees -k test_capsys -s`
qui passe toujours.

**À montrer en direct.** Demander `capsys` et `capfd` dans le même test. Erreur
réelle :

```
E       cannot use capfd and capsys at the same time
```

Puis, dans `test_capsys`, remplacer `afficher_rapport(LIGNES)` par
`afficher_rapport(LIGNES[:1])` pour voir la différence de liste affichée par
l'introspection des assertions.

**Pièges et erreurs fréquentes.**
- Oublier `.out` et comparer le tuple à une chaîne.
- Oublier le `\n` final : `print("un")` produit `"un\n"`.
- Tester l'affichage plutôt que la valeur de retour : si la fonction peut
  renvoyer la donnée, préférer tester la donnée. `capsys` est fait pour les
  interfaces en ligne de commande (voir `test_cli.py` du TP11).

### Section 4 : `caplog`, capturer les logs

**Ce que montre le code.** `test_caplog_texte` se contente de `caplog.text`,
la sortie formatée complète. `test_caplog_records` est le test à détailler :

```python
with caplog.at_level(logging.DEBUG, logger="fichiers"):
    n = traiter(gros_fichier)

niveaux = [r.levelname for r in caplog.records]
assert niveaux == ["DEBUG", "WARNING", "INFO"]
assert ("fichiers", logging.WARNING, "fichier volumineux (1500 lignes)") in caplog.record_tuples
```

`test_caplog_set_level_et_clear` montre que `set_level(WARNING)` fait
disparaître un `INFO`, et que `clear()` vide la liste.

**À dire aux stagiaires.** `caplog` ajoute un handler sur le logger racine et
enregistre tout ce qui lui parvient. Le niveau capturé par défaut est celui
des loggers eux-mêmes, en général `WARNING` pour le logger racine : un
`logger.info(...)` n'apparaît pas tant qu'on n'a pas appelé
`caplog.set_level(logging.INFO)` ou ouvert un bloc `caplog.at_level(...)`.
C'est la première cause de "mon log n'est pas capturé". Le paramètre `logger=`
permet de ne régler qu'un logger précis. Trois vues sur le même contenu :
`caplog.text` (chaîne formatée avec le `log_format` du `pyproject.toml`),
`caplog.records` (objets `LogRecord`, avec `levelname`, `levelno`, `name`,
`getMessage()`, `exc_info`), `caplog.record_tuples` (liste de tuples
`(nom_du_logger, niveau, message)`, la forme la plus pratique pour une
assertion d'égalité). Il existe aussi `caplog.messages` (messages seuls).

Si un logger a `propagate = False`, ses messages ne remontent pas jusqu'au
handler de `caplog` et ne sont pas capturés.

**À montrer en direct.** Voir les logs défiler en temps réel :

```bash
uv run pytest tp08_fixtures_integrees -k caplog_records --log-cli-level=DEBUG
```

Sortie réelle :

```
tp08_fixtures_integrees/test_fixtures_integrees.py::test_caplog_records
-------------------------------- live log call ---------------------------------
07:38:41 DEBUG    fichiers: début du traitement de .../donnees0/gros.txt
07:38:41 WARNING  fichiers: fichier volumineux (1500 lignes)
07:38:41 INFO     fichiers: traitement terminé : 1500 lignes
PASSED
```

Le format `HH:MM:SS NIVEAU logger: message` vient des clés `log_format` et
`log_date_format` du `pyproject.toml`. Montrer aussi qu'un test qui échoue
affiche automatiquement une section "Captured log call" dans son rapport,
sans rien demander : c'est souvent suffisant pour diagnostiquer.

**Pièges et erreurs fréquentes.**
- Oublier `set_level` et conclure que le code ne journalise pas.
- Comparer `caplog.text` à une chaîne exacte : le format contient l'heure.
  Utiliser `in`, ou `record_tuples`.
- `caplog.records` cumule setup, call et teardown ; `caplog.get_records("call")`
  isole une phase.

### Section 5 : avertissements, `pytest.warns` et `recwarn`

**Ce que montre le code.** `test_pytest_warns` exige un `DeprecationWarning`
dont le message correspond à la regex `"obsolète"`. `test_recwarn` laisse le
test se dérouler, puis inspecte la liste : longueur, `pop(DeprecationWarning)`
qui renvoie le premier avertissement de ce type. `test_aucun_avertissement`
prend le chemin inverse avec la bibliothèque standard :
`warnings.simplefilter("error")` transforme tout avertissement en exception.

**À dire aux stagiaires.** `pytest.warns` est le symétrique de
`pytest.raises` : le bloc échoue si l'avertissement attendu n'est pas émis.
`recwarn` est l'outil d'observation : rien n'est exigé, on compte et on
inspecte. Le `warnings.simplefilter("always")` dans `test_recwarn` est là
parce que Python n'émet un `DeprecationWarning` identique qu'une seule fois
par emplacement de code par défaut ; sans ce filtre, le second appel ne
produirait rien.

Troisième niveau, global : la clé `filterwarnings` du `pyproject.toml`.
`filterwarnings = ["error::DeprecationWarning"]` fait échouer tout test qui
déclenche une dépréciation non gérée. C'est la configuration recommandée en
intégration continue pour ne pas découvrir une API supprimée le jour de la
mise à jour d'une dépendance.

**À montrer en direct.** Retirer le `stacklevel=2` de `ancienne_fonction`
puis regarder, avec `-W error`, l'emplacement signalé : sans `stacklevel`,
l'avertissement pointe dans `fichiers.py` au lieu de pointer chez l'appelant.

**Pièges et erreurs fréquentes.**
- Un avertissement émis mais déjà vu : `pytest.warns` échoue avec
  `DID NOT WARN`. Ajouter `warnings.simplefilter("always")` ou utiliser le
  paramètre `-W always`.
- Confondre le résumé "warnings summary" en fin de rapport (avertissements
  non capturés, informatifs) avec un échec.

### Section 6 : `cache`, persister entre deux exécutions

**Ce que montre le code.** `test_cache` lit un compteur, l'incrémente et le
réécrit :

```python
precedent = cache.get("tp08/executions", 0)
cache.set("tp08/executions", precedent + 1)
```

**À dire aux stagiaires.** Les valeurs sont sérialisées en JSON dans le
répertoire `.pytest_cache/` à la racine du projet, à ajouter au `.gitignore`.
Les clés sont des chemins : préfixer par le nom du projet ou du plugin. C'est
exactement le mécanisme derrière `--lf` et `--ff` : pytest y stocke la liste
des derniers échecs sous la clé `cache/lastfailed`, et `--sw` y stocke sa
position sous `cache/stepwise`. Cas d'usage pour un projet : mémoriser un
résultat coûteux entre deux lancements, comme la version d'un service ou un
jeu de données téléchargé.

**À montrer en direct.**

```bash
uv run pytest tp08_fixtures_integrees -k test_cache -q
uv run pytest tp08_fixtures_integrees -k test_cache -q
uv run pytest --cache-show
```

Sortie réelle abrégée :

```
cachedir: /Users/fgaurat/local_dev/formations/prep/formation-pytest/.pytest_cache
----------------------------- cache values for '*' -----------------------------
cache/lastfailed contains:
  {'tp01_bases/demo_echecs.py::test_echec_approx': True,
   'tp01_bases/demo_echecs.py::test_echec_chaine_longue': True,
   ...
cache/nodeids contains:
  [...]
tp08/executions contains:
  7
```

Le compteur `tp08/executions` augmente à chaque lancement. Puis désactiver le
plugin qui fournit la fixture :

```bash
uv run pytest tp08_fixtures_integrees -k test_cache -p no:cacheprovider
```

Erreur réelle :

```
E       fixture 'cache' not found
>       available fixtures: capfd, capfdbinary, caplog, capsys, capsysbinary, ...
>       use 'pytest --fixtures [testpath]' for help on them.
```

C'est l'occasion de dire que chaque fixture intégrée appartient à un plugin
interne, désactivable, et que ce message "fixture not found" avec la liste des
fixtures disponibles est celui qu'on obtient pour toute faute de frappe dans
un nom de fixture.

**Pièges et erreurs fréquentes.** Un `.pytest_cache/` versionné par erreur ;
un cache incohérent après un renommage de tests, à vider avec `--cache-clear`.

### Section 7 : `pytestconfig` et `request.config`

**Ce que montre le code.** `test_pytestconfig` lit quatre choses :

```python
pytestconfig.rootpath.name           # "formation-pytest"
pytestconfig.getini("pythonpath")    # [Path(rootpath)] : "." résolu en absolu
pytestconfig.getoption("--env")      # option maison du conftest racine
pytestconfig.getini("markers")       # la liste déclarée dans pyproject.toml
```

`test_request_config` montre que `request.config` est le même objet.

**À dire aux stagiaires.** `pytestconfig` est de scope session ; c'est l'objet
`Config` que reçoivent aussi les hooks (TP10). `getoption("nom")` lit une
option de ligne de commande, `getini("cle")` une clé de configuration,
`rootpath` la racine du projet, `invocation_params.args` les arguments tels
que tapés, `inipath` le fichier de configuration trouvé. Usage typique : une
fixture qui adapte son comportement à `--env`, ou qui construit un chemin
relatif à la racine du projet plutôt qu'au répertoire courant.

**À montrer en direct.**

```bash
uv run pytest tp08_fixtures_integrees -k pytestconfig --env staging
```

Le test passe toujours, et l'en-tête du rapport affiche
`Formation pytest -- environnement : staging` grâce au hook
`pytest_report_header` du conftest racine.

**Pièges et erreurs fréquentes.** `getoption("--env")` et `getoption("env")`
fonctionnent tous les deux ; en revanche `getoption("inconnue")` lève
`ValueError: no option named 'inconnue'`. Une option définie dans un
`conftest.py` qui n'est pas à la racine n'est pas garantie d'exister au
moment où on la lit : c'est pour cela que `--env` est déclarée dans le
`conftest.py` racine (détails au TP10).

### Section 8 : les autres fixtures intégrées

**Ce que montre le code.** `test_env` utilise la fixture `env` du conftest
racine, pour rappeler qu'une fixture maison se consomme exactement comme une
fixture intégrée.

**À dire aux stagiaires.** Liste des fixtures intégrées non illustrées dans
ce TP, pour que personne ne les découvre par hasard :

| Fixture | Rôle |
|---|---|
| `monkeypatch` | TP06 |
| `mocker` (plugin pytest-mock) | TP07 |
| `request` | contexte du test, TP03 |
| `capsysbinary`, `capfdbinary` | comme `capsys` / `capfd` mais en `bytes` |
| `capteesys` | capture qui laisse aussi passer la sortie vers le terminal (pytest 8.4+) |
| `doctest_namespace` | injecter des noms dans l'espace des doctests (TP09) |
| `record_property`, `record_testsuite_property` | ajouter des métadonnées au rapport JUnit XML (`--junitxml`) |
| `record_xml_attribute` | idem, sous forme d'attribut |
| `tmpdir`, `tmpdir_factory` | ancêtres de `tmp_path`, renvoient un `py.path.local` ; à ne plus utiliser |
| `pytester` (ex `testdir`) | lancer pytest dans pytest, pour tester un plugin ; activer avec `-p pytester` |

## Questions fréquentes des stagiaires

**Où vont les fichiers de `tmp_path` et sont-ils supprimés ?**
Dans `pytest-of-<utilisateur>/pytest-N/` sous le répertoire temporaire du
système. pytest garde les trois dernières exécutions et efface les plus
anciennes au démarrage suivant. `--basetemp` impose un autre emplacement.

**Puis-je utiliser `tmp_path` dans une fixture de scope module ?**
Non, `ScopeMismatch`. Utiliser `tmp_path_factory.mktemp("nom")`.

**Pourquoi mon `logger.info` n'apparaît pas dans `caplog` ?**
Le niveau effectif du logger est `WARNING` par défaut. Appeler
`caplog.set_level(logging.INFO)` ou utiliser `with caplog.at_level(...)`. Si
le logger a `propagate = False`, les messages ne remontent pas.

**`capsys` ou `capfd` ?**
`capsys` pour du code Python qui fait `print`. `capfd` si le code lance un
sous-processus ou appelle une bibliothèque C qui écrit sur le descripteur.
Jamais les deux dans le même test.

**Est-ce que `-s` empêche `capsys` de fonctionner ?**
Non. `-s` désactive la capture globale (les `print` des tests s'affichent),
mais `capsys` met en place sa propre capture pour le test qui le demande.

**`pytest.warns` ou `recwarn` ?**
`pytest.warns` quand l'avertissement est un comportement attendu et exigé.
`recwarn` quand on veut compter, inspecter ou vérifier l'absence
d'avertissement (`len(recwarn) == 0`).

**Que contient `.pytest_cache/` et faut-il le versionner ?**
Les derniers échecs (`--lf`), les node ids, la position `--sw`, et vos
propres valeurs via `cache.set`. Ne pas le versionner.

**Comment lire une option maison dans un test ?**
`pytestconfig.getoption("--env")`, ou via une fixture dédiée comme `env` dans
le conftest racine. L'option doit être déclarée avec `pytest_addoption` dans
le conftest racine ou un plugin.

**Y a-t-il une fixture pour les tests réseau, les bases de données ?**
Pas dans pytest lui-même. Ce sont des plugins : `pytest-httpserver`,
`responses`, `pytest-django`, `pytest-postgresql`, ou des conteneurs (TP13).

## Ce qu'il faut retenir

| Fixture | Renvoie | Quand l'utiliser | Point d'attention |
|---|---|---|---|
| `tmp_path` | `pathlib.Path` vide, unique par test | tout test qui touche au disque | conservation des 3 dernières exécutions |
| `tmp_path_factory` | fabrique, `mktemp("nom")` | fixtures de scope class / module / session | données en lecture seule |
| `capsys` | `.readouterr()` → `(out, err)` | CLI, `print` | `readouterr()` vide le tampon |
| `capfd` | idem au niveau descripteur | sous-processus, code C | incompatible avec `capsys` dans un même test |
| `caplog` | `.text`, `.records`, `.record_tuples`, `.messages` | vérifier la journalisation | `set_level` / `at_level` obligatoires sous WARNING |
| `pytest.warns` | gestionnaire de contexte | exiger un avertissement | `DID NOT WARN` si déjà émis une fois |
| `recwarn` | liste d'avertissements | compter, inspecter | `simplefilter("always")` |
| `cache` | `.get(cle, defaut)`, `.set(cle, valeur)` | persister entre exécutions | JSON, `.pytest_cache/` à ignorer en git |
| `pytestconfig` | objet `Config` | options, clés ini, `rootpath` | `getoption` sur une option inconnue lève `ValueError` |

## Exercices

1. **Arborescence dans `tmp_path`.** Créer `a/b/c.txt` avec trois lignes et
   vérifier `compter_lignes`.

   Indice / corrigé :
   ```python
   def test_arborescence(tmp_path):
       fichier = tmp_path / "a" / "b" / "c.txt"
       fichier.parent.mkdir(parents=True)
       fichier.write_text("1\n2\n3\n", encoding="utf-8")
       assert compter_lignes(fichier) == 3
   ```

2. **Aucun WARNING sur un petit fichier.** Vérifier que `traiter` sur un
   fichier de 10 lignes n'émet aucun avertissement de niveau WARNING ou plus.

   Indice / corrigé : filtrer sur `levelno`, penser au niveau capturé.
   ```python
   def test_petit_fichier_sans_alerte(caplog, tmp_path):
       fichier = tmp_path / "petit.txt"
       fichier.write_text("\n".join("x" * 10), encoding="utf-8")
       with caplog.at_level(logging.DEBUG, logger="fichiers"):
           traiter(fichier)
       assert not [r for r in caplog.records if r.levelno >= logging.WARNING]
   ```

3. **CSV partagé par un module.** Écrire une fixture de scope `module` qui
   produit un CSV via `tmp_path_factory` et l'utiliser dans deux tests.

   Indice / corrigé :
   ```python
   @pytest.fixture(scope="module")
   def csv_personnes(tmp_path_factory):
       chemin = tmp_path_factory.mktemp("csv") / "personnes.csv"
       ecrire_csv(chemin, LIGNES)
       return chemin

   def test_lecture(csv_personnes):
       assert len(lire_csv(csv_personnes)) == 2

   def test_lignes(csv_personnes):
       assert compter_lignes(csv_personnes) == 3
   ```

4. **`filterwarnings = ["error"]`.** Activer cette clé dans `pyproject.toml`,
   lancer le TP et observer.

   Indice / corrigé : `test_recwarn` échoue car ses appels à
   `ancienne_fonction` ne sont pas dans un `pytest.warns` ; l'avertissement
   devient une exception. Le corriger en entourant les appels d'un
   `with pytest.warns(DeprecationWarning):`, ou en marquant le test
   `@pytest.mark.filterwarnings("always::DeprecationWarning")`. Retirer la clé
   ensuite pour ne pas impacter les autres TPs.

5. **Sortie d'un sous-processus.** Écrire un test qui lance
   `subprocess.run([sys.executable, "-c", "print('hello')"])` sans capturer
   dans `subprocess`, et vérifier la sortie avec la bonne fixture.

   Indice / corrigé : `capsys` ne voit pas le sous-processus, `capfd` oui.
   ```python
   def test_sous_processus(capfd):
       subprocess.run([sys.executable, "-c", "print('hello')"], check=True)
       assert capfd.readouterr().out == "hello\n"
   ```

## Transition vers le TP suivant

Toutes ces fixtures se pilotent aussi par la configuration : `log_format`,
`filterwarnings`, `--basetemp`, `--cache-clear`. Le TP09 ouvre le
`pyproject.toml` et fait le tour des options qui règlent le comportement de
pytest pour tout le projet.
