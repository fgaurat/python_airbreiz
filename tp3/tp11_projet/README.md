# TP11 – Projet fil rouge : gestion de stock

## En une phrase

Une petite application réaliste (modèle, persistance, client HTTP, service
métier, ligne de commande) testée avec toutes les techniques vues dans les
TP01 à TP10, organisée comme un vrai projet avec un paquet `stock/` et un
répertoire `tests/`.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- structurer un projet testable : injection de dépendances, interface
  commune (`Protocol`), frontière réseau isolée dans une seule classe ;
- écrire un `conftest.py` de projet : données de test, fakes, mocks,
  fixture paramétrée qui fait tourner une suite contre plusieurs
  implémentations ;
- choisir le bon outil pour chaque couche : test unitaire pur pour le
  modèle, fake pour le dépôt, mock pour le client HTTP, `tmp_path` et
  `capsys` pour la CLI, scénario d'intégration bout en bout ;
- protéger la suite contre les appels réseau accidentels ;
- lire un rapport de couverture et comprendre ce qu'il ne garantit pas ;
- appliquer la pyramide des tests à un projet concret.

## Prérequis

TP03 (fixtures, `conftest.py`), TP04 (fixtures paramétrées), TP05
(marqueur `integration`), TP06 (`monkeypatch`), TP07 (`mocker`, fakes,
injection de dépendances), TP08 (`tmp_path`, `capsys`, `caplog`). Le TP09
sert pour les commandes de couverture et de parallélisation.

## Fichiers

| Fichier | Rôle |
|---|---|
| `stock/modeles.py` | `Produit` : dataclass validée, `en_rupture`, `prix_ttc`, `to_dict` / `from_dict` |
| `stock/depot.py` | `Depot` (Protocol), `DepotMemoire` (fake), `DepotJSON` (fichier), `ProduitInconnu` |
| `stock/tarification.py` | `ClientTaux` : appel HTTP avec `urllib`, `ServiceTauxIndisponible` |
| `stock/service.py` | `ServiceStock` : règles métier, logs, `StockInsuffisant` |
| `stock/cli.py` | `main(argv)` avec `argparse`, codes de retour |
| `tests/conftest.py` | garde-fou réseau, produits de test, fixture `depot` paramétrée, `client_taux` mocké, `service` |
| `tests/test_modeles.py` | tests unitaires purs, paramétrés |
| `tests/test_depot.py` | `TestContratDepot` (les deux implémentations) et `TestDepotJSON` |
| `tests/test_tarification.py` | `urlopen` patché avec `mocker` |
| `tests/test_service.py` | service avec dépôt en mémoire et client mocké, logs, garde-fou |
| `tests/test_cli.py` | `capsys`, `tmp_path`, `monkeypatch.chdir`, `SystemExit` |
| `tests/test_integration.py` | scénario complet sur fichier réel, `skipif` par environnement |

Tableau de correspondance entre les techniques et l'endroit où les montrer :

| Technique | Où la voir | TP d'origine |
|---|---|---|
| Fonctions et classes de test | partout | TP01, TP02 |
| Fixtures, `conftest.py`, `yield` | `tests/conftest.py` | TP03 |
| Fixture `autouse` | `_pas_de_reseau` | TP03 |
| Fixture paramétrée + `getfixturevalue` | `depot` | TP04 |
| `parametrize` empilé, `ids` | `test_modeles.py`, `TestMouvements.test_quantite_invalide` | TP04 |
| Marqueur de module, `skipif` avec chaîne | `test_integration.py` | TP05 |
| `monkeypatch.setattr` sur `socket`, `chdir` | `conftest.py`, `test_cli.py` | TP06 |
| `mocker.Mock`, `return_value`, `side_effect`, `assert_called_once_with` | `client_taux`, `TestValeurStock` | TP07 |
| `mocker.patch` d'`urlopen` | `test_tarification.py` | TP07 |
| Fake (`DepotMemoire`) et injection de dépendances | `ServiceStock.__init__`, fixture `service` | TP07 |
| `tmp_path`, `capsys`, `caplog` | `test_depot.py`, `test_cli.py`, `test_service.py` | TP08 |
| Couverture, xdist, option `--env` | commandes ci-dessous | TP09, TP10 |

## Mise en route

```bash
uv run pytest tp11_projet -v
```

Sortie attendue : `63 passed` en moins d'une seconde. Le décompte détaillé :
`test_modeles` 12, `test_depot` 15 (6 tests de contrat x 2 implémentations
+ 3 spécifiques JSON), `test_tarification` 8, `test_service` 19, `test_cli`
6, `test_integration` 2.

Commandes à préparer pour la démonstration :

