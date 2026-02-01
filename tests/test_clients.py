"""Tests unitaires pour le module Clients"""
import unittest
from tests.conftest import reset_db

import database
from modules.clients import Client


class TestClientCRUD(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM details_ventes")
        database.db.execute_query("DELETE FROM paiements")
        database.db.execute_query("DELETE FROM ventes")
        database.db.execute_query("DELETE FROM clients")

    def test_ajouter_client_valide(self):
        client_id = Client.ajouter("Koffi Jean", "22990001234", "koffi@mail.bj")
        self.assertIsNotNone(client_id)
        self.assertIsInstance(client_id, int)

    def test_ajouter_nom_vide_refuse(self):
        result = Client.ajouter("")
        self.assertIsNone(result)

    def test_ajouter_nom_none_refuse(self):
        result = Client.ajouter(None)
        self.assertIsNone(result)

    def test_obtenir_par_id(self):
        client_id = Client.ajouter("Ama Sophie", "22997001234")
        client = Client.obtenir_par_id(client_id)
        self.assertIsNotNone(client)
        self.assertEqual(client[1], "Ama Sophie")
        self.assertEqual(client[2], "22997001234")

    def test_modifier_client(self):
        client_id = Client.ajouter("Test Client")
        result = Client.modifier(client_id, "Nouveau Nom", "22990009999", "new@mail.bj", "Notes")
        self.assertTrue(result)
        client = Client.obtenir_par_id(client_id)
        self.assertEqual(client[1], "Nouveau Nom")
        self.assertEqual(client[2], "22990009999")

    def test_modifier_nom_vide_refuse(self):
        client_id = Client.ajouter("Test Client")
        result = Client.modifier(client_id, "")
        self.assertFalse(result)

    def test_supprimer_client(self):
        client_id = Client.ajouter("A Supprimer")
        result = Client.supprimer(client_id)
        self.assertTrue(result)
        client = Client.obtenir_par_id(client_id)
        self.assertIsNone(client)

    def test_supprimer_detache_ventes(self):
        client_id = Client.ajouter("Client Ventes")
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, client_id) VALUES (?, ?, ?, ?)",
            ("V-TEST-001", "2025-01-01 10:00:00", 5000, client_id)
        )
        Client.supprimer(client_id)
        vente = database.db.fetch_one("SELECT client_id FROM ventes WHERE numero_vente = 'V-TEST-001'")
        self.assertIsNone(vente[0])

    def test_rechercher(self):
        Client.ajouter("Alpha Koffi", "22990001111")
        Client.ajouter("Beta Ama", "22990002222")
        Client.ajouter("Gamma Koffi", "22990003333")

        results = Client.rechercher("Koffi")
        self.assertEqual(len(results), 2)

    def test_rechercher_par_telephone(self):
        Client.ajouter("Test Tel", "22990005555")
        results = Client.rechercher("5555")
        self.assertEqual(len(results), 1)

    def test_pagination(self):
        for i in range(10):
            Client.ajouter(f"Client {i:02d}")

        page1 = Client.rechercher_filtre("", limit=3, offset=0)
        self.assertEqual(len(page1), 3)

        page2 = Client.rechercher_filtre("", limit=3, offset=3)
        self.assertEqual(len(page2), 3)

        total = Client.compter_filtre("")
        self.assertEqual(total, 10)

    def test_obtenir_tous(self):
        Client.ajouter("A Client")
        Client.ajouter("B Client")
        tous = Client.obtenir_tous()
        self.assertEqual(len(tous), 2)


