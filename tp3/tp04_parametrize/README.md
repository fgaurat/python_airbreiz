# TP04 – Paramétrage

## En une phrase

Un seul test, plusieurs jeux de données : `@pytest.mark.parametrize` et les
fixtures paramétrées génèrent automatiquement un test indépendant par cas,
avec un identifiant lisible, sélectionnable et rapportable séparément.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- écrire `@pytest.mark.parametrize` avec un ou plusieurs paramètres ;
- lire et contrôler les identifiants de cas (`ids`, `pytest.param(id=...)`) ;
- marquer un cas précis (`skip`, `xfail`) sans toucher aux autres ;
- empiler des paramétrages (produit cartésien) et paramétrer une classe ;
- paramétrer une **fixture** (`params=`) et choisir entre fixture paramétrée et `parametrize` ;
- utiliser le paramétrage **indirect** (`indirect=True`, `request.param`) ;
- générer des cas dynamiquement avec le hook `pytest_generate_tests` ;
- sélectionner un cas unique par `-k` ou par son node id.

## Prérequis

- TP01 : fonctions de test, `assert`, `pytest.raises`, `pytest.approx`.
- TP03 : fixtures, `conftest.py`, objet `request` (indispensable pour les
  sections 7 à 9).

## Fichiers

| Fichier | Rôle |
|---|---|
| `validation.py` | Fonctions pures, faciles à paramétrer : `valider_email`, `est_palindrome`, `fizzbuzz`, `celsius_vers_fahrenheit`, `classer_age`, `est_premier` |
| `conftest.py` | Deux fixtures paramétrées (`moteur_bdd`, `nombre_et_libelle`) et le hook `pytest_generate_tests` |
| `test_parametrize.py` | Neuf sections numérotées, de la forme de base au hook de génération |

## Mise en route

```bash
uv run pytest tp04_parametrize -q
```

Sortie attendue :

```
58 passed, 1 skipped, 1 xfailed in 0.11s
```

Le `skipped` et le `xfailed` sont voulus : ce sont deux cas de
`test_classer_age` marqués via `pytest.param` (section 4).

Commande à garder ouverte dans un second terminal pendant toute la présentation :

```bash
uv run pytest tp04_parametrize --collect-only -q
```

Elle liste les 60 node ids sans rien exécuter et permet de montrer, à chaque
section, comment les identifiants sont fabriqués.

## Déroulé de la présentation

### Le code métier : `validation.py`

Six fonctions pures, sans état ni dépendance externe. C'est volontaire : le
paramétrage brille sur les fonctions « entrée → sortie » où l'on veut couvrir
beaucoup de cas limites (frontières d'âge, valeurs de FizzBuzz, emails
malformés). `classer_age` lève `ValueError` pour un âge négatif, ce qui donne
un cas d'erreur à traiter à part. `est_premier` sert uniquement au hook de la
section 9.

À dire : « quand on se surprend à copier-coller un test en changeant deux
valeurs, c'est le signal qu'il faut paramétrer ».

### Section 1 : forme de base, un paramètre

**Ce que montre le code.**

```python
@pytest.mark.parametrize("texte", ["kayak", "Radar", "A man, a plan, a canal: Panama", ""])
def test_palindromes(texte):
    assert est_palindrome(texte)
```

Le premier argument est le **nom** du paramètre (une chaîne), le second la
liste des valeurs. Le nom doit correspondre exactement à un paramètre de la
fonction de test. pytest crée quatre tests : `test_palindromes[kayak]`,
`[Radar]`, `[A man, a plan, a canal: Panama]`, `[]`.

**À dire aux stagiaires.** Chaque cas est un test à part entière : il a son
propre identifiant, son propre résultat, et l'échec de l'un n'empêche pas les
autres de s'exécuter. C'est la différence fondamentale avec une boucle `for`
dans le test, qui s'arrête au premier `assert` faux et ne dit pas quel cas a
échoué.

**À montrer en direct.**

```bash
uv run pytest tp04_parametrize -k palindromes -v
```

