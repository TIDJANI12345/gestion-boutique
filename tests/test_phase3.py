"""Tests unitaires pour la Phase 3 - Experience utilisateur"""
import unittest
from tests.conftest import reset_db

import database
from modules.rapports import Rapport
from modules.produits import Produit


class TestComparaisonJour(unittest.TestCase):
    """Test comparaison ventes jour vs hier"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def test_comparaison_retourne_structure(self):
        """La comparaison retourne les bonnes cles"""
        data = Rapport.comparaison_jour_precedent()
        self.assertIn('aujourd_hui', data)
        self.assertIn('hier', data)
        self.assertIn('variation_ca_pct', data)
        self.assertIn('nb', data['aujourd_hui'])
        self.assertIn('ca', data['aujourd_hui'])

    def test_variation_zero_sans_donnees(self):
        """Sans ventes, la variation est 0%"""
        data = Rapport.comparaison_jour_precedent()
        self.assertEqual(data['variation_ca_pct'], 0.0)


class TestDonneesGraphique(unittest.TestCase):
    """Test donnees formatees pour graphiques"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def test_graphique_jour(self):
        """Donnees graphique par jour = liste"""
        data = Rapport.donnees_graphique_ventes('jour')
        self.assertIsInstance(data, list)

    def test_graphique_semaine(self):
        """Donnees graphique par semaine = liste"""
        data = Rapport.donnees_graphique_ventes('semaine')
        self.assertIsInstance(data, list)

    def test_graphique_mois(self):
        """Donnees graphique par mois = liste"""
        data = Rapport.donnees_graphique_ventes('mois')
        self.assertIsInstance(data, list)

    def test_graphique_invalide(self):
        """Periode invalide retourne liste vide"""
        data = Rapport.donnees_graphique_ventes('annee')
        self.assertEqual(data, [])


class TestRechercheFiltre(unittest.TestCase):
    """Test recherche filtree avec pagination"""

    @classmethod
    def setUpClass(cls):
        reset_db()
        # Creer des produits de test
        database.db.execute_query("DELETE FROM produits")
        for i in range(10):
            Produit.ajouter(f"Produit_{i}", "CatA", 100, 200 + i * 100, 20, 5)
        for i in range(5):
            Produit.ajouter(f"Article_{i}", "CatB", 50, 100, 2, 5)
        # Un produit en rupture
        Produit.ajouter("Rupture_item", "CatC", 10, 500, 0, 5)

    def test_recherche_par_terme(self):
        """Recherche par terme filtre correctement"""
        results = Produit.rechercher_filtre(terme="Produit")
        self.assertEqual(len(results), 10)

    def test_recherche_par_categorie(self):
        """Filtre par categorie"""
        results = Produit.rechercher_filtre(categorie="CatB")
        self.assertEqual(len(results), 5)

    def test_filtre_stock_faible(self):
        """Filtre stock faible"""
        results = Produit.rechercher_filtre(stock_filter="Stock faible")
        self.assertEqual(len(results), 5)  # Les 5 articles CatB (stock 2 <= seuil 5)

    def test_filtre_rupture(self):
        """Filtre rupture de stock"""
        results = Produit.rechercher_filtre(stock_filter="Rupture")
        self.assertEqual(len(results), 1)

    def test_filtre_prix_min(self):
        """Filtre par prix minimum"""
        results = Produit.rechercher_filtre(prix_min=500)
        self.assertGreaterEqual(len(results), 1)

    def test_pagination_limit(self):
        """Pagination limite les resultats"""
        results = Produit.rechercher_filtre(limit=5, offset=0)
        self.assertEqual(len(results), 5)

    def test_pagination_offset(self):
        """Pagination avec offset"""
        page1 = Produit.rechercher_filtre(limit=5, offset=0)
        page2 = Produit.rechercher_filtre(limit=5, offset=5)
        # Les pages ne doivent pas avoir les memes produits
        ids1 = {p[0] for p in page1}
        ids2 = {p[0] for p in page2}
        self.assertEqual(len(ids1 & ids2), 0)

    def test_compter_filtre(self):
        """Compter les resultats filtres"""
        total = Produit.compter_filtre(categorie="CatA")
        self.assertEqual(total, 10)

    def test_compter_total(self):
        """Compter sans filtre = tous les produits"""
        total = Produit.compter_filtre()
        self.assertEqual(total, 16)  # 10 + 5 + 1

    def test_filtres_combines(self):
        """Combiner terme + categorie"""
        results = Produit.rechercher_filtre(terme="Produit", categorie="CatA")
        self.assertEqual(len(results), 10)

        results = Produit.rechercher_filtre(terme="Produit", categorie="CatB")
        self.assertEqual(len(results), 0)


class TestThemeManager(unittest.TestCase):
    """Test du gestionnaire de theme"""

    @classmethod
    def setUpClass(cls):
        reset_db()

    def test_theme_defaut_clair(self):
        """Le theme par defaut est clair"""
        from modules.theme import ThemeManager
        tm = ThemeManager.instance()
        # Reset to default
        database.db.set_parametre('theme', 'clair')
        tm._current_theme = 'clair'
        tm._apply_to_colors()
        self.assertFalse(tm.est_sombre)

    def test_basculer_theme(self):
        """Basculer le theme change l'etat"""
        from modules.theme import ThemeManager
        tm = ThemeManager.instance()
        initial = tm.est_sombre
        tm.basculer()
        self.assertNotEqual(tm.est_sombre, initial)
        # Remettre
        tm.basculer()
        self.assertEqual(tm.est_sombre, initial)

    def test_theme_persiste(self):
        """Le theme est sauvegarde en base"""
        from modules.theme import ThemeManager
        tm = ThemeManager.instance()
        tm._current_theme = 'clair'
        database.db.set_parametre('theme', 'clair')
        tm.basculer()
        saved = database.db.get_parametre('theme', 'clair')
        self.assertEqual(saved, 'sombre')
        # Remettre
        tm.basculer()

    def test_colors_mises_a_jour(self):
        """COLORS est mis a jour apres basculement"""
        from modules.theme import ThemeManager
        from config import COLORS, THEME_SOMBRE
        tm = ThemeManager.instance()
        tm._current_theme = 'clair'
        tm._apply_to_colors()
        tm.basculer()
        # En mode sombre, bg devrait etre sombre
        self.assertEqual(COLORS['bg'], THEME_SOMBRE['bg'])
        # Remettre
        tm.basculer()


if __name__ == '__main__':
    unittest.main()
