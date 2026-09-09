"""Second module : fx_module est recréée, fx_package et fx_session sont conservées."""

from tp03_fixtures.scopes.conftest import CREATIONS


def test_nouveau_module(fx_function, fx_class, fx_module, fx_package, fx_session):
    assert fx_module == "module-2"
    assert fx_package == "package-1"
    assert fx_session == "session-1"


def test_scope_dynamique(fx_dynamique, request):
    attendu = "function" if request.config.getoption(
        "--env") == "dev" else "session"
    assert fx_dynamique == attendu


def test_scope_dynamique_bis(fx_dynamique):
    # En dev : 2e création (scope function). Sinon : même instance (scope session).
    assert CREATIONS["dynamique"] == (2 if fx_dynamique == "function" else 1)


def test_bilan(fx_session):
    """Dernier test : les compteurs résument tout ce qui précède."""
    assert CREATIONS["function"] == 5  # test_a1, a2, b1, hors_classe, nouveau_module
    # TestClasseA, TestClasseB, hors classe (module a), module b
    assert CREATIONS["class"] == 4
    assert CREATIONS["module"] == 2  # module a, module b
    assert CREATIONS["package"] == 1  # le paquet tp03_fixtures/scopes
    assert CREATIONS["session"] == 1  # une seule pour toute l'exécution
