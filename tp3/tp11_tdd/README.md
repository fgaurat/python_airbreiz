# TP11 TDD – Construire la gestion de stock en rouge, vert, refactor

## En une phrase

Le TP11 montre une application déjà testée ; ce kit la fait **naître test
par test** : on écrit un test qui échoue, le code minimal qui le fait
passer, on nettoie, on recommence.

## Objectifs pédagogiques

À la fin de ce TP, le stagiaire sait :

- dérouler le cycle rouge, vert, refactor sans sauter d'étape ;
- écrire **un seul** test à la fois, le plus petit possible ;
- vérifier qu'un test rouge échoue **pour la bonne raison** ;
- utiliser « fake it », l'implémentation évidente et la triangulation ;
- laisser la conception émerger : fixtures, injection de dépendances,
  interface commune, mocks à la frontière ;
- utiliser pytest comme boucle courte (`-x --lf`, `--sw`, `-k`) ;
- travailler en binôme ping-pong.

## Prérequis

TP01 à TP08 vus. Le TP11 n'a pas besoin d'avoir été présenté : il sert de
corrigé à consulter après coup.

## Fichiers

| Fichier | Rôle |
|---|---|
| `BACKLOG.md` | Les 8 histoires utilisateur découpées en tranches, avec pour chacune la notion pytest qui apparaît et un premier test suggéré |
| `stock/__init__.py` | Paquet **vide** : c'est vous qui le remplissez |
| `tests/conftest.py` | Uniquement le garde-fou réseau ; les fixtures viendront quand un test en aura besoin |
| `tests/test_00_environnement.py` | Test de fumée, reste vert tout le TP |
| `../tp11_projet/` | Une solution possible, à regarder **après** chaque histoire |

## Mise en route

```bash
uv run pytest tp11_tdd -q          # 1 passed : l'environnement est prêt
```

Créer le fichier `tp11_tdd/tests/test_01_produit.py` et commencer
l'histoire 1. La boucle de travail :

```bash
uv run pytest tp11_tdd -x -q --tb=short     # tout, stop au premier rouge
uv run pytest tp11_tdd --lf -x -q           # seulement le dernier rouge
uv run pytest tp11_tdd -k produit -q        # se concentrer sur un sujet
uv run pytest tp11_tdd --sw                 # pas à pas : s'arrête au rouge, reprend là
```

Un commit à chaque vert, avec un message qui nomme la tranche :

```bash
git add -A && git commit -m "1.2 référence vide refusée"
```

## Déroulé de la présentation

### Le cycle, en trois règles

1. **Rouge** : écrire un test qui échoue. Le lancer. Lire le message :
   il doit échouer pour la raison attendue (`ModuleNotFoundError`,
   `AttributeError`, `DID NOT RAISE`, `assert 120.0 == 12.0`), pas à cause
   d'une faute de frappe.
2. **Vert** : écrire le code **le plus simple** qui fait passer ce test,
   même si c'est une constante en dur. Relancer : tout est vert.
3. **Refactor** : améliorer le code et les tests **sans changer le
   comportement**. Relancer : toujours vert. Commiter.

Ce qui est interdit : écrire du code de production sans test rouge, écrire
plusieurs tests rouges à la fois, passer au refactoring alors que c'est
rouge.

### Journal de bord de l'histoire 1, tel qu'il s'est réellement passé

Toutes les sorties ci-dessous ont été produites avec ce kit. C'est le
modèle à reproduire en direct devant les stagiaires, en verbalisant chaque
décision.

#### Cycle 1 : un produit existe

**Rouge.** Fichier `tests/test_01_produit.py` :

```python
from tp11_tdd.stock.modeles import Produit


def test_creer_un_produit():
    p = Produit("STY-01", "Stylo bleu", prix_ht=1.50)
    assert p.reference == "STY-01"
    assert p.quantite == 0
```

```
$ uv run pytest tp11_tdd -q --tb=short
ERROR collecting tp11_tdd/tests/test_01_produit.py
tp11_tdd/tests/test_01_produit.py:1: in <module>
    from tp11_tdd.stock.modeles import Produit
E   ModuleNotFoundError: No module named 'tp11_tdd.stock.modeles'
1 error in 0.19s
```

