# Backlog du kit TDD : gestion de stock

## Qu'est-ce qu'un backlog ?

Un backlog est la liste **ordonnée** de tout ce qu'il reste à faire sur un
produit, exprimé du point de vue de l'utilisateur. Le terme vient des
méthodes agiles (Scrum).

- **Ordonné par priorité** : ce qui est en haut se fait en premier ; l'ordre
  traduit la valeur pour l'utilisateur et les dépendances techniques.
- **Composé d'histoires utilisateur** : chaque entrée décrit un besoin
  (« en tant que gestionnaire, je veux... »), pas une tâche technique.
- **Vivant** : on y ajoute, retire, réordonne au fil des découvertes.
- **Affiné progressivement** : les histoires du haut sont petites et
  précises, avec des critères d'acceptation ; celles du bas restent floues.

Dans ce kit, chaque **tranche** d'une histoire correspond à un test rouge :
le critère d'acceptation dit ce que le test doit vérifier, et l'ordre du
backlog dicte l'ordre des cycles rouge, vert, refactor.

## Mode d'emploi

Les histoires sont ordonnées. Chacune se découpe en **tranches** : une
tranche = un test rouge, puis le code minimal, puis un refactoring, puis un
commit. Ne passez à la tranche suivante qu'au vert.

La colonne « pytest » indique la notion qui apparaît naturellement à ce
moment-là. Le « premier test suggéré » est là pour débloquer, pas pour
imposer : si vous voyez un test plus petit, prenez-le.

Le TP11 (`../tp11_projet/`) est une solution possible, à consulter
**après** avoir terminé une histoire, jamais avant.

---

## Histoire 1 : décrire un produit

*En tant que gestionnaire, je crée un produit avec une référence, un nom,
un prix HT et une quantité en stock (0 par défaut).*

| Tranche | Critère d'acceptation | pytest | Premier test suggéré |
|---|---|---|---|
| 1.1 | Un produit se construit avec référence, nom, prix HT ; quantité 0 par défaut | `assert` | `Produit("STY-01", "Stylo", prix_ht=1.5).quantite == 0` |
| 1.2 | Référence vide refusée (`ValueError`, message contenant « référence ») | `pytest.raises(match=)` | `with pytest.raises(ValueError, match="référence")` |
| 1.3 | Prix négatif refusé, quantité négative refusée | `parametrize` sur les cas d'erreur | trois cas dans un seul test paramétré |
| 1.4 | `prix_ttc()` : 100 HT donne 120 TTC | fake it | `assert p.prix_ttc() == 120.0` puis `return 120.0` |
| 1.5 | `prix_ttc()` : 10 HT donne 12 TTC (triangulation) puis 19.99 donne 23.99 (arrondi) | `approx` | ajouter un cas au `parametrize` : la fausse implémentation casse |
| 1.6 | `en_rupture` : vrai si quantité <= seuil (5 par défaut), seuil configurable | `parametrize` avec `ids` | `(0, True), (5, True), (6, False)` |

Refactoring attendu au fil de l'histoire : constante de TVA nommée,
validations regroupées dans `__post_init__`.

## Histoire 2 : mémoriser les produits

*En tant que gestionnaire, je sauvegarde des produits et je les retrouve
par référence.*

| Tranche | Critère d'acceptation | pytest | Premier test suggéré |
|---|---|---|---|
| 2.1 | Un dépôt vide ne liste rien | fixture `depot_memoire` | `assert DepotMemoire().tous() == []` |
| 2.2 | Sauvegarder puis charger renvoie un produit égal | fixture `produit_stylo` | comparer avec `==` (dataclass) |
| 2.3 | Charger une référence inconnue lève `ProduitInconnu` | exception métier, `pytest.raises` | définir l'exception dans le module du dépôt |
| 2.4 | Sauvegarder deux fois la même référence écrase (pas de doublon) | | `len(depot.tous()) == 1` |
| 2.5 | `tous()` renvoie trié par référence | | sauvegarder « STY » puis « CAH », vérifier l'ordre |
| 2.6 | `supprimer()` ; supprimer une inconnue lève `ProduitInconnu` | | |

Refactoring attendu : fixtures `produit_stylo` et `produit_cahier` dans
`conftest.py` dès qu'un second fichier de test en a besoin.

## Histoire 3 : faire bouger le stock

*En tant que gestionnaire, j'ajoute un produit au catalogue, j'entre et je
sors des quantités.*

| Tranche | Critère d'acceptation | pytest | Premier test suggéré |
|---|---|---|---|
| 3.1 | `ServiceStock(depot).ajouter_produit(ref, nom, prix, quantite)` sauvegarde dans le dépôt | **injection de dépendances** : le service reçoit le dépôt | utiliser `DepotMemoire` comme fake, sans mock |
| 3.2 | Ajouter une référence existante lève `ValueError` « existe déjà » | | |
| 3.3 | `entrer_stock(ref, 50)` augmente la quantité | fixture `service` pré-remplie | |
| 3.4 | `sortir_stock(ref, 30)` diminue la quantité | | |
| 3.5 | Sortir plus que le stock lève `StockInsuffisant` et **ne modifie rien** | `pytest.raises` puis vérification d'état | vérifier la quantité après l'exception |
| 3.6 | Quantité nulle ou négative refusée pour entrer et sortir | `parametrize` empilé (méthode × quantité) | `getattr(service, methode)` |
| 3.7 | Sortir **exactement** tout le stock est permis (quantité finale 0) | cas limite | c'est le test qui manque au TP11, voir son README |

