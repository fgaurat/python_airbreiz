from todoapp.export import ExportTodos
from todoapp.journal import Journal

if __name__ == "__main__":
    ExportTodos(Journal()).exporter_restantes("todos.csv", "restantes.txt")
