# TP12 (bonus) – Tests par propriétés avec Hypothesis

## En une phrase

Au lieu de choisir des exemples à la main, on décrit la forme des entrées
et une propriété qui doit toujours être vraie ; Hypothesis génère des
centaines de cas, cherche un contre-exemple et le réduit au plus petit cas
qui échoue.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- écrire un test `@given` avec les stratégies de base (`integers`,
  `floats`, `text`, `lists`, `dictionaries`) et leurs options ;
- reconnaître les familles de propriétés : invariant, conservation,
  idempotence, aller-retour, oracle, encadrement ;
- utiliser `@example`, `assume`, `@settings` ;
- lire un contre-exemple, comprendre le *shrinking* et rejouer un échec ;
- combiner Hypothesis avec les fixtures et marqueurs pytest, et connaître
  les limites de cette combinaison ;
- juger si une propriété est assez forte pour détecter un bug.

## Prérequis

TP01 (assertions, `pytest.raises`), TP04 (paramétrage, pour comparer les
deux approches), TP09 (options de ligne de commande). Le paquet
`hypothesis` est déjà dans les dépendances de développement.

## Fichiers

| Fichier | Rôle |
|---|---|
| `algos.py` | `tri_insertion`, `encoder_rle` / `decoder_rle`, `mediane` |
| `test_hypothesis.py` | dix tests : propriétés du tri, aller-retour RLE, encadrement de la médiane, stratégies composées |

## Mise en route

```bash
uv run pytest tp12_bonus_hypothesis -v
```

Sortie attendue : `10 passed` en moins d'une seconde. Chaque test `@given`
a exécuté 100 exemples (300 pour celui qui a `max_examples=300`), soit
environ 1 200 cas pour dix fonctions de test.

Commandes à préparer :

```bash
uv run pytest tp12_bonus_hypothesis --hypothesis-show-statistics
uv run pytest tp12_bonus_hypothesis --hypothesis-seed=0
uv run pytest tp12_bonus_hypothesis --durations=3
uv run pytest tp12_bonus_hypothesis --hypothesis-verbosity=verbose -k aller_retour
```

## Déroulé de la présentation

Ordre conseillé : cinq minutes sur la philosophie, puis `algos.py`, puis
les quatre sections de `test_hypothesis.py`, puis la démonstration du bug
réel de la médiane. Compter 30 minutes plus 20 minutes d'exercices.

### Philosophie : de l'exemple à la propriété

- **À dire aux stagiaires** : un test classique dit « pour cette entrée,
  j'attends cette sortie ». Un test par propriétés dit « pour toute entrée
  de cette forme, cette relation est vraie ». La différence pratique : on
  ne connaît pas la sortie attendue à l'avance, on connaît une loi.
  Exemple : on ne sait pas ce que vaut `tri_insertion([3, 1, 2, 1])` sans
  réfléchir, mais on sait que le résultat est ordonné et contient les mêmes
  éléments.
- Le TP04 paramétrait un test avec dix cas choisis par un humain. Ici,
  Hypothesis choisit les cas, et il est bien plus vicieux qu'un humain :
  listes vides, zéros, négatifs, flottants énormes, caractères Unicode
  exotiques, doublons.
- Trois étapes à chaque exécution : **génération** (100 exemples par
  défaut), **réduction** si un échec est trouvé (shrinking), **mémorisation**
  dans `.hypothesis/` pour rejouer l'échec en priorité la prochaine fois.

### algos.py : trois fonctions simples

- **Ce que montre le code** : `tri_insertion` (tri stable en O(n²)),
  `encoder_rle` qui transforme `"aaab"` en `[("a", 3), ("b", 1)]` et
  `decoder_rle` qui fait l'inverse, `mediane` qui trie puis prend l'élément
  central ou la moyenne des deux centraux.
- **À dire aux stagiaires** : regarder la fin de `mediane` : `a / 2 + b / 2`
  au lieu de `(a + b) / 2`. Le commentaire explique pourquoi ; on y revient
  dans la démonstration.

### test_hypothesis.py, section 1 : propriétés d'un tri

```python
@given(st.lists(st.integers()))
def test_tri_est_ordonne(valeurs):
    resultat = tri_insertion(valeurs)
    assert all(a <= b for a, b in zip(resultat, resultat[1:]))
```

- **Ce que montre le code** : quatre propriétés sur la même stratégie
  `st.lists(st.integers())`. Ordre (invariant), conservation des éléments
  (`sorted(resultat) == sorted(valeurs)`), idempotence
  (`tri(tri(x)) == tri(x)`), et oracle (`== sorted(valeurs)`).
