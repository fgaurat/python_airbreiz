from todo import Todo
from todo_dao import TodoDAO


class TodoService:
    """Règles métier au-dessus du DAO."""

    def __init__(self):
        self._dao = TodoDAO("todos.db")
        self._dao.creer_table()

    def ajouter(self, titre: str) -> Todo:
        return self._dao.save(Todo(title=titre))

    def restantes(self) -> list[Todo]:
        return [t for t in self._dao.find_all() if not t.completed]

    def resume(self) -> str:
        n = len(self.restantes())
        return f"{n} tâches restantes"