Puis faire l'expérience inverse : écrire au tableau la version « boucle » et
demander ce qu'on perd (le nom du cas fautif, les cas suivants, la sélection).

**Pièges et erreurs fréquentes.**

- Oublier le paramètre dans la signature : `def test_palindromes():` avec le
  décorateur donne à la collecte :
  `In test_palindromes: function uses no argument 'texte'`.
- Nommer le paramètre différemment du décorateur : même erreur.
- Une chaîne vide comme valeur donne l'id `[]` : c'est normal, mais peu
  lisible ; voir `ids` en section 3.

### Section 2 : plusieurs paramètres

**Ce que montre le code.**

```python
@pytest.mark.parametrize(
    "n, attendu",
    [(1, "1"), (3, "Fizz"), (5, "Buzz"), (15, "FizzBuzz"), (30, "FizzBuzz"), (7, "7")],
)
def test_fizzbuzz(n, attendu):
    assert fizzbuzz(n) == attendu
```

Les noms sont donnés dans **une seule chaîne** séparée par des virgules (une
liste `["n", "attendu"]` est aussi acceptée). Chaque valeur est alors un
tuple de même longueur.

**À dire aux stagiaires.** C'est la forme la plus courante : « entrée,
sortie attendue ». L'id est construit en joignant les valeurs par un tiret :
`[3-Fizz]`, `[15-FizzBuzz]`.

**À montrer en direct.** Dans la sortie de `--collect-only -q`, repérer les
six lignes `test_fizzbuzz[...]`. Faire remarquer que `[7-7]` est ambigu à
lire : les ids par défaut ne sont pas toujours suffisants.

**Pièges et erreurs fréquentes.**

- Tuple trop long ou trop court. Avec `[(1, 2, 3)]` pour `"a, b"`, la
  collecte échoue :
  ```
  in "parametrize" the number of names (2):
    ['a', 'b']
  must be equal to the number of values (3):
    (1, 2, 3)
  ```
- Oublier les parenthèses du tuple pour un cas unique : `[1, "1"]` au lieu
  de `[(1, "1")]` donne deux cas avec une seule valeur chacun, et la même
  erreur de comptage.

### Section 3 : `ids`, rendre les cas lisibles

**Ce que montre le code.** Deux formes :

1. Une **liste** de chaînes, de même longueur que les valeurs :
   ```python
   ids=["simple", "avec_plus_et_point", "sans_arobase", "sans_local", "sans_domaine"]
   ```
   donne `test_valider_email[sans_arobase]`.

2. Une **fonction** appelée pour chaque valeur individuelle (pas pour chaque
   tuple) :
   ```python
   def _id_temperature(valeur):
       if isinstance(valeur, (int, float)):
           return f"{valeur}deg"
       return None  # None -> id par défaut
   ```
   donne `test_conversion[0deg-32deg]`, `test_conversion[-40deg--40deg]`.

**À dire aux stagiaires.** Règles de génération par défaut :

| Type de valeur | Id produit |
|---|---|
| `int`, `float`, `str`, `bool`, `None` | la valeur elle-même (`3`, `Fizz`, `None`) |
| Enum, classe, fonction | leur nom |
| autre objet (liste, dict, instance) | le nom du paramètre suivi d'un index : `n0`, `n1`... |
| plusieurs paramètres | valeurs jointes par `-` |
| caractères non imprimables ou non ASCII | échappés (`\xe9` pour `é`) |