- **À dire aux stagiaires** : `@given` prend une stratégie par paramètre du
  test. `st.integers()` sans borne génère des entiers arbitrairement grands,
  `st.lists(...)` des listes de longueur 0 à quelques dizaines. Pourquoi
  quatre tests alors que l'oracle suffit ? Parce qu'on n'a pas toujours
  d'oracle. Quand on réécrit un algorithme, l'ancienne version est
  l'oracle ; quand on écrit le premier, il faut des propriétés.
- **Pièges** : la propriété « ordonné » seule est trop faible. Une fonction
  qui renvoie `[]` la satisfait. Il faut au moins la combiner avec la
  conservation. Question à poser : quelle implémentation triviale passe
  chaque test pris isolément ?

### Section 2 : aller-retour et `@example`

```python
@given(st.text())
@example("")
@example("aaaaaaaaaaaaaaaa")
def test_rle_aller_retour(texte):
    assert decoder_rle(encoder_rle(texte)) == texte
```

- **Ce que montre le code** : la propriété d'aller-retour, la plus
  rentable de toutes pour tout ce qui encode, sérialise, compresse ou
  parse. `@example` ajoute des cas explicites qui sont toujours exécutés en
  plus des cas générés. Le second test vérifie que l'encodeur ne produit
  jamais deux paires consécutives de même caractère et que tous les
  compteurs sont positifs.
- **À dire aux stagiaires** : `st.text()` génère des chaînes Unicode
  complètes : caractères combinants, emojis, surrogates, caractères de
  contrôle. C'est bien plus que ce qu'un humain testerait. Les `@example`
  documentent des cas que l'on tient à voir couverts (ici la chaîne vide et
  une longue répétition), et servent de tests de non-régression après un
  bug corrigé.
- **À montrer en direct** : `--hypothesis-show-statistics` :

  ```
  tp12_bonus_hypothesis/test_hypothesis.py::test_rle_aller_retour:
    - during generate phase (0.02 seconds):
      - Typical runtimes: < 1ms, of which < 1ms in data generation
      - 100 passing, 0 failing, and 0 invalid test cases
    - Stopped because settings.max_examples=100
  ```

- **Pièges** : `@example` se place entre `@given` et la fonction, ou
  au-dessus de `@given` ; l'ordre entre les deux n'a pas d'importance, mais
  les deux doivent être au-dessus de tout décorateur pytest comme
  `@pytest.mark.xxx`.

### Section 3 : `assume` et cas exclus

```python
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False)))
def test_mediane_entre_min_et_max(valeurs):
    assume(valeurs)
    m = mediane(valeurs)
    assert min(valeurs) <= m <= max(valeurs)
```

- **Ce que montre le code** : `assume(condition)` rejette l'exemple courant
  sans le compter comme échec ; Hypothesis en génère un autre. Ici la liste
  vide est exclue parce qu'elle lève `ValueError`, testée séparément dans
  `test_mediane_vide` avec un `pytest.raises` classique. Les options
  `allow_nan=False` et `allow_infinity=False` évitent les valeurs pour
  lesquelles la comparaison n'a pas de sens.
- **À dire aux stagiaires** : deux façons d'exclure des entrées.
  `assume(...)` dans le test, ou `.filter(...)` sur la stratégie
  (`st.lists(...).filter(bool)`). Les deux rejettent après génération. Si
  plus de la moitié des exemples sont rejetés, Hypothesis lève le health
  check `filter_too_much`. La bonne solution est alors de construire une
  stratégie qui ne génère que des cas valides : ici `min_size=1`, comme dans
  la section 4.
- **Pièges** : sans `allow_nan=False`, `nan <= nan` est faux et le test
  échoue avec un contre-exemple `[nan]` qui n'est pas un bug du code.

### Section 4 : stratégies composées et `@settings`

```python
@settings(max_examples=300)
@given(
    st.lists(st.integers(min_value=-1000, max_value=1000), min_size=1, max_size=50),
    st.integers(min_value=1, max_value=10),
)
def test_mediane_invariante_par_ajout_symetrique(valeurs, k):
```

- **Ce que montre le code** : deux stratégies positionnelles pour deux
  paramètres. `min_value` / `max_value` bornent les entiers, `min_size` /
  `max_size` la longueur de la liste. `@settings(max_examples=300)` triple
  le nombre d'exemples pour ce test. Le dernier test utilise
  `st.dictionaries(st.text(min_size=1), st.integers(min_value=0))`.
