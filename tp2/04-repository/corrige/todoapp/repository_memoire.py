from typing import Optional

from todoapp.erreurs import TodoIntrouvable
from todoapp.todo import Todo


class TodoRepositoryMemoire:
    """Implémentation en mémoire : tests, démos, prototypes."""

    def __init__(self, todos=()):
        self._todos: dict[int, Todo] = {}
        for todo in todos:
            self.ajouter(todo)

    def ajouter(self, todo: Todo) -> Todo:
        todo.id = max(self._todos, default=0) + 1
        self._todos[todo.id] = todo
        return todo

    def obtenir(self, id_: int) -> Optional[Todo]:
        return self._todos.get(id_)

    def enregistrer(self, todo: Todo) -> None:
        if todo.id not in self._todos:
            raise TodoIntrouvable(f"aucune tâche n°{todo.id}")
        self._todos[todo.id] = todo

    def lister(self) -> list[Todo]:
        return list(self._todos.values())
