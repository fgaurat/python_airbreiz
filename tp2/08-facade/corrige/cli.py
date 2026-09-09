"""python cli.py todos.csv sortie.txt"""
import sys

from todoapp.export import ExportTodos
from todoapp.journal import Journal

if __name__ == "__main__":
    n = ExportTodos(Journal()).exporter_restantes(sys.argv[1], sys.argv[2])
    print(f"export terminé : {n} tâches")
