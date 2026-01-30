"""Tests unitaires pour le module Produits"""
import unittest
from tests.conftest import reset_db

import database
from modules.produits import Produit


class TestProduitAjouter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM historique_stock")
        database.db.execute_query("DELETE FROM produits")

    def test_ajouter_produit_valide(self):
        code = Produit.ajouter("Savon", "Hygiene", 200, 350, 10, 5)
        self.assertIsNotNone(code)
        self.assertTrue(code.startswith("PRD"))

    def test_ajouter_produit_prix_vente_negatif(self):
        result = Produit.ajouter("Test", "Cat", 100, -50, 10, 5)
        self.assertIsNone(result)

    def test_ajouter_produit_prix_achat_negatif(self):
        result = Produit.ajouter("Test", "Cat", -100, 50, 10, 5)
        self.assertIsNone(result)

    def test_ajouter_produit_stock_negatif(self):
        result = Produit.ajouter("Test", "Cat", 100, 50, -5, 5)
        self.assertIsNone(result)


class TestProduitModifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM historique_stock")
        database.db.execute_query("DELETE FROM produits")
        self.code = Produit.ajouter("Savon", "Hygiene", 200, 350, 10, 5)
        produit = Produit.obtenir_par_code_barre(self.code)
        self.produit_id = produit[0]

    def test_modifier_produit_valide(self):
        result = Produit.modifier(self.produit_id, "Savon XL", "Hygiene", 250, 400, 15, 5)
        self.assertTrue(result)
        produit = Produit.obtenir_par_id(self.produit_id)
        self.assertEqual(produit[1], "Savon XL")

    def test_modifier_prix_vente_negatif(self):
        result = Produit.modifier(self.produit_id, "Savon", "Hygiene", 200, -100, 10, 5)
        self.assertFalse(result)

    def test_modifier_prix_achat_negatif(self):
        result = Produit.modifier(self.produit_id, "Savon", "Hygiene", -200, 350, 10, 5)
        self.assertFalse(result)

    def test_modifier_stock_negatif(self):
        result = Produit.modifier(self.produit_id, "Savon", "Hygiene", 200, 350, -10, 5)
        self.assertFalse(result)


class TestProduitSupprimer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM historique_stock")
        database.db.execute_query("DELETE FROM produits")

    def test_supprimer_produit(self):
        code = Produit.ajouter("Savon", "Hygiene", 200, 350, 10, 5)
        produit = Produit.obtenir_par_code_barre(code)
        result = Produit.supprimer(produit[0])
        self.assertTrue(result)
        self.assertIsNone(Produit.obtenir_par_id(produit[0]))


class TestProduitRechercher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM historique_stock")
        database.db.execute_query("DELETE FROM produits")
        Produit.ajouter("Savon Palmolive", "Hygiene", 200, 350, 10, 5)
        Produit.ajouter("Riz local", "Alimentation", 500, 700, 50, 10)
        Produit.ajouter("Savon Dove", "Hygiene", 300, 450, 8, 5)

    def test_rechercher_par_nom(self):
        results = Produit.rechercher("Savon")
        self.assertEqual(len(results), 2)

    def test_rechercher_par_categorie(self):
        results = Produit.rechercher("Alimentation")
        self.assertEqual(len(results), 1)

    def test_rechercher_sans_resultat(self):
        results = Produit.rechercher("Inexistant")
        self.assertEqual(len(results), 0)


if __name__ == '__main__':
    unittest.main()
