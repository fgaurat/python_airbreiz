# TP 07 : Factory

**Durée : 45 min**

## Contexte

`depart/geo/` reprend `Rectangle`, `Carre` et `Cercle` du tp1, et y ajoute
`chargeur.py`, qui construit des formes à partir de lignes `type;valeur;valeur`.
`main.py` lit `formes.txt`, ou construit une forme depuis la ligne de commande.

```bash
cd depart
python main.py
python main.py cercle 2
python -m pytest -v
```

## Objectif

Centraliser la construction des formes en un seul endroit, qui refuse
clairement ce qu'il ne connaît pas et accepte de nouvelles formes sans être
modifié.

## Étapes

### 1. Le bug silencieux (5 min)

`python main.py` annonce quatre lignes et trois formes. La ligne `triangle`
a disparu sans un mot. Écrivez le test :

```python
def test_forme_inconnue():
    with pytest.raises(FormeInconnue):
        charger(["triangle;3;4;5"])
```

`FormeInconnue` existe déjà dans `geo/erreurs.py`. Le test est rouge.

### 2. La demande qui fait mal (10 min)

On veut accepter `disque` comme synonyme de `cercle`, et un nouveau type
`ellipse`. Comptez les fichiers à modifier : `grep -rn '"cercle"' .`

La même cascade de `if` existe dans `chargeur.py` et dans `main.py`. Elles
divergent déjà : l'une ignore l'inconnu, l'autre fait `sys.exit`. Et
`rectangle;2` plante avec un `IndexError` dans les deux.

### 3. Nommer le problème (5 min)

La logique « quel nom donne quelle classe, avec quels arguments » est écrite
partout où on construit une forme. Chaque copie a ses propres bugs.

Une fabrique, c'est cette table, écrite une fois.

### 4. La fabrique (15 min)

Créez `geo/fabrique.py` :

```python
class FabriqueFormes:
    def __init__(self):
        self._constructeurs = {}

    def enregistrer(self, nom, constructeur): ...
    def creer(self, nom, *valeurs) -> CalcGeo: ...
    def noms(self) -> list[str]: ...
```

`creer` convertit les valeurs en `float`, cherche le constructeur, et lève
`FormeInconnue` avec la liste des noms connus dans le message. Un mauvais
nombre de valeurs (`rectangle;2`) devient une `DimensionInvalide`, pas un
`TypeError`.

Une fonction `fabrique_par_defaut()` enregistre les trois formes. `charger`
et `main.py` reçoivent une fabrique et ne contiennent plus aucun `if`.

### 5. Tester la fabrique (10 min)

- `creer` pour chacun des trois noms ;
- nom inconnu : `FormeInconnue`, et le message cite `rectangle` ;
- `creer("rectangle", 2)` : `DimensionInvalide` ;
- **enregistrer une forme depuis le test** : une classe `Triangle` définie
  dans le fichier de test, enregistrée, puis créée. Le package `geo` n'a pas
  été modifié. C'est le test qui prouve le principe ouvert / fermé.

`charger` se teste avec une fabrique reçue : celle par défaut, ou une fabrique
de test avec une seule forme bidon.

## Critères de réussite

- Aucun `if type_ ==` dans `geo/` ni dans `main.py`.
- `python main.py` lève `FormeInconnue` sur le triangle (ou l'affiche proprement, à vous de choisir).
- `python main.py disque 2` marche après une seule ligne ajoutée.
- Un test enregistre une forme inconnue de `geo` et la crée.

## Discussion (5 min)

`Rectangle.build_from_str` du tp1 est déjà une fabrique : une `classmethod`
qui construit à partir d'autre chose que les arguments du constructeur. Le
pattern existe à trois tailles : la `classmethod`, la fonction, la classe avec
registre. Prenez la plus petite qui répond au problème.

Sur-design : un seul type, ou deux qui ne changeront pas. Un `dict` de
constructeurs suffit alors, sans classe.

## Corrigé

```bash
cd corrige
python -m pytest -v
python main.py
python main.py disque 2
python main.py triangle 3 4 5
```
