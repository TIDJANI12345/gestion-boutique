"""Tests unitaires pour le module Utilisateurs"""
import unittest
from tests.conftest import reset_db

import database
from modules.utilisateurs import Utilisateur


class TestValiderMotDePasse(unittest.TestCase):
    def test_mot_de_passe_valide(self):
        valide, msg = Utilisateur.valider_mot_de_passe("monpass1")
        self.assertTrue(valide)

    def test_mot_de_passe_trop_court(self):
        valide, msg = Utilisateur.valider_mot_de_passe("abc1")
        self.assertFalse(valide)
        self.assertIn("8 caracteres", msg)

    def test_mot_de_passe_sans_chiffre(self):
        valide, msg = Utilisateur.valider_mot_de_passe("abcdefgh")
        self.assertFalse(valide)
        self.assertIn("chiffre", msg)

    def test_mot_de_passe_vide(self):
        valide, msg = Utilisateur.valider_mot_de_passe("")
        self.assertFalse(valide)

    def test_mot_de_passe_exactement_8_avec_chiffre(self):
        valide, msg = Utilisateur.valider_mot_de_passe("abcdefg1")
        self.assertTrue(valide)


class TestCreerUtilisateur(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM logs_actions")
        database.db.execute_query("DELETE FROM utilisateurs")

    def test_creer_utilisateur_valide(self):
        ok, msg = Utilisateur.creer_utilisateur(
            "Dupont", "Jean", "jean@test.com", "password1", "patron"
        )
        self.assertTrue(ok, f"Creation echouee: {msg}")

    def test_creer_utilisateur_mdp_invalide(self):
        ok, msg = Utilisateur.creer_utilisateur(
            "Dupont", "Jean", "jean@test.com", "123", "patron"
        )
        self.assertFalse(ok)
        self.assertIn("8 caracteres", msg)

    def test_creer_utilisateur_email_duplique(self):
        Utilisateur.creer_utilisateur(
            "Dupont", "Jean", "jean@test.com", "password1", "patron"
        )
        ok, msg = Utilisateur.creer_utilisateur(
            "Martin", "Paul", "jean@test.com", "password2", "caissier"
        )
        self.assertFalse(ok)


class TestAuthentification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM logs_actions")
        database.db.execute_query("DELETE FROM utilisateurs")
        Utilisateur.creer_utilisateur(
            "Dupont", "Jean", "jean@test.com", "password1", "patron"
        )

    def test_authentifier_valide(self):
        user = Utilisateur.authentifier("jean@test.com", "password1")
        self.assertIsNotNone(user, "Authentification a echoue alors qu'elle devrait reussir")
        self.assertEqual(user[3], "jean@test.com")

    def test_authentifier_mauvais_mdp(self):
        user = Utilisateur.authentifier("jean@test.com", "mauvais11")
        self.assertIsNone(user)

    def test_authentifier_email_inconnu(self):
        user = Utilisateur.authentifier("inconnu@test.com", "password1")
        self.assertIsNone(user)

    def test_authentifier_utilisateur_inactif(self):
        users = Utilisateur.obtenir_tous()
        user_id = users[0][0]
        Utilisateur.changer_statut(user_id, False)
        user = Utilisateur.authentifier("jean@test.com", "password1")
        self.assertIsNone(user)


if __name__ == '__main__':
    unittest.main()
