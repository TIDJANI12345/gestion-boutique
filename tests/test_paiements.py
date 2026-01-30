"""Tests unitaires pour le module Paiements (Phase 2.2)"""
import unittest
from tests.conftest import reset_db

import database
from modules.produits import Produit
from modules.ventes import Vente
from modules.paiements import Paiement


class TestPaiementEspeces(unittest.TestCase):
    """Test paiement en especes avec rendu monnaie"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM paiements")
        database.db.execute_query("DELETE FROM details_ventes")
        database.db.execute_query("DELETE FROM ventes")
        database.db.execute_query("DELETE FROM produits")
        # Creer un produit et une vente
        self.code = Produit.ajouter("Savon", "Hygiene", 200, 350, 20, 5)
        produit = Produit.obtenir_par_code_barre(self.code)
        self.produit_id = produit[0]
        self.vente_id = Vente.creer_vente("Client Test")
        Vente.ajouter_produit(self.vente_id, self.produit_id, 2)
        # Total = 2 x 350 = 700

    def test_enregistrer_paiement_especes(self):
        """Paiement especes simple"""
        result = Paiement.enregistrer_paiement(
            self.vente_id, 'especes', 700,
            montant_recu=1000, monnaie_rendue=300
        )
        self.assertIsNotNone(result)

    def test_recuperer_paiement(self):
        """Verifier qu'on peut recuperer les paiements"""
        Paiement.enregistrer_paiement(
            self.vente_id, 'especes', 700,
            montant_recu=1000, monnaie_rendue=300
        )
        paiements = Paiement.obtenir_paiements_vente(self.vente_id)
        self.assertEqual(len(paiements), 1)
        self.assertEqual(paiements[0][2], 'especes')  # mode
        self.assertEqual(paiements[0][3], 700)  # montant
        self.assertEqual(paiements[0][5], 1000)  # montant_recu
        self.assertEqual(paiements[0][6], 300)  # monnaie_rendue

    def test_rendu_monnaie_correct(self):
        """Verifier que le rendu de monnaie est coherent"""
        montant_recu = 1000
        total = 700
        monnaie = montant_recu - total
        self.assertEqual(monnaie, 300)

        Paiement.enregistrer_paiement(
            self.vente_id, 'especes', total,
            montant_recu=montant_recu, monnaie_rendue=monnaie
        )
        paiements = Paiement.obtenir_paiements_vente(self.vente_id)
        self.assertEqual(paiements[0][6], 300)


