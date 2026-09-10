"""TP08 - Fixtures intégrées : tmp_path, capsys, caplog, recwarn, cache...

`pytest --fixtures` liste toutes les fixtures disponibles, intégrées ou non.
"""

import sys
import logging
import warnings

import pytest

from tp08_fixtures_integrees.fichiers import (
    afficher_rapport,
    ancienne_fonction,
    compter_lignes,
    ecrire_csv,
    lire_csv,
    nouvelle_fonction,
    traiter,
)

LIGNES = [{"nom": "alice", "age": "30"}, {"nom": "bob", "age": "25"}]

# ---------------------------------------------------------------------------
# 1. tmp_path : un répertoire temporaire vide, unique par test (pathlib.Path)
# ---------------------------------------------------------------------------


def test_tmp_path_est_vide_et_unique(tmp_path):
    assert tmp_path.is_dir()
    assert list(tmp_path.iterdir()) == []
    # Le nom contient celui du test : pratique pour le débogage
    assert "test_tmp_path_est_vide" in str(tmp_path)


def test_aller_retour_csv(tmp_path):
    fichier = tmp_path / "personnes.csv"
    ecrire_csv(fichier, LIGNES)
    assert lire_csv(fichier) == LIGNES
    assert compter_lignes(fichier) == 3  # en-tête + 2 lignes


def test_ecrire_csv_vide(tmp_path):
    with pytest.raises(ValueError):
        ecrire_csv(tmp_path / "x.csv", [])


# ---------------------------------------------------------------------------
# 2. tmp_path_factory : répertoires temporaires pour des scopes larges
# ---------------------------------------------------------------------------


def test_gros_fichier(gros_fichier):
    assert compter_lignes(gros_fichier) == 1500


def test_gros_fichier_partage(gros_fichier):
    # Même chemin que dans le test précédent (scope session)
    assert gros_fichier.name == "gros.txt"


# ---------------------------------------------------------------------------
# 3. capsys : capturer stdout / stderr
# ---------------------------------------------------------------------------


def test_capsys(capsys):
    afficher_rapport(LIGNES)
    capture = capsys.readouterr()  # vide le tampon
    assert capture.out.splitlines() == [
        "Rapport : 2 enregistrement(s)",
        " - nom=alice, age=30",
        " - nom=bob, age=25",
    ]
    assert capture.err == ""


def test_capsys_stderr(capsys):
    afficher_rapport([])
    capture = capsys.readouterr()
    assert "0 enregistrement" in capture.out
    assert "rapport vide" in capture.err


def test_capsys_lecture_incrementale(capsys):
    print("un")
    assert capsys.readouterr().out == "un\n"
    print("deux")
    # seulement ce qui suit la lecture précédente
    assert capsys.readouterr().out == "deux\n"


def test_capfd(capfd):
    # capfd capture au niveau du descripteur de fichier : fonctionne aussi
    # pour les sous-processus et les bibliothèques C qui écrivent sur fd 1.
    import os

    os.write(1, b"ecrit directement sur le fd 1\n")
    assert "fd 1" in capfd.readouterr().out


# ---------------------------------------------------------------------------
# 4. caplog : capturer les logs
# ---------------------------------------------------------------------------


def test_caplog_texte(caplog, tmp_path):
    traiter(tmp_path / "absent.txt")
    assert "fichier introuvable" in caplog.text


def test_caplog_records(caplog, gros_fichier):
    with caplog.at_level(logging.DEBUG, logger="fichiers"):
        n = traiter(gros_fichier)

    assert n == 1500
    niveaux = [r.levelname for r in caplog.records]
    assert niveaux == ["DEBUG", "WARNING", "INFO"]
    assert caplog.records[1].getMessage() == "fichier volumineux (1500 lignes)"
    # Tuples (logger, niveau, message) : pratique pour une comparaison globale
    assert ("fichiers", logging.WARNING,
            "fichier volumineux (1500 lignes)") in caplog.record_tuples


def test_caplog_set_level_et_clear(caplog, tmp_path):
    caplog.set_level(logging.WARNING)  # les INFO ne sont plus capturés
    fichier = tmp_path / "p.csv"
    ecrire_csv(fichier, LIGNES)  # émet un INFO
    assert caplog.records == []

    caplog.set_level(logging.INFO)
    ecrire_csv(fichier, LIGNES)
    assert len(caplog.records) == 1
    caplog.clear()
    assert caplog.records == []


# ---------------------------------------------------------------------------
# 5. Avertissements : pytest.warns et recwarn
# ---------------------------------------------------------------------------


def test_pytest_warns():
    with pytest.warns(DeprecationWarning, match="obsolète"):
        assert ancienne_fonction(2) == 4


def test_recwarn(recwarn):
    warnings.simplefilter("always")
    ancienne_fonction(1)
    ancienne_fonction(2)
    assert len(recwarn) == 2
    w = recwarn.pop(DeprecationWarning)
    assert "nouvelle_fonction" in str(w.message)


def test_aucun_avertissement():
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # tout warning devient une exception
        assert nouvelle_fonction(3) == 6  # ne doit rien émettre


# ---------------------------------------------------------------------------
# 6. cache : persister une valeur entre deux exécutions de pytest
# ---------------------------------------------------------------------------

def test_cache(cache):
    # Stocké dans .pytest_cache/ ; survit d'une exécution à l'autre.
    # C'est ce mécanisme qu'utilisent --lf et --ff.
    precedent = cache.get("tp08/executions", 0)
    cache.set("tp08/executions", precedent + 1)
    assert cache.get("tp08/executions", None) == precedent + 1


# ---------------------------------------------------------------------------
# 7. pytestconfig / request.config : accéder à la configuration
# ---------------------------------------------------------------------------


def test_pytestconfig(pytestconfig):
    assert pytestconfig.rootpath.name == "formation-pytest"
    assert pytestconfig.getini("pythonpath") == [
        pytestconfig.rootpath]  # "." résolu en chemin absolu
    assert pytestconfig.getoption("--env") in {"dev", "staging", "prod"}
    assert "lent: test long a executer (desactivable avec -m 'not lent')" in pytestconfig.getini(
        "markers")


def test_request_config(request):
    assert request.config is request.session.config


# ---------------------------------------------------------------------------
# 8. monkeypatch (TP06) et mocker (TP07) sont aussi des fixtures intégrées ;
#    `env` vient du conftest racine.
# ---------------------------------------------------------------------------


def test_env(env):
    assert env == "dev" or env in {"staging", "prod"}


# write to stderr
print("This goes to stderr", file=sys.stderr)
print("This goes to stdout", file=sys.stdout)
print("This goes to stdout")
