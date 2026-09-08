# TP 04 : Repository et test de contrat

**Durée : 60 min**

## Contexte

On repart du corrigé du TP 03 : le `TodoService` reçoit son DAO, et les tests
lui donnent un `FauxDAO` en mémoire. Depuis, quelqu'un a ajouté `terminer(id)`
au service, `trouver(id)` au DAO, et les tests correspondants.

```bash
cd depart
python -m pytest -v
```

Trois tests, tous verts.

## Objectif

Découvrir qu'un faux écrit « pour que le test passe » ne prouve rien, et
remplacer le duo DAO + faux par un Repository avec un contrat, vérifié sur les
deux implémentations.


## Pattern repository
Le pattern repository consiste à créer une couche d'abstraction entre le domaine métier et la persistance des données. Il permet de centraliser la logique d'accès aux données et de fournir une interface cohérente pour manipuler les objets métier, indépendamment de la technologie de stockage sous-jacente.

## Étapes

### 1. Vert en test, faux en production (5 min)

```bash
python main.py
```

Après `terminer`, le résumé annonce encore une tâche restante, et la base
contient deux lignes. Les tests sont verts. Trouvez pourquoi : comparez
`FauxDAO.save` et `TodoDAO.save`.

### 2. Reproduire par un test (10 min)

Écrivez `tests/test_todo_dao.py` avec un test sur le vrai DAO (`tmp_path`,
comme au TP 02) : sauver un todo, le modifier, le sauver à nouveau, compter.
Il est rouge.

Le faux fait un *upsert* (remplace si l'id existe). Le vrai fait toujours un
`INSERT`. Deux comportements pour un seul nom de méthode, et rien ne dit
lequel est le bon.

### 3. Nommer le problème (5 min)

Le `FauxDAO` a été écrit dans le fichier de test, à partir de ce dont le
service avait besoin ce jour-là. Il n'a jamais été confronté au vrai. Il
n'existe aucune spécification de « ce qu'un DAO doit faire » : ni interface,
ni test partagé.

Le service dépend d'une abstraction qui n'a pas été écrite.

### 4. Écrire le contrat : le Repository (15 min)

Un Repository présente le stockage comme une collection d'objets métier. Son
interface parle métier, pas SQL. Créez `todoapp/repository.py` :

```python
class TodoRepository(Protocol):
    def ajouter(self, todo: Todo) -> Todo: ...        # attribue un id
    def obtenir(self, id_: int) -> Todo | None: ...
    def enregistrer(self, todo: Todo) -> None: ...    # met à jour, TodoIntrouvable sinon
    def lister(self) -> list[Todo]: ...
```

Deux implémentations :

- `SqliteTodoRepository`, à partir du DAO : `enregistrer` fait un `UPDATE` et
  lève `TodoIntrouvable` si aucune ligne n'est touchée (`cursor.rowcount`) ;
- `TodoRepositoryMemoire`, à partir du `FauxDAO`, mais dans le package et non
  dans les tests : il servira aux tests des autres packages, et aux démos.

Adaptez le service : `ajouter`, `obtenir`, `enregistrer`, `lister`.

### 5. Le test de contrat (15 min)

Un seul fichier de tests, lancé sur les deux implémentations, grâce à une
fixture paramétrée (TP 02, étape 5) :

```python
@pytest.fixture(params=["memoire", "sqlite"])
def repo(request, tmp_path):
    ...
```

Cas à couvrir : `ajouter` attribue un id croissant ; `obtenir` d'un inconnu
renvoie `None` ; `enregistrer` modifie sans dupliquer ; `enregistrer` d'un
inconnu lève `TodoIntrouvable` ; `lister` rend l'ordre d'ajout.

Le test qui a échoué à l'étape 2 en fait partie. Il est vert sur les deux.

Les tests du service n'utilisent que `TodoRepositoryMemoire`. Ils sont rapides,
sans fichier, et le contrat garantit que le vrai se comporterait pareil.

## Critères de réussite

- `python main.py` annonce « aucune tâche restante » après `terminer`, une seule ligne en base.
- `tests/test_contrat_repository.py` tourne sur les deux implémentations, et chaque test apparaît deux fois dans `-v`.
- `todo_service.py` ne contient aucun mot de vocabulaire SQL ni le mot `DAO`.
- Le faux n'existe plus dans les tests : c'est une implémentation du package.

## Discussion (5 min)

DAO ou Repository, quelle différence ? Le DAO expose des opérations de
stockage (`save`, `find_all`). Le Repository expose une collection métier
(`ajouter`, `lister`) et cache complètement le stockage. En pratique, la
différence qui compte est le contrat partagé par toutes les implémentations.

Quand est-ce du sur-design ? Quand il n'y a qu'une implémentation et qu'il
n'y en aura jamais d'autre, y compris en test.

## Corrigé

```bash
cd corrige
python -m pytest -v
python main.py
```