```bash
uv run pytest tp11_projet --collect-only -q          # les ids [memoire] / [json]
uv run pytest tp11_projet -m "not integration"
uv run pytest tp11_projet -k json                    # seulement l'implémentation fichier
uv run pytest tp11_projet --cov=tp11_projet/stock --cov-report=term-missing
uv run pytest tp11_projet --cov=tp11_projet/stock --cov-report=html && open htmlcov/index.html
uv run pytest tp11_projet -n auto
uv run pytest tp11_projet --env prod -ra
uv run pytest tp11_projet --durations=5
```

Et l'application elle-même, pour montrer qu'elle fonctionne vraiment :

```bash
uv run python -m tp11_projet.stock.cli --fichier /tmp/stock.json ajouter STY-01 "Stylo bleu" 1.5 --quantite 10
uv run python -m tp11_projet.stock.cli --fichier /tmp/stock.json lister
uv run python -m tp11_projet.stock.cli --fichier /tmp/stock.json sortir STY-01 20
```

## Déroulé de la présentation

Ordre conseillé : présenter d'abord le code métier de bas en haut (modèle,
dépôt, client HTTP, service, CLI), puis les tests dans le même ordre, en
commençant par le `conftest.py`. Comptez environ 45 minutes de présentation
puis 1 h 15 d'exercices.

### stock/modeles.py : le modèle

- **Ce que montre le code** : une dataclass `Produit` avec validation dans
  `__post_init__` (référence obligatoire, prix et quantité positifs), une
  propriété `en_rupture` (`quantite <= seuil_alerte`), un calcul `prix_ttc`
  arrondi à 2 décimales et une sérialisation `to_dict` / `from_dict` où la
  date passe par `isoformat` / `fromisoformat`.
- **À dire aux stagiaires** : ce module ne dépend de rien. C'est la couche la
  plus facile à tester, et celle où l'on veut le plus de tests unitaires purs.
  La validation est faite ici, une seule fois, pour toutes les implémentations
  de dépôt.
- **À montrer en direct** : `Produit("", "x", 1.0)` dans un shell Python pour
  voir la `ValueError`.
- **Pièges** : `date_creation` utilise `field(default_factory=date.today)`.
  Un défaut mutable ou une valeur évaluée une seule fois à l'import serait
  un bug classique de dataclass.

### stock/depot.py : deux implémentations, une interface

- **Ce que montre le code** : `Depot` est un `typing.Protocol` avec quatre
  méthodes (`sauvegarder`, `charger`, `tous`, `supprimer`). `DepotMemoire`
  est un dictionnaire, `DepotJSON` relit et réécrit un fichier à chaque
  opération. Les deux lèvent `ProduitInconnu`, qui hérite de `KeyError`.

  ```python
  class Depot(Protocol):
      def sauvegarder(self, produit: Produit) -> None: ...
      def charger(self, reference: str) -> Produit: ...
      def tous(self) -> list[Produit]: ...
      def supprimer(self, reference: str) -> None: ...
  ```

- **À dire aux stagiaires** : `DepotMemoire` n'est pas seulement un outil de
  test, c'est un vrai *fake* (vu au TP07) : une implémentation complète mais
  simplifiée. Il sert dans les tests du service pour ne pas toucher au disque.
  `Protocol` permet le typage structurel : aucune des deux classes n'hérite
  de `Depot`, il suffit qu'elles aient les bonnes méthodes.
- **À montrer en direct** : ouvrir un fichier `stock.json` généré par la CLI
  pour montrer le format (`indent=2`, `ensure_ascii=False`).
- **Pièges** : `tous()` trie par référence dans les deux implémentations.
  C'est une décision de contrat : le test `test_tous_trie_par_reference`
  l'impose à toute implémentation future.

### stock/tarification.py : la frontière réseau

- **Ce que montre le code** : `ClientTaux.taux(devise)` fait un vrai appel
  HTTP avec `urllib.request.urlopen`. Deux familles d'erreurs sont
  converties en `ServiceTauxIndisponible` : les `OSError` (réseau, DNS,
  timeout) et les réponses mal formées (`KeyError`, `TypeError`,
  `ValueError`). Le cas `EUR` court-circuite l'appel.
- **À dire aux stagiaires** : c'est le seul endroit du projet qui parle au
  réseau. Isoler la frontière dans une classe de quelques lignes, c'est ce
  qui rend tout le reste testable sans patch. Le service ne connaît que
  l'exception métier `ServiceTauxIndisponible`, jamais `urllib`.
- **Pièges** : l'ordre des deux blocs `try` compte. Si on mettait
  `json.loads` dans le second, une réponse non JSON lèverait
  `json.JSONDecodeError`, qui hérite de `ValueError`, donc serait bien
  attrapée, mais avec un message moins précis.

### stock/service.py : les règles métier

