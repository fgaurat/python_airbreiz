# TP05 – Les marqueurs

## En une phrase

Un marqueur est une étiquette posée sur un test pour changer son traitement
(`skip`, `xfail`), le sélectionner (`-m lent`) ou lui transmettre des
données ; avec `--strict-markers`, pytest refuse toute étiquette non déclarée.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- lire les lettres du rapport (`.`, `F`, `E`, `s`, `x`, `X`) et le résumé `-ra` ;
- ignorer un test avec `skip`, `skipif`, `pytest.skip()`, `pytest.importorskip()` ;
- déclarer un échec attendu avec `xfail` et choisir `strict`, `raises`, `run` ;
- créer des marqueurs personnalisés, les déclarer, les combiner avec `-m` ;
- marquer une fonction, une classe, un module (`pytestmark`), un cas de `parametrize` ;
- lire un marqueur et ses arguments depuis une fixture (`get_closest_marker`, `iter_markers`).

## Prérequis

- TP01 : rapport, `-k`, `pytest.raises`.
- TP03 : fixtures et objet `request` (section 5 et 6).
- TP04 : `pytest.param(marks=...)` a déjà montré `skip` et `xfail` sur un cas.

## Fichiers

| Fichier | Rôle |
|---|---|
| `traitement.py` | `calcul_lourd` (0,2 s), `telecharger` (lève `ConnectionError`), `charger_donnees`, `fonction_buggee` (bug volontaire sur les négatifs) |
| `test_marqueurs.py` | Six sections : skip, xfail, marqueurs personnalisés, classe, marqueur avec arguments, introspection |
| `test_module_marque.py` | `pytestmark` : marquer tout un module |
| `../pyproject.toml` | Section `markers` et `--strict-markers` dans `addopts` |

## Mise en route

```bash
uv run pytest tp05_marqueurs -q -ra
```

Sortie attendue (résumé) :

```
SKIPPED [1] tp05_marqueurs/test_marqueurs.py:27: fonctionnalité pas encore implémentée
SKIPPED [1] tp05_marqueurs/test_marqueurs.py:37: nécessite Python 3.14+
SKIPPED [1] tp05_marqueurs/test_marqueurs.py:45: uniquement sur Android
SKIPPED [1] tp05_marqueurs/test_marqueurs.py:51: could not import 'module_qui_n_existe_pas': ...
XFAIL tp05_marqueurs/test_marqueurs.py::test_xfail_bug_connu - bug #42 : les négatifs ne sont pas doublés
XFAIL tp05_marqueurs/test_marqueurs.py::test_xfail_strict - on s'attend à un échec
XFAIL tp05_marqueurs/test_marqueurs.py::test_xfail_raises - pas de réseau en formation
XFAIL tp05_marqueurs/test_marqueurs.py::test_xfail_run_false - [NOTRUN] fait planter l'interpréteur, ne pas exécuter
XFAIL tp05_marqueurs/test_marqueurs.py::test_xfail_conditionnel - xfail conditionnel
XFAIL tp05_marqueurs/test_marqueurs.py::test_xfail_dynamique - bug encore présent
XFAIL tp05_marqueurs/test_marqueurs.py::test_reseau
12 passed, 4 skipped, 7 xfailed in 0.56s
```

Tout est vert : les skips et xfails sont le sujet du TP, pas des problèmes.
Le `-ra` est déjà dans `addopts` ; le répéter en commande est inoffensif.

## Déroulé de la présentation

### Le code métier : `traitement.py`

Quatre fonctions choisies pour donner une **raison** à chaque marqueur :
`calcul_lourd` dort 0,2 s (marqueur `lent`), `telecharger` lève toujours
`ConnectionError` (réseau absent en formation, `xfail(raises=...)`),
`charger_donnees` fabrique des lignes à partir d'un nom de fichier (marqueur
avec argument), `fonction_buggee` renvoie `x` au lieu de `x * 2` pour les
négatifs (bug connu, `xfail`). Le bug est volontaire : ne pas le corriger
avant l'exercice 2.

Commencer par le tableau des lettres :

| Lettre | Résultat | Signification |
|---|---|---|
| `.` | PASSED | le test a réussi |
| `F` | FAILED | un `assert` est faux, ou `pytest.fail()` |
| `E` | ERROR | exception hors du test : fixture, hook, collecte |
| `s` | SKIPPED | non exécuté |
| `x` | XFAILED | exécuté, a échoué, et c'était attendu |
| `X` | XPASSED | exécuté, a réussi, alors qu'on attendait un échec |

