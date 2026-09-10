# TP06 – monkeypatch

## En une phrase

La fixture intégrée `monkeypatch` remplace temporairement une fonction, un
attribut, une variable d'environnement, une entrée de dictionnaire ou le
répertoire courant, et restaure tout à la fin du test : c'est l'outil pour
isoler le code de ses dépendances externes.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- utiliser chaque méthode de `monkeypatch` : `setattr`, `delattr`, `setitem`,
  `delitem`, `setenv`, `delenv`, `chdir`, `syspath_prepend`, `context()` ;
- déterminer **où** patcher selon la façon dont le code importe sa dépendance ;
- contourner les objets non patchables (types C comme `datetime`) ;
- contrôler le temps (`time.time`, `datetime.now`) dans un test ;
- combiner `monkeypatch` et `tmp_path` pour isoler le système de fichiers ;
- encapsuler des patchs dans une fixture réutilisable ;
- situer `monkeypatch` par rapport à `unittest.mock` et à l'injection de dépendances.

## Prérequis

- TP03 : fixtures, `yield`, `tmp_path` (vu rapidement).
- TP04 : `parametrize` (utilisé dans `test_salutation`).
- TP05 : le `xfail` sur `telecharger` a montré le problème que ce TP résout.

## Fichiers

| Fichier | Rôle |
|---|---|
| `meteo.py` | Client météo qui dépend de `os.environ`, `urllib`, `time.time`, `datetime.now`, d'une config globale, d'un cache global et du répertoire courant |
| `test_monkeypatch.py` | Neuf sections : une par méthode ou technique |

## Mise en route

```bash
uv run pytest tp06_monkeypatch -q
```

Sortie attendue :

```
20 passed in 0.10s
```

Aucun accès réseau, aucune variable d'environnement requise, aucun fichier
créé hors des répertoires temporaires : c'est le but.

## Déroulé de la présentation

### Le code métier : `meteo.py`

Un module écrit « comme dans la vraie vie », avec tout ce qui rend un test
difficile. Faire lister par les stagiaires les dépendances externes en
lisant le code :

| Fonction | Dépendance | Problème pour un test |
|---|---|---|
| `cle_api()` | `os.environ["METEO_API_KEY"]` | dépend de la machine |
| `appeler_api(ville)` | `urllib.request.urlopen` | réseau, lent, non reproductible |
| `temperature(ville)` | `CONFIG["unite"]` | état global partagé |
| `temperature_en_cache(ville)` | `time.time()` et `_CACHE` | temps réel, état global |
| `salutation()` | `datetime.now()` | dépend de l'heure |
| `lire_config_locale()` | `Path("meteo.json")` relatif | dépend du répertoire courant |
| `Station.lire_capteur()` | matériel (lève `RuntimeError`) | impossible en test |

À dire : « chaque ligne de ce tableau est une raison de ne pas tester, ou
une occasion d'utiliser `monkeypatch` ». Noter que `temperature` appelle
`appeler_api` **par le nom du module** (`meteo.appeler_api` résolu à
l'exécution), ce qui rend le patch possible.

### Section 1 : `setenv` / `delenv`, variables d'environnement

**Ce que montre le code.**

```python
def test_cle_api_presente(monkeypatch):
    monkeypatch.setenv("METEO_API_KEY", "secret-de-test")
    assert meteo.cle_api() == "secret-de-test"

def test_cle_api_absente(monkeypatch):
    monkeypatch.delenv("METEO_API_KEY", raising=False)
    with pytest.raises(meteo.ConfigError, match="manquante"):
        meteo.cle_api()
```

`test_env_restaure` vérifie ensuite que rien n'a fui.

**À dire aux stagiaires.**

- `monkeypatch` est une fixture intégrée : il suffit de la nommer en
  paramètre. Elle enregistre chaque modification et les **annule toutes** à
  la fin du test, dans l'ordre inverse (LIFO), même si le test échoue.
- `raising=False` : ne pas lever `KeyError` si la variable n'existe pas.
  Sans lui, `delenv` d'une variable absente est une erreur (protection
  contre les fautes de frappe).
- On teste ainsi les deux branches (présente / absente) sans toucher au
  shell ni dépendre du poste.

**À montrer en direct.**