- **Ce que montre le code** : `ServiceStock(depot, client_taux=None)`
  reçoit ses deux dépendances. `ajouter_produit` refuse les doublons,
  `entrer_stock` et `sortir_stock` valident la quantité, `sortir_stock`
  lève `StockInsuffisant` et journalise un `WARNING` sous le seuil,
  `valeur_stock` se replie sur le taux 1.0 avec un `ERROR` dans les logs si
  le service de taux est indisponible.

  ```python
  def __init__(self, depot: Depot, client_taux: ClientTaux | None = None):
      self.depot = depot
      self.client_taux = client_taux or ClientTaux()
  ```

- **À dire aux stagiaires** : voilà l'injection de dépendances (vue au
  TP07). En production, `cli.py` passe un `DepotJSON` et laisse le
  `ClientTaux` par défaut. En test, on passe un `DepotMemoire` et un
  `Mock`. Aucun `patch` nécessaire pour tester le service.
- **À montrer en direct** : le repli de `valeur_stock` quand le taux est
  indisponible. Demander aux stagiaires si ce comportement (renvoyer une
  valeur en EUR alors qu'on a demandé des USD) est une bonne idée : c'est un
  choix métier discutable, et le test `test_service_taux_indisponible`
  documente ce choix.
- **Pièges** : `ajouter_produit` utilise `try / except ProduitInconnu /
  else`. Le `else` d'un `try` s'exécute seulement si aucune exception n'a
  été levée : c'est la façon propre d'écrire « si le produit existe déjà ».

### stock/cli.py : la ligne de commande

- **Ce que montre le code** : `main(argv=None)` renvoie un code de retour
  entier au lieu d'appeler `sys.exit` directement. Les erreurs métier vont
  sur `stderr` avec le code 1. Le bloc `if __name__ == "__main__"` porte un
  `# pragma: no cover`.
- **À dire aux stagiaires** : une CLI testable prend `argv` en paramètre et
  renvoie un code. `sys.exit(main())` n'est appelé qu'au tout dernier niveau.
  Ce pattern vaut pour n'importe quel point d'entrée : un `main` Flask, un
  handler de tâche, etc.
- **Pièges** : `argparse` appelle `sys.exit(2)` lui-même en cas d'arguments
  invalides. On ne peut pas l'intercepter par un code de retour, d'où le
  test avec `pytest.raises(SystemExit)`.

### tests/conftest.py : les fondations

Le fichier se lit en quatre blocs.

**Bloc 1 : le garde-fou réseau**

```python
@pytest.fixture(autouse=True)
def _pas_de_reseau(monkeypatch):
    def interdit(*args, **kwargs):
        raise RuntimeError("accès réseau interdit pendant les tests")
    monkeypatch.setattr(socket, "getaddrinfo", interdit)
    monkeypatch.setattr(socket, "socket", interdit)
```

- **Ce que montre le code** : une fixture `autouse` (TP03) qui, pour chaque
  test du répertoire, remplace deux fonctions du module `socket` par une
  fonction qui lève `RuntimeError`.
- **À dire aux stagiaires** : trois questions à poser et à répondre.
  Pourquoi `autouse` ? Parce que la protection doit s'appliquer même au test
  qui a oublié de la demander. Pourquoi les deux fonctions ? Parce que
  `urllib` appelle d'abord `socket.getaddrinfo` pour résoudre le nom DNS,
  puis `socket.socket` pour ouvrir la connexion. Sur une machine hors ligne,
  la résolution DNS échoue avec `socket.gaierror`, qui est un `OSError`, que
  `ClientTaux` attrape gentiment : le test passerait en silence au lieu de
  signaler l'oubli. Pourquoi `RuntimeError` et pas `OSError` ? Justement
  parce que `ClientTaux` attrape `OSError` : on choisit une exception que le
  code métier ne rattrape pas, pour qu'elle remonte jusqu'au rapport.
- **À montrer en direct** : créer un fichier temporaire
  `tests/test_zz_demo.py` avec un test qui oublie le mock, puis le lancer :

  ```python
  from tp11_projet.stock.service import ServiceStock

  def test_oubli_du_mock(depot_memoire):
      ServiceStock(depot_memoire).valeur_stock("USD")
  ```

  ```
  tp11_projet/tests/conftest.py:21: in interdit
      raise RuntimeError("accès réseau interdit pendant les tests")
  E   RuntimeError: accès réseau interdit pendant les tests
  FAILED tp11_projet/tests/test_zz_demo.py::test_oubli_du_mock
  ```

  Supprimer le fichier ensuite.
- **Pièges** : ce garde-fou est limité au répertoire `tests/` du TP11. Dans
  un vrai projet, on le met dans le `conftest.py` racine. Les plugins
  `pytest-socket` ou `pytest-recording` font la même chose en mieux.

**Bloc 2 : les données de test**

- **Ce que montre le code** : `produit_stylo` (100 unités, au-dessus du
  seuil) et `produit_cahier` (4 unités, sous le seuil de 5). Scope
  `function` : chaque test reçoit un objet neuf.
- **À dire aux stagiaires** : les valeurs sont choisies pour que les
  assertions soient calculables de tête : 100 x 1.50 = 150, 4 x 3.20 = 12.80,
  total 162.80. Nommer les fixtures d'après le rôle de la donnée, pas d'après
  sa forme.

**Bloc 3 : la fixture `depot` paramétrée**

```python
@pytest.fixture(params=["memoire", "json"])
def depot(request):
    return request.getfixturevalue(f"depot_{request.param}")
```

- **Ce que montre le code** : une fixture paramétrée (TP04) qui délègue à
  `depot_memoire` ou `depot_json` selon `request.param`.
- **À dire aux stagiaires** : `request.getfixturevalue(nom)` demande une
  fixture par son nom, dynamiquement, au lieu de la déclarer en paramètre.
  On l'utilise ici parce qu'on ne veut instancier que l'implémentation
  demandée : déclarer `depot(request, depot_memoire, depot_json)` créerait
  les deux à chaque test, y compris un fichier dans `tmp_path` pour rien.
  Résultat : tout test qui demande `depot` s'exécute deux fois, avec les ids
  `[memoire]` et `[json]`. Ajouter une troisième implémentation revient à
  ajouter une chaîne dans `params` et une fixture `depot_xxx`.
- **À montrer en direct** :

  ```
  $ uv run pytest tp11_projet --collect-only -q | grep Contrat
  tp11_projet/tests/test_depot.py::TestContratDepot::test_vide_au_depart[memoire]
  tp11_projet/tests/test_depot.py::TestContratDepot::test_vide_au_depart[json]
  tp11_projet/tests/test_depot.py::TestContratDepot::test_sauvegarder_et_charger[memoire]
  tp11_projet/tests/test_depot.py::TestContratDepot::test_sauvegarder_et_charger[json]
  ...
  ```

**Bloc 4 : le client mocké et le service**

- **Ce que montre le code** : `client_taux` est un `mocker.Mock()` dont
  `taux.return_value = 1.0`. `service` assemble un `DepotMemoire` pré-rempli
  avec les deux produits et ce client.
- **À dire aux stagiaires** : la fixture `service` est le point d'entrée de
  la plupart des tests. Un `Mock` pour le client car on veut vérifier les
  appels (`assert_called_once_with`), un fake pour le dépôt car on veut un
  comportement réel sans I/O.

### tests/test_modeles.py : tests unitaires purs

- **Ce que montre le code** : `TestValidation.test_valeurs_invalides` est
  paramétré avec des `ids` lisibles (`reference-vide`, `prix-negatif`,
  `quantite-negative`) et fusionne un dictionnaire de base avec le cas
  invalide : `Produit(**{**base, **kwargs})`. `test_prix_ttc` utilise
  `pytest.approx`, `test_en_rupture` teste les bornes (5 est en rupture, 6
  ne l'est pas), `test_aller_retour_dict` vérifie la sérialisation.
- **À dire aux stagiaires** : ces tests s'exécutent en microsecondes et ne
  demandent aucune fixture d'infrastructure. C'est la base de la pyramide.
- **Pièges** : tester les bornes exactes (`<=` contre `<`) est ce qui
  distingue un test utile d'un test décoratif.

### tests/test_depot.py : le contrat et le spécifique

- **Ce que montre le code** : `TestContratDepot` contient six tests qui ne
  savent pas quelle implémentation ils testent. `TestDepotJSON` contient
  trois tests qui n'ont de sens que pour le fichier : création au premier
  enregistrement, format lisible, persistance entre deux instances.
- **À dire aux stagiaires** : c'est le pattern « tests de contrat ». Le jour
  où l'on ajoute PostgreSQL (TP13) ou SQLite (exercice 3), les six tests
  sont réutilisés sans une ligne de modification. Le contrat inclut les cas
  d'erreur : `ProduitInconnu` sur `charger` et sur `supprimer`.
- **À montrer en direct** : `uv run pytest tp11_projet/tests/test_depot.py -v`
  pour voir les 15 lignes, puis `-k json` pour n'en garder que 9.
- **Pièges** : `test_sauvegarder_ecrase` modifie `produit_stylo.quantite`
  puis resauvegarde. Avec `DepotMemoire`, l'objet stocké est le même que
  celui du test (pas de copie), alors qu'avec `DepotJSON` c'est une
  nouvelle instance. Le test passe dans les deux cas parce qu'il relit via
  `charger`. Bon exemple de subtilité qu'un contrat doit tolérer.

### tests/test_tarification.py : patcher la frontière

- **Ce que montre le code** : `_reponse(donnees)` fabrique un objet qui
  imite le retour d'`urlopen` : `closing(io.BytesIO(...))` fournit à la fois
  `read()` et le gestionnaire de contexte. Chaque test fait
  `mocker.patch("tp11_projet.stock.tarification.urllib.request.urlopen")`.
  On teste l'URL construite, le timeout, l'erreur réseau (`side_effect=OSError`),
  quatre réponses mal formées (paramétrées), et le court-circuit `EUR`
  (`assert_not_called`).
- **À dire aux stagiaires** : on patche là où le nom est utilisé, comme au
  TP06 et TP07. Le garde-fou réseau est toujours actif dans ces tests, mais
  il n'est jamais atteint puisque `urlopen` est remplacé avant.
- **Pièges** : `closing` est nécessaire parce que le code fait
  `with urlopen(...) as rep`. Un simple `BytesIO` fonctionnerait aussi (il
  est lui-même un gestionnaire de contexte), mais `closing` rend l'intention
  explicite.

### tests/test_service.py : le cœur

- **`TestAjouterProduit`** : ajout, doublon (`match="existe déjà"`), et
  vérification du log `INFO` avec `caplog.at_level(logging.INFO, logger="stock")`.
  Rappeler que sans `at_level`, le niveau `INFO` n'est pas capturé (TP08).
- **`TestMouvements`** : entrée, sortie, quantités invalides en `parametrize`
  empilé (2 méthodes x 2 valeurs = 4 tests, `getattr(service, methode)`),
  `StockInsuffisant` avec vérification que le stock est inchangé après
  l'échec, `ProduitInconnu`, et les deux tests sur l'alerte de seuil :
  présence d'un `WARNING` après une sortie de 96 (reste 4), absence après
  une sortie de 10.
- **`TestRupture`** et **`TestValeurStock`** : avec les valeurs de test,
  `valeur_stock()` vaut 162.80 en EUR, 179.08 en USD au taux 1.10.
  `client_taux.taux.assert_called_once_with("USD")` vérifie la collaboration.
  `test_service_taux_indisponible` positionne `side_effect =
  ServiceTauxIndisponible("timeout")` et vérifie le repli et le log `ERROR`.
- **`test_le_garde_fou_reseau_fonctionne`** : construit un `ServiceStock`
  sans client mocké, donc avec le vrai `ClientTaux`, et attend
  `RuntimeError` avec `match="réseau interdit"`. C'est un test du
  `conftest.py` lui-même. Si quelqu'un retire le garde-fou, ce test échoue.
- **À montrer en direct** : introduire un bug dans `sortir_stock`
  (`+=` au lieu de `-=`), relancer :

  ```
  FAILED tp11_projet/tests/test_cli.py::test_sortir
  FAILED tp11_projet/tests/test_integration.py::test_scenario_complet
  FAILED tp11_projet/tests/test_service.py::TestMouvements::test_sortir
  FAILED tp11_projet/tests/test_service.py::TestMouvements::test_alerte_seuil
  4 failed, 59 passed
  ```

  Faire remarquer que le test unitaire du service, le test de la CLI et le
  test d'intégration échouent tous : c'est normal et souhaitable, chaque
  couche a son test. Le premier à lire est celui du service, le plus
  proche du bug. Remettre `-=`.

  Deuxième expérience, plus troublante : remplacer `<` par `<=` dans
  `if produit.quantite < quantite`. Résultat : `63 passed`. Aucun test ne
  sort exactement toute la quantité disponible. Couverture 100 %, bug
  non détecté. C'est l'introduction parfaite à la section suivante et à
  l'exercice 1. Remettre `<`.

### tests/test_cli.py : sortie standard et codes de retour

- **Ce que montre le code** : une fixture locale `fichier` donne un chemin
  dans `tmp_path`. Chaque test appelle `cli.main([...])` avec une liste
  d'arguments et lit `capsys.readouterr()`. `test_erreur_metier_sur_stderr`
  vérifie que `out` est vide et que `err` contient le message.
  `test_commande_manquante` attend `SystemExit` de code 2.
  `test_fichier_par_defaut_dans_cwd` utilise `monkeypatch.chdir(tmp_path)`.
- **À dire aux stagiaires** : `capsys.readouterr()` vide le tampon. Dans
  `test_sortir`, l'appel intermédiaire sert à jeter la sortie de la commande
  `ajouter` pour ne lire que celle de `sortir`.
- **Pièges** : ne jamais lancer ces tests avec `-s`, la capture serait
  désactivée et `capsys` renverrait des chaînes vides.

### tests/test_integration.py : bout en bout

- **Ce que montre le code** : `pytestmark = pytest.mark.integration` marque
  tout le module. `client_taux_fixe` répond avec un dictionnaire de taux via
  `side_effect`. `test_scenario_complet` enchaîne des opérations sur un
  `DepotJSON` réel, puis recrée un second service sur le même fichier pour
  prouver la persistance, et vérifie `caplog.text`.
  `test_skip_conditionnel_par_env` utilise la forme chaîne de `skipif` :

  ```python
  @pytest.mark.skipif("config.getoption('--env') == 'prod'", reason="jamais contre la prod")
  ```

- **À dire aux stagiaires** : quand la condition de `skipif` est une
  chaîne, pytest l'évalue avec `eval` dans un espace de noms qui contient
  `config`, `os`, `sys` et `platform`. C'est la seule façon d'accéder à une
  option de ligne de commande dans un décorateur, puisque `config` n'existe
  pas encore au moment où le module est importé.
- **À montrer en direct** :

  ```
  $ uv run pytest tp11_projet --env prod -ra
  SKIPPED [1] tp11_projet/tests/test_integration.py:34: jamais contre la prod
  62 passed, 1 skipped
  ```

- **Pièges** : un seul test d'intégration suffit ici. Il est lent par
  nature (fichier réel) et fragile (dépend de tout). La règle : peu de
  tests d'intégration, larges ; beaucoup de tests unitaires, étroits.

### Couverture et parallélisation

```
$ uv run pytest tp11_projet --cov=tp11_projet/stock --cov-report=term-missing
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

- **À dire aux stagiaires** : 100 % de lignes couvertes signifie que chaque
  ligne a été exécutée au moins une fois. Cela ne dit rien sur la qualité
  des assertions (le bug `<=` passe inaperçu), ni sur les branches non
  prises (`--cov-branch` aide), ni sur les combinaisons d'états. La
  couverture sert à trouver ce qui n'est pas testé du tout, pas à prouver
  que c'est bien testé. Pour aller plus loin : le *mutation testing*
  (`mutmut`, `cosmic-ray`) introduit des bugs automatiquement et compte
  ceux que la suite détecte.
- `uv run pytest tp11_projet -n auto` : 63 tests répartis sur tous les
  cœurs. Cela fonctionne parce qu'aucun test ne partage d'état : chaque
  fichier est dans son `tmp_path`, chaque `DepotMemoire` est neuf.

### La pyramide des tests appliquée au projet

| Niveau | Fichiers | Nombre | Vitesse | Ce qui est simulé |
|---|---|---|---|---|
| Unitaire pur | `test_modeles.py` | 12 | µs | rien |
| Unitaire avec doublures | `test_depot.py`, `test_tarification.py`, `test_service.py` | 42 | ms | réseau (mock), disque (fake ou `tmp_path`) |
| Composant | `test_cli.py` | 6 | ms | rien sauf le répertoire |
| Intégration | `test_integration.py` | 2 | ms ici, secondes en vrai | réseau seulement |
| Intégration réelle | TP13 | 15 | secondes | rien |

## Questions fréquentes des stagiaires

**Pourquoi ne pas tester `ServiceStock` directement avec `DepotJSON` et
`tmp_path` plutôt qu'avec `DepotMemoire` ?**
On pourrait, et le test d'intégration le fait. Mais le dépôt en mémoire est
plus rapide, ne dépend pas du système de fichiers, et surtout isole le
service : si `DepotJSON` a un bug, seuls les tests de `test_depot.py`
échouent, pas ceux du service.

**`request.getfixturevalue` fonctionne-t-il avec n'importe quelle fixture ?**
Oui, y compris celles des `conftest.py` parents et les fixtures intégrées.
Limite : la fixture demandée doit avoir un scope compatible, et le nom est
une chaîne, donc pas de vérification statique. À réserver aux cas
dynamiques comme celui-ci.

**Pourquoi `ProduitInconnu` hérite-t-elle de `KeyError` ?**
Pour que du code existant qui attrape `KeyError` continue de fonctionner, et
parce que sémantiquement c'est une clé absente. Le test utilise le type
précis `ProduitInconnu`, ce qui évite d'attraper par erreur un `KeyError`
venu d'ailleurs.

**Le garde-fou bloque-t-il aussi `requests` ou `httpx` ?**
Oui, toutes ces bibliothèques finissent par appeler `socket.getaddrinfo`
puis `socket.socket`. Il ne bloque pas les connexions Unix locales ni les
sockets déjà ouverts avant le test.

**Pourquoi `mocker.Mock()` et pas `Mock(spec=ClientTaux)` ?**
`spec=ClientTaux` serait mieux (TP07) : il refuserait `client.tau()` avec
une faute de frappe. C'est laissé tel quel pour la lisibilité ; en faire un
point d'amélioration avec les stagiaires.

**Comment tester `cli.py` sans passer par `main` ?**
`construire_parser()` est une fonction séparée précisément pour pouvoir
tester le parsing seul : `construire_parser().parse_args(["lister"]).commande == "lister"`.

**Que se passe-t-il si deux tests écrivent le même `stock.json` ?**
Impossible : chaque test reçoit son propre `tmp_path`. C'est ce qui rend
`-n auto` sûr. Le seul fichier partagé serait celui du test
`test_fichier_par_defaut_dans_cwd`, mais il change de répertoire courant
avant d'écrire.

**Le marqueur `integration` est-il obligatoire ?**
Non, mais il permet `-m "not integration"` pour une boucle de développement
rapide et `-m integration` en CI nocturne. Avec `--strict-markers`, il doit
être déclaré dans `pyproject.toml`, ce qui est fait.

**Où mettre les tests dans un projet réel : à côté du code ou dans
`tests/` ?**
Les deux se voient. `tests/` séparé est le plus courant pour une
application ; à côté du code convient aux bibliothèques. Ce TP montre la
première forme, les TP01 à TP10 la seconde.

## Ce qu'il faut retenir

| Décision de conception | Bénéfice pour les tests |
|---|---|
| Dépendances passées au constructeur | fakes et mocks sans `patch` |
| Interface commune (`Protocol`) | une suite de contrat pour toutes les implémentations |
| Réseau isolé dans `ClientTaux.taux` | un seul point à patcher |
| `main(argv)` renvoie un code | CLI testable avec `capsys` |
| Garde-fou `autouse` sur `socket` | aucun appel réseau accidentel |
| Fixture `depot` paramétrée + `getfixturevalue` | ajout d'une implémentation en deux lignes |
| Valeurs de test calculables de tête | assertions lisibles |

Et trois messages : chaque couche a son niveau de test ; la couverture
mesure l'absence de tests, pas leur qualité ; un test du `conftest.py`
(`test_le_garde_fou_reseau_fonctionne`) vaut la peine quand le `conftest.py`
porte une règle de sécurité.

## Exercices

### 1. Couverture et test manquant

Le rapport affiche 100 %, pourtant le bug `<=` dans `sortir_stock` n'est
pas détecté. Écrire le test qui le détecte, puis activer `--cov-branch`.

**Indice / corrigé** : il manque le cas limite « sortir exactement le stock
disponible ».

```python
def test_sortir_tout_le_stock(self, service):
    assert service.sortir_stock("STY-01", 100).quantite == 0
    assert service.depot.charger("STY-01").en_rupture
```

Avec `--cov-branch`, la colonne `Branch` apparaît. Le `if __name__ ==
"__main__"` de `cli.py` est exclu par `# pragma: no cover`. Pour aller plus
loin, `uv add --dev mutmut` puis `uv run mutmut run --paths-to-mutate
tp11_projet/stock` liste les mutants survivants.

### 2. Nouvelle fonctionnalité en TDD : `renommer`

Ajouter `ServiceStock.renommer(reference, nouveau_nom)`. Écrire d'abord
les tests (nominal, produit inconnu, nom vide), les voir échouer, puis
implémenter.

**Corrigé.** Tests à ajouter dans `test_service.py` :

```python
class TestRenommer:
    def test_nominal(self, service):
        assert service.renommer("STY-01", "Stylo noir").nom == "Stylo noir"
        assert service.depot.charger("STY-01").nom == "Stylo noir"

    def test_produit_inconnu(self, service):
        with pytest.raises(ProduitInconnu):
            service.renommer("NOPE", "x")

    @pytest.mark.parametrize("nom", ["", "   "])
    def test_nom_vide(self, service, nom):
        with pytest.raises(ValueError, match="vide"):
            service.renommer("STY-01", nom)
        assert service.depot.charger("STY-01").nom == "Stylo bleu"  # inchangé
```

Implémentation dans `service.py` :

```python
def renommer(self, reference: str, nouveau_nom: str) -> Produit:
    if not nouveau_nom.strip():
        raise ValueError("le nom ne peut pas être vide")
    produit = self.depot.charger(reference)
    produit.nom = nouveau_nom
    self.depot.sauvegarder(produit)
    return produit
```

Point à discuter : valider le nom avant de charger le produit fait que
`renommer("NOPE", "")` lève `ValueError` et non `ProduitInconnu`. Les deux
ordres se défendent ; le test doit documenter le choix.

### 3. Nouvelle implémentation : `DepotSQLite`

Écrire `DepotSQLite` avec le module `sqlite3` de la bibliothèque standard
et l'ajouter aux `params` de la fixture `depot`. Les six tests de contrat
doivent passer sans modification.

**Corrigé.** Dans `stock/depot.py` :

```python
import sqlite3
from datetime import date


class DepotSQLite:
    def __init__(self, chemin: Path | str = ":memory:"):
        self._conn = sqlite3.connect(str(chemin))
        self._conn.execute(
            """CREATE TABLE IF NOT EXISTS produits (
                reference TEXT PRIMARY KEY, nom TEXT NOT NULL, prix_ht REAL NOT NULL,
                quantite INTEGER NOT NULL, seuil_alerte INTEGER NOT NULL,
                date_creation TEXT NOT NULL)"""
        )

    def sauvegarder(self, produit: Produit) -> None:
        with self._conn:  # commit automatique, rollback si exception
            self._conn.execute(
                "INSERT OR REPLACE INTO produits VALUES "
                "(:reference, :nom, :prix_ht, :quantite, :seuil_alerte, :date_creation)",
                produit.to_dict(),
            )

    def charger(self, reference: str) -> Produit:
        ligne = self._conn.execute(
            "SELECT * FROM produits WHERE reference = ?", (reference,)
        ).fetchone()
        if ligne is None:
            raise ProduitInconnu(reference)
        return self._vers_produit(ligne)

    def tous(self) -> list[Produit]:
        lignes = self._conn.execute("SELECT * FROM produits ORDER BY reference")
        return [self._vers_produit(l) for l in lignes]

    def supprimer(self, reference: str) -> None:
        with self._conn:
            curseur = self._conn.execute("DELETE FROM produits WHERE reference = ?", (reference,))
            if curseur.rowcount == 0:
                raise ProduitInconnu(reference)

    @staticmethod
    def _vers_produit(ligne) -> Produit:
        reference, nom, prix_ht, quantite, seuil, date_creation = ligne
        return Produit(reference, nom, prix_ht, quantite, seuil, date.fromisoformat(date_creation))
```

Dans `tests/conftest.py` :

```python
@pytest.fixture
def depot_sqlite(tmp_path):
    return DepotSQLite(tmp_path / "stock.db")


@pytest.fixture(params=["memoire", "json", "sqlite"])
def depot(request):
    return request.getfixturevalue(f"depot_{request.param}")
```

Résultat : `--collect-only` montre désormais `[sqlite]` et la suite passe à
69 tests. `to_dict()` fournit directement les paramètres nommés de la
requête, ce qui évite de répéter les colonnes. Le `with self._conn` gère la
transaction.

### 4. Historique des mouvements avec horloge contrôlée

Faire journaliser chaque mouvement dans une liste `service.historique`
sous la forme `(horodatage, reference, delta)`, avec `datetime.now()`
patché.

**Indice** : dans `service.py`, `from datetime import datetime` puis
`datetime.now()` dans `entrer_stock` et `sortir_stock`. Dans le test,
comme au TP06 :

```python
class FauxDatetime:
    @classmethod
    def now(cls):
        return datetime(2024, 1, 1, 12, 0)

monkeypatch.setattr("tp11_projet.stock.service.datetime", FauxDatetime)
service.sortir_stock("STY-01", 10)
assert service.historique == [(datetime(2024, 1, 1, 12, 0), "STY-01", -10)]
```

Paramétrer avec `(methode, quantite, delta)` : `("entrer_stock", 5, 5)`,
`("sortir_stock", 5, -5)`.

### 5. Fichier JSON corrompu

Que se passe-t-il si `stock.json` contient `{not json` ? Écrire le test,
choisir un comportement, l'implémenter.

**Indice** : aujourd'hui, `json.loads` lève `json.JSONDecodeError` qui
remonte brute jusqu'à la CLI, qui ne l'attrape pas (code de sortie avec
traceback). Deux choix : lever une exception métier `DepotCorrompu` que la
CLI transforme en message d'erreur et code 1, ou repartir d'un dépôt vide
avec un `WARNING`. Le test avec `tmp_path` :

```python
def test_fichier_corrompu(tmp_path):
    chemin = tmp_path / "stock.json"
    chemin.write_text("{not json", encoding="utf-8")
    with pytest.raises(DepotCorrompu, match="stock.json"):
        DepotJSON(chemin).tous()
```

Puis un test de `cli.main` qui vérifie le code 1 et le message sur `stderr`.

## Transition / conclusion

Ce projet est complet au sens des tests unitaires et de composant. Il lui
manque deux choses que les deux derniers TP apportent. Le TP12 montre
comment laisser une machine chercher les cas limites que nous n'avons pas
imaginés, comme ce `<=` que 63 tests n'ont pas vu. Le TP13 remplace le
`DepotJSON` par une vraie base PostgreSQL dans un conteneur et rejoue les
six tests de contrat sans en modifier un seul : c'est la récompense de
l'architecture mise en place ici.