### Section 1 : `skip` et `skipif`, ne pas exécuter

**Ce que montre le code.**

```python
@pytest.mark.skip(reason="fonctionnalité pas encore implémentée")
def test_skip_inconditionnel():
    raise AssertionError("ne doit jamais s'exécuter")

@pytest.mark.skipif(sys.platform == "win32", reason="chemins POSIX uniquement")
def test_skipif_plateforme(): ...

@pytest.mark.skipif(sys.version_info < (3, 14), reason="nécessite Python 3.14+")
def test_skipif_version_python(): ...
```

Puis les formes **dynamiques** : `pytest.skip("...")` à l'intérieur du test
(`test_skip_dynamique`) et `pytest.importorskip("module")` qui renvoie le
module s'il existe, sinon skippe (`test_importorskip`).

**À dire aux stagiaires.**

- `reason` est obligatoire en pratique : c'est ce qu'on lit dans `-ra`.
  Un skip sans raison est une dette invisible.
- La condition de `skipif` est évaluée **à la collecte**, une seule fois
  par test, dans l'ordre du fichier. `pytest.skip()` est évalué **pendant**
  le test : utile quand la décision dépend d'une fixture ou d'une ressource.
- La condition peut aussi être une **chaîne** évaluée par pytest avec
  `sys`, `os`, `platform`, `config` disponibles :
  `@pytest.mark.skipif("config.getoption('--env') == 'prod'")` (utilisé au TP11).
- Un test skippé ne coûte rien mais **ne prouve rien** : un `skip` oublié
  pendant six mois est un test mort.

**À montrer en direct.**

```bash
uv run pytest tp05_marqueurs -k "skip or importorskip" -v -ra
```

Remplacer `"module_qui_n_existe_pas"` par `"json"` dans `test_importorskip`
et relancer : le test s'exécute (et passe, il ne fait rien d'autre).

**Pièges et erreurs fréquentes.**

- `@pytest.mark.skip` sans parenthèses fonctionne, `@pytest.mark.skipif` sans
  condition lève une erreur.
