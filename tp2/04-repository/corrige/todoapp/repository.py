from typing import Optional, Protocol

from todoapp.todo import Todo


class TodoRepository(Protocol):
    """Le contrat que toute implémentation doit respecter.

    Il est vérifié par tests/test_contrat_repository.py sur chacune d'elles.
    """

    def ajouter(self, todo: Todo) -> Todo:
        """Stocke un nouveau todo, lui attribue un id, le retourne."""

    def obtenir(self, id_: int) -> Optional[Todo]:
        """Le todo portant cet id, ou None."""

    def enregistrer(self, todo: Todo) -> None:
        """Met à jour un todo existant. TodoIntrouvable si l'id est inconnu."""

    def lister(self) -> list[Todo]:
        """Tous les todos, dans l'ordre d'ajout."""
