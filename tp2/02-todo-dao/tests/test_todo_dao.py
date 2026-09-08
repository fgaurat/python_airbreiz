import pytest

from todo_dao import TodoDAO
from todo import Todo


def test_save_puis_find_all(dao):
    dao.good_save(Todo(title="Faire des tests"))
    all = dao.find_all()
    assert len(list(all)) == 1


def test_dao_rempli_contient_trois_todos(dao_rempli):
    # Arrange
    todos = dao_rempli.find_all()

    # Act
    todos_count = len(list(todos))

    # assert
    assert todos_count == 3


def test_dao_rempli_contient_trois_todos_sauvegardees(dao_rempli, todos):
    # Arrange
    read_todos = dao_rempli.find_all()

    # Act
    read_todos = list(todos)

    # assert
    assert [t.title for t in todos] == [t.title for t in read_todos]


def test_table_vide(dao):
    assert list(dao.find_all()) == []


def test_apostrophe_dans_le_titre(dao):
    todo = Todo(title="L'essentiel de python")
    dao.good_save(todo)
    all = dao.find_all()
    assert len(list(all)) == 1


def test_injection_sql_sans_effet(dao):
    titre = "'Robert'); DROP TABLE todos_tbl; --"
    # dao.bad_save(Todo(title=titre))
    dao.good_save(Todo(title=titre))
    assert list(dao.find_all())[0].title == titre
