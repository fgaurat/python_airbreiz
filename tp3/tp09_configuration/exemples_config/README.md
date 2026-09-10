# Exemples de fichiers de configuration

Cinq façons d'écrire la **même** configuration que celle du `pyproject.toml`
racine. Ces fichiers ne sont **pas actifs** : pytest ne cherche un fichier
de configuration que dans le répertoire commun aux arguments et ses parents,
et ce dossier ne contient aucun test.

| Fichier | Section | Types | Remarque |
|---|---|---|---|
| `pytest.ini` | `[pytest]` | INI (chaînes, listes sur plusieurs lignes) | prioritaire sur tous les autres, même vide |
| `pytest.toml` | `[pytest]` | TOML natifs (`addopts` = liste) | pytest 9, même priorité qu'un `pytest.ini` |
| `pyproject.toml` | `[tool.pytest.ini_options]` ou `[tool.pytest]` | INI dans des chaînes / TOML natifs | le choix moderne, tout l'outillage Python y est |
| `tox.ini` | `[pytest]` | INI | projets qui utilisent tox |
| `setup.cfg` | `[tool:pytest]` | INI | historique, déconseillé |

Ordre de recherche dans un même répertoire : `pytest.ini` et `pytest.toml`,
puis `pyproject.toml` (seulement s'il contient une section pytest), `tox.ini`,
`setup.cfg`. Le premier trouvé fixe la configuration et le `rootdir`.

Pour essayer l'un d'eux sur le projet sans le déplacer :

```bash
uv run pytest -c tp09_configuration/exemples_config/pytest.ini --rootdir=. tp01_bases -q
```

`-c` impose le fichier, `--rootdir=.` garde la racine du projet (sinon le
`rootdir` deviendrait ce dossier et `pythonpath = .` pointerait dessus).