Un id explicite est utile dès qu'on veut cibler un cas avec `-k`, ou que la
sortie sert de documentation (« quels cas d'email testons-nous ? »).

**À montrer en direct.**

```bash
uv run pytest tp04_parametrize -k valider_email -v
uv run pytest "tp04_parametrize/test_parametrize.py::test_valider_email[sans_arobase]"
```

Insister sur les **guillemets** autour du node id : les crochets sont
interprétés par zsh (et bash avec `nullglob`) comme un motif de fichiers.
Sans guillemets, zsh affiche `no matches found`.

**Pièges et erreurs fréquentes.**

- Liste `ids` de mauvaise longueur : erreur à la collecte.
- Des ids en double sont automatiquement suffixés `0`, `1`... par pytest.
- Un accent dans une valeur devient `\xe9` dans l'id : utiliser `ids` ou
  l'option ini `disable_test_id_escaping_and_forfeit_all_rights_to_community_support = true`
  (le nom est volontairement dissuasif).

### Section 4 : `pytest.param`, id et marqueurs sur un cas précis

**Ce que montre le code.**

```python
pytest.param(0, "mineur", id="nouveau-ne"),
pytest.param(150, "invalide", marks=pytest.mark.xfail(reason="âge non plausible : règle métier à définir")),
pytest.param(-1, "erreur", marks=pytest.mark.skip(reason="cas d'erreur testé ailleurs")),
```

`pytest.param(*valeurs, id=..., marks=...)` enveloppe un cas pour lui
attacher un identifiant et/ou des marqueurs. `marks` accepte un marqueur ou
une liste.

**À dire aux stagiaires.** C'est la réponse à « j'ai dix cas, un seul est
un bug connu, je ne veux pas désactiver les neuf autres ». Le cas 150 est
en `xfail` : il s'exécute, échoue (la fonction renvoie `"senior"`, pas
`"invalide"`) et pytest le compte comme attendu. Le cas -1 est `skip`, et
testé à part par `test_classer_age_negatif` avec `pytest.raises`.

Ce cas illustre aussi une pratique : les cas d'erreur (exception) ne se
mélangent pas aux cas nominaux dans le même `parametrize`, car l'assert n'a
pas la même forme.

**À montrer en direct.**

```bash
uv run pytest tp04_parametrize -k classer_age -v -ra
```

On lit `s` pour `[-1-erreur]`, `x` pour `[150-invalide]`, et le résumé
`-ra` donne les raisons. Modification en live : passer `"invalide"` à
`"senior"` sur le cas 150, relancer, observer `XPASS` (le test passe alors
qu'on l'attendait en échec). Cela prépare le TP05 (`strict=True`).

**Pièges et erreurs fréquentes.**

- Mettre `id=` sur certains cas seulement : c'est autorisé, les autres
  gardent l'id par défaut (`[64-adulte]`).
- Mélanger `pytest.param` et tuples nus dans la même liste : autorisé aussi.
- Écrire `marks="xfail"` (chaîne) : erreur, il faut un objet `pytest.mark.xfail`.

### Section 5 : empilement, produit cartésien

**Ce que montre le code.**

```python
@pytest.mark.parametrize("x", [0, 1, 2])
@pytest.mark.parametrize("y", [10, 20])
def test_produit_cartesien(x, y):
```

Deux décorateurs indépendants : pytest génère 3 × 2 = 6 tests.

**À dire aux stagiaires.** L'ordre des ids suit l'ordre d'application des
décorateurs, c'est-à-dire **du plus proche de la fonction vers le plus
éloigné** : le décorateur `y` (le plus bas) est appliqué en premier, donc
`y` apparaît en premier dans l'id : `[10-0]`, `[10-1]`, `[10-2]`, `[20-0]`...
Vérifier dans `--collect-only -q`. L'ordre d'exécution est le même.

Utile pour tester toutes les combinaisons (plateforme × version, format ×
encodage). Attention à l'explosion combinatoire : 5 × 5 × 5 = 125 tests.

**À montrer en direct.**

```bash
uv run pytest tp04_parametrize -k produit_cartesien --collect-only -q
```

**Pièges et erreurs fréquentes.**

- Croire que c'est un « zip » (appariement 1 à 1) : non, c'est un produit.
  Pour un appariement, mettre les deux noms dans un seul `parametrize`.

### Section 6 : paramétrer une classe entière

**Ce que montre le code.**

```python
@pytest.mark.parametrize("n", [3, 6, 9])
class TestMultiplesDeTrois:
    def test_fizz(self, n): ...
    def test_divisible(self, n): ...
```

