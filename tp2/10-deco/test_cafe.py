from main import Expresso, Sumatra, Chocolat, Chantilly



def test_expresso():
    boisson = Expresso()
    assert boisson.prix == 2.0
    assert boisson.title == "Expresso"


def test_expresso_chantilly():
    boisson = Expresso()
    boisson = Chantilly(boisson)
    assert boisson.prix == 2.5
    assert boisson.title == "Expresso, Chantilly"

def test_sumatra_chocolat_chantilly():
    boisson = Sumatra()
    boisson = Chocolat(boisson)
    boisson = Chantilly(boisson)
    assert boisson.prix == 5.0
    assert boisson.title == "Sumatra, Chocolat, Chantilly"

def test_double_chocolat_expresso():
    boisson = Expresso()
    boisson = Chocolat(boisson)
    boisson = Chocolat(boisson)
    assert boisson.prix == 4.0
    assert boisson.title == "Expresso, Chocolat, Chocolat"