- Écrire `pytest.skip` sans parenthèses dans le corps : ne fait rien.
- Confondre skip (choix) et xfail (constat d'échec).

### Section 2 : `xfail`, l'échec attendu

**Ce que montre le code.** Six variantes :

| Test | Option | Comportement |
|---|---|---|
| `test_xfail_bug_connu` | `reason` | s'exécute, échoue, compté `x` |
| `test_xfail_strict` | `strict=True` | s'il **passe**, c'est un FAILED (`[XPASS(strict)]`) |
| `test_xfail_raises` | `raises=ConnectionError` | seule cette exception est un échec attendu ; une autre serait un vrai `F` |
| `test_xfail_run_false` | `run=False` | jamais exécuté, marqué `[NOTRUN]` : pour un test qui plante l'interpréteur |
| `test_xfail_conditionnel` | condition en premier argument | xfail uniquement si la condition est vraie |
| `test_xfail_dynamique` | `pytest.xfail("...")` dans le corps | décidé pendant le test |

**À dire aux stagiaires.**

- `xfail` documente un **bug connu** ou une fonctionnalité en cours : le test
  reste dans la suite, on sait qu'il échoue, il ne casse pas la CI.
- `strict=True` est la bonne pratique : le jour où le bug est corrigé, le
  test passe, pytest le signale en échec, on retire le marqueur. Sans
  `strict`, l'`XPASS` passe inaperçu et le marqueur reste pour toujours.
  L'option ini `xfail_strict = true` rend tous les xfail stricts.
- `raises=` évite qu'un `xfail` cache une **autre** régression : si
  `telecharger` levait `TypeError` au lieu de `ConnectionError`, le test
  serait FAILED.
- `pytest.xfail()` arrête le test immédiatement (contrairement à un `assert`
  qui échoue et laisse pytest conclure).

**À montrer en direct.**

```bash
uv run pytest tp05_marqueurs -k xfail -v
uv run pytest tp05_marqueurs -k xfail --runxfail
```

`--runxfail` ignore les marqueurs xfail : les tests deviennent de vrais
échecs, utile pour déboguer. Puis corriger `fonction_buggee` :

```python
def fonction_buggee(x):
    return x * 2
```

Relancer `-k xfail -v` : `test_xfail_bug_connu` devient `XPASS`,
`test_xfail_strict` devient **FAILED** avec le message
`[XPASS(strict)] on s'attend à un échec`, `test_xfail_dynamique` passe (le
`if` n'appelle plus `pytest.xfail`). Remettre le bug ensuite.

**Pièges et erreurs fréquentes.**

- Utiliser `xfail` pour faire taire un test cassé sans comprendre pourquoi :
  c'est un skip déguisé. Toujours une `reason` avec référence de ticket.
- `raises` avec un tuple d'exceptions est accepté ; une liste ne l'est pas.
- `run=False` sans `reason` : peu lisible dans le rapport.

### Section 3 : marqueurs personnalisés et sélection `-m`

**Ce que montre le code.** `test_calcul_lourd` (`lent`),
`test_lent_et_integration` (`lent` + `integration`), `test_integration_seule`,
`test_reseau` (`reseau` + `xfail`), `test_sans_marqueur`.

Déclaration dans `pyproject.toml` :

```toml
addopts = "-ra --strict-markers"
markers = [
    "lent: test long a executer (desactivable avec -m 'not lent')",
    "integration: test necessitant une ressource externe (BDD, API...)",
    ...
]
```

**À dire aux stagiaires.**

- Un marqueur personnalisé n'a **aucun effet** par lui-même : c'est une
  étiquette. Il sert à sélectionner avec `-m`, ou à être lu par une fixture
  ou un hook (sections 5 et 6, TP10).
- `-m` accepte une expression booléenne : `and`, `or`, `not`, parenthèses.
  Contrairement à `-k`, `-m` compare des **noms exacts** : `-m len` ne
  sélectionne pas `lent` (0 test), alors que `-k len` sélectionne tout ce
  qui contient « len ».
- `--strict-markers` : sans lui, une faute de frappe (`@pytest.mark.lentt`)
  crée silencieusement un nouveau marqueur, le test sort de la sélection
  `-m lent`, et personne ne s'en aperçoit. Avec lui, la collecte échoue :
  ```
  ERROR collecting test session
  'lentt' not found in `markers` configuration option
  ```
- Deux façons de déclarer : la section `markers` du fichier de config, ou
  `config.addinivalue_line("markers", "chrono: ...")` dans `pytest_configure`
  (utilisé au TP10, pratique pour un plugin).

**À montrer en direct.**

```bash
uv run pytest tp05_marqueurs -m lent -v
uv run pytest tp05_marqueurs -m "not lent" -q
uv run pytest tp05_marqueurs -m "lent and not integration" -v
uv run pytest tp05_marqueurs -m "integration or bdd" --collect-only -q
uv run pytest tp05_marqueurs -m len -q            # 0 sélectionné : nom exact
uv run pytest --markers                           # liste des marqueurs, intégrés et déclarés
```

Modification en live : renommer un `@pytest.mark.lent` en `lentt`, relancer,
lire l'erreur, remettre.

**Pièges et erreurs fréquentes.**

- Oublier les guillemets autour d'une expression avec espaces :
  `-m not lent` est lu comme `-m not` puis un argument `lent` (chemin inexistant).
- Déclarer le marqueur avec sa description mais l'utiliser avec des arguments
  non prévus : autorisé, pytest ne vérifie que le nom.
- Croire que `-m lent` exécute **aussi** les tests non marqués : non, il ne
  garde que les marqués.

### Section 4 : marquer une classe, un module

**Ce que montre le code.** `@pytest.mark.bdd` sur `TestAvecBdd` : les deux
méthodes héritent du marqueur. `test_module_marque.py` :

```python
pytestmark = pytest.mark.integration   # ou une liste [pytest.mark.a, pytest.mark.b]
```

Tout test du module porte `integration` ; `test_b` le vérifie avec
`request.node.get_closest_marker("integration")`.

**À dire aux stagiaires.** Hiérarchie d'héritage des marqueurs : module →
classe → fonction → cas de `parametrize`. Un même test peut cumuler
plusieurs niveaux. Le nom `pytestmark` est réservé : pytest le cherche au
niveau module **et** comme attribut de classe.

**À montrer en direct.**

```bash
uv run pytest tp05_marqueurs -m bdd -v
uv run pytest tp05_marqueurs -m integration --collect-only -q
```

La seconde commande liste `test_lent_et_integration`,
`test_integration_seule` et les deux tests de `test_module_marque.py`.

**Pièges et erreurs fréquentes.**

- `pytestmark` dans un `conftest.py` : **aucun effet** (piège rencontré
  au TP13). Pour marquer un répertoire entier, utiliser le hook
  `pytest_collection_modifyitems` (TP10).
- Marquer une classe non préfixée `Test` : la classe n'est pas collectée,
  le marqueur ne sert à rien.

### Section 5 : marqueur avec arguments, lu par une fixture

**Ce que montre le code.**

```python
@pytest.fixture
def donnees(request):
    marqueur = request.node.get_closest_marker("donnees")
    if marqueur is None:
        pytest.fail("ce test doit être décoré avec @pytest.mark.donnees(...)")
    return charger_donnees(marqueur.args[0])

@pytest.mark.donnees("clients.csv")
def test_marqueur_avec_argument(donnees): ...
```

Le marqueur transporte une valeur ; la fixture la lit via `request.node`
(le test en cours) et construit la donnée. Déclaré dans `pyproject.toml`
comme `"donnees(fichier): ..."`.

**À dire aux stagiaires.** C'est une alternative élégante à un paramètre de
fixture : le test déclare **ce dont il a besoin** en une ligne, la fixture
fait le travail. Cas réels : `@pytest.mark.utilisateur(role="admin")`,
`@pytest.mark.fixture_sql("jeu_de_donnees.sql")`, `@pytest.mark.timeout(10)`
de pytest-timeout fonctionne exactement ainsi. `marqueur.args` est un tuple,
`marqueur.kwargs` un dict.

**À montrer en direct.**

```bash
uv run pytest tp05_marqueurs -k marqueur_avec -v
```

Retirer le décorateur d'un des deux tests et relancer : `pytest.fail` dans
la fixture donne un **ERROR** (pas un FAILED) puisque l'exception vient de
la fixture.

**Pièges et erreurs fréquentes.**

- `get_closest_marker` renvoie `None` si absent : toujours tester.
- Confondre `marqueur.args[0]` et `marqueur.args` (le tuple).

### Section 6 : lire ses propres marqueurs

**Ce que montre le code.**

```python
@pytest.mark.lent
@pytest.mark.bdd
def test_lister_ses_marqueurs(request):
    noms = {m.name for m in request.node.iter_markers()}
    assert {"lent", "bdd"} <= noms
```

**À dire aux stagiaires.** Deux API :

| Méthode | Renvoie | Usage |
|---|---|---|
| `request.node.get_closest_marker("nom")` | le marqueur le plus proche (fonction avant classe avant module), ou `None` | lire une valeur, avec priorité au plus spécifique |
| `request.node.iter_markers("nom")` ou sans argument | itérateur sur **tous** les marqueurs, du plus proche au plus lointain | cumuler, vérifier la présence |

L'ordre de `iter_markers` inclut les marqueurs hérités de la classe et du
module. Même API dans les hooks sur `item` (TP10 : `item.get_closest_marker("prioritaire")`).

**Pièges et erreurs fréquentes.** `request.node.keywords` contient aussi les
noms de marqueurs (c'est ce que `-k` interroge), mais mélangés aux noms de
test et de fixtures : préférer `iter_markers`.

## Questions fréquentes des stagiaires

**Quelle différence entre skip et xfail, concrètement ?**
Skip : le test n'est pas exécuté (prérequis absent, plateforme). Xfail : le
test est exécuté et son échec est documenté (bug connu). Le skip ne dit rien
sur le code, le xfail dit « ça échoue toujours ».

**Un test xfail qui passe fait-il échouer la CI ?**
Seulement avec `strict=True` (ou `xfail_strict = true` en config). Sinon
c'est un `X` dans le rapport, code de sortie 0.

**Peut-on skipper tout un fichier ?**
`pytestmark = pytest.mark.skip(...)` en tête de module, ou, pour arrêter
même l'import (dépendance absente) :
`pytest.skip("raison", allow_module_level=True)` avant les imports.
`pytest.importorskip("module")` au niveau module fait la même chose.

**Où voir les raisons de skip ?**
`-ra` (dans `addopts` ici) ou `-rs` pour les skips seulement, `-rx` pour les
xfails, `-rA` pour tout y compris les passed.

**Comment exécuter uniquement les tests non marqués ?**
Il n'y a pas d'opérateur « sans marqueur » : `-m "not lent and not integration and not bdd"`.

**Les marqueurs sont-ils visibles dans le nom du test ?**
Non. Le node id ne contient pas les marqueurs. `--collect-only` avec `-m`
permet de vérifier la sélection.

**Peut-on combiner `-m` et `-k` ?**
Oui, les deux filtres s'appliquent (intersection).

**Un marqueur peut-il porter un `reason` sur `-m` ?**
Non. Pour skipper automatiquement les tests `lent` sauf sur demande, c'est
un hook (`pytest_collection_modifyitems`, TP10) qui ajoute le marqueur skip.

**`skipif` avec plusieurs conditions ?**
Empiler plusieurs `skipif` (OU logique : le premier vrai skippe), ou une
seule condition composée avec `or`.

## Ce qu'il faut retenir

| Besoin | Outil |
|---|---|
| Ne pas exécuter | `@pytest.mark.skip(reason=)`, `skipif(cond, reason=)`, `pytest.skip()`, `pytest.importorskip()` |
| Échec attendu | `@pytest.mark.xfail(reason=, strict=True, raises=Exc, run=False)`, `pytest.xfail()` |
| Étiqueter | `@pytest.mark.nom` déclaré dans `markers`, `--strict-markers` |
| Sélectionner | `-m "a and not b"` (noms exacts), `-k` (sous-chaînes) |
| Portée | fonction, classe, `pytestmark` module, `pytest.param(marks=)` |
| Lire | `request.node.get_closest_marker("nom")`, `.args`, `.kwargs`, `iter_markers()` |

## Exercices

**1. Ajouter un marqueur `securite`, l'utiliser sur deux tests, ne lancer que ceux-là.**

Indice / corrigé : dans `pyproject.toml`, ajouter
`"securite: test lie a la securite"` dans `markers` (sinon `--strict-markers`
refuse). Décorer deux tests, puis `uv run pytest tp05_marqueurs -m securite -v`.
Faire d'abord l'oubli de déclaration pour lire l'erreur.

**2. Corriger `fonction_buggee` et observer `test_xfail_strict` et `test_xfail_bug_connu`.**

Indice / corrigé : avec `return x * 2`, `test_xfail_bug_connu` passe en
`XPASS` (toléré), `test_xfail_strict` en `FAILED [XPASS(strict)]`,
`test_xfail_dynamique` passe. Retirer les trois marqueurs/appels devenus
inutiles ; c'est exactement le cycle de vie prévu d'un xfail.

**3. Fixture lisant `@pytest.mark.timeout_max(secondes)` et échouant si le test dépasse la durée.**

Indice / corrigé : déclarer `"timeout_max(secondes): duree maximale"` dans
`markers`, puis :

```python
import time

@pytest.fixture(autouse=True)
def _timeout_max(request):
    marqueur = request.node.get_closest_marker("timeout_max")
    debut = time.perf_counter()
    yield
    if marqueur is not None:
        duree = time.perf_counter() - debut
        limite = marqueur.args[0]
        assert duree <= limite, f"test trop lent : {duree:.2f}s > {limite}s"
```

Tester avec `@pytest.mark.timeout_max(0.1)` sur `test_calcul_lourd` (0,2 s) :
l'échec survient au teardown, donc en **ERROR**, pas en FAILED. Bonne
occasion de rappeler la différence.

**4. (bonus) Skipper tout le module `test_module_marque.py` si la variable d'environnement `CI` est absente.**

Indice / corrigé :

```python
import os
import pytest

if "CI" not in os.environ:
    pytest.skip("uniquement en CI", allow_module_level=True)
```

Vérifier avec `CI=1 uv run pytest tp05_marqueurs/test_module_marque.py`.

## Transition vers le TP suivant

Les marqueurs disent **quand** exécuter un test. Reste le problème du **quoi** :
`telecharger` lève `ConnectionError` parce qu'il n'y a pas de réseau, et on
s'en est sorti avec un `xfail`. Le TP06 montre comment tester ce genre de
code pour de vrai, en remplaçant temporairement ses dépendances avec
`monkeypatch`.