Refactoring attendu : `DepotMemoire` devient le fake officiel du service ;
si `ProduitInconnu` doit traverser le service, ne pas la rattraper.

## Histoire 4 : être alerté des ruptures

*En tant que gestionnaire, je vois les produits sous leur seuil et je suis
alerté quand une sortie fait passer un produit sous le seuil.*

| Tranche | Critère d'acceptation | pytest | Premier test suggéré |
|---|---|---|---|
| 4.1 | `produits_en_rupture()` liste les produits dont `en_rupture` est vrai | | fixture `service` avec un produit à 4 unités |
| 4.2 | Une sortie qui passe sous le seuil journalise un `WARNING` mentionnant la référence | `caplog` | `assert any(r.levelno == logging.WARNING ...)` |
| 4.3 | Une sortie qui reste au-dessus du seuil ne journalise aucun `WARNING` | `caplog` : absence | |
| 4.4 | `ajouter_produit` journalise un `INFO` | `caplog.at_level` | |

## Histoire 5 : persister dans un fichier

*En tant que gestionnaire, je retrouve mon stock après avoir relancé
l'application.*

| Tranche | Critère d'acceptation | pytest | Premier test suggéré |
|---|---|---|---|
| 5.1 | `DepotJSON(chemin)` : le fichier n'existe pas tant que rien n'est sauvegardé | `tmp_path` | |
| 5.2 | Sauvegarder puis relire avec une **nouvelle instance** sur le même fichier | persistance réelle | |
| 5.3 | `DepotJSON` passe **tous** les tests de l'histoire 2 sans les réécrire | **fixture `depot` paramétrée** (`params=["memoire", "json"]`, `request.getfixturevalue`) | transformer les tests de l'histoire 2 en classe `TestContratDepot` utilisant `depot` |
| 5.4 | Le fichier est du JSON lisible (indenté, clés = références) | `json.loads` sur `chemin.read_text()` | |
| 5.5 | La date de création survit à l'aller-retour | sérialisation `date` (`isoformat`) | |

Refactoring attendu : `to_dict` / `from_dict` sur `Produit`, protocole
`Depot` (`typing.Protocol`) documentant l'interface commune.

## Histoire 6 : valoriser le stock dans une devise

*En tant que gestionnaire, je connais la valeur HT de mon stock en euros,
et dans une autre devise via un service de taux de change.*

| Tranche | Critère d'acceptation | pytest | Premier test suggéré |
|---|---|---|---|
| 6.1 | `valeur_stock()` en EUR = somme prix × quantité | | stock vide vaut 0.0 |
| 6.2 | `valeur_stock("USD")` multiplie par le taux fourni par un `client_taux` injecté | `Mock` avec `return_value`, `assert_called_once_with("USD")` | le service reçoit `client_taux` en second paramètre |
| 6.3 | Si le client lève `ServiceTauxIndisponible`, repli en EUR et `ERROR` journalisé | `side_effect`, `caplog` | |
| 6.4 | `ClientTaux.taux("EUR")` renvoie 1.0 sans appel réseau | `mocker.patch("...urlopen")` + `assert_not_called` | |
| 6.5 | `ClientTaux.taux("USD")` appelle l'URL attendue et lit `rates.USD` | `mocker.patch` avec une fausse réponse (`io.BytesIO` + `closing`) | |
| 6.6 | Erreur réseau (`OSError`) ou réponse invalide → `ServiceTauxIndisponible` | `side_effect=OSError`, `parametrize` sur les corps invalides | |
| 6.7 | Un test qui oublie de mocker le client échoue immédiatement | garde-fou réseau déjà dans `conftest.py` | `pytest.raises(RuntimeError, match="réseau interdit")` |

## Histoire 7 : piloter en ligne de commande

*En tant que gestionnaire, j'utilise l'application depuis un terminal.*

| Tranche | Critère d'acceptation | pytest | Premier test suggéré |
|---|---|---|---|
| 7.1 | `main(["--fichier", f, "ajouter", "STY-01", "Stylo", "1.5"])` renvoie 0 et affiche « ajouté : STY-01 (0) » | `capsys` | |
| 7.2 | `lister` affiche une ligne par produit | `capsys.readouterr().out` | |
| 7.3 | Erreur métier : message sur **stderr**, code 1, rien sur stdout | `capsys` `.err` | |
| 7.4 | Sans sous-commande : `SystemExit` code 2 et « usage » sur stderr | `pytest.raises(SystemExit)` | |
| 7.5 | Fichier par défaut `stock.json` dans le répertoire courant | `monkeypatch.chdir(tmp_path)` | |

## Histoire 8 (bonus) : scénario de bout en bout

*Tout le circuit sur un vrai fichier, seul le réseau est simulé.*

| Tranche | Critère d'acceptation | pytest |
|---|---|---|
| 8.1 | Ajouter, sortir, entrer, puis relire avec une nouvelle instance : ruptures et valeur correctes | marqueur `integration`, `-m "not integration"` |
| 8.2 | Ce test est skippé si `--env prod` | `skipif` avec condition chaîne |

## Pour aller plus loin (après la formation)

- Historique des mouvements avec horodatage (`monkeypatch` sur `datetime`).
- `renommer(reference, nouveau_nom)` : nominal, inconnu, nom vide.
- `DepotSQLite` ajouté aux `params` de `depot` : zéro test réécrit.
- Fichier JSON corrompu : décider du comportement, l'écrire en test d'abord.
