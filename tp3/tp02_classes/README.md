# TP02 – Tests sous forme de classes

## En une phrase

Une classe dont le nom commence par `Test` regroupe des tests qui partagent
un sujet et une préparation ; pytest crée une **nouvelle instance pour chaque
test**, ce qui garantit l'isolation sans effort.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- écrire une classe de test collectée par pytest, et pourquoi elle ne doit
  pas avoir de `__init__` ;
- utiliser le cycle de vie « xunit » : `setup_method` / `teardown_method`,
  `setup_class` / `teardown_class`, `setup_module` / `teardown_module`, et
  dans quel ordre ils s'exécutent ;
- expliquer qu'une instance est créée par test et ce que cela implique pour
  `self` ;
- combiner classes et fixtures, imbriquer des classes ;
- lancer une classe ou une méthode précise par son node id ;
- faire tourner une suite `unittest` existante sous pytest et en connaître
  les limites ;
- choisir entre fonction et classe pour organiser ses tests.

## Prérequis

TP01 : découverte des tests, `assert`, `pytest.raises`, options `-v` et `-k`.
Notions de classes Python (méthodes, `self`, `@classmethod`).

## Fichiers

| Fichier | Rôle |
|---|---|
| `panier.py` | Code métier : `Article`, `Panier`, exception `PanierVide` |
| `test_panier.py` | 23 tests en classes, 6 sections numérotées |
| `test_panier_unittest.py` | 2 tests en style `unittest.TestCase`, exécutés par pytest |

## Mise en route

```bash
uv run pytest tp02_classes
```

Sortie attendue : `25 passed` en moins de 0,2 s (23 tests pytest + 2 tests
unittest).

## Déroulé de la présentation

### Le code métier : `panier.py`

Un panier d'achats en mémoire. `Article` est une dataclass avec une propriété
`sous_total`. `Panier` expose `ajouter`, `retirer`, `quantite_de`,
`appliquer_remise`, `total`, `est_vide`, `valider`, et `__len__` (nombre
d'articles distincts). Trois validations lèvent `ValueError` (quantité,
prix, remise hors bornes), `retirer` lève `KeyError`, `valider` lève
`PanierVide`.

```python
def ajouter(self, nom, prix, quantite=1):
    if quantite <= 0:
        raise ValueError("la quantité doit être strictement positive")
    if nom in self._articles:
        self._articles[nom].quantite += quantite
    else:
        self._articles[nom] = Article(nom, prix, quantite)
```

Pourquoi ce choix : un objet **avec état** que chaque test doit recevoir
neuf. C'est exactement le cas où une préparation commune (`setup_method`)
est utile, et où l'isolation entre tests devient un vrai sujet.

### Section 1 : classe simple sans état partagé

- **Ce que montre le code** : `TestArticle` contient deux méthodes qui
  construisent chacune leur `Article`. Pas de setup, pas d'attribut.
- **À dire aux stagiaires** : la classe ne sert ici qu'à **nommer un
  groupe**. Règles de collecte : nom préfixé par `Test` (`python_classes`),
  méthodes préfixées par `test`, aucune classe parente requise. Le premier
  paramètre `self` est obligatoire puisque ce sont des méthodes.
- **À montrer en direct** :

  ```bash
  uv run pytest tp02_classes --collect-only
  ```

  ```
  <Module test_panier.py>
    <Class TestArticle>
      <Function test_sous_total_quantite_1>
      <Function test_sous_total_quantite_multiple>
    <Class TestPanier>
      <Function test_nombre_articles>
      ...
  ```

  Sans `-q`, on voit l'arborescence Module > Class > Function. Puis lancer
  une seule classe et une seule méthode :

  ```bash
  uv run pytest tp02_classes/test_panier.py::TestArticle -v
  uv run pytest tp02_classes/test_panier.py::TestPanier::test_total -v
  ```