Chaque méthode de la classe reçoit le paramètre : 2 méthodes × 3 valeurs =
6 tests, `TestMultiplesDeTrois::test_fizz[3]`, etc.

**À dire aux stagiaires.** Toutes les méthodes **doivent** déclarer le
paramètre `n`, sinon erreur `function uses no argument 'n'` pour la méthode
fautive. Même mécanisme au niveau module avec
`pytestmark = pytest.mark.parametrize(...)`.

**Pièges et erreurs fréquentes.** Ajouter une méthode utilitaire
`test_xxx(self)` sans `n` dans la classe : erreur à la collecte.

### Section 7 : fixtures paramétrées (`conftest.py`)

**Ce que montre le code.**

```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def moteur_bdd(request):
    return {"moteur": request.param, "connecte": True}
```

`params=` sur une fixture : **tout test qui la demande** s'exécute une fois
par valeur. La valeur courante est dans `request.param`. `ids=` fonctionne
comme pour `parametrize` (voir `nombre_et_libelle` avec `ids=["premier", "second"]`).

**À dire aux stagiaires.** Quand choisir quoi :

| Besoin | Outil |
|---|---|
| Données d'entrée / sortie propres à un test | `@pytest.mark.parametrize` sur le test |
| Faire tourner **plusieurs tests** contre plusieurs implémentations, configurations, environnements | fixture avec `params=` |
| Valeur qui nécessite une construction (connexion, objet complexe) | fixture avec `params=` ou `indirect` |

La fixture paramétrée est le mécanisme du TP11 : une fixture `depot` avec
`params=["memoire", "json"]` fait tourner la même suite de tests de contrat
contre deux implémentations. Le TP13 ajoute Postgres de la même manière.

**À montrer en direct.**

```bash
uv run pytest tp04_parametrize -k "moteur_bdd or nombre_et_libelle" -v
uv run pytest tp04_parametrize -k postgres -v
```

Faire remarquer que `-k postgres` sélectionne par l'id de la fixture, alors
qu'aucun test ne contient « postgres » dans son nom.

**Pièges et erreurs fréquentes.**

- Oublier `request` dans la signature de la fixture : `request.param`
  inaccessible, `NameError`.
- Une fixture paramétrée de scope `module` ou `session` : pytest regroupe
  les tests par valeur de paramètre pour minimiser les setup/teardown, ce
  qui modifie l'ordre d'exécution des tests. Surprenant la première fois.

### Section 8 : paramétrage indirect

**Ce que montre le code.**

```python
@pytest.fixture
def utilisateur(request):
    age = request.param
    return {"nom": f"user{age}", "age": age, "categorie": classer_age(age)}

@pytest.mark.parametrize("utilisateur", [10, 30, 70], indirect=True)
def test_indirect(utilisateur):
```

Sans `indirect`, `utilisateur` recevrait directement `10`, `30`, `70`. Avec
`indirect=True`, pytest cherche une **fixture** nommée `utilisateur`, lui
passe la valeur dans `request.param`, et le test reçoit ce que la fixture
renvoie.

Schéma à dessiner :

```
parametrize("utilisateur", [10, 30, 70], indirect=True)
        │ 10
        ▼
fixture utilisateur(request)  →  request.param == 10  →  construit {"nom": "user10", ...}
        │
        ▼
test_indirect(utilisateur)    reçoit le dict
```

**À dire aux stagiaires.** Intérêt : le test déclare des valeurs simples et
lisibles (un âge), la fixture fait le travail de construction (et son
teardown éventuel, avec `yield`). `indirect` peut aussi être une liste de
noms quand seuls certains paramètres passent par une fixture :
`indirect=["utilisateur"]`.

**À montrer en direct.**

```bash
uv run pytest "tp04_parametrize/test_parametrize.py::test_indirect[10]" --setup-show
```

Sortie :

```
SETUP    F utilisateur[10]
tp04_parametrize/test_parametrize.py::test_indirect[10] (fixtures used: request, utilisateur) .
TEARDOWN F utilisateur[10]
```

