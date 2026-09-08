from todo import Todo
from todo_dao import TodoDAO
from typing import Protocol, Iterable


class SourceTodos(Protocol):
    def save(self, todo: Todo) -> Todo: ...
    def creer_table(self): ...
    def find_all(self) -> Iterable[Todo]: ...


class TodoService:
    """Règles métier au-dessus du DAO."""

    def __init__(self, dao: SourceTodos):
        self._dao = dao
        self._dao.creer_table()

    def ajouter(self, titre: str) -> Todo:
        return self._dao.save(Todo(title=titre))

    def restantes(self) -> list[Todo]:
        return [t for t in self._dao.find_all() if not t.completed]

    def resume(self) -> str:
        n = len(self.restantes())
        return f"{n} tâches restantes"
