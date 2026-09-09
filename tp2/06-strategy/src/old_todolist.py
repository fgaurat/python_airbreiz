from todoapp.todo import Todo


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

    def lister(self, tri: str = "ajout") -> list[Todo]:
        todos = list(self._todos)
        if tri == "ajout":
            return todos
        elif tri == "titre":
            return sorted(todos, key=lambda t: t.title.lower())
        elif tri == "priorite":
            return sorted(todos, key=lambda t: t.priorite, reverse=True)
        elif tri == "restantes":
            return sorted(todos, key=lambda t: t.completed)
        else:
            raise ValueError(f"tri inconnu : {tri!r}")
