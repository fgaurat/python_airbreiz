"""Tests de la CLI : capsys + tmp_path + monkeypatch (TP06, TP08)."""

import pytest

from tp11_projet.stock import cli


@pytest.fixture
def fichier(tmp_path):
    return str(tmp_path / "stock.json")


def test_ajouter_puis_lister(fichier, capsys):
    assert cli.main(["--fichier", fichier, "ajouter", "STY-01", "Stylo", "1.5", "--quantite", "10"]) == 0
    assert capsys.readouterr().out == "ajouté : STY-01 (10)\n"

    assert cli.main(["--fichier", fichier, "lister"]) == 0
    sortie = capsys.readouterr().out
    assert "STY-01" in sortie and "Stylo" in sortie and "1.50 €" in sortie


def test_sortir(fichier, capsys):
    cli.main(["--fichier", fichier, "ajouter", "STY-01", "Stylo", "1.5", "--quantite", "10"])
    capsys.readouterr()
    assert cli.main(["--fichier", fichier, "sortir", "STY-01", "3"]) == 0
    assert capsys.readouterr().out == "STY-01 : reste 7\n"


def test_erreur_metier_sur_stderr(fichier, capsys):
    cli.main(["--fichier", fichier, "ajouter", "STY-01", "Stylo", "1.5", "--quantite", "1"])
    capsys.readouterr()
    assert cli.main(["--fichier", fichier, "sortir", "STY-01", "5"]) == 1
    capture = capsys.readouterr()
    assert capture.out == ""
    assert "erreur : STY-01: 1 disponible(s), 5 demandé(s)" in capture.err


def test_produit_inconnu(fichier, capsys):
    assert cli.main(["--fichier", fichier, "sortir", "NOPE", "1"]) == 1
    assert "erreur" in capsys.readouterr().err


def test_commande_manquante(capsys):
    # argparse appelle sys.exit(2) -> SystemExit
    with pytest.raises(SystemExit) as excinfo:
        cli.main([])
    assert excinfo.value.code == 2
    assert "usage" in capsys.readouterr().err


def test_fichier_par_defaut_dans_cwd(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    cli.main(["ajouter", "X", "x", "1"])
    assert (tmp_path / "stock.json").exists()
