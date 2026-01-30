"""Tests unitaires pour le module Ventes"""
import unittest
from tests.conftest import reset_db

import database
from modules.produits import Produit
from modules.ventes import Vente


class TestVenteCycleComplet(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM details_ventes")
        database.db.execute_query("DELETE FROM ventes")
        database.db.execute_query("DELETE FROM historique_stock")
        database.db.execute_query("DELETE FROM produits")
        self.code = Produit.ajouter("Savon", "Hygiene", 200, 350, 20, 5)
        produit = Produit.obtenir_par_code_barre(self.code)
        self.produit_id = produit[0]

    def test_creer_vente(self):
        vente_id = Vente.creer_vente("Client Test")
        self.assertIsNotNone(vente_id)
        self.assertIsInstance(vente_id, int)

    def test_ajouter_produit_a_vente(self):
        vente_id = Vente.creer_vente("Client Test")
        result = Vente.ajouter_produit(vente_id, self.produit_id, 3)
        self.assertTrue(result)
        produit = Produit.obtenir_par_id(self.produit_id)
        self.assertEqual(produit[5], 17)  # 20 - 3

    def test_ajouter_produit_stock_insuffisant(self):
        vente_id = Vente.creer_vente()
        result = Vente.ajouter_produit(vente_id, self.produit_id, 100)
        self.assertFalse(result)

    def test_ajouter_produit_quantite_zero(self):
        vente_id = Vente.creer_vente()
        result = Vente.ajouter_produit(vente_id, self.produit_id, 0)
        self.assertFalse(result)

    def test_ajouter_produit_quantite_negative(self):
        vente_id = Vente.creer_vente()
        result = Vente.ajouter_produit(vente_id, self.produit_id, -5)
        self.assertFalse(result)

    def test_total_vente(self):
        vente_id = Vente.creer_vente()
        Vente.ajouter_produit(vente_id, self.produit_id, 2)
        total = Vente.calculer_total(vente_id)
        self.assertEqual(total, 700)  # 2 x 350

    def test_annuler_vente(self):
        vente_id = Vente.creer_vente()
        Vente.ajouter_produit(vente_id, self.produit_id, 5)
        produit = Produit.obtenir_par_id(self.produit_id)
        self.assertEqual(produit[5], 15)

        Vente.annuler_vente(vente_id)
        produit = Produit.obtenir_par_id(self.produit_id)
        self.assertEqual(produit[5], 20)
        self.assertIsNone(Vente.obtenir_vente(vente_id))

    def test_supprimer_ligne_vente(self):
        vente_id = Vente.creer_vente()
        Vente.ajouter_produit(vente_id, self.produit_id, 3)
        details = Vente.obtenir_details_vente(vente_id)
        self.assertEqual(len(details), 1)

        Vente.supprimer_ligne_vente(details[0][0], vente_id)
        produit = Produit.obtenir_par_id(self.produit_id)
        self.assertEqual(produit[5], 20)


if __name__ == '__main__':
    unittest.main()
