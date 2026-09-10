import pytest


@pytest.fixture(scope="session")
def gros_fichier(tmp_path_factory):
    """Fichier de 1500 lignes créé UNE fois pour toute la session.

    `tmp_path` est de scope function : pour un scope plus large on passe par
    `tmp_path_factory`.
    """
    dossier = tmp_path_factory.mktemp("donnees")
    chemin = dossier / "gros.txt"
    chemin.write_text("\n".join(f"ligne {i}" for i in range(1500)), encoding="utf-8")
    return chemin
