"""Tests pour le module import_csv."""
import unittest
from tests.conftest import reset_db
import database
from modules.import_csv import analyser_csv, importer_lignes, modele_csv, ENTETES_TOUS


CSV_VALIDE = """nom;categorie;prix_achat;prix_vente;stock_actuel;stock_alerte
Coca Cola;Boissons;400;600;50;10
Riz local;Alimentation;500;750;100;20
Savon Dove;Hygiene;200;350;30;5
"""

CSV_AVEC_ERREURS = """nom;categorie;prix_achat;prix_vente;stock_actuel;stock_alerte
Bon Produit;Cat;100;200;10;5
;Cat;100;200;10;5
MauvasPrix;Cat;abc;200;10;5
PrixNegatif;Cat;100;-50;10;5
"""

CSV_VIRGULE = """nom,categorie,prix_achat,prix_vente,stock_actuel,stock_alerte
Produit A,Cat,100,200,10,5
"""

CSV_SANS_ENTETE_REQUIS = """nom;prix_achat
Produit X;100
"""


class TestAnalyserCSV(unittest.TestCase):

    def test_csv_valide_3_lignes(self):
        lignes, erreurs = analyser_csv(CSV_VALIDE)
        self.assertEqual(erreurs, [])
        self.assertEqual(len(lignes), 3)
        self.assertTrue(all(l.valide for l in lignes))

    def test_separateur_virgule_auto(self):
        lignes, erreurs = analyser_csv(CSV_VIRGULE)
        self.assertEqual(erreurs, [])
        self.assertEqual(len(lignes), 1)
        self.assertTrue(lignes[0].valide)

    def test_colonne_manquante(self):
        _, erreurs = analyser_csv(CSV_SANS_ENTETE_REQUIS)
        self.assertTrue(len(erreurs) > 0)
        self.assertTrue(any('categorie' in e.lower() or 'prix_vente' in e.lower()
                            for e in erreurs))

    def test_lignes_avec_erreurs(self):
        lignes, erreurs = analyser_csv(CSV_AVEC_ERREURS)
        self.assertEqual(erreurs, [])
        valides = [l for l in lignes if l.valide]
        invalides = [l for l in lignes if not l.valide]
        self.assertEqual(len(valides), 1)   # "Bon Produit"
        self.assertEqual(len(invalides), 3)

    def test_nom_manquant_invalide(self):
        lignes, _ = analyser_csv(CSV_AVEC_ERREURS)
        # ligne 2 : nom vide
        ligne_sans_nom = next(l for l in lignes if not l.donnees.get('nom'))
        self.assertFalse(ligne_sans_nom.valide)
        self.assertTrue(any("nom" in e.lower() for e in ligne_sans_nom.erreurs))

    def test_prix_negatif_invalide(self):
        lignes, _ = analyser_csv(CSV_AVEC_ERREURS)
        ligne_neg = next(l for l in lignes if l.donnees.get('nom') == 'PrixNegatif')
        self.assertFalse(ligne_neg.valide)

    def test_donnees_correctement_typees(self):
        lignes, _ = analyser_csv(CSV_VALIDE)
        d = lignes[0].donnees
        self.assertIsInstance(d['prix_achat'], float)
        self.assertIsInstance(d['prix_vente'], float)
        self.assertIsInstance(d['stock_actuel'], int)

    def test_modele_csv_parseable(self):
        contenu = modele_csv()
        lignes, erreurs = analyser_csv(contenu)
        self.assertEqual(erreurs, [])
        self.assertEqual(len(lignes), 1)  # 1 ligne d'exemple
        self.assertTrue(lignes[0].valide)


class TestImporterLignes(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_import_3_produits(self):
        lignes, _ = analyser_csv(CSV_VALIDE)
        nb_ok, nb_err, msgs = importer_lignes(lignes)
        self.assertEqual(nb_ok, 3)
        self.assertEqual(nb_err, 0)

    def test_import_ignore_invalides(self):
        lignes, _ = analyser_csv(CSV_AVEC_ERREURS)
        nb_ok, nb_err, msgs = importer_lignes(lignes)
        self.assertEqual(nb_ok, 1)
        self.assertEqual(nb_err, 3)

    def test_produits_bien_inseres_en_db(self):
        from modules.produits import Produit
        lignes, _ = analyser_csv(CSV_VALIDE)
        importer_lignes(lignes)
        tous = Produit.rechercher("Coca")
        self.assertTrue(len(tous) >= 1)
        self.assertEqual(tous[0]['nom'], 'Coca Cola')
        self.assertEqual(tous[0]['prix_vente'], 600.0)

    def test_import_valeurs_par_defaut(self):
        """Colonnes optionnelles absentes → valeurs par défaut."""
        from modules.produits import Produit
        csv_minimal = "nom;categorie;prix_achat;prix_vente\nProduit Min;Cat;50;100\n"
        lignes, _ = analyser_csv(csv_minimal)
        self.assertTrue(lignes[0].valide)
        nb_ok, _, _ = importer_lignes(lignes)
        self.assertEqual(nb_ok, 1)
        p = Produit.rechercher("Produit Min")[0]
        self.assertEqual(p['stock_actuel'], 0)
        self.assertEqual(p['unite_mesure'], 'pièce')


if __name__ == '__main__':
    unittest.main()
