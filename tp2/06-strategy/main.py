from todoapp import tris
from todoapp.todolist import TodoList

# La table nom -> stratégie vit à la frontière (ici, l'affichage), pas dans TodoList.
TRIS = {
    "ajout": tris.par_ajout,
    "titre": tris.par_titre,
    "priorite": tris.par_priorite,
    "priorite+titre": tris.par_priorite_puis_titre,
    "restantes": tris.restantes_d_abord,
    "restantes p>=1": tris.RestantesAuMoins(1),
}

FILE_EXT = {
    ".csv":trucs.csv,
    ".xml":trucs.xml,
}


def main():
    liste = TodoList()
    liste.ajouter("relire le rapport", priorite=1)
    liste.ajouter("Envoyer le compte rendu")
    liste.ajouter("appeler le client", priorite=2)
    liste.terminer(2)


    compute(filename, FILE_EXT[".csv"]) # trucs.csv()


    for nom, tri in TRIS.items():
        print(f"--- {nom}")
        for todo in liste.lister(tri):
            print(f"  [{'x' if todo.completed else ' '}] p{todo.priorite} {todo.title}")


if __name__ == "__main__":
    main()