À dire : « Le test échoue parce que le module n'existe pas. C'est la bonne
raison. Remarquez : on a écrit le test **en pensant à l'usage** : comment
j'aimerais construire un produit, ce que j'attends par défaut. Le test est
la première ligne de documentation. »

**Vert.** Fichier `stock/modeles.py`, le strict minimum :

```python
from dataclasses import dataclass


@dataclass
class Produit:
    reference: str
    nom: str
    prix_ht: float
    quantite: int = 0
```

```
$ uv run pytest tp11_tdd -q
2 passed in 0.10s
```

**Refactor.** Rien à nettoyer. Commit `1.1 produit minimal`.

#### Cycle 2 : la référence est obligatoire

**Rouge.**

```python
import pytest


def test_reference_vide_refusee():
    with pytest.raises(ValueError, match="référence"):
        Produit("", "Stylo", prix_ht=1.0)
```

```
E   Failed: DID NOT RAISE ValueError
FAILED tp11_tdd/tests/test_01_produit.py::test_reference_vide_refusee
1 failed, 2 passed in 0.08s
```

À dire : « `DID NOT RAISE` : le test exprime une règle métier que le code
ignore encore. Le `match=` fixe déjà le vocabulaire du message d'erreur. »

**Vert.**

```python
    def __post_init__(self):
        if not self.reference:
            raise ValueError("référence obligatoire")
```

```
3 passed in 0.07s
```

**Refactor.** Remonter l'`import pytest` en tête de fichier (il avait été
ajouté au milieu pendant le rouge). Commit.

#### Cycle 3 : le prix TTC, avec « fake it »

**Rouge.**

```python
def test_prix_ttc():
    assert Produit("R", "n", prix_ht=100).prix_ttc() == 120.0
```

```
E   AttributeError: 'Produit' object has no attribute 'prix_ttc'. Did you mean: 'prix_ht'?
1 failed, 3 passed in 0.08s
```

**Vert, volontairement faux.**

```python
    def prix_ttc(self) -> float:
        return 120.0  # "fake it" : le test ne demande rien de plus
```

```
4 passed in 0.07s
```

À dire : « Oui, c'est tricher. Et c'est vert. Le test actuel ne distingue
pas une vraie formule d'une constante : il est donc **insuffisant**. C'est
le test suivant qui va nous forcer à généraliser. On appelle cela la
triangulation. Ne restez pas plus d'un cycle avec un fake. »

#### Cycle 4 : triangulation

**Rouge.** On remplace le test par une version paramétrée avec un second
cas :

```python
@pytest.mark.parametrize("prix_ht, ttc", [(100, 120.0), (10, 12.0)])
def test_prix_ttc(prix_ht, ttc):
    assert Produit("R", "n", prix_ht=prix_ht).prix_ttc() == pytest.approx(ttc)
```

```
E   assert 120.0 == 12.0 ± 1.2e-05
E     Obtained: 120.0
E     Expected: 12.0 ± 1.2e-05
FAILED tp11_tdd/tests/test_01_produit.py::test_prix_ttc[10-12.0]
```

À dire : « Le premier cas passe toujours, le second révèle la constante en
dur. `approx` arrive maintenant, parce qu'on manipule des flottants. »

**Vert.** L'implémentation évidente :

```python
    def prix_ttc(self) -> float:
        return round(self.prix_ht * 1.20, 2)
```

```
5 passed in 0.07s
```

**Refactor.** Le `1.20` est un nombre magique : constante nommée.

```python
TAUX_TVA_NORMAL = 0.20
...
        return round(self.prix_ht * (1 + TAUX_TVA_NORMAL), 2)
```

```
5 passed in 0.07s
```

À dire : « Le refactoring ne change pas le comportement : les cinq tests
restent verts sans être modifiés. C'est le filet de sécurité qu'on vient de
se construire. » Commit `1.4 prix TTC`.

#### Ensuite

Les tranches 1.5 (arrondi de 19.99) et 1.6 (`en_rupture`) se déroulent de
la même façon. À partir de là, passer la main aux stagiaires.

### Les moments de conception à guetter

Ils arrivent dans le backlog à des endroits précis. Le formateur les laisse
venir plutôt que de les annoncer.