```bash
uv run pytest tp06_monkeypatch -k cle_api -v
METEO_API_KEY=xyz uv run pytest tp06_monkeypatch -k cle_api -v   # passe aussi : le test ne dépend pas du shell
```

**Pièges et erreurs fréquentes.**

- Écrire `os.environ["X"] = "y"` directement dans le test : ça marche, mais
  ce n'est jamais restauré et les tests suivants en héritent.
- `setenv` accepte uniquement des chaînes : `setenv("PORT", 8080)` échoue.
  Utiliser `"8080"`.

### Section 2 : `setattr`, remplacer une fonction d'un module

**Ce que montre le code.**

```python
def test_temperature_sans_reseau(monkeypatch):
    def faux_appel(ville):
        assert ville == "Paris"
        return {"temp": 21.0, "ville": ville}

    monkeypatch.setattr(meteo, "appeler_api", faux_appel)
    assert meteo.temperature("Paris") == 21.0
```

Deux autres formes : `setattr("tp06_monkeypatch.meteo.appeler_api", lambda ville: ...)`
avec le chemin en chaîne (`test_setattr_par_chaine`), et le patch plus bas
niveau de `urlopen` lui-même (`test_patcher_plus_bas_urlopen`) avec une
classe `FausseReponse` qui imite l'objet réponse (`read`, `__enter__`, `__exit__`).

**À dire aux stagiaires.** La règle centrale du TP, à écrire au tableau :
**on patche le nom là où le code testé va le chercher.**

```
# meteo.py fait :  import urllib.request  puis  urllib.request.urlopen(...)
#   -> le nom est cherché dans l'objet urllib.request au moment de l'appel
monkeypatch.setattr(meteo.urllib.request, "urlopen", faux)      # fonctionne
monkeypatch.setattr("urllib.request.urlopen", faux)             # fonctionne aussi (même objet)

# si meteo.py faisait :  from urllib.request import urlopen  puis  urlopen(...)
#   -> le nom `urlopen` est une variable du module meteo, copiée à l'import
monkeypatch.setattr(meteo, "urlopen", faux)                     # la seule forme qui marche
monkeypatch.setattr("urllib.request.urlopen", faux)             # SANS EFFET sur meteo
```

Choix du niveau : patcher `appeler_api` (haut niveau) rend le test de
`temperature` simple et lisible. Patcher `urlopen` (bas niveau) sert à
tester `appeler_api` elle-même : construction de l'URL, timeout. Les deux
sont légitimes, à des niveaux différents.

**À montrer en direct.**

```bash
uv run pytest tp06_monkeypatch -k "sans_reseau or par_chaine or urlopen" -v
```

Puis, dans `test_patcher_plus_bas_urlopen`, changer le timeout attendu de
`5` en `10` : l'assert sur `urls_appelees` échoue et montre le tuple réel.
C'est un test qui vérifie **comment** la dépendance est appelée, pas
seulement le résultat.

**Pièges et erreurs fréquentes.**

- `monkeypatch.setattr(meteo.appeler_api, faux)` (deux arguments, sans le
  nom) : erreur `TypeError`, la forme courte n'existe que pour la chaîne
  `"module.attr"`.
- Fonction de remplacement avec une mauvaise signature : `TypeError` au
  moment de l'appel, souvent obscur. Copier la signature de l'original.
- Par défaut `setattr` exige que l'attribut **existe** déjà
  (`raising=True`) : `setattr(meteo, "appeler_apii", ...)` lève
  `AttributeError`. C'est une protection contre les fautes de frappe.

### Section 3 : `setattr` sur une classe ou une instance

**Ce que montre le code.**

```python
monkeypatch.setattr(meteo.Station, "lire_capteur", lambda self: 18.25)   # toutes les instances
monkeypatch.setattr(station, "lire_capteur", lambda: 12.0)               # une seule instance
```

**À dire aux stagiaires.** Sur la **classe**, la fonction remplace une
méthode : elle doit accepter `self`. Sur l'**instance**, on pose un attribut
qui masque la méthode : pas de `self`. `test_methode_d_instance` prouve que
l'autre instance (`autre`) lève toujours `RuntimeError`.

Cas d'usage : remplacer une méthode coûteuse (`envoyer_email`,
`lire_capteur`) sur une classe qu'on ne contrôle pas, ou sur un seul objet.

**Pièges et erreurs fréquentes.** Oublier `self` sur le patch de classe :
`TypeError: <lambda>() takes 0 positional arguments but 1 was given`.