class TestPaiementMobileMoney(unittest.TestCase):
    """Test paiement Mobile Money"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM paiements")
        database.db.execute_query("DELETE FROM details_ventes")
        database.db.execute_query("DELETE FROM ventes")
        database.db.execute_query("DELETE FROM produits")
        self.code = Produit.ajouter("Huile", "Alimentaire", 2000, 2500, 30, 5)
        produit = Produit.obtenir_par_code_barre(self.code)
        self.produit_id = produit[0]
        self.vente_id = Vente.creer_vente("Client MoMo")
        Vente.ajouter_produit(self.vente_id, self.produit_id, 1)
        # Total = 2500

    def test_paiement_orange_money(self):
        """Paiement Orange Money avec reference"""
        result = Paiement.enregistrer_paiement(
            self.vente_id, 'orange_money', 2500,
            reference='OM-123456789'
        )
        self.assertIsNotNone(result)
        paiements = Paiement.obtenir_paiements_vente(self.vente_id)
        self.assertEqual(paiements[0][2], 'orange_money')
        self.assertEqual(paiements[0][4], 'OM-123456789')

    def test_paiement_mtn_momo(self):
        """Paiement MTN MoMo"""
        result = Paiement.enregistrer_paiement(
            self.vente_id, 'mtn_momo', 2500,
            reference='MTN-987654321'
        )
        self.assertIsNotNone(result)
        paiements = Paiement.obtenir_paiements_vente(self.vente_id)
        self.assertEqual(paiements[0][2], 'mtn_momo')

    def test_paiement_moov_money(self):
        """Paiement Moov Money"""
        result = Paiement.enregistrer_paiement(
            self.vente_id, 'moov_money', 2500,
            reference='MOOV-555111222'
        )
        self.assertIsNotNone(result)


class TestPaiementMixte(unittest.TestCase):
    """Test paiement mixte (especes + Mobile Money)"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM paiements")
        database.db.execute_query("DELETE FROM details_ventes")
        database.db.execute_query("DELETE FROM ventes")
        database.db.execute_query("DELETE FROM produits")
        self.code = Produit.ajouter("Riz 5kg", "Alimentaire", 6000, 7500, 50, 5)
        produit = Produit.obtenir_par_code_barre(self.code)
        self.produit_id = produit[0]
        self.vente_id = Vente.creer_vente("Client Mixte")
        Vente.ajouter_produit(self.vente_id, self.produit_id, 1)
        # Total = 7500

    def test_paiement_mixte_deux_lignes(self):
        """Paiement mixte = 2 lignes dans la table paiements"""
        paiements_list = [
            {'mode': 'especes', 'montant': 3000, 'montant_recu': 3000, 'monnaie_rendue': 0},
            {'mode': 'orange_money', 'montant': 4500, 'reference': 'OM-MIX-001'},
        ]
        result = Paiement.enregistrer_paiement_mixte(self.vente_id, paiements_list)
        self.assertTrue(result)

        # Verifier 2 lignes en base
        paiements = Paiement.obtenir_paiements_vente(self.vente_id)
        self.assertEqual(len(paiements), 2)

    def test_paiement_mixte_somme_correcte(self):
        """La somme des paiements mixtes doit egaliser le total"""
        total_vente = 7500
        especes = 2000
        mobile = 5500

        self.assertEqual(especes + mobile, total_vente)

        paiements_list = [
            {'mode': 'especes', 'montant': especes, 'montant_recu': especes, 'monnaie_rendue': 0},
            {'mode': 'mtn_momo', 'montant': mobile, 'reference': 'MTN-MIX-002'},
        ]
        Paiement.enregistrer_paiement_mixte(self.vente_id, paiements_list)

        paiements = Paiement.obtenir_paiements_vente(self.vente_id)
        total_paye = sum(p[3] for p in paiements)
        self.assertEqual(total_paye, total_vente)


class TestRapportCaisse(unittest.TestCase):
    """Test rapport de rapprochement de caisse"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM paiements")
        database.db.execute_query("DELETE FROM details_ventes")
        database.db.execute_query("DELETE FROM ventes")
        database.db.execute_query("DELETE FROM produits")

    def test_rapport_caisse_vide(self):
        """Rapport de caisse sans ventes"""
        rapport = Paiement.rapport_caisse_jour()
        self.assertEqual(rapport['total_general'], 0)
        self.assertEqual(rapport['nb_transactions'], 0)

    def test_rapport_caisse_avec_ventes(self):
        """Rapport de caisse avec plusieurs types de paiement"""
        code = Produit.ajouter("Produit A", "Cat", 100, 500, 50, 5)
        produit = Produit.obtenir_par_code_barre(code)
        pid = produit[0]

        # Vente 1 - especes
        v1 = Vente.creer_vente("Client 1")
        Vente.ajouter_produit(v1, pid, 2)
        Paiement.enregistrer_paiement(v1, 'especes', 1000, montant_recu=1000, monnaie_rendue=0)

        # Vente 2 - Orange Money
        v2 = Vente.creer_vente("Client 2")
        Vente.ajouter_produit(v2, pid, 3)
        Paiement.enregistrer_paiement(v2, 'orange_money', 1500, reference='OM-TEST')

        rapport = Paiement.rapport_caisse_jour()
        self.assertEqual(rapport['total_especes'], 1000)
        self.assertEqual(rapport['total_orange_money'], 1500)
        self.assertEqual(rapport['total_general'], 2500)
        self.assertEqual(rapport['nb_transactions'], 2)


if __name__ == '__main__':
    unittest.main()
