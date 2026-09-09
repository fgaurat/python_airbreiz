from html import escape

from todoapp.todo import Todo


def generer(todos: list[Todo], titre: str = "Rapport") -> str:
    lignes = [f"<h1>{escape(titre)}</h1>", "<ul>"]
    for todo in todos:
        classe = "faite" if todo.completed else "a-faire"
        lignes.append(f'<li class="{classe}">{escape(todo.title)}</li>')
    lignes.append("</ul>")
    restantes = sum(1 for t in todos if t.completed)
    lignes.append(f"<p>{restantes} restante(s) sur {len(todos)}</p>")
    return "\n".join(lignes) + "\n"