- **Pièges et erreurs fréquentes** : oublier `self` dans la signature
  (`TypeError: test_x() takes 0 positional arguments but 1 was given`).
  Nommer la classe `PanierTests` : elle n'est pas collectée, sans aucun
  message, et le stagiaire croit que ses tests passent.

### Section 2 : `setup_method` / `teardown_method`

- **Ce que montre le code** : `TestPanier.setup_method` construit un panier
  avec deux articles ; six tests le manipulent. `test_isolation_entre_tests`
  vérifie qu'il retrouve un panier neuf malgré les modifications faites par
  `test_ajouter_meme_article_cumule_la_quantite` et `test_retirer`.

  ```python
  def setup_method(self, method):
      self.panier = Panier()
      self.panier.ajouter("stylo", 2.0, quantite=3)
      self.panier.ajouter("cahier", 5.0)
  ```

- **À dire aux stagiaires** : `setup_method` s'exécute **avant chaque**
  méthode de test, `teardown_method` **après chaque**, même si le test
  échoue. Le paramètre `method` est la fonction de test qui va s'exécuter ;
  il est optionnel (pytest accepte `def setup_method(self)`). Point capital :
  pytest crée **une instance de la classe par test**. Un attribut posé sur
  `self` dans un test n'existe pas dans le suivant. C'est ce qui rend
  `test_isolation_entre_tests` vrai quel que soit l'ordre d'exécution.
- **À montrer en direct** : dans `test_retirer`, ajouter en fin de test
  `self.panier.ajouter("gomme", 1.0)`, puis relancer : `test_isolation_entre_tests`
  passe toujours puisque `setup_method` a reconstruit le panier. Retirer la
  ligne. Ensuite, commenter `setup_method` entier et relancer : six tests
  échouent avec `AttributeError: 'TestPanier' object has no attribute 'panier'`.
  Remettre.
- **Pièges et erreurs fréquentes** : croire que `self` est partagé et
  vouloir compter des choses dans un attribut d'instance à travers les
  tests. Nommer la méthode `setUp` (camelCase de `unittest`) dans une classe
  pytest : elle n'est pas appelée.

### Section 3 : `setup_class` / `teardown_class`

- **Ce que montre le code** : `TestPanierRemise` compte les appels avec deux
  attributs de classe. `setup_class` (un `@classmethod`) charge un
  « catalogue » une fois ; `setup_method` reconstruit un panier à partir de
  ce catalogue pour chaque test. `test_setup_class_appele_une_seule_fois`
  vérifie les compteurs. `test_remise_invalide` est paramétré (aperçu du
  TP04) et génère trois tests.

  ```python
  @classmethod
  def setup_class(cls):
      cls.compteur_setup_class += 1
      cls.catalogue = {"stylo": 2.0, "cahier": 5.0, "sac": 30.0}
  ```

- **À dire aux stagiaires** : l'ordre complet du cycle de vie « xunit » est
  le suivant, observé avec `-s` sur un fichier de démonstration :

  ```
  setup_module
    setup_class
      setup_method (test_1)
        test_1
      teardown_method (test_1)
      setup_method (test_2)
        test_2
      teardown_method (test_2)
    teardown_class
  teardown_module
  ```

  `setup_class` reçoit `cls` et doit être un `@classmethod` : ce qu'il pose
  sur `cls` est visible de toutes les instances. `setup_module` et
  `teardown_module` sont des fonctions de module (hors classe) appelées une
  fois par fichier. Ces méthodes sont l'héritage de la famille xUnit ; elles
  fonctionnent, mais elles ne se composent pas, ne se partagent pas entre
  fichiers, et n'ont pas de scope intermédiaire. Les fixtures du TP03 les
  remplacent avantageusement.
- **À montrer en direct** : ajouter un `print` dans `setup_class` et dans
  `setup_method`, lancer
  `uv run pytest tp02_classes/test_panier.py::TestPanierRemise -s -v` :
  un seul affichage de `setup_class`, six de `setup_method` (les trois cas
  paramétrés comptent chacun).
