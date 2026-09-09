import pytest

from todoapp.erreurs import SourceIntrouvable
from todoapp.export import ExportTodos


def test_export_complet(source, tmp_path, journal):
    destination = tmp_path / "restantes.txt"
    n = ExportTodos(journal).exporter_restantes(source, destination)
    assert n == 2
    assert destination.read_text(encoding="utf-8") == (
        "[ ] Relire le rapport\n[ ] Appeler le client\n"
    )


def test_export_quand_tout_est_termine(tmp_path, journal):
    source = tmp_path / "todos.csv"
    source.write_text("id,title,completed\n1,a,1\n", encoding="utf-8")
    destination = tmp_path / "restantes.txt"
    n = ExportTodos(journal).exporter_restantes(source, destination)
    assert n == 0
    assert destination.read_text(encoding="utf-8") == "\n"


def test_source_introuvable(tmp_path, journal):
    with pytest.raises(SourceIntrouvable):
        ExportTodos(journal).exporter_restantes(tmp_path / "absent.csv", tmp_path / "x")


def test_le_journal_recoit_deux_messages(source, tmp_path, journal):
    ExportTodos(journal).exporter_restantes(source, tmp_path / "r.txt")
    assert len(journal.messages) == 2
    assert journal.messages[0].startswith("3 tâches lues")
    assert journal.messages[1].startswith("2 tâches exportées")
