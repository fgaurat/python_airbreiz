from todoapp.todo import Todo


def restantes(todos: list[Todo]) -> list[Todo]:
    return [t for t in todos if not t.completed]
