from todoapp.erreurs import TodoIntrouvable
from todoapp.repository import TodoRepository
from todoapp.todo import Todo


class TodoService:

    def __init__(self, repo: TodoRepository):
        self._repo = repo

    def ajouter(self, titre: str) -> Todo:
        return self._repo.ajouter(Todo(title=titre))

    def terminer(self, id_: int) -> Todo:
        todo = self._repo.obtenir(id_)
        if todo is None:
            raise TodoIntrouvable(f"aucune tâche n°{id_}")
        todo.completed = True
        self._repo.enregistrer(todo)
        return todo

    def restantes(self) -> list[Todo]:
        return [t for t in self._repo.lister() if not t.completed]

    def resume(self) -> str:
        n = len(self.restantes())
        if n == 0:
            return "aucune tâche restante"
        if n == 1:
            return "1 tâche restante"
        return f"{n} tâches restantes"