Modification en live : retirer `indirect=True` et relancer. Le test reçoit
l'entier 10, `utilisateur["categorie"]` lève `TypeError: 'int' object is not subscriptable`.

**Pièges et erreurs fréquentes.**

- Fixture sans `request.param` mais appelée en indirect : la valeur est
  ignorée silencieusement.
- Utiliser `request.param` dans une fixture appelée **sans** paramétrage :
  `AttributeError: 'FixtureRequest' object has no attribute 'param'`.

### Section 9 : `pytest_generate_tests` (`conftest.py`)

**Ce que montre le code.**

```python
def pytest_generate_tests(metafunc):
    if "nombre_premier" in metafunc.fixturenames:
        premiers = [2, 3, 5, 7, 11, 13]
        metafunc.parametrize("nombre_premier", premiers, ids=[f"p{p}" for p in premiers])
```

Hook appelé à la collecte **pour chaque fonction de test**. `metafunc`
décrit la fonction : `metafunc.fixturenames` (les paramètres qu'elle
demande), `metafunc.function`, `metafunc.config` (accès aux options, par
exemple `metafunc.config.getoption("--env")`). `metafunc.parametrize(...)`
a la même signature que le décorateur.

**À dire aux stagiaires.** C'est du paramétrage **calculé** : lecture d'un
fichier CSV de cas, d'une variable d'environnement, d'une option en ligne
de commande, ou génération à partir d'une liste de plugins installés. Le
test ne sait pas d'où viennent ses valeurs : `test_nombres_premiers(nombre_premier)`
ressemble à un test avec fixture.

**À montrer en direct.**

```bash
uv run pytest tp04_parametrize -k nombres_premiers -v
```

Les ids `p2`, `p3`... viennent du hook.

**Pièges et erreurs fréquentes.**

- Appeler `metafunc.parametrize` pour un nom qui n'est pas dans
  `metafunc.fixturenames` : erreur `function uses no argument`. D'où le `if`.
- Paramétrer deux fois le même nom (décorateur + hook) : erreur `duplicate 'nombre_premier'`.

## Questions fréquentes des stagiaires

**Peut-on paramétrer avec des objets complexes (dataclasses, dict) ?**
Oui. L'id par défaut sera `n0`, `n1`... : fournir `ids=` ou une fonction
d'id, ou `pytest.param(..., id=...)`.

**Comment lancer un seul cas ?**
Par node id entre guillemets : `pytest "fichier.py::test_x[id]"`, ou par
sous-chaîne : `-k "test_x and id"`. Le node id exact se lit dans
`--collect-only -q`.

**`parametrize` et fixtures paramétrées se combinent-ils ?**
Oui, en produit cartésien. `test_moteur_bdd` avec un `parametrize("x", [1, 2])`
en plus donnerait 3 × 2 = 6 tests.

**Peut-on paramétrer une fixture avec `yield` (teardown) ?**
Oui, `params=` et `yield` sont indépendants. Le teardown s'exécute pour
chaque valeur.

**Comment faire un « zip » de deux listes plutôt qu'un produit ?**
Un seul `parametrize("a, b", list(zip(liste_a, liste_b)))`.

**Peut-on lire les valeurs depuis un fichier ?**
Oui, soit en construisant la liste au niveau module (`CAS = json.load(...)`)
avant le décorateur, soit dans `pytest_generate_tests`. Attention : le
fichier est lu à la **collecte**, à chaque lancement.

**L'ordre d'exécution des cas est-il garanti ?**
Oui, l'ordre de la liste, sauf regroupement par pytest pour les fixtures
paramétrées de scope large.

**Que se passe-t-il si la liste de valeurs est vide ?**
Le test est collecté puis **skippé** avec la raison
`got empty parameter set`. Configurable avec `empty_parameter_set_mark`
(`skip`, `xfail` ou `fail_at_collect`).

**`parametrize` fonctionne-t-il avec `unittest.TestCase` ?**
Non. C'est une des raisons de migrer vers le style pytest natif (TP02).

## Ce qu'il faut retenir

