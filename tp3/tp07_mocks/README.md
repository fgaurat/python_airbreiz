# TP07 – Mocks et doublures de test

## En une phrase

Une doublure remplace une dépendance réelle (SMTP, HTTP) par un objet
contrôlé ; `unittest.mock` fournit des `Mock` qui enregistrent leurs appels,
`pytest-mock` les intègre à pytest via la fixture `mocker`, et l'injection
de dépendances rend souvent le patch inutile.

## Objectifs pédagogiques

À la fin du TP, le stagiaire sait :

- nommer les doublures : dummy, stub, fake, spy, mock ;
- configurer un `Mock` : `return_value`, `side_effect` (exception, séquence, fonction) ;
- vérifier des appels : `assert_called_once_with`, `call_args_list`, `call_count`, `assert_any_call` ;
- sécuriser un mock avec `spec`, `spec_set`, `create_autospec` ;
- remplacer une dépendance là où elle est utilisée avec `patch` (décorateur, contexte), `patch.object` ;
- utiliser `mocker.patch`, `mocker.patch.object`, `mocker.spy` ;
- écrire un fake et préférer l'injection de dépendances quand on maîtrise le code ;
- reconnaître un test fragile parce que trop couplé aux mocks.

## Prérequis

- TP03 : fixtures.
- TP06 : « patcher là où c'est utilisé », `monkeypatch`.
- TP08 sera vu après, mais `caplog` apparaît en section 9 (aperçu).

## Fichiers

| Fichier | Rôle |
|---|---|
| `notifications.py` | `EmailClient` (SMTP via `smtplib`), `AnnuaireClient` (HTTP via `urllib`), `ServiceNotification` (métier, reçoit les deux par injection) |
| `test_mocks.py` | Neuf sections, du `Mock` de base aux fakes |

## Mise en route

```bash
uv run pytest tp07_mocks -q
```

Sortie attendue :

```
17 passed in 0.09s
```

