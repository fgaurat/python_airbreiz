from pathlib import Path
from typing import Protocol

from todoapp.chargeur import lire_csv
from todoapp.ecrivain import ecrire
from todoapp.erreurs import SourceIntrouvable
from todoapp.filtres import restantes
from todoapp.formateur import en_texte


class JournalProtocol(Protocol):
    def noter(self, message: str) -> None: ...


class ExportTodos:
    """Façade du cas d'usage « exporter les tâches restantes ».

    Le seul endroit où l'enchaînement lire / filtrer / formater / écrire est
    écrit. Les modules derrière restent utilisables et testés séparément.
    """

    def __init__(self, journal: JournalProtocol):
        self._journal = journal

    def exporter_restantes(self, source, destination) -> int:
        if not Path(source).exists():
            raise SourceIntrouvable(f"fichier introuvable : {source}")
        todos = lire_csv(source)
        self._journal.noter(f"{len(todos)} tâches lues depuis {source}")
        a_faire = restantes(todos)
        ecrire(destination, en_texte(a_faire))
        self._journal.noter(
            f"{len(a_faire)} tâches exportées vers {destination}")
        return len(a_faire)