- **Pièges et erreurs fréquentes** : oublier `@classmethod` sur
  `setup_class` (pytest l'appelle quand même mais `cls` sera la classe,
  cela fonctionne par accident ; le décorateur reste la forme correcte).
  Modifier dans un test un objet mutable créé par `setup_class` : les tests
  suivants le voient modifié, l'ordre devient significatif.
  `type(self).compteur += 1` est nécessaire pour incrémenter un attribut de
  classe ; `self.compteur += 1` créerait un attribut d'instance.

### Section 4 : classes et fixtures

- **Ce que montre le code** : la fixture `panier_rempli` est définie au
  niveau du module ; `TestValidation.test_valider_panier_rempli` et
  `test_est_vide` la reçoivent en paramètre, `test_valider_panier_vide` n'en
  a pas besoin.

  ```python
  @pytest.fixture
  def panier_rempli():
      panier = Panier()
      panier.ajouter("stylo", 2.0, quantite=3)
      panier.ajouter("cahier", 5.0)
      return panier

  class TestValidation:
      def test_valider_panier_rempli(self, panier_rempli):
          assert panier_rempli.valider() == 11.0
  ```

- **À dire aux stagiaires** : c'est la combinaison la plus courante dans les
  projets réels. La différence avec `setup_method` : chaque test **choisit**
  ce dont il a besoin, la préparation est réutilisable par d'autres classes
  et d'autres fichiers. Le TP03 y est entièrement consacré ; ici, on se
  contente de montrer que les deux approches coexistent.
- **À montrer en direct** : rien de plus que `-v` sur `TestValidation`.
  Annoncer que `--setup-show` sera vu au TP03.
- **Pièges et erreurs fréquentes** : appeler `panier_rempli()` directement
  dans un test (voir TP03 pour le message exact de pytest).

### Section 5 : classes imbriquées

- **Ce que montre le code** : `TestAjouter` contient `TestCasNominaux` et
  `TestCasErreurs`. Les node ids deviennent
  `test_panier.py::TestAjouter::TestCasErreurs::test_prix_negatif`.
- **À dire aux stagiaires** : les classes imbriquées permettent une
  hiérarchie « fonctionnalité > famille de cas ». Chaque niveau doit
  commencer par `Test`. C'est un choix de lisibilité, pas une nécessité : un
  nommage `test_ajouter_prix_negatif` ferait aussi bien pour un petit module.
- **À montrer en direct** :

  ```bash
  uv run pytest tp02_classes -k "TestCasErreurs" -v
  ```

  `-k` filtre aussi sur les noms de classes.
- **Pièges et erreurs fréquentes** : trop de niveaux rend les node ids
  interminables. Une classe interne nommée `Erreurs` (sans `Test`) est
  silencieusement ignorée.

### Section 6 : ce qui n'est pas collecté

- **Ce que montre le code** : `OutilsPanier` (pas de préfixe `Test`) est un
  helper avec une méthode statique. `test_helper_classe`, fonction de module,
  l'utilise.
- **À dire aux stagiaires** : fonctions et classes de test peuvent cohabiter
  dans un même fichier. Une classe utilitaire peut vivre dans le module de
  test tant qu'elle ne commence pas par `Test`.
- **À montrer en direct** : `--collect-only -q | grep -c ::` donne 23 pour
  `test_panier.py`, sans `OutilsPanier`.
- **Pièges et erreurs fréquentes** : nommer un helper `TestData` ou
  `TestConfig` : pytest tente de le collecter. S'il a un `__init__`, on
  obtient l'avertissement de la question fréquente ci-dessous.

### `test_panier_unittest.py` : compatibilité `unittest`

- **Ce que montre le code** : `PanierTestCase(unittest.TestCase)` avec
  `setUp`, `assertEqual`, `assertRaises`.
