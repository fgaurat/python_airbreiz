"""Premier module : deux classes et une fonction, tous demandent les 5 fixtures."""

class TestClasseA:
    def test_a1(self, fx_function, fx_class, fx_module, fx_package, fx_session):
        # Première demande : les 5 fixtures sont créées, du scope le plus large au plus étroit
        assert (fx_session, fx_package, fx_module, fx_class, fx_function) == (
            "session-1",
            "package-1",
            "module-1",
            "class-1",
            "function-1",
        )

    def test_a2(self, fx_function, fx_class, fx_module, fx_package, fx_session):
        # Même classe : seule fx_function est recréée
        assert fx_class == "class-1"
        assert fx_function == "function-2"


class TestClasseB:
    def test_b1(self, fx_function, fx_class, fx_module, fx_package, fx_session):
        # Nouvelle classe : fx_class est recréée, fx_module toujours la même
        assert fx_class == "class-2"
        assert fx_module == "module-1"
        assert fx_function == "function-3"


def test_hors_classe(fx_function, fx_class, fx_module, fx_package, fx_session):
    # Pour une fonction HORS classe, le scope "class" se comporte comme "function" :
    # la fixture est recréée pour chaque fonction de ce type (voir la trace avec -s)
    assert fx_class == "class-3"
    assert fx_module == "module-1"