### Section 4 : `setitem` / `delitem`, dictionnaires et config globale

**Ce que montre le code.**

```python
monkeypatch.setitem(meteo.CONFIG, "unite", "fahrenheit")
assert meteo.temperature("X") == 212.0
```

`test_config_restauree` vérifie que `CONFIG["unite"]` vaut de nouveau
`"celsius"` dans le test suivant.

**À dire aux stagiaires.** `setitem` modifie **la clé** d'un dictionnaire
existant, pas la variable. C'est ce qu'on veut pour une config globale :
le module continue de lire le même objet `CONFIG`. Un `setattr(meteo, "CONFIG", {...})`
fonctionnerait aussi ici, mais casserait un code qui aurait gardé une
référence vers l'ancien dict. `delitem` retire une clé (avec `raising=`).
Fonctionne sur `sys.modules` (voir section 7) et sur n'importe quel objet
indexable.

**Pièges et erreurs fréquentes.** `meteo.CONFIG["unite"] = "fahrenheit"`
dans le test : non restauré, le test suivant hérite du Fahrenheit. Avec
pytest-randomly ou `-p no:randomly`, ce genre de fuite donne des échecs
intermittents difficiles à diagnostiquer.

### Section 5 : contrôler le temps

**Ce que montre le code.** Deux techniques.

`time.time` est une fonction d'un module : patchable directement.

```python
horloge = {"t": 1_000.0}
monkeypatch.setattr(meteo.time, "time", lambda: horloge["t"])
...
horloge["t"] += 61   # on avance le temps de 61 s
```

`datetime.now` est une méthode d'un **type écrit en C**, immuable :

```python
monkeypatch.setattr(datetime, "now", ...)
# TypeError: cannot set 'now' attribute of immutable type 'datetime.datetime'
```

La solution : remplacer la **classe** `datetime` telle que le module `meteo`
la voit (il a fait `from datetime import datetime`) par une classe factice
qui expose `now()` :

```python
class FauxDatetime:
    @classmethod
    def now(cls):
        return datetime(2024, 1, 1, heure, 0)

monkeypatch.setattr(meteo, "datetime", FauxDatetime)
```

**À dire aux stagiaires.**

- Le test du cache (`test_cache_expire`) montre le pattern « horloge
  contrôlée » : un dict mutable capturé par la lambda, qu'on avance à la
  main. On teste l'expiration du cache en une milliseconde au lieu d'attendre 60 s.
- Il réinitialise aussi `_CACHE` par `monkeypatch.setattr(meteo, "_CACHE", {})` :
  **tout état global** (cache, singleton, registre) doit être remis à zéro
  par le test, sinon l'ordre d'exécution influence le résultat.
- Le message d'erreur sur `datetime` est à montrer tel quel : il est
  fréquent et déroutant. Alternatives dans la vraie vie : la bibliothèque
  `freezegun` (`@freeze_time("2024-01-01 08:00")`) ou `time-machine`, ou
  mieux, injecter une fonction `horloge` en paramètre du code métier.

**À montrer en direct.**

```bash
uv run pytest tp06_monkeypatch -k "cache or salutation" -v
```

Puis dans un fichier temporaire ou en REPL :

```bash
uv run python -c "from datetime import datetime; setattr(datetime, 'now', None)"
```

pour afficher le `TypeError` réel.

**Pièges et erreurs fréquentes.**

- Patcher `datetime.datetime.now` via `unittest.mock.patch("datetime.datetime.now")` :
  même `TypeError`.
- `FauxDatetime` ne remplace que `now` : si le code appelle aussi
  `datetime.fromisoformat`, il faut l'ajouter, ou faire hériter
  `FauxDatetime(datetime)`.

### Section 6 : `chdir`, répertoire courant

**Ce que montre le code.**

```python
def test_config_locale_presente(monkeypatch, tmp_path):
    (tmp_path / "meteo.json").write_text('{"ville": "Brest"}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert meteo.lire_config_locale() == {"ville": "Brest"}
```

**À dire aux stagiaires.** `lire_config_locale` lit un chemin **relatif** :
son résultat dépend de l'endroit d'où on lance pytest. `chdir` vers un
`tmp_path` vide donne un environnement propre et jetable ; on y dépose
exactement les fichiers voulus. Le répertoire courant est restauré après le
test (sinon les tests suivants, et pytest lui-même, seraient perturbés).