`pytest-mock` est installé (visible dans la ligne `plugins: mock-3.15.1, ...`
de l'en-tête).

## Déroulé de la présentation

### Le code métier : `notifications.py`

Trois classes en couches :

- `EmailClient.envoyer` construit un `EmailMessage` et l'envoie avec
  `with smtplib.SMTP(hote, port) as smtp: smtp.send_message(message)`.
  Impossible à exécuter en test sans serveur SMTP.
- `AnnuaireClient.email_de` fait un `urllib.request.urlopen` et renvoie
  l'email trouvé, ou `None`.
- `ServiceNotification` reçoit **les deux clients dans son constructeur**.
  `notifier` cherche l'email puis envoie ; `notifier_tous` boucle, compte
  les envois réussis, journalise et **continue** en cas d'exception.

La conception est le point clé : parce que le service reçoit ses
dépendances, on peut lui donner des mocks ou des fakes **sans aucun patch**
(sections 1 à 4, 8). Le patch n'est nécessaire que pour tester les clients
eux-mêmes, qui parlent à `smtplib` et `urllib` (sections 5 et 7).

Ouvrir avec le vocabulaire, à écrire au tableau :

| Doublure | Définition | Dans ce TP |
|---|---|---|
| Dummy | passé pour remplir une signature, jamais utilisé | `mocker.Mock()` donné comme `email_client` dans `test_mocker_patch_object` |
| Stub | renvoie des réponses préparées, pas de vérification | `annuaire.email_de.return_value = ...` |
| Fake | implémentation simplifiée mais fonctionnelle | `FakeEmailClient` avec sa liste `boite_envoi` |
| Spy | enregistre les appels **et** appelle le vrai code | `mocker.spy(annuaire, "email_de")` |
| Mock | enregistre les appels et permet de vérifier qu'ils ont eu lieu | `email_client.envoyer.assert_called_once_with(...)` |

En Python, un seul objet (`Mock`) joue les rôles dummy, stub et mock selon
l'usage qu'on en fait.

### Section 1 : `Mock` de base, `return_value` et assertions

**Ce que montre le code.**

```python
annuaire = Mock()
annuaire.email_de.return_value = "alice@example.com"
email_client = Mock()

service = ServiceNotification(email_client, annuaire)
assert service.notifier("alice", "Bonjour !") is True

annuaire.email_de.assert_called_once_with("alice")
email_client.envoyer.assert_called_once_with("alice@example.com", "Notification", "Bonjour !")
```

**À dire aux stagiaires.**

- Un `Mock()` accepte **n'importe quel** attribut et le crée à la volée,
  lui-même un `Mock`. `annuaire.email_de` existe donc sans déclaration, et
  est appelable. Sans `return_value`, un appel renvoie... un autre `Mock`.
- Structure d'un test avec mock : **arrange** (créer et configurer),
  **act** (appeler le code), **assert** (résultat + interactions).
- `assert_not_called()` dans `test_notifier_utilisateur_sans_email` vérifie
  une **absence** d'appel : on teste que le service n'envoie rien quand il
  n'y a pas d'adresse.

Famille complète des assertions :

| Méthode | Vérifie |
|---|---|
| `assert_called()` | au moins un appel |
| `assert_called_once()` | exactement un appel, arguments indifférents |
| `assert_called_with(*a, **k)` | le **dernier** appel a ces arguments |
| `assert_called_once_with(*a, **k)` | un seul appel, avec ces arguments |
| `assert_any_call(*a, **k)` | un appel parmi tous a ces arguments |
| `assert_has_calls([call(..), call(..)], any_order=False)` | cette séquence apparaît dans les appels |
| `assert_not_called()` | aucun appel |

**À montrer en direct.**

```bash
uv run pytest tp07_mocks -k "envoie_un_email or sans_email" -v
```

Changer `"alice@example.com"` en `"bob@example.com"` dans l'assertion et
relancer. Le message est lisible, et pytest y ajoute son introspection :

```
E   AssertionError: expected call not found.
E   Expected: envoyer('bob@example.com', 'Notification', 'Bonjour !')
E     Actual: envoyer('alice@example.com', 'Notification', 'Bonjour !')
E   pytest introspection follows:
E   Args:
E   assert ('alice@example.com', ...) == ('bob@example.com', ...)
E     At index 0 diff: 'alice@example.com' != 'bob@example.com'
```

**Pièges et erreurs fréquentes.**

- **Oublier les parenthèses** : `m.envoyer.assert_called_once` sans `()`
  ne fait rien et ne lève rien (c'est un accès d'attribut). Le test passe
  toujours. C'est le piège numéro un des mocks.
- Faute de frappe dans le nom de l'assertion : depuis Python 3.5, tout
  attribut commençant par `assert` qui n'existe pas lève
  `AttributeError: 'assert_called_onse' is not a valid assertion ... Did you mean: 'assert_called_once'?`.
  Depuis Python 3.12, `called_once()` et variantes sont refusés aussi. Mais
  `m.verifier_appel()` (nom inventé sans `assert`) passe silencieusement :
  voir `spec` en section 4.
- Comparer des arguments par égalité : `assert_called_with` utilise `==`.
  Un objet sans `__eq__` ne sera égal qu'à lui-même.

### Section 2 : inspecter les appels

**Ce que montre le code.**

```python
annuaire.email_de.side_effect = lambda u: f"{u}@example.com"
...
assert email_client.envoyer.call_count == 3
assert email_client.envoyer.call_args_list == [
    call("a@example.com", "Notification", "msg"),
    call("b@example.com", "Notification", "msg"),
    call("c@example.com", "Notification", "msg"),
]
assert email_client.envoyer.call_args.args[0] == "c@example.com"
annuaire.email_de.assert_any_call("b")
```

**À dire aux stagiaires.**

- `call_args` est le **dernier** appel, avec `.args` (tuple) et `.kwargs` (dict).
- `call_args_list` est la liste de tous les appels ; `call(...)` construit un
  objet comparable.
- `called` (booléen), `call_count`, `mock_calls` (inclut les appels sur les
  attributs enfants, par exemple `call.envoyer(...)`).
- `side_effect` avec une **fonction** : le mock l'appelle avec les mêmes
  arguments et renvoie son résultat. Ici l'annuaire « calcule » l'email.

**À montrer en direct.** Ajouter `print(email_client.mock_calls)` dans le
test et lancer avec `-s` pour voir la représentation complète.

**Pièges et erreurs fréquentes.** `call_args` vaut `None` si jamais appelé :
`call_args.args` lève alors `AttributeError`. Vérifier `called` d'abord ou
utiliser `assert_called()`.

### Section 3 : `side_effect`, exception ou séquence

**Ce que montre le code.** Les trois formes de `side_effect` :

| Forme | Effet | Test |
|---|---|---|
| une exception (classe ou instance) | levée à l'appel | `email_client.envoyer.side_effect = ConnectionError("SMTP injoignable")` |
| un itérable | une valeur par appel, `StopIteration` au-delà | `annuaire.email_de.side_effect = ["a@ex.com", None, "c@ex.com"]` |
| une fonction | appelée, son retour est renvoyé (sauf si elle renvoie `DEFAULT`) | section 2 |

`test_side_effect_exception` vérifie que `notifier` **propage** l'erreur et
que `notifier_tous` la **journalise et continue** (résultat 0).

**À dire aux stagiaires.** C'est ainsi qu'on teste les chemins d'erreur,
impossibles à provoquer avec un vrai serveur : timeout, panne, réponse
malformée. Un élément de la liste peut être une exception : `["ok", ConnectionError("x"), "ok"]`
lève au deuxième appel. `side_effect` a priorité sur `return_value`.

**Pièges et erreurs fréquentes.** Liste trop courte : `StopIteration` au
quatrième appel, souvent transformé en `RuntimeError` dans un générateur.
Le message ne dit pas clairement « ton mock manque de valeurs ».

### Section 4 : `spec` et `autospec`, un mock qui respecte l'interface

**Ce que montre le code.**

```python
m = Mock()
m.methode_qui_n_existe_pas()          # accepté : dangereux

m = Mock(spec=EmailClient)
m.envoyerr("a", "b", "c")             # AttributeError : faute de frappe détectée

m = create_autospec(EmailClient, instance=True)
m.envoyer("un seul argument")         # TypeError : signature vérifiée
```

**À dire aux stagiaires.**

- Sans `spec`, le code testé peut appeler une méthode qui **n'existe pas**
  sur la vraie classe, le test passe, la production échoue. `spec=Classe`
  limite les attributs à ceux de la classe (et `isinstance(m, Classe)`
  devient vrai).
- `spec_set` va plus loin : interdit aussi d'**affecter** un attribut
  inconnu (`m.nouveau_attr = 1` lève `AttributeError`). Utile pour
  détecter un test qui configure un attribut mal orthographié.
- `create_autospec(Classe, instance=True)` (ou `patch(..., autospec=True)`)
  vérifie en plus les **signatures** des méthodes. C'est le réglage à
  recommander par défaut.
- Limite : les attributs créés dynamiquement (`__getattr__`, propriétés
  calculées) ne sont pas dans le spec.

**À montrer en direct.**

```bash
uv run pytest tp07_mocks -k "spec" -v
```

Dans `test_mock_sans_spec_accepte_n_importe_quoi`, remplacer `Mock()` par
`Mock(spec=EmailClient)` : le test échoue avec `AttributeError: Mock object has no attribute 'methode_qui_n_existe_pas'`.

**Pièges et erreurs fréquentes.** `spec=EmailClient` donne le spec de la
**classe** : `m.envoyer` existe, mais la signature attend `self` en plus si
on n'a pas `instance=True` avec `autospec`. Sans `autospec`, aucune
vérification de signature.

### Section 5 : `patch`, remplacer un objet là où il est utilisé

**Ce que montre le code.** Trois formes :

```python
@patch("tp07_mocks.notifications.smtplib.SMTP")      # 1. décorateur : mock injecté en paramètre
def test_email_client_avec_patch_decorateur(smtp_mock): ...

with patch("tp07_mocks.notifications.smtplib.SMTP") as smtp_mock:   # 2. contexte
    ...

with patch.object(AnnuaireClient, "email_de", return_value="z@ex.com") as m:   # 3. patch.object
    ...
```

Le piège du gestionnaire de contexte, détaillé dans le premier test :

```python
# le code fait : with smtplib.SMTP(...) as smtp: smtp.send_message(message)
smtp_mock                                       # la classe SMTP (mock)
smtp_mock.return_value                          # l'instance SMTP(...) (mock)
smtp_mock.return_value.__enter__.return_value   # ce que `as smtp` reçoit
instance.send_message.assert_called_once()
```

**À dire aux stagiaires.**

- Même règle qu'au TP06 : la chaîne passée à `patch` est le chemin **vu par
  le module testé**. `notifications.py` fait `import smtplib` puis
  `smtplib.SMTP` : on patche `tp07_mocks.notifications.smtplib.SMTP`
  (équivalent à `smtplib.SMTP`, même objet). Avec `from smtplib import SMTP`,
  il faudrait `tp07_mocks.notifications.SMTP`.
- `patch` crée un `MagicMock` par défaut (d'où `__enter__` disponible).
  `new=objet` remplace par un objet précis ; `autospec=True` recommandé.
- Avec **plusieurs décorateurs** `@patch`, les mocks sont injectés **de bas
  en haut** : le décorateur le plus proche de la fonction correspond au
  premier paramètre.
- `patch.object(cible, "attr", ...)` évite la chaîne quand on a déjà
  l'objet ; `patch.dict(dico, {...})` patche un dictionnaire (comme
  `monkeypatch.setitem`, en plus versatile : `os.environ` inclus).
- Le message via `message["To"]` : on inspecte l'objet réel passé au mock,
  c'est un test précis du comportement de `EmailClient`.

**À montrer en direct.**

```bash
uv run pytest tp07_mocks -k "patch" -v
```

Dans `test_email_client_avec_patch_decorateur`, remplacer l'assertion par
`smtp_mock.return_value.send_message.assert_called_once()` : échec
`Expected 'send_message' to have been called once. Called 0 times.` C'est
la démonstration du piège `__enter__`.

**Pièges et erreurs fréquentes.**

- Patcher `smtplib.SMTP` **après** un `from smtplib import SMTP` dans le
  module : sans effet, le test appelle le vrai SMTP et échoue sur une
  erreur réseau.
- Décorateur `@patch` sur une méthode de classe de test : le mock arrive
  après `self`.
- Oublier `as` dans le `with` : le mock existe mais on ne peut pas l'inspecter.

### Section 6 : `MagicMock`, méthodes spéciales

**Ce que montre le code.**

```python
m = MagicMock()
m.__len__.return_value = 3
m.__iter__.return_value = iter([1, 2, 3])
assert len(m) == 3
assert list(m) == [1, 2, 3]
```

**À dire aux stagiaires.** `Mock` ne supporte pas `len()`, `for`, `with`,
`in`, opérateurs. `MagicMock` préconfigure ces méthodes spéciales avec des
valeurs par défaut (`__len__` renvoie 0, `__iter__` un itérateur vide,
`__enter__` renvoie le mock lui-même). `NonCallableMock` /
`NonCallableMagicMock` : un mock qui refuse d'être appelé, pour simuler un
objet de données. Dans le doute, `MagicMock` ; `patch` l'utilise par défaut.

**Pièges et erreurs fréquentes.** `__iter__.return_value = iter(...)` : un
itérateur s'épuise, la deuxième boucle est vide. Utiliser `side_effect = lambda: iter([...])`
pour un itérable réutilisable.

### Section 7 : pytest-mock, la fixture `mocker`

**Ce que montre le code.**

```python
def test_mocker_patch(mocker):
    smtp_mock = mocker.patch("tp07_mocks.notifications.smtplib.SMTP")
    EmailClient("h").envoyer("d", "s", "c")
    smtp_mock.assert_called_once_with("h", 25)

def test_mocker_spy(mocker):
    spy = mocker.spy(annuaire, "email_de")
    ...
    spy.assert_called_once_with("eve")
    assert spy.spy_return == "eve@memoire.local"
```

**À dire aux stagiaires.**

- `mocker` est `unittest.mock` avec nettoyage automatique en fin de test :
  ni décorateur, ni `with`, ni indentation. Se combine naturellement avec
  les autres fixtures (`tmp_path`, `caplog`).
- API : `mocker.patch`, `mocker.patch.object`, `mocker.patch.dict`,
  `mocker.Mock`, `mocker.MagicMock`, `mocker.stub(name)` (un mock nommé
  pour un callback), `mocker.spy(obj, "methode")`, `mocker.resetall()`,
  `mocker.stopall()`.
- Un **spy** garde le vrai comportement : on vérifie l'appel **et** le
  code réel s'exécute. `spy_return` et `spy_exception` capturent le résultat.
  Cas d'usage : vérifier qu'un cache évite un second appel sans remplacer
  la fonction.

**À montrer en direct.**

```bash
uv run pytest tp07_mocks -k mocker -v
```

Comparer côte à côte `test_email_client_avec_patch_contexte` et
`test_mocker_patch` : même test, moins de bruit.

**Pièges et erreurs fréquentes.** `mocker` n'est pas disponible dans un
`unittest.TestCase` (comme toutes les fixtures pytest).

### Section 8 : les fakes, parfois plus simples qu'un mock

**Ce que montre le code.**

```python
class FakeEmailClient:
    def __init__(self):
        self.boite_envoi = []
    def envoyer(self, destinataire, sujet, corps):
        self.boite_envoi.append((destinataire, sujet, corps))

class FakeAnnuaire:
    def __init__(self, **emails): self._emails = emails
    def email_de(self, utilisateur): return self._emails.get(utilisateur)
```

Le test lit `email_client.boite_envoi` et compare une liste de tuples.

**À dire aux stagiaires.**

- Un fake est du **vrai code**, lisible, réutilisable dans plusieurs tests,
  avec un comportement cohérent (l'annuaire renvoie `None` pour un inconnu
  sans qu'on ait à configurer `side_effect`).
- Le test avec fakes décrit un **scénario** (« alice et bob reçoivent,
  carol n'a pas d'adresse ») plutôt que des interactions techniques. Il
  survit à un refactoring interne du service (changement d'ordre des
  appels, ajout d'un log), là où un test bardé de `assert_called_with`
  casserait.
- Coût : il faut maintenir le fake en phase avec l'interface réelle. Un
  `Protocol` ou une classe abstraite commune aide (TP11 : `Depot`).

**Pièges et erreurs fréquentes.** Un fake qui devient plus complexe que le
vrai code : signe qu'il faut découper la dépendance.

### Section 9 : vérifier les logs (aperçu de `caplog`)

**Ce que montre le code.** `email_client.envoyer.side_effect = RuntimeError("boum")`,
puis `assert "échec pour x" in caplog.text` et `caplog.records[0].levelname == "ERROR"`.

**À dire aux stagiaires.** `logger.exception` dans `notifier_tous` est un
comportement à tester : c'est la seule trace de l'échec. `caplog` est
détaillé au TP08 ; retenir ici que mocks et fixtures intégrées se combinent.

## Questions fréquentes des stagiaires

**`Mock` ou `MagicMock` par défaut ?**
`MagicMock` si l'objet est utilisé avec `len`, `for`, `with`, `in` ou des
opérateurs. `Mock` sinon, pour ne pas masquer un usage inattendu. `patch`
crée des `MagicMock`.

**`monkeypatch` ou `mocker.patch` ?**
`monkeypatch` pour l'environnement (env, cwd, config, `sys.path`) et pour
remplacer par un objet maison. `mocker.patch` quand on veut un `Mock` pour
vérifier les appels. `mocker.patch` accepte aussi `new=objet` pour un
remplacement simple.

**Pourquoi mon `patch` n'a aucun effet ?**
Dans 90 % des cas : le module testé a fait `from x import y` et vous avez
patché `x.y`. Patcher `module_teste.y`.

**Comment mocker une méthode d'une classe pour toutes ses instances ?**
`mocker.patch.object(Classe, "methode", return_value=...)` ou
`patch("module.Classe.methode")`. Avec `autospec=True`, la méthode reçoit
`self` en premier argument dans `call_args`.

**Comment vérifier l'ordre des appels entre deux mocks ?**
Attacher les deux à un parent : `parent = Mock(); parent.attach_mock(a, "a"); parent.attach_mock(b, "b")`
puis inspecter `parent.mock_calls`.

**Un mock renvoie un `Mock` partout, mon test passe sans rien vérifier.**
Symptôme classique d'un mock sans `return_value` : le code compare un
`Mock` à autre chose et le `assert` est vrai par hasard (un `Mock` est
truthy). Toujours configurer `return_value` ou utiliser `spec`.

**Peut-on mocker une fonction `async` ?**
`AsyncMock` (Python 3.8+) : `mocker.patch("mod.f", new_callable=AsyncMock)`.
`patch` détecte automatiquement les coroutines et utilise `AsyncMock`.

**Combien de mocks par test, c'est trop ?**
Quand le test contient plus de configuration de mocks que de logique testée,
ou casse à chaque refactoring sans bug réel. Mocker la **frontière**
(réseau, fichiers, temps, matériel), pas les objets du domaine.

**Comment tester `AnnuaireClient.email_de` ?**
Exercice 2 : patcher `urllib.request.urlopen` avec un objet supportant
`with` et `read()`. `MagicMock` fournit `__enter__` ; configurer
`mock.return_value.__enter__.return_value.read.return_value = b'{"email": ...}'`.

## Ce qu'il faut retenir

| Besoin | Outil |
|---|---|
| Réponse préparée | `m.methode.return_value = x` |
| Exception, séquence, calcul | `m.methode.side_effect = Exc / [..] / fonction` |
| Vérifier un appel | `assert_called_once_with`, `assert_any_call`, `assert_has_calls`, `assert_not_called` |
| Inspecter | `call_args`, `call_args_list`, `call_count`, `mock_calls` |
| Interface respectée | `Mock(spec=C)`, `spec_set`, `create_autospec(C, instance=True)`, `patch(..., autospec=True)` |
| Remplacer là où c'est utilisé | `patch("module_teste.nom")`, `patch.object`, `patch.dict`, `mocker.patch` |
| Vrai code + enregistrement | `mocker.spy` |
| Lisibilité, robustesse | fake + injection de dépendances |

Réflexe : après chaque `assert_*`, vérifier les parenthèses.

## Exercices

**1. Ajouter `ServiceNotification.notifier_admin(message)` et la tester avec `Mock(spec=EmailClient)`.**

Indice / corrigé :

```python
# notifications.py
ADMIN = "admin@example.com"

def notifier_admin(self, message: str) -> None:
    self.email_client.envoyer(ADMIN, "[ADMIN]", message)

# test
def test_notifier_admin():
    email_client = Mock(spec=EmailClient)
    service = ServiceNotification(email_client, Mock())
    service.notifier_admin("disque plein")
    email_client.envoyer.assert_called_once_with("admin@example.com", "[ADMIN]", "disque plein")
```

**2. Tester `AnnuaireClient.email_de` en patchant `urlopen`.**

Indice / corrigé :

```python
def test_email_de(mocker):
    urlopen = mocker.patch("tp07_mocks.notifications.urllib.request.urlopen")
    urlopen.return_value.__enter__.return_value.read.return_value = b'{"email": "z@ex.com"}'
    assert AnnuaireClient("http://annuaire").email_de("z") == "z@ex.com"
    urlopen.assert_called_once_with("http://annuaire/utilisateurs/z")
```

Comparer avec la version `monkeypatch` + classe `FausseReponse` du TP06 :
plus de code, mais aucune chaîne `__enter__.return_value` à mémoriser. Le
TP11 (`test_tarification.py`) montre une troisième voie avec `io.BytesIO`
et `contextlib.closing`.

**3. Réécrire `test_notifier_tous_inspecte_les_appels` avec les fakes.**

Indice / corrigé :

```python
def test_notifier_tous_avec_fakes():
    email_client = FakeEmailClient()
    annuaire = FakeAnnuaire(a="a@example.com", b="b@example.com", c="c@example.com")
    assert ServiceNotification(email_client, annuaire).notifier_tous(["a", "b", "c"], "msg") == 3
    assert [d for d, _, _ in email_client.boite_envoi] == ["a@example.com", "b@example.com", "c@example.com"]
```

Discussion attendue : la version fake est plus lisible et résiste à un
changement d'implémentation ; la version mock détecte un appel en trop ou
un argument modifié. Les deux ont leur place.

**4. (bonus) Vérifier avec un spy que `notifier_tous` appelle `notifier` une fois par utilisateur.**

Indice / corrigé : `spy = mocker.spy(service, "notifier")` puis
`assert spy.call_count == 3` ; le vrai `notifier` s'exécute toujours.

## Transition vers le TP suivant

La section 9 a utilisé `caplog` sans l'expliquer. Le TP08 passe en revue les
fixtures intégrées de pytest (`tmp_path`, `capsys`, `caplog`, `recwarn`,
`cache`...) qui, combinées aux mocks, couvrent la quasi-totalité des
besoins d'isolation.
