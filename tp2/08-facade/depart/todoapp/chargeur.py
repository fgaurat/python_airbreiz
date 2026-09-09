import csv
from pathlib import Path

from todoapp.todo import Todo


def lire_csv(chemin) -> list[Todo]:
    """Lit un fichier "id,title,completed" et rend des Todo."""
    with Path(chemin).open(encoding="utf-8", newline="") as f:
        return [
            Todo(int(ligne["id"]), ligne["title"], ligne["completed"] == "1")
            for ligne in csv.DictReader(f)
        ]