class TestFidelite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM clients")
        # S'assurer que les parametres fidelite sont definis
        database.db.set_parametre('fidelite_active', '1')
        database.db.set_parametre('fidelite_points_par_fcfa', '1000')
        database.db.set_parametre('fidelite_remise_seuil', '100')
        database.db.set_parametre('fidelite_remise_pct', '5')

    def test_ajouter_points(self):
        client_id = Client.ajouter("Fidele Client")
        points = Client.ajouter_points(client_id, 5000)
        self.assertEqual(points, 5)
        self.assertEqual(Client.obtenir_points(client_id), 5)

    def test_ajouter_points_cumul(self):
        client_id = Client.ajouter("Fidele Client")
        Client.ajouter_points(client_id, 50000)
        Client.ajouter_points(client_id, 30000)
        self.assertEqual(Client.obtenir_points(client_id), 80)

    def test_seuil_remise_non_atteint(self):
        client_id = Client.ajouter("Nouveau Client")
        Client.ajouter_points(client_id, 50000)  # 50 points
        remise_pct, points = Client.calculer_remise_fidelite(client_id)
        self.assertEqual(remise_pct, 0)
        self.assertEqual(points, 0)

    def test_seuil_remise_atteint(self):
        client_id = Client.ajouter("Bon Client")
        Client.ajouter_points(client_id, 100000)  # 100 points
        remise_pct, points = Client.calculer_remise_fidelite(client_id)
        self.assertEqual(remise_pct, 5)
        self.assertEqual(points, 100)

    def test_utiliser_points(self):
        client_id = Client.ajouter("Client Points")
        Client.ajouter_points(client_id, 100000)  # 100 points
        result = Client.utiliser_points(client_id, 100)
        self.assertTrue(result)
        self.assertEqual(Client.obtenir_points(client_id), 0)

    def test_utiliser_points_insuffisants(self):
        client_id = Client.ajouter("Pauvre Client")
        Client.ajouter_points(client_id, 5000)  # 5 points
        result = Client.utiliser_points(client_id, 100)
        self.assertFalse(result)

    def test_fidelite_inactive(self):
        database.db.set_parametre('fidelite_active', '0')
        client_id = Client.ajouter("Client Inactif")
        points = Client.ajouter_points(client_id, 100000)
        self.assertEqual(points, 0)
        database.db.set_parametre('fidelite_active', '1')


class TestHistoriqueAchats(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM details_ventes")
        database.db.execute_query("DELETE FROM paiements")
        database.db.execute_query("DELETE FROM ventes")
        database.db.execute_query("DELETE FROM clients")

    def test_historique_vide(self):
        client_id = Client.ajouter("Client Sans Achats")
        historique = Client.obtenir_historique_achats(client_id)
        self.assertEqual(len(historique), 0)
        self.assertEqual(Client.compter_achats(client_id), 0)
        self.assertEqual(Client.calculer_total_achats(client_id), 0.0)

    def test_historique_avec_ventes(self):
        client_id = Client.ajouter("Client Achats")
        for i in range(3):
            database.db.execute_query(
                "INSERT INTO ventes (numero_vente, date_vente, total, client_id) VALUES (?, ?, ?, ?)",
                (f"V-HIST-{i}", f"2025-01-0{i+1} 10:00:00", 10000 * (i + 1), client_id)
            )

        historique = Client.obtenir_historique_achats(client_id)
        self.assertEqual(len(historique), 3)
        self.assertEqual(Client.compter_achats(client_id), 3)
        self.assertEqual(Client.calculer_total_achats(client_id), 60000.0)

    def test_historique_ignore_ventes_supprimees(self):
        client_id = Client.ajouter("Client Soft Del")
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, client_id, deleted_at) VALUES (?, ?, ?, ?, ?)",
            ("V-DEL-1", "2025-01-01 10:00:00", 5000, client_id, "2025-01-02 10:00:00")
        )
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, client_id) VALUES (?, ?, ?, ?)",
            ("V-OK-1", "2025-01-01 10:00:00", 3000, client_id)
        )
        self.assertEqual(Client.compter_achats(client_id), 1)
        self.assertEqual(Client.calculer_total_achats(client_id), 3000.0)


if __name__ == '__main__':
    unittest.main()
