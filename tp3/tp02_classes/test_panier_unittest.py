"""pytest sait aussi exécuter les tests écrits avec `unittest` de la stdlib.

Utile pour migrer progressivement une base de tests existante :
on lance `pytest`, tout passe, puis on convertit fichier par fichier.
Limites : les fixtures pytest ne sont pas injectables en paramètres de
méthodes TestCase (seules les fixtures `autouse` fonctionnent).
"""

import unittest

from tp02_classes.panier import Panier


class PanierTestCase(unittest.TestCase):
    def setUp(self):
        self.panier = Panier()
        self.panier.ajouter("stylo", 2.0, quantite=2)

    def test_total(self):
        self.assertEqual(self.panier.total(), 4.0)

    def test_retirer_inconnu(self):
        with self.assertRaises(KeyError):
            self.panier.retirer("gomme")