**Pièges et erreurs fréquentes.** `os.chdir(tmp_path)` direct dans un test :
non restauré, les chemins relatifs des tests suivants cassent.

### Section 7 : `syspath_prepend`, rendre un module importable

**Ce que montre le code.** Écrit `module_temporaire.py` dans `tmp_path`,
ajoute le dossier en tête de `sys.path`, importe, puis nettoie
`sys.modules` avec `monkeypatch.delitem(sys.modules, "module_temporaire")`.

**À dire aux stagiaires.** Cas d'usage : tester un mécanisme de plugins,
un chargeur dynamique, un code qui génère des modules. `syspath_prepend`
restaure `sys.path` mais **pas** `sys.modules` : un module importé reste en
cache, d'où le `delitem` explicite. Sans lui, un second test important un
autre `module_temporaire` obtiendrait l'ancien.

**Pièges et erreurs fréquentes.** Oublier `delitem(sys.modules, ...)` :
tests dépendants de l'ordre.

### Section 8 : `monkeypatch.context()`, annuler avant la fin du test

**Ce que montre le code.**

```python
with monkeypatch.context() as m:
    m.setitem(meteo.CONFIG, "unite", "kelvin")
    assert meteo.CONFIG["unite"] == "kelvin"
assert meteo.CONFIG["unite"] == "celsius"   # restauré à la sortie du with
```

