from todoapp import tris


def titres(todos):
    return [t.title for t in todos]


def test_par_ajout_ne_change_rien(todos):
    assert tris.par_ajout(todos) == todos


def test_par_ajout_rend_une_copie(todos):
    assert tris.par_ajout(todos) is not todos


def test_par_titre_ignore_la_casse(todos):
    assert titres(tris.par_titre(todos)) == [
        "appeler le client", "Archiver", "Envoyer le compte rendu", "relire le rapport"
    ]


def test_par_priorite_decroissante(todos):
    assert [t.priorite for t in tris.par_priorite(todos)] == [2, 1, 1, 0]


def test_par_priorite_est_stable(todos):
    # Deux tâches de priorité 1 : l'ordre d'ajout est conservé.
    assert titres(tris.par_priorite(todos))[1:3] == ["relire le rapport", "Archiver"]


def test_par_priorite_puis_titre(todos):
    assert titres(tris.par_priorite_puis_titre(todos)) == [
        "appeler le client", "Archiver", "relire le rapport", "Envoyer le compte rendu"
    ]


def test_restantes_d_abord(todos):
    assert [t.completed for t in tris.restantes_d_abord(todos)] == [False, False, False, True]


def test_restantes_au_moins_filtre_puis_trie(todos):
    tri = tris.RestantesAuMoins(seuil=1)
    assert titres(tri(todos)) == ["relire le rapport", "appeler le client", "Archiver"]


def test_tous_les_tris_sur_liste_vide():
    for tri in (tris.par_ajout, tris.par_titre, tris.par_priorite, tris.RestantesAuMoins(0)):
        assert tri([]) == []
