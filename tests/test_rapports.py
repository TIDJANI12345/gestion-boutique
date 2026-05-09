"""Tests pour modules/rapports.py."""
import unittest
from datetime import datetime
from tests.conftest import reset_db
import database
from modules.rapports import Rapport


def _creer_produit(nom='TestProd', prix=1000, code='TP001', categorie='Test', stock=10):
    return database.db.execute_query(
        "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel, categorie) VALUES (?, ?, ?, ?, ?)",
        (nom, code, prix, stock, categorie)
    )


def _creer_vente(numero='V001', total=1000, produit_id=None, qte=1, date=None, statut='terminee'):
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    vid = database.db.execute_query(
        "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, ?)",
        (numero, date, total, statut)
    )
    if produit_id:
        database.db.execute_query(
            "INSERT INTO details_ventes (vente_id, produit_id, quantite, prix_unitaire, sous_total) VALUES (?, ?, ?, ?, ?)",
            (vid, produit_id, qte, total // qte if qte else total, total)
        )
    return vid


class TestStatistiquesGenerales(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_structure_retour(self):
        s = Rapport.statistiques_generales()
        for k in ('nb_ventes', 'ca_jour', 'ca_mois', 'ca_total', 'nb_produits', 'valeur_stock'):
            self.assertIn(k, s)

    def test_sans_donnees(self):
        s = Rapport.statistiques_generales()
        self.assertEqual(s['nb_ventes'], 0)
        self.assertEqual(s['ca_total'], 0)
        self.assertEqual(s['nb_produits'], 0)

    def test_avec_vente_du_jour(self):
        pid = _creer_produit()
        _creer_vente(total=5000, produit_id=pid)
        s = Rapport.statistiques_generales()
        self.assertEqual(s['nb_ventes'], 1)
        self.assertEqual(s['ca_jour'], 5000)
        self.assertEqual(s['ca_total'], 5000)

    def test_vente_annulee_ignoree(self):
        _creer_vente('VAN', 9999, statut='annulee')
        s = Rapport.statistiques_generales()
        self.assertEqual(s['nb_ventes'], 0)
        self.assertEqual(s['ca_total'], 0)

    def test_nb_produits(self):
        _creer_produit('P1', code='C1')
        _creer_produit('P2', code='C2')
        s = Rapport.statistiques_generales()
        self.assertEqual(s['nb_produits'], 2)

    def test_valeur_stock(self):
        _creer_produit('P1', prix=1000, code='C1', stock=5)
        s = Rapport.statistiques_generales()
        self.assertEqual(s['valeur_stock'], 5000)


class TestStatistiquesUtilisateur(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.uid = database.db.execute_query(
            "INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role, actif) VALUES (?, ?, ?, ?, ?, 1)",
            ('Test', '', 'u@t.com', 'x', 'caissier')
        )

    def test_sans_ventes(self):
        s = Rapport.statistiques_utilisateur(self.uid)
        self.assertEqual(s['nb_ventes'], 0)
        self.assertEqual(s['ca_jour'], 0)

    def test_avec_ventes_utilisateur(self):
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, utilisateur_id, statut) VALUES (?, ?, ?, ?, 'terminee')",
            ('VU01', today, 3000, self.uid)
        )
        s = Rapport.statistiques_utilisateur(self.uid)
        self.assertEqual(s['nb_ventes'], 1)
        self.assertEqual(s['ca_jour'], 3000)

    def test_ventes_autre_utilisateur_ignorees(self):
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, utilisateur_id, statut) VALUES (?, ?, ?, ?, 'terminee')",
            ('VU02', today, 5000, 9999)
        )
        s = Rapport.statistiques_utilisateur(self.uid)
        self.assertEqual(s['nb_ventes'], 0)


class TestTopProduits(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_vide(self):
        result = list(Rapport.top_produits())
        self.assertEqual(result, [])

    def test_avec_ventes(self):
        p1 = _creer_produit('Prod1', code='P1')
        p2 = _creer_produit('Prod2', code='P2')
        _creer_vente('V1', 2000, p1, qte=2)
        _creer_vente('V2', 1000, p2, qte=1)
        top = list(Rapport.top_produits())
        self.assertEqual(len(top), 2)
        self.assertEqual(top[0]['nom'], 'Prod1')

    def test_limite(self):
        for i in range(5):
            pid = _creer_produit(f'P{i}', code=f'C{i}')
            _creer_vente(f'V{i}', 1000, pid, qte=1)
        top = list(Rapport.top_produits(limite=3))
        self.assertEqual(len(top), 3)


class TestVentesParPeriode(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_vide(self):
        result = list(Rapport.ventes_par_periode('2020-01-01', '2020-01-31'))
        self.assertEqual(result, [])

    def test_avec_ventes_dans_periode(self):
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VP1', '2026-05-09 10:00:00', 3000)
        )
        result = list(Rapport.ventes_par_periode('2026-05-09', '2026-05-09 23:59:59'))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['nb_ventes'], 1)

    def test_ventes_hors_periode_exclues(self):
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VP2', '2026-01-01 10:00:00', 3000)
        )
        result = list(Rapport.ventes_par_periode('2026-05-01', '2026-05-31'))
        self.assertEqual(result, [])


