from typing import Callable

from todoapp.todo import Todo
from todoapp.tris import par_ajout

Tri = Callable[[list[Todo]], list[Todo]]


class TodoList:

    def __init__(self):
        self._todos: list[Todo] = []

    def ajouter(self, titre: str, priorite: int = 0) -> Todo:
        todo = Todo(len(self._todos) + 1, titre, False, priorite)
        self._todos.append(todo)
        return todo

    def terminer(self, id_: int) -> None:
        for todo in self._todos:
            if todo.id == id_:
                todo.completed = True
                return
        raise LookupError(f"aucune tâche n°{id_}")

    def lister(self, tri: Tri = par_ajout) -> list[Todo]:
        # La liste ne sait pas trier : elle applique la stratégie reçue.
        return tri(list(self._todos))