- **À dire aux stagiaires** : pytest collecte les sous-classes de
  `unittest.TestCase` quel que soit leur nom (ici `PanierTestCase`, sans
  préfixe `Test`), et exécute `setUp` / `tearDown` / `setUpClass`. On peut
  donc migrer une base existante en lançant simplement `pytest`, puis
  convertir fichier par fichier. Ce qu'on gagne immédiatement : la sélection
  `-k`, `--lf`, les marqueurs, les plugins, et l'introspection des `assert`
  nus si on en ajoute. Ce qui ne marche **pas** : injecter une fixture en
  paramètre d'une méthode `TestCase` (seules les fixtures `autouse` sont
  possibles, TP03), et paramétrer avec `@pytest.mark.parametrize`.
- **À montrer en direct** :

  ```bash
  uv run pytest tp02_classes/test_panier_unittest.py -v
  ```

  Les deux tests apparaissent comme `PanierTestCase::test_total PASSED`.
- **Pièges et erreurs fréquentes** : mélanger les deux styles dans une même
  classe (`setUp` et `setup_method`). Choisir un style par classe, et viser
  la conversion complète à terme.

### Choisir entre fonction et classe

À dire en synthèse. Une classe se justifie quand :

- plusieurs tests partagent une préparation ou un sujet et qu'on veut les
  lancer ensemble par `::TestXxx` ;
- on veut poser un marqueur (TP05) ou `@pytest.mark.usefixtures` (TP03) sur
  tout un groupe d'un coup ;
- on veut une fixture `scope="class"` (TP03).

Sinon, les fonctions de module suffisent et restent plus simples. Les deux
approches sont équivalentes fonctionnellement : c'est de l'organisation.

## Questions fréquentes des stagiaires

**Pourquoi pas de `__init__` dans une classe de test ?**
Parce que pytest instancie la classe lui-même, sans argument, pour chaque
test. Un `__init__` personnalisé le mettrait en difficulté ; il préfère
ignorer la classe avec l'avertissement
`PytestCollectionWarning: cannot collect test class 'TestAvecInit' because it
has a __init__ constructor`. Aucun test de la classe ne tourne, et la session
se termine par `1 warning` sans échec : très facile à rater.