class TestCaParCategorie(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_vide(self):
        result = list(Rapport.ca_par_categorie())
        self.assertEqual(result, [])

    def test_avec_donnees(self):
        p = _creer_produit('Sucre', categorie='Alimentaire')
        _creer_vente('V1', 2000, p, qte=2)
        result = list(Rapport.ca_par_categorie())
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['categorie'], 'Alimentaire')
        self.assertEqual(result[0]['ca_total'], 2000)

    def test_plusieurs_categories(self):
        p1 = _creer_produit('Sucre', code='S1', categorie='Alimentaire')
        p2 = _creer_produit('Stylo', code='S2', categorie='Papeterie')
        _creer_vente('V1', 3000, p1, qte=1)
        _creer_vente('V2', 1000, p2, qte=1)
        result = list(Rapport.ca_par_categorie())
        self.assertEqual(len(result), 2)
        cats = {r['categorie'] for r in result}
        self.assertEqual(cats, {'Alimentaire', 'Papeterie'})


class TestEvolution7Jours(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_sans_ventes(self):
        result = list(Rapport.evolution_ventes_7_jours())
        self.assertEqual(result, [])

    def test_avec_ventes_recentes(self):
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VR1', today, 4000)
        )
        result = list(Rapport.evolution_ventes_7_jours())
        self.assertGreater(len(result), 0)
        cas = [r[2] for r in result]
        self.assertIn(4000, cas)

    def test_ventes_anciennes_exclues(self):
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VA1', '2020-01-01 10:00:00', 9999)
        )
        result = list(Rapport.evolution_ventes_7_jours())
        self.assertEqual(result, [])


class TestRapportJournalier(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_structure(self):
        r = Rapport.rapport_journalier()
        for k in ('date', 'nb_ventes', 'ca_total', 'nb_articles', 'ventes', 'top_produits'):
            self.assertIn(k, r)

    def test_sans_ventes(self):
        r = Rapport.rapport_journalier()
        self.assertEqual(r['nb_ventes'], 0)
        self.assertEqual(r['ca_total'], 0)
        self.assertEqual(r['nb_articles'], 0)

    def test_avec_ventes(self):
        pid = _creer_produit()
        today = datetime.now().strftime('%Y-%m-%d')
        _creer_vente('VJ1', 3000, pid, qte=3)
        r = Rapport.rapport_journalier(today)
        self.assertEqual(r['nb_ventes'], 1)
        self.assertEqual(r['ca_total'], 3000)
        self.assertEqual(r['nb_articles'], 3)

    def test_date_specifique(self):
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VD1', '2026-01-15 10:00:00', 5000)
        )
        r = Rapport.rapport_journalier('2026-01-15')
        self.assertEqual(r['nb_ventes'], 1)
        self.assertEqual(r['ca_total'], 5000)


class TestComparaisonJourPrecedent(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_sans_donnees(self):
        r = Rapport.comparaison_jour_precedent()
        self.assertIn('aujourd_hui', r)
        self.assertIn('hier', r)
        self.assertIn('variation_ca_pct', r)
        self.assertEqual(r['variation_ca_pct'], 0.0)

    def test_avec_ventes_aujourd_hui_seulement(self):
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VC1', today, 6000)
        )
        r = Rapport.comparaison_jour_precedent()
        self.assertEqual(r['aujourd_hui']['ca'], 6000)
        self.assertEqual(r['variation_ca_pct'], 100.0)

    def test_variation_positive_hier(self):
        # Hier avec ventes, aujourd'hui vide → variation = -100%
        from datetime import timedelta
        hier = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VH1', hier, 4000)
        )
        r = Rapport.comparaison_jour_precedent()
        self.assertEqual(r['hier']['ca'], 4000)
        self.assertEqual(r['aujourd_hui']['ca'], 0)
        self.assertLess(r['variation_ca_pct'], 0)


class TestDonneesGraphique(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_periodes_invalides_retour_vide(self):
        self.assertEqual(Rapport.donnees_graphique_ventes('inconnu'), [])

    def test_jour_vide(self):
        self.assertEqual(Rapport.donnees_graphique_ventes('jour'), [])

    def test_semaine_vide(self):
        self.assertEqual(Rapport.donnees_graphique_ventes('semaine'), [])

    def test_mois_vide(self):
        self.assertEqual(Rapport.donnees_graphique_ventes('mois'), [])

    def test_semaine_avec_vente(self):
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VG1', today, 2500)
        )
        result = Rapport.donnees_graphique_ventes('semaine')
        self.assertGreater(len(result), 0)
        amounts = [r[1] for r in result]
        self.assertIn(2500, amounts)

    def test_jour_avec_vente(self):
        today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, ?, ?, 'terminee')",
            ('VG2', today, 1800)
        )
        result = Rapport.donnees_graphique_ventes('jour')
        self.assertGreater(len(result), 0)
        amounts = [r[1] for r in result]
        self.assertIn(1800, amounts)


if __name__ == '__main__':
    unittest.main()
