"""Tests pour le module ardoise (crédit client)."""
import unittest
from tests.conftest import reset_db
import database
from modules.produits import Produit
from modules.ardoise import (
    creer_ardoise, encaisser, solde_client,
    liste_ardoise_client, liste_debiteurs, stats_ardoise,
)


def _creer_client(nom="Client Test", tel="0000"):
    db = database.db
    cid = db.execute_query(
        "INSERT INTO clients (nom, telephone) VALUES (?, ?)", (nom, tel)
    )
    return cid


class TestCreerArdoise(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.client_id = _creer_client()

    def test_creer_valide(self):
        aid = creer_ardoise(self.client_id, 5000)
        self.assertIsNotNone(aid)
        self.assertIsInstance(aid, int)

    def test_montant_zero_refuse(self):
        self.assertIsNone(creer_ardoise(self.client_id, 0))

    def test_montant_negatif_refuse(self):
        self.assertIsNone(creer_ardoise(self.client_id, -100))

    def test_sans_client_refuse(self):
        self.assertIsNone(creer_ardoise(None, 1000))

    def test_statut_initial_en_cours(self):
        aid = creer_ardoise(self.client_id, 3000)
        row = database.db.fetch_one("SELECT * FROM ardoise WHERE id = ?", (aid,))
        self.assertEqual(row['statut'], 'en_cours')
        self.assertEqual(row['montant_restant'], 3000)


class TestEncaisser(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.client_id = _creer_client("Débiteur", "0601")
        self.aid = creer_ardoise(self.client_id, 10000)

    def test_paiement_partiel(self):
        ok, msg, enc_id = encaisser(self.aid, 4000)
        self.assertTrue(ok)
        self.assertIsNotNone(enc_id)
        row = database.db.fetch_one("SELECT * FROM ardoise WHERE id = ?", (self.aid,))
        self.assertEqual(row['montant_restant'], 6000)
        self.assertEqual(row['statut'], 'partiel')

    def test_paiement_total(self):
        ok, msg, enc_id = encaisser(self.aid, 10000)
        self.assertTrue(ok)
        self.assertIsNotNone(enc_id)
        row = database.db.fetch_one("SELECT * FROM ardoise WHERE id = ?", (self.aid,))
        self.assertEqual(row['statut'], 'solde')
        self.assertIn("soldée", msg.lower())

    def test_paiement_superieur_ajuste(self):
        ok, msg, enc_id = encaisser(self.aid, 99999)
        self.assertTrue(ok)
        row = database.db.fetch_one("SELECT * FROM ardoise WHERE id = ?", (self.aid,))
        self.assertEqual(row['statut'], 'solde')

    def test_deja_solde_refuse(self):
        encaisser(self.aid, 10000)
        ok, msg, enc_id = encaisser(self.aid, 500)
        self.assertFalse(ok)
        self.assertIsNone(enc_id)
        self.assertIn("déjà", msg.lower())

    def test_montant_zero_refuse(self):
        ok, msg, enc_id = encaisser(self.aid, 0)
        self.assertFalse(ok)
        self.assertIsNone(enc_id)

    def test_ardoise_inexistante(self):
        ok, msg, enc_id = encaisser(9999, 100)
        self.assertFalse(ok)
        self.assertIsNone(enc_id)


class TestSoldeClient(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.client_id = _creer_client("Multi", "0602")

    def test_solde_sans_ardoise(self):
        self.assertEqual(solde_client(self.client_id), 0.0)

    def test_solde_avec_plusieurs_ardoises(self):
        creer_ardoise(self.client_id, 3000)
        creer_ardoise(self.client_id, 2000)
        self.assertEqual(solde_client(self.client_id), 5000.0)

    def test_solde_ignore_soldees(self):
        aid = creer_ardoise(self.client_id, 3000)
        encaisser(aid, 3000)  # soldée
        creer_ardoise(self.client_id, 1500)
        self.assertEqual(solde_client(self.client_id), 1500.0)


class TestListeDebiteurs(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_liste_vide(self):
        self.assertEqual(liste_debiteurs(), [])

    def test_liste_avec_debiteurs(self):
        c1 = _creer_client("Alice", "0001")
        c2 = _creer_client("Bob", "0002")
        creer_ardoise(c1, 8000)
        creer_ardoise(c2, 2000)
        debiteurs = liste_debiteurs()
        self.assertEqual(len(debiteurs), 2)
        # Triés par solde décroissant
        self.assertEqual(debiteurs[0]['client_nom'], 'Alice')
        self.assertEqual(debiteurs[1]['client_nom'], 'Bob')

    def test_stats(self):
        c = _creer_client("Stats", "0003")
        creer_ardoise(c, 5000)
        s = stats_ardoise()
        self.assertGreaterEqual(s['total_du'], 5000)
        self.assertGreaterEqual(s['nb_debiteurs'], 1)


if __name__ == '__main__':
    unittest.main()