**Une instance par test, vraiment ? Ce n'est pas coûteux ?**
Oui, une instance par test. Le coût est négligeable (une allocation d'objet).
C'est le prix de l'isolation : aucun test ne peut polluer le suivant via
`self`.

**Comment partager un objet coûteux entre les tests d'une classe ?**
`setup_class` avec `cls.objet = ...`, ou mieux une fixture
`scope="class"` (TP03). Dans les deux cas, ne pas modifier cet objet dans
les tests, sinon l'ordre d'exécution devient significatif.

**Peut-on hériter d'une classe de test pour réutiliser des tests ?**
Oui. Une classe `TestBase` avec des tests, puis `class TestImplA(TestBase)`
qui surcharge un setup : les tests de la base sont exécutés pour chaque
sous-classe. Attention, `TestBase` elle-même est aussi collectée ; la nommer
sans préfixe `Test` (`_BaseTests`) évite cela. Le TP11 montre une alternative
plus idiomatique avec une fixture paramétrée.

**`setup_method` ou fixture, que choisir ?**
Fixture, sauf pour convertir du code xunit existant. Les fixtures se
composent, se partagent via `conftest.py`, ont des scopes, et se
sélectionnent test par test.

**Faut-il un `teardown_method` si on ne libère rien ?**
Non. Il est utile pour fermer un fichier, une connexion, ou restaurer un
état global. Dans `TestPanier`, il est présent à titre d'illustration.

**`-k TestPanier` sélectionne aussi `TestPanierRemise` ?**
Oui, `-k` fait une recherche de sous-chaîne. Pour cibler précisément,
utiliser le node id complet `tp02_classes/test_panier.py::TestPanier`.

**Peut-on mélanger `unittest.TestCase` et paramétrage ?**
Non. `@pytest.mark.parametrize` ne fonctionne pas sur les méthodes
`TestCase`. Il faut convertir la classe en style pytest, ou utiliser
`subTest` de `unittest`.

## Ce qu'il faut retenir

| Sujet | À retenir |
|---|---|
| Collecte | `class Test*`, méthodes `test*`, pas de `__init__`, pas d'héritage requis |
| Instance | une nouvelle instance par test ; `self` n'est pas partagé |
| Par test | `setup_method(self, method)` / `teardown_method` |
| Par classe | `@classmethod setup_class(cls)` / `teardown_class` |
| Par module | `setup_module()` / `teardown_module()` |
| Ordre | module > class > method > test > method > class > module |
| Node id | `fichier.py::Classe::Interne::methode` ; `-k` filtre sur tout |
| unittest | collecté et exécuté, mais sans fixtures en paramètre ni `parametrize` |
| Choix | classe pour grouper, sélectionner, marquer ; sinon fonctions |

## Exercices

1. **Ajouter `vider()` à `Panier`** et la tester dans une classe `TestVider`
   avec un `setup_method`.

   Indice / corrigé :

   ```python
   # panier.py
   def vider(self) -> None:
       self._articles.clear()
       self._remise = 0.0

   # test_panier.py
   class TestVider:
       def setup_method(self):
           self.panier = Panier()
           self.panier.ajouter("stylo", 2.0)

       def test_vider(self):
           self.panier.vider()
           assert self.panier.est_vide()
           assert len(self.panier) == 0
   ```

2. **Convertir `test_panier_unittest.py` en style pytest natif.**

   Indice / corrigé :

   ```python
   class TestPanierConverti:
       def setup_method(self):
           self.panier = Panier()
           self.panier.ajouter("stylo", 2.0, quantite=2)

       def test_total(self):
           assert self.panier.total() == 4.0

       def test_retirer_inconnu(self):
           with pytest.raises(KeyError):
               self.panier.retirer("gomme")
   ```

   Faire remarquer que `assertEqual(a, b)` devient `assert a == b` et
   `assertRaises` devient `pytest.raises`.

3. **Ajouter un `__init__` à `TestArticle`**, lancer, lire l'avertissement,
   puis le retirer.

   Indice / corrigé : la sortie se termine par `23 passed, 1 warning` au
   lieu de `25 passed` ; les deux tests de `TestArticle` ont disparu sans
   échec. C'est l'occasion de dire qu'en CI on peut transformer les
   avertissements en erreurs avec `-W error` ou `filterwarnings = ["error"]`.

4. **Exercice supplémentaire : prouver l'ordre du cycle de vie.** Dans un
   nouveau fichier `test_cycle.py`, écrire `setup_module`, `setup_class`,
   `setup_method` et leurs `teardown` avec des `print`, puis lancer avec
   `-s`.

   Indice / corrigé : reprendre la trace donnée dans la section 3. Sans
   `-s`, les `print` sont capturés et invisibles (voir `capsys` au TP08).

5. **Exercice supplémentaire : classe partagée mutable.** Dans
   `TestPanierRemise`, faire modifier `cls.catalogue` par un test
   (`self.catalogue["stylo"] = 100`) et observer quels tests cassent selon
   l'ordre.

   Indice / corrigé : les tests suivants dans le fichier voient le prix
   modifié et `test_sans_remise` échoue s'il passe après. Leçon : un état
   de classe doit être en lecture seule.

## Transition vers le TP suivant

`setup_method` prépare un objet pour tous les tests d'une classe, sans
choix possible et sans partage entre fichiers. Le TP03 introduit les
**fixtures** : des fonctions de préparation nommées, que chaque test demande
explicitement, réutilisables partout via `conftest.py`, avec un nettoyage
garanti et un scope réglable.