- **À dire aux stagiaires** : les stratégies positionnelles sont affectées
  aux paramètres dans l'ordre, en partant de la droite si le test a des
  fixtures avant. La forme par mots-clés `@given(valeurs=..., k=...)` est
  plus lisible dès qu'il y a deux paramètres et évite toute ambiguïté.
  Autres options de `@settings` : `deadline` (200 ms par défaut par exemple,
  au-delà le test échoue avec `DeadlineExceeded` ; mettre `deadline=None`
  pour du code lent), `suppress_health_check=[HealthCheck.too_slow]`,
  `database=None` pour désactiver la mémorisation, `derandomize=True` pour
  une graine fixe.
- **Pièges** : `@settings` doit être au-dessus de `@given`. Le health
  check `too_slow` se déclenche quand la génération des données (pas le
  test) est lente, typiquement une stratégie `.filter` trop restrictive ou
  une liste gigantesque d'objets composés.

### Démonstration : le bug réel de la médiane

- **Ce qui s'est passé** : la première version de `mediane` calculait
  `(a + b) / 2`. En rédigeant ce TP, `test_mediane_entre_min_et_max` a
  échoué :

  ```
  valeurs = [8.988465674311579e+307, 8.98846567431158e+307]
  >       assert min(valeurs) <= m <= max(valeurs)
  E       assert inf <= 8.98846567431158e+307
  E       Failing test case: test_mediane_entre_min_et_max(
  E           valeurs=[8.988465674311579e+307, 8.98846567431158e+307],
  E       )
  ```

  `a + b` dépasse le plus grand flottant représentable (environ
  1.8 x 10^308) et devient `inf`. `inf / 2` reste `inf`. Correction :
  `a / 2 + b / 2`, qui ne peut pas déborder.
- **À montrer en direct** : remettre `(a + b) / 2` dans `algos.py`, lancer
  `uv run pytest tp12_bonus_hypothesis -k entre_min_et_max`, lire le
  contre-exemple, remettre la bonne formule. Ne pas oublier de remettre le
  code d'origine avant de continuer.
