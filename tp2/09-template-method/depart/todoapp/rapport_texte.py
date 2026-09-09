from todoapp.todo import Todo


def generer(todos: list[Todo], titre: str = "Rapport") -> str:
    lignes = [f"== {titre} ==", ""]
    if not todos:
        lignes.append("(aucune tâche)")
    for todo in todos:
        case = "x" if todo.completed else " "
        lignes.append(f"[{case}] {todo.title}")
    restantes = sum(1 for t in todos if not t.completed)
    lignes.append("")
    lignes.append(f"{restantes} restante(s) sur {len(todos)}")
    return "\n".join(lignes) + "\n"