| Mécanisme | Syntaxe | Quand |
|---|---|---|
| Un paramètre | `@pytest.mark.parametrize("x", [..])` | données d'un test |
| Plusieurs | `parametrize("a, b", [(..), (..)])` | entrée / sortie |
| Ids | `ids=[...]`, `ids=fonction`, `pytest.param(id=)` | lisibilité, sélection |
| Marquer un cas | `pytest.param(.., marks=pytest.mark.xfail)` | bug connu isolé |
| Produit cartésien | deux décorateurs empilés | combinaisons |
| Classe | décorateur sur la classe | toutes les méthodes |
| Fixture paramétrée | `@pytest.fixture(params=[..])` + `request.param` | même suite, plusieurs implémentations |
| Indirect | `parametrize("fx", [..], indirect=True)` | valeur simple → objet construit par fixture |
| Dynamique | `pytest_generate_tests(metafunc)` | cas calculés, lus d'un fichier ou d'une option |

Rappel : chaque cas est un test indépendant, avec son id, son résultat, sa
sélection.

## Exercices

**1. Paramétrer `test_classer_age_negatif` avec plusieurs valeurs négatives.**

Indice / corrigé :

```python
@pytest.mark.parametrize("age", [-1, -10, -1000])
def test_classer_age_negatif(age):
    with pytest.raises(ValueError, match="négatif"):
        classer_age(age)
```

**2. Ajouter un cas `("kayak ", True)` à `test_valider_email` qui échoue, puis le marquer `xfail`.**

Indice / corrigé : le cas échoue car `"kayak "` n'est pas un email.
Ajouter dans la liste :

```python
pytest.param("kayak ", True, id="pas-un-email", marks=pytest.mark.xfail(reason="cas volontairement faux")),
```

et ajouter `"pas-un-email"` à la liste `ids`... ou, plus simple, supprimer
la liste `ids` globale et passer chaque cas en `pytest.param(..., id=...)`.
Piège à faire découvrir : on ne peut pas avoir à la fois `ids=` de longueur
5 et 6 cas.

**3. Fixture paramétrée `separateur` (`","`, `";"`, `"\t"`) et test de découpage.**

Indice / corrigé :

```python
@pytest.fixture(params=[",", ";", "\t"], ids=["virgule", "point-virgule", "tab"])
def separateur(request):
    return request.param

def test_decoupage(separateur):
    ligne = separateur.join(["a", "b", "c"])
    assert ligne.split(separateur) == ["a", "b", "c"]
```

Sans `ids`, l'id de la tabulation serait `\t` échappé : bon exemple pour
justifier `ids`.

**4. Faire lire à `pytest_generate_tests` les nombres premiers depuis `premiers.txt`.**

Indice / corrigé : créer `tp04_parametrize/premiers.txt` avec un nombre par
ligne, puis :

```python
from pathlib import Path

def pytest_generate_tests(metafunc):
    if "nombre_premier" in metafunc.fixturenames:
        fichier = Path(__file__).parent / "premiers.txt"
        premiers = [int(l) for l in fichier.read_text().split()]
        metafunc.parametrize("nombre_premier", premiers, ids=[f"p{p}" for p in premiers])
```

Discussion : que se passe-t-il si le fichier est vide ? (test skippé,
`empty parameter set`.)

**5. (bonus) Rendre `moteur_bdd` sélectionnable par une option `--moteur`.**

Indice : l'option est déclarée dans le `conftest.py` racine avec
`parser.addoption("--moteur", action="append")`, puis dans
`pytest_generate_tests` : `metafunc.config.getoption("--moteur") or ["sqlite", "postgres", "mysql"]`.
Il faut alors transformer `moteur_bdd` en paramètre généré par le hook plutôt
qu'en fixture `params=`.

## Transition vers le TP suivant

Les cas `skip` et `xfail` de `pytest.param` ont montré qu'on peut étiqueter
un test pour changer son traitement. Le TP05 généralise ce mécanisme : les
**marqueurs**, intégrés ou personnalisés, pour ignorer, attendre un échec,
sélectionner ou transporter des données.