- **Le shrinking, pas à pas** : Hypothesis n'a pas trouvé ce contre-exemple
  du premier coup. Il a d'abord trouvé une liste quelconque qui échouait,
  par exemple une liste de 7 flottants énormes et négatifs mélangés. Puis
  il a essayé de la simplifier : retirer des éléments (une liste de 2
  suffit, puisqu'il faut deux valeurs centrales à additionner), remplacer
  chaque flottant par une valeur plus « simple » (plus proche de zéro, moins
  de décimales) tant que le test échoue encore. Il s'arrête sur deux
  valeurs juste au-dessus de la moitié du maximum représentable : la plus
  petite paire qui déborde. C'est ce qui rend le contre-exemple lisible : on
  comprend immédiatement que le problème est le débordement, alors qu'une
  liste de 7 valeurs aléatoires aurait demandé une enquête.
- **Rejouer** : le contre-exemple est stocké dans `.hypothesis/examples/`.
  Au prochain lancement, il est essayé en premier, avant toute génération
  aléatoire. Pour partager une reproduction avec un collègue :
  `--hypothesis-seed=<n>` (la graine est affichée dans le rapport d'échec
  quand l'exemple ne tient pas dans la base), ou copier le contre-exemple
  dans un `@example(...)`.

### Une propriété trop faible

- **À montrer en direct** : supprimer le `sorted` dans `mediane`
  (`v = list(valeurs)`). Relancer `test_mediane_entre_min_et_max` : il
  **passe**. La médiane d'une liste non triée reste soit un élément de la
  liste, soit la moyenne de deux éléments, donc toujours entre le minimum
  et le maximum. La propriété d'encadrement ne détecte pas ce bug.
  Ajouter un oracle :

  ```python
  import statistics

  @given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
  def test_mediane_oracle(valeurs):
      assert mediane(valeurs) == statistics.median(valeurs)
  ```

  ```
  E       assert 1.0 == 0.0
  E        +  where 1.0 = mediane([0.0, 1.0, 0.0])
  E       Failing test case: test_mediane_oracle(valeurs=[0.0, 1.0, 0.0])
  ```

  Trois éléments, deux zéros, un un : le plus petit contre-exemple
  possible. Remettre le `sorted`.
- **À dire aux stagiaires** : Hypothesis ne trouve que ce que la propriété
  permet de trouver. Le travail difficile n'est pas d'écrire `@given`, c'est
  de choisir des propriétés assez fortes. Quand un oracle existe
  (bibliothèque standard, ancienne implémentation, calcul lent mais sûr),
  l'utiliser.

### Hypothesis et pytest : ce qui se combine, ce qui ne se combine pas

- **Fixtures** : un test `@given` peut recevoir des fixtures pytest. Elles
  sont créées **une fois par test**, pas une fois par exemple : les 100
  exemples partagent la même instance. Hypothesis le signale par un health
  check `function_scoped_fixture` pour éviter les surprises avec un état
  mutable :

  ```
  E   hypothesis.errors.FailedHealthCheck: 'test_x' uses a function-scoped fixture 'ressource'.
  ```

  Si l'on sait ce que l'on fait (fixture en lecture seule), on le supprime :
  `@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])`.
  Sinon, construire la ressource dans le corps du test.
- **`parametrize`** : compatible, à condition que les noms ne se recoupent
  pas. `@pytest.mark.parametrize("taux", [0.2, 0.055])` plus
  `@given(prix=st.floats(...))` fonctionne. En revanche, `parametrize` et
  `@given` sur le **même** nom de paramètre est une erreur : chaque
  paramètre a une seule source.
- **Marqueurs, `pytest.raises`, `pytest.approx`** : tout fonctionne à
  l'intérieur du test.
- **`-x`, `--lf`** : fonctionnent ; l'échec est en plus mémorisé par
  Hypothesis.
- **xdist** : fonctionne, chaque worker a sa propre séquence aléatoire.

## Questions fréquentes des stagiaires

**Est-ce que ça remplace les tests classiques ?**
Non. Les tests par exemples documentent des comportements précis
(« 19.99 HT donne 23.99 TTC »), les propriétés couvrent l'espace des
entrées. Un bon module a les deux. Souvent trois ou quatre propriétés
suffisent, à côté d'une dizaine d'exemples.

**Les tests sont-ils déterministes ?**
Non par défaut : les exemples changent à chaque exécution, c'est voulu
pour explorer davantage. Mais un échec trouvé est rejoué en premier grâce
à la base `.hypothesis/`. Pour une CI reproductible :
`@settings(derandomize=True)` ou `--hypothesis-seed=0`. Beaucoup d'équipes
gardent l'aléatoire en CI et fixent la graine seulement pour déboguer.

**Faut-il commiter `.hypothesis/` ?**
Non, il est dans `.gitignore`. C'est un cache local. Pour figer un cas
important, le copier dans un `@example`.

**Combien d'exemples faut-il ?**
100 par défaut, c'est un bon compromis. Monter à 1 000 pour un algorithme
critique, ou dans un profil CI :
`settings.register_profile("ci", max_examples=1000)` puis
`--hypothesis-profile=ci`.

**Comment générer des objets métier, par exemple un `Produit` du TP11 ?**
`st.builds(Produit, reference=st.text(min_size=1), nom=st.text(),
prix_ht=st.floats(min_value=0, allow_nan=False), quantite=st.integers(min_value=0))`.
`st.builds` appelle le constructeur avec des valeurs générées. Pour une
dataclass, `st.from_type(Produit)` devine les stratégies à partir des
annotations, mais ne connaît pas les contraintes de `__post_init__`.

**Que veut dire `DeadlineExceeded` ?**
Un exemple a dépassé 200 ms. Soit le code est lent pour certaines entrées
(un vrai résultat intéressant), soit la machine est chargée. Remède :
`@settings(deadline=None)` ou `deadline=1000`.

**Pourquoi le test avec `st.text()` a trouvé un caractère bizarre ?**
`st.text()` couvre tout Unicode. Voir l'exercice 3 : `'İ'.lower()` donne
deux code points, ce qui casse une fonction de palindrome naïve. C'est un
vrai bug, pas un caprice. Pour restreindre :
`st.text(alphabet=st.characters(categories=("L", "N")))` ou
`st.text(alphabet="abc")`.

**Le shrinking peut-il être long ?**
Parfois quelques secondes sur des structures profondes. On peut le limiter
avec `@settings(phases=[Phase.generate])` pendant l'exploration, mais on
perd alors la lisibilité du contre-exemple.

## Ce qu'il faut retenir

| Famille de propriété | Exemple dans ce TP |
|---|---|
| Invariant | le résultat est ordonné |
| Conservation | mêmes éléments avant et après |
| Idempotence | `tri(tri(x)) == tri(x)` |
| Aller-retour | `decoder(encoder(x)) == x` |
| Oracle | `tri_insertion(x) == sorted(x)` |
| Encadrement | `min <= mediane <= max` (trop faible seule) |

| Outil | Rôle |
|---|---|
| `@given(strategie, ...)` | génère les entrées |
| `st.integers / floats / text / lists / dictionaries / builds` | stratégies de base |
| `min_value`, `max_value`, `min_size`, `max_size`, `allow_nan`, `alphabet` | contraintes |
| `@example(...)` | cas explicite toujours joué |
| `assume(cond)` / `.filter(f)` | rejeter un exemple (avec modération) |
| `@settings(max_examples, deadline, suppress_health_check, derandomize)` | réglages par test |
| `.hypothesis/` | mémorise et rejoue les échecs |
| `--hypothesis-show-statistics`, `--hypothesis-seed`, `--hypothesis-verbosity` | options de ligne de commande |

Message principal : Hypothesis a trouvé deux vrais bugs en préparant ce TP
(débordement de flottants dans `mediane`, Unicode dans `est_palindrome`)
que ni l'auteur ni les tests paramétrés n'avaient vus.

## Exercices

### 1. Propriété sur `encoder_rle`

La somme des compteurs vaut `len(texte)`, et le nombre de paires est au
plus `len(texte)`.

**Corrigé** :

```python
@given(st.text())
def test_somme_des_compteurs(texte):
    assert sum(n for _, n in encoder_rle(texte)) == len(texte)


@given(st.text())
def test_nombre_de_paires_borne(texte):
    assert len(encoder_rle(texte)) <= len(texte)
```

Propriété bonus : concaténer les caractères de chaque paire répétés
`n` fois redonne le texte, ce qui est exactement `decoder_rle`, donc
déjà couvert par l'aller-retour.

### 2. Un bug dans `mediane`

Supprimer le tri dans `mediane` et observer que
`test_mediane_entre_min_et_max` passe encore. Écrire une propriété qui
détecte le bug.

**Corrigé** : la section « Une propriété trop faible » ci-dessus donne
l'oracle avec `statistics.median` et le contre-exemple `[0.0, 1.0, 0.0]`.
Variante sans oracle : au moins la moitié des valeurs sont inférieures ou
égales à la médiane, et au moins la moitié supérieures ou égales.

```python
@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
def test_mediane_partage_la_liste(valeurs):
    m = mediane(valeurs)
    n = len(valeurs)
    assert sum(v <= m for v in valeurs) * 2 >= n
    assert sum(v >= m for v in valeurs) * 2 >= n
```

### 3. Palindromes générés

Tester `tp04_parametrize/validation.py::est_palindrome` avec une stratégie
qui construit des palindromes.

**Corrigé** et surprise :

```python
from tp04_parametrize.validation import est_palindrome


def palindromes():
    return st.text().map(lambda s: s + s[::-1])


@given(palindromes())
def test_palindromes_generes(texte):
    assert est_palindrome(texte)
```

Ce test **échoue** :

```
E       assert False
E        +  where False = est_palindrome('İİ')
E       Failing test case: test_palindromes_generes(texte='İİ')
```

`'İ'` (I majuscule avec point, U+0130) devient `'i̇'` en minuscules, soit
deux code points (`i` puis un point combinant). `est_palindrome` fait
`c.lower()` caractère par caractère puis compare la chaîne à son inverse :
`'i̇i̇'` inversé donne `'̇i̇i'`, qui est différent. Le bug est dans
`est_palindrome`, pas dans le test. Deux corrections possibles : normaliser
avec `unicodedata.normalize("NFKD", ...)` et retirer les combinants, ou
utiliser `casefold()` sur la chaîne entière puis filtrer. Pour l'exercice,
on peut aussi restreindre la stratégie et documenter la limite :

```python
def palindromes():
    lettres = st.characters(categories=("L", "N"))
    return st.text(alphabet=lettres).map(lambda s: s + s[::-1])
```

Ce qui échoue encore sur `'İ'` (catégorie `L`). Il faut donc bien corriger
la fonction, ou exclure explicitement ce genre de caractères avec
`st.characters(categories=("L", "N"), exclude_characters="İ")`. Belle
illustration : le test a raison, le code a tort.

## Transition / conclusion

Hypothesis explore l'espace des entrées d'une fonction pure. Il reste une
dimension que ni les exemples ni les propriétés ne couvrent : le
comportement des vraies dépendances, base de données, cache, file de
messages. C'est l'objet du TP13, qui remplace les fakes du TP11 par un
PostgreSQL et un Redis réels, lancés dans des conteneurs le temps des
tests.
