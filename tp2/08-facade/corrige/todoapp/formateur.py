from todoapp.todo import Todo


def en_texte(todos: list[Todo]) -> str:
    lignes = [f"[{'x' if t.completed else ' '}] {t.title}" for t in todos]
    return "\n".join(lignes) + "\n"