| Tranche | Ce qui émerge | Comment l'amener |
|---|---|---|
| 2.2 | Première fixture (`produit_stylo`) | « Vous avez copié trois fois la même construction de produit. » |
| 3.1 | **Injection de dépendances** | « Comment tester le service sans fichier ni base ? Donnez-lui le dépôt en paramètre. » Le `DepotMemoire` de l'histoire 2 devient le fake. |
| 3.5 | Vérifier l'état **après** une exception | « Le test passe, mais le stock a-t-il bougé ? » |
| 3.7 | Le cas limite que la couverture ne voit pas | Sortir exactement tout le stock. Le TP11 ne le teste pas : voir son README. |
| 4.2 | `caplog` | « Comment vérifier qu'une alerte a été émise sans la voir ? » |
| 5.3 | **Fixture paramétrée** + `getfixturevalue` | « Le dépôt JSON doit respecter le même contrat. Allez-vous copier six tests ? » |
| 5.5 | Sérialisation | Le test d'aller-retour de la date échoue : `date` n'est pas JSON. |
| 6.2 | **Mock à la frontière** | « Le taux vient d'un service HTTP. On ne l'appelle pas en test. » `Mock` avec `return_value`, puis `side_effect` en 6.3. |
| 6.4 | `mocker.patch` sur `urlopen` | On teste le client lui-même, une couche plus bas que 6.2. |
| 6.7 | Le garde-fou réseau | Faire volontairement un test sans mock : `RuntimeError: accès réseau interdit`. |
| 7.3 | `capsys` `.err` | « Une erreur ne doit jamais sortir sur stdout. » |

### TDD et BDD : introduire la distinction

Le backlog emprunte au BDD (Behavior Driven Development) les histoires
utilisateur et les critères d'acceptation, mais pas les scénarios Gherkin.
Trois points à dire, à placer après le premier cycle en direct :

- **Le TDD part du développeur** : le test décrit une unité de code et
  guide sa conception. **Le BDD part du métier** : le scénario décrit un
  comportement observable dans un langage partagé avec le product owner.
- **Le format Gherkin** structure chaque scénario en trois temps.
  La tranche 3.5 du backlog s'écrirait ainsi :

  ```gherkin
  Scénario : sortie supérieure au stock disponible
    Étant donné un produit "STY-01" avec 100 unités en stock
    Quand je sors 101 unités de "STY-01"
    Alors une erreur "stock insuffisant" est signalée
    Et le stock de "STY-01" reste à 100 unités
  ```

  Un test pytest garde naturellement cette structure : préparation
  (fixture), action, assertions. Faire remarquer que `test_sortir_trop`
  du TP11 suit exactement ces trois temps.
- **Les outils** : `pytest-bdd` (ou `behave`) exécute directement les
  fichiers `.feature` en reliant chaque phrase à une fonction Python.
  On paie une couche d'indirection ; elle se justifie quand des
  non-développeurs lisent ou écrivent les scénarios.

Message de conclusion : le cycle rouge, vert, refactor est le même dans les
deux cas ; ce qui change, c'est qui écrit la spécification et dans quel
langage.

### Format d'animation

1. **Le formateur seul** : cycles 1 à 4 ci-dessus, en direct, avec commit à
   chaque vert (montrer `git log --oneline` à la fin : l'historique raconte
   le cycle).
2. **Binômes en ping-pong** : A écrit un test rouge et passe le clavier,
   B écrit le vert et refactore, B écrit le test rouge suivant et repasse
   le clavier. Le formateur circule et pose les questions du tableau
   ci-dessus.
3. **Points de synchronisation** : à la fin des histoires 3 et 5, 10 minutes
   de comparaison avec le TP11. Différences de conception acceptées si
   les tests le justifient.
4. **Rétrospective** : qu'est-ce que le cycle a rendu plus facile ?
   Plus lent ? Quels tests auraient été oubliés sans TDD (3.5, 3.7, 6.3) ?

Durée : compter 3 h pour les histoires 1 à 5 en binômes ; 6 et 7 en
autonomie ou en devoir.

## Questions fréquentes des stagiaires

