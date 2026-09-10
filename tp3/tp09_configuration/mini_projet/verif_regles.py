"""Collecté UNIQUEMENT via le pytest.ini de ce dossier (python_files = verif_*.py).

Depuis la racine, le pyproject.toml ne connaît que test_*.py : ce fichier est
invisible, et son marqueur `regle` (déclaré ici seulement) ne pose aucun
problème à --strict-markers.
"""

import pytest


@pytest.mark.regle
def test_regle_metier():
    assert 2 + 2 == 4