**À dire aux stagiaires.** Utile quand un test veut vérifier **deux**
configurations successivement, ou quand un patch ne doit couvrir qu'une
partie du test. Sert aussi dans une fixture de scope `session` ou `module`
(la fixture `monkeypatch` est de scope function : pour un scope plus
large, on crée `pytest.MonkeyPatch()` soi-même et on l'utilise en `with`).

### Section 9 : fixture réutilisable construite sur `monkeypatch`

**Ce que montre le code.**

```python
@pytest.fixture
def api_factice(monkeypatch):
    reponses = {}
    monkeypatch.setattr(meteo, "appeler_api", lambda ville: reponses[ville])
    monkeypatch.setenv("METEO_API_KEY", "fixture")
    return reponses

def test_avec_fixture_api(api_factice):
    api_factice["Rome"] = {"temp": 28.0}
    assert meteo.temperature("Rome") == 28.0
```

**À dire aux stagiaires.** Une fixture peut demander `monkeypatch` comme
n'importe quelle autre fixture. Les patchs vivent le temps du test qui
utilise `api_factice`. Le dict renvoyé permet au test de **piloter** la
réponse. C'est la forme à mettre dans un `conftest.py` : « réseau coupé pour
tout le monde, réponses configurables ». Le TP11 pousse l'idée jusqu'au
bout avec une fixture `autouse` qui interdit tout accès réseau.

**Pièges et erreurs fréquentes.** Mettre le patch dans une fixture
`session` avec la fixture `monkeypatch` : `ScopeMismatch`. Voir la remarque
de la section 8.

## Questions fréquentes des stagiaires

**`monkeypatch` ou `unittest.mock.patch` ?**
`monkeypatch` remplace un objet par ce que vous fournissez et restaure tout ;
il ne sait pas ce qui a été appelé. `unittest.mock` fournit des objets
`Mock` qui enregistrent les appels et permettent `assert_called_with`
(TP07). Les deux se combinent : `monkeypatch.setattr(meteo, "appeler_api", Mock(return_value={...}))`.
En pratique, `monkeypatch` pour l'environnement (env, cwd, config, temps),
`Mock` pour vérifier des interactions.

**Pourquoi ne pas simplement passer la dépendance en paramètre ?**
C'est mieux quand on maîtrise le code : `temperature(ville, appeler=appeler_api)`
se teste sans aucun patch. `monkeypatch` sert surtout pour du code qu'on
ne peut pas (ou pas encore) réorganiser, ou pour des dépendances trop
basses (`os.environ`, `time`).

**Le patch est-il visible par les autres threads ou processus ?**
Par les threads du même processus, oui (c'est une modification globale).
Par un sous-processus, non.

**Que se passe-t-il si deux tests patchent la même chose en parallèle avec xdist ?**
Chaque worker xdist est un processus séparé : pas d'interférence.

**Comment patcher une constante de module utilisée par défaut dans une signature (`def f(url=API_URL)`) ?**
Impossible par `setattr` : la valeur par défaut est capturée à la définition
de la fonction. Il faut passer l'argument explicitement ou patcher la
fonction elle-même.

**Peut-on patcher une propriété (`@property`) ?**
Oui, sur la classe : `monkeypatch.setattr(Classe, "prop", property(lambda self: 42))`.

**Comment vérifier qu'une fonction patchée a bien été appelée ?**
Enregistrer dans une liste (comme `urls_appelees`) ou utiliser un `Mock`
(TP07).

**Faut-il nettoyer `_CACHE` dans chaque test ?**
Mieux : une fixture `autouse` dans `conftest.py` qui fait
`monkeypatch.setattr(meteo, "_CACHE", {})`. Ou, à la conception, éviter
les caches au niveau module.

## Ce qu'il faut retenir

| Méthode | Cible | Restauré |
|---|---|---|
| `setattr(obj, "nom", val)` / `setattr("mod.chemin.nom", val)` | fonction, méthode, attribut, classe | oui |
| `delattr(obj, "nom")` | attribut | oui |
| `setitem(d, cle, val)` / `delitem(d, cle)` | dictionnaire, `sys.modules` | oui |
| `setenv("VAR", "val")` / `delenv("VAR")` | environnement | oui |
| `chdir(chemin)` | répertoire courant | oui |
| `syspath_prepend(chemin)` | `sys.path` | oui (`sys.modules` non) |
| `context()` | bloc `with` | à la sortie du bloc |

`raising=False` sur `setattr` / `delattr` / `delitem` / `delenv` pour ne pas
exiger l'existence préalable.

Règle d'or : patcher là où le nom est **utilisé**, pas là où il est défini.
`from x import y` copie le nom dans le module appelant : patcher ce module.

## Exercices

**1. Tester `temperature_en_cache` avec deux villes différentes.**

Indice / corrigé :

```python
def test_cache_par_ville(monkeypatch):
    appels = []
    monkeypatch.setattr(meteo, "appeler_api", lambda v: appels.append(v) or {"temp": len(v)})
    monkeypatch.setattr(meteo, "_CACHE", {})
    assert meteo.temperature_en_cache("Nice") == 4
    assert meteo.temperature_en_cache("Lyon") == 4
    assert meteo.temperature_en_cache("Nice") == 4
    assert appels == ["Nice", "Lyon"]   # Nice servie par le cache la 2e fois
```

**2. `salutation` à 17h59 et 18h00.**

Indice / corrigé : `parametrize("heure, minute, attendu", [(17, 59, "Bonjour"), (18, 0, "Bonsoir")])`
et `FauxDatetime.now` renvoyant `datetime(2024, 1, 1, heure, minute)`.
Le code ne regarde que `.hour`, mais le test documente la frontière.

**3. Fixture `autouse` posant `METEO_API_KEY` pour tous les tests.**

Indice / corrigé : créer `tp06_monkeypatch/conftest.py` :

```python
import pytest

@pytest.fixture(autouse=True)
def _cle_api(monkeypatch):
    monkeypatch.setenv("METEO_API_KEY", "cle-de-test")
```

Puis retirer les `setenv` devenus redondants. Attention :
`test_cle_api_absente` doit toujours faire son `delenv` (il annule la
fixture autouse pour lui seul), et `test_env_restaure` reste valide.

**4. `urlopen` qui lève `TimeoutError`.**

Indice / corrigé :

```python
def test_appeler_api_timeout(monkeypatch):
    monkeypatch.setenv("METEO_API_KEY", "k")

    def urlopen_lent(url, timeout=None):
        raise TimeoutError("trop lent")

    monkeypatch.setattr(meteo.urllib.request, "urlopen", urlopen_lent)
    with pytest.raises(TimeoutError):
        meteo.appeler_api("Lille")
```

Discussion : faut-il que `appeler_api` convertisse en `ConfigError` ou une
exception métier ? Le test rend la question visible.

## Transition vers le TP suivant

Avec `monkeypatch`, on remplace une dépendance par une fonction maison, et
on doit écrire soi-même la liste `urls_appelees` pour savoir ce qui a été
appelé. Le TP07 introduit les objets `Mock` qui font ce travail
automatiquement, avec des assertions dédiées sur les appels.
