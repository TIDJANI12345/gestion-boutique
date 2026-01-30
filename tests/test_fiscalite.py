"""Tests unitaires pour le module Fiscalite (Phase 2.4)"""
import unittest
from tests.conftest import reset_db

import database
from modules.fiscalite import Fiscalite


class TestCalculTVA(unittest.TestCase):
    """Test calculs HT/TVA/TTC"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def test_calcul_tva_18_pourcent(self):
        """Decomposition TVA a 18% (standard Benin)"""
        result = Fiscalite.calculer_tva(11800, taux=18)
        self.assertAlmostEqual(result['ht'], 10000, places=0)
        self.assertAlmostEqual(result['tva'], 1800, places=0)
        self.assertEqual(result['ttc'], 11800)
        self.assertEqual(result['taux'], 18)

    def test_calcul_tva_zero(self):
        """Pas de TVA (taux 0)"""
        result = Fiscalite.calculer_tva(5000, taux=0)
        self.assertEqual(result['ht'], 5000)
        self.assertEqual(result['tva'], 0)
        self.assertEqual(result['ttc'], 5000)

    def test_calcul_tva_20_pourcent(self):
        """TVA a 20%"""
        result = Fiscalite.calculer_tva(12000, taux=20)
        self.assertAlmostEqual(result['ht'], 10000, places=0)
        self.assertAlmostEqual(result['tva'], 2000, places=0)

    def test_calcul_tva_petit_montant(self):
        """TVA sur un petit montant"""
        result = Fiscalite.calculer_tva(100, taux=18)
        self.assertAlmostEqual(result['ht'] + result['tva'], 100, places=1)

    def test_formule_coherente(self):
        """Verifier que HT + TVA = TTC"""
        for montant in [500, 1000, 7500, 15000, 100000]:
            result = Fiscalite.calculer_tva(montant, taux=18)
            self.assertAlmostEqual(
                result['ht'] + result['tva'], result['ttc'], places=1,
                msg=f"HT + TVA != TTC pour montant {montant}"
            )


class TestTVAActivation(unittest.TestCase):
    """Test activation/desactivation TVA"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def test_tva_desactivee_par_defaut(self):
        """La TVA est desactivee par defaut"""
        self.assertFalse(Fiscalite.tva_active())

    def test_activer_tva(self):
        """Activer la TVA"""
        database.db.set_parametre('tva_active', '1')
        self.assertTrue(Fiscalite.tva_active())

    def test_desactiver_tva(self):
        """Desactiver la TVA"""
        database.db.set_parametre('tva_active', '1')
        database.db.set_parametre('tva_active', '0')
        self.assertFalse(Fiscalite.tva_active())

    def test_taux_defaut(self):
        """Taux par defaut = 18%"""
        taux = Fiscalite.taux_tva_defaut()
        self.assertEqual(taux, 18.0)

    def test_modifier_taux_defaut(self):
        """Modifier le taux par defaut"""
        database.db.set_parametre('tva_taux_defaut', '20')
        taux = Fiscalite.taux_tva_defaut()
        self.assertEqual(taux, 20.0)
        # Remettre la valeur par defaut
        database.db.set_parametre('tva_taux_defaut', '18')


class TestTauxParCategorie(unittest.TestCase):
    """Test taux TVA par categorie"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def setUp(self):
        database.db.execute_query("DELETE FROM taux_tva")

    def test_definir_taux_categorie(self):
        """Definir un taux pour une categorie"""
        result = Fiscalite.definir_taux_categorie("Boissons", 10, "Taux reduit boissons")
        self.assertIsNotNone(result)

    def test_obtenir_taux_categorie(self):
        """Recuperer le taux d'une categorie"""
        Fiscalite.definir_taux_categorie("Alimentaire", 5, "Taux reduit alimentaire")
        taux = Fiscalite.obtenir_taux_categorie("Alimentaire")
        self.assertEqual(taux, 5)

    def test_categorie_sans_taux_specifique(self):
        """Categorie sans taux => retourne le taux par defaut"""
        taux = Fiscalite.obtenir_taux_categorie("Inconnu")
        self.assertEqual(taux, Fiscalite.taux_tva_defaut())

    def test_lister_taux(self):
        """Lister tous les taux par categorie"""
        Fiscalite.definir_taux_categorie("Alimentaire", 5, "Reduit")
        Fiscalite.definir_taux_categorie("Boissons", 10, "Intermediaire")
        taux = Fiscalite.lister_taux_tva()
        self.assertEqual(len(taux), 2)

    def test_supprimer_taux_categorie(self):
        """Supprimer le taux d'une categorie"""
        Fiscalite.definir_taux_categorie("Test", 15, "Test")
        Fiscalite.supprimer_taux_categorie("Test")
        taux = Fiscalite.lister_taux_tva()
        self.assertEqual(len(taux), 0)


class TestDevises(unittest.TestCase):
    """Test gestion multi-devises"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def test_devise_principale(self):
        """La devise principale est XOF/FCFA"""
        devise = Fiscalite.devise_principale()
        self.assertEqual(devise['code'], 'XOF')
        self.assertEqual(devise['symbole'], 'FCFA')

    def test_devises_par_defaut(self):
        """Les devises XOF, EUR, USD sont presentes par defaut"""
        devises = Fiscalite.lister_devises()
        codes = [d[1] for d in devises]
        self.assertIn('XOF', codes)
        self.assertIn('EUR', codes)
        self.assertIn('USD', codes)

    def test_conversion_xof_vers_eur(self):
        """Conversion XOF vers EUR"""
        # 655.957 XOF = 1 EUR
        montant_eur = Fiscalite.convertir(655957, 'EUR')
        self.assertAlmostEqual(montant_eur, 1000, places=0)

    def test_conversion_xof_identique(self):
        """Conversion XOF vers XOF = meme montant"""
        montant = Fiscalite.convertir(10000, 'XOF')
        self.assertEqual(montant, 10000)

    def test_ajouter_devise(self):
        """Ajouter une nouvelle devise"""
        Fiscalite.ajouter_devise('GBP', '£', 780.0)
        devises = Fiscalite.lister_devises()
        codes = [d[1] for d in devises]
        self.assertIn('GBP', codes)

    def test_maj_taux_change(self):
        """Mettre a jour un taux de change"""
        Fiscalite.maj_taux_change('USD', 610.0)
        montant = Fiscalite.convertir(6100, 'USD')
        self.assertAlmostEqual(montant, 10, places=0)
        # Remettre la valeur originale
        Fiscalite.maj_taux_change('USD', 600.0)


class TestRapportTVA(unittest.TestCase):
    """Test rapport TVA mensuel"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def test_rapport_tva_mensuel(self):
        """Rapport TVA retourne les bons champs"""
        rapport = Fiscalite.rapport_tva_mensuel()
        self.assertIn('mois', rapport)
        self.assertIn('annee', rapport)
        self.assertIn('total_ttc', rapport)
        self.assertIn('total_ht', rapport)
        self.assertIn('total_tva', rapport)
        self.assertIn('taux', rapport)

    def test_rapport_tva_coherence(self):
        """HT + TVA = TTC dans le rapport"""
        rapport = Fiscalite.rapport_tva_mensuel()
        self.assertAlmostEqual(
            rapport['total_ht'] + rapport['total_tva'],
            rapport['total_ttc'],
            places=1
        )


if __name__ == '__main__':
    unittest.main()