**Faut-il vraiment écrire `return 120.0` ?** Non, ce n'est pas une
obligation. Si l'implémentation est évidente et que vous êtes sûr de vous,
écrivez-la directement. Le fake est utile quand on hésite, ou pour montrer
qu'un test seul ne contraint pas assez.

**Quelle taille pour un test ?** Un comportement, une assertion principale
(plusieurs `assert` sur le même objet sont acceptables). Si le nom du test
contient « et », il y en a probablement deux.

**Combien de temps entre deux verts ?** Quelques minutes. Si un rouge dure
plus de dix minutes, la tranche est trop grosse : revenir au dernier vert
(`git checkout .`) et découper.

**Doit-on tester les méthodes privées ?** Non. On teste le comportement
observable. Si une méthode privée est complexe au point de mériter ses
tests, elle mérite sans doute d'être une fonction ou une classe à part.

**Refactorer les tests aussi ?** Oui, au même moment : extraire une fixture,
paramétrer, renommer. Les tests sont du code.

**Que faire d'un test qui devient inutile ?** Le supprimer. Après la
triangulation, le premier cas de `prix_ttc` est couvert par le `parametrize`.

**Et si je découvre un bug en cours de route ?** Écrire d'abord le test qui
le reproduit (rouge), corriger ensuite. C'est le cycle, appliqué au bug.

**Le mock en 6.2, c'est du TDD ou de la triche ?** Du TDD : le test décrit
la collaboration attendue (« le service demande le taux USD au client »).
C'est la frontière avec le monde extérieur, le seul endroit où le mock est
pleinement justifié.

**Comment savoir qu'on a fini une histoire ?** Quand tous ses critères
d'acceptation ont un test vert et qu'on ne voit plus de test à écrire qui
échouerait.

## Ce qu'il faut retenir

| Étape | Question à se poser | Commande |
|---|---|---|
| Rouge | Échoue-t-il pour la bonne raison ? | `uv run pytest tp11_tdd -x -q --tb=short` |
| Vert | Est-ce le code le plus simple qui passe ? | `uv run pytest tp11_tdd --lf -x -q` |
| Refactor | Le comportement est-il inchangé ? Tout est-il encore vert ? | `uv run pytest tp11_tdd -q` puis commit |

- Un test à la fois, le plus petit possible.
- Fake it, puis triangulation ; implémentation évidente quand elle l'est.
- La conception émerge des tests : fixtures, injection, interfaces, mocks à la frontière.
- Le corrigé (`tp11_projet`) est une solution, pas la solution.

## Exercices

1. **Terminer l'histoire 1** (tranches 1.5 et 1.6) en respectant le cycle,
   avec un commit par tranche. Vérifier avec `git log --oneline` que
   l'historique se lit comme le backlog.

   *Indice* : pour 1.6, le test paramétré `(0, True), (5, True), (6, False)`
   force la comparaison `<=` et non `<` dès le second cas.

2. **Histoire 3, tranche 3.7** : sortir exactement tout le stock. Écrire le
   test avant de regarder le TP11, puis comparer : le TP11 ne le teste pas.
   Que se passe-t-il si on remplace `<` par `<=` dans `sortir_stock` ?

3. **Histoire 5, tranche 5.3** : transformer les tests de l'histoire 2 en
   classe `TestContratDepot` utilisant une fixture `depot` paramétrée.
   Compter les tests avant et après avec `--collect-only -q`.

   *Corrigé* :

   ```python
   @pytest.fixture(params=["memoire", "json"])
   def depot(request):
       return request.getfixturevalue(f"depot_{request.param}")
   ```

4. **Kata de refactoring** : à la fin de l'histoire 6, `ServiceStock` a
   deux dépendances. Extraire un `Protocol` `Depot` et vérifier que rien ne
   change (tests verts, `mypy` optionnel).

5. **Sans filet** : histoire 7 en solo, chronométrée. Combien de cycles ?
   Combien de commits ?

## Transition vers le TP suivant

Le kit s'arrête là où le TP11 est complet. Le TP12 (Hypothesis) montre
comment générer les cas qu'on n'aurait pas pensé écrire, et le TP13
(Testcontainers) ajoute une troisième implémentation du dépôt qui doit
passer le même contrat, contre une vraie base.
