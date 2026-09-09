# TP 08 : Facade

**Durée : 45 min**

## Contexte

`depart/todoapp/` exporte les tâches restantes d'un CSV vers un fichier texte.
Cinq petits modules, chacun propre et testable : lire, filtrer, formater,
écrire, journaliser. Deux points d'entrée les enchaînent : `main.py` et
`cli.py`.

```bash
cd depart
python main.py            && cat restantes.txt
python cli.py todos.csv sortie.txt && cat sortie.txt
```

Les deux fichiers produits ne sont pas les mêmes.

## Objectif

Donner au cas d'usage « exporter les restantes » un seul point d'entrée,
testable, que tous les appelants utilisent.

## Étapes

### 1. Le test qui en sait trop (10 min)

Écrivez dans `tests/test_export.py` un test de l'export complet : un CSV dans
`tmp_path`, l'export, le contenu du fichier produit.

Vous ne pouvez rien appeler : `main()` a ses chemins en dur, et `cli.main`
est faux. Vous finissez par recopier les cinq appels dans le test. Le test
connaît l'ordre des opérations, les cinq modules, et le journal. S'il change
un détail interne, le test casse.

### 2. Le bug dans `cli.py` (5 min)

Comparez `cli.py` et `main.py`. `cli.py` formate avant de filtrer, et jette le
résultat du filtre. Personne ne s'en est aperçu : il n'y a pas de test, et le
« bon » enchaînement n'est écrit nulle part ailleurs que dans `main.py`.

### 3. Nommer le problème (5 min)

Le sous-système expose cinq fonctions, et chaque appelant doit savoir les
assembler. Le cas d'usage n'a pas de nom dans le code. Il existe autant de
versions de l'orchestration que d'appelants.

### 4. La façade (15 min)

Créez `todoapp/export.py` :

```python
class ExportTodos:
    def __init__(self, journal):
        self._journal = journal

    def exporter_restantes(self, source, destination) -> int:
        """Lit, filtre, formate, écrit, journalise. Rend le nombre exporté."""
```

Le corps est le contenu de `main()`, une fois. `main.py` et `cli.py`
deviennent trois lignes chacun, et produisent le même fichier.

Le journal est injecté (TP 03) : la façade ne le crée pas.

### 5. Tester la façade (10 min)

- l'export complet avec `tmp_path` : c'est le test de l'étape 1, en deux
  lignes d'`Act` ;
- un CSV où tout est terminé : fichier vide, valeur de retour 0 ;
- un source inexistante : quelle exception ? Décidez, testez ;
- le journal : donnez-lui un faux journal qui garde les messages, et vérifiez
  qu'il en reçoit deux. C'est un *spy*, au sens du jour 3.

Les cinq modules gardent leurs tests unitaires à eux. La façade ne les
remplace pas, elle les assemble.

## Critères de réussite

- `main.py` et `cli.py` n'importent que `ExportTodos` et `Journal`.
- `python cli.py todos.csv sortie.txt` produit le même fichier que `main.py`.
- Le test de l'export complet ne mentionne ni `lire_csv`, ni `en_texte`, ni `ecrire`.
- Un test vérifie les messages du journal via un faux.

## Discussion (5 min)

Une façade n'interdit pas d'utiliser les modules derrière elle. Elle donne un
nom et une signature au cas d'usage. Le risque est qu'elle grossisse jusqu'à
tout faire : une façade par cas d'usage, pas une classe `Application` qui
sait tout.

Sur-design : un seul appelant, un enchaînement de deux lignes.

## Corrigé

```bash
cd corrige
python -m pytest -v
python main.py
python cli.py todos.csv sortie.txt
```
