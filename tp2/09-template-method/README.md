# TP 09 : Template Method

**Durée : 45 min**

## Contexte

`depart/todoapp/` produit un rapport de tâches en texte et en HTML. Deux
modules, deux fonctions `generer`, écrites à trois mois d'écart par deux
personnes. Le texte a deux tests, le HTML aucun.

```bash
cd depart
python main.py
python -m pytest -v
```

## Objectif

Écrire le déroulé du rapport une seule fois, et ne laisser aux formats que ce
qui leur est propre.

## Étapes

### 1. Les mêmes tests pour le HTML (10 min)

Recopiez les deux tests du texte pour le HTML, en adaptant l'attendu. Les deux
sont rouges :

- le pied compte les tâches *terminées* au lieu des restantes ;
- la liste vide ne dit rien.

Ces deux bugs ont été corrigés dans le texte il y a trois mois. Le HTML n'a
pas suivi : personne ne savait qu'il fallait corriger deux fois.

### 2. Nommer le problème (5 min)

Mettez les deux fonctions côte à côte. Le déroulé est identique : en-tête,
cas vide, une ligne par tâche, pied avec le compte. Seule la mise en forme de
chaque partie change. Le déroulé est dupliqué, et c'est dans le déroulé que
sont les règles (comment on compte les restantes).

### 3. Le squelette et ses trous (15 min)

Créez `todoapp/rapport.py` avec une classe abstraite, comme `CalcGeo` au tp1 :

```python
class Rapport(ABC):
    def generer(self, todos, titre="Rapport") -> str:
        # le déroulé, écrit une fois, qui appelle les méthodes ci-dessous
        ...

    @abstractmethod
    def entete(self, titre: str) -> str: ...
    @abstractmethod
    def ligne(self, todo: Todo) -> str: ...
    @abstractmethod
    def pied(self, restantes: int, total: int) -> str: ...

    def vide(self) -> str:                 # hook avec défaut
        return ""
```

`generer` est la *template method* : elle fixe l'ordre et calcule le compte.
Les sous-classes ne peuvent pas se tromper sur le compte, elles ne le
calculent plus.

`RapportTexte` et `RapportHtml` ne contiennent que leurs quatre méthodes. Les
deux modules de départ disparaissent.

### 4. Tester à deux niveaux (10 min)

Le squelette se teste **une fois**, avec une sous-classe de test qui rend des
marqueurs :

```python
class RapportEspion(Rapport):
    def entete(self, titre): return f"E({titre})"
    def ligne(self, todo): return f"L({todo.id})"
    def pied(self, restantes, total): return f"P({restantes}/{total})"
    def vide(self): return "V"
```

Avec elle, vérifiez l'ordre des appels, le compte des restantes, et le cas
vide. Ce test ne changera jamais quand on ajoutera un format.

Chaque format teste ses méthodes directement : `RapportHtml().ligne(Todo(...))`
rend la bonne balise, le titre est échappé. Un seul test de bout en bout par
format suffit.

### 5. Un troisième format (5 min)

Ajoutez `RapportMarkdown` : `# titre`, `- [x] tâche`, `_N restantes_`. Comptez
les lignes. Écrivez seulement ses tests de méthodes.

## Critères de réussite

- Le mot `restante` et le calcul du compte n'apparaissent qu'à un seul endroit.
- Les deux tests de l'étape 1 passent pour les trois formats.
- Le squelette a un test qui n'utilise aucun format réel.
- Instancier un format à qui il manque une méthode est une erreur à la construction.

## Discussion (5 min)

Template Method est le pattern de l'héritage : le parent appelle les enfants.
Strategy (TP 06) est celui de la composition : l'objet appelle ce qu'on lui
donne. Quand les trous se multiplient ou qu'un format a besoin d'un état, la
composition redevient plus simple. Ici, quatre méthodes et rien à configurer :
l'héritage est le bon outil.

Sur-design : un seul format. Deux formats stables sans bug commun.

## Corrigé

```bash
cd corrige
python -m pytest -v
python main.py
```
