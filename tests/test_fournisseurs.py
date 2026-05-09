"""Tests pour modules/fournisseurs.py."""
import unittest
from tests.conftest import reset_db
import database
from modules.fournisseurs import Fournisseur, CommandeFournisseur


def _clear_fournisseurs():
    for tbl in ('details_commandes_fournisseurs', 'commandes_fournisseurs', 'fournisseurs'):
        try:
            database.db.execute_query(f"DELETE FROM {tbl}")
        except Exception:
            pass


def _creer_produit(nom='ProdTest', code='PT001', prix=500, stock=20):
    return database.db.execute_query(
        "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
        (nom, code, prix, stock)
    )


class TestFournisseur(unittest.TestCase):
    def setUp(self):
        reset_db()
        _clear_fournisseurs()

    def test_liste_vide(self):
        self.assertEqual(list(Fournisseur.lister()), [])

    def test_creer(self):
        Fournisseur.creer('Grossiste A', '0101010101', 'g@a.com', 'Cotonou', 'Ali')
        rows = list(Fournisseur.lister())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['nom'], 'Grossiste A')

    def test_creer_minimal(self):
        Fournisseur.creer('Fournisseur Min')
        rows = list(Fournisseur.lister())
        self.assertEqual(len(rows), 1)

    def test_obtenir(self):
        Fournisseur.creer('Distrib B')
        fid = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'Distrib B'")['id']
        f = Fournisseur.obtenir(fid)
        self.assertIsNotNone(f)
        self.assertEqual(f['nom'], 'Distrib B')

    def test_obtenir_inexistant(self):
        self.assertIsNone(Fournisseur.obtenir(9999))

    def test_modifier(self):
        Fournisseur.creer('Ancien Nom')
        fid = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'Ancien Nom'")['id']
        Fournisseur.modifier(fid, 'Nouveau Nom', '0202020202')
        f = Fournisseur.obtenir(fid)
        self.assertEqual(f['nom'], 'Nouveau Nom')
        self.assertEqual(f['telephone'], '0202020202')

    def test_supprimer_soft_delete(self):
        Fournisseur.creer('A Supprimer')
        fid = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'A Supprimer'")['id']
        Fournisseur.supprimer(fid)
        self.assertEqual(list(Fournisseur.lister()), [])
        f = database.db.fetch_one("SELECT actif FROM fournisseurs WHERE id = ?", (fid,))
        self.assertEqual(f['actif'], 0)

    def test_plusieurs_fournisseurs(self):
        for nom in ('FN1', 'FN2', 'FN3'):
            Fournisseur.creer(nom)
        self.assertEqual(len(list(Fournisseur.lister())), 3)

    def test_lister_exclut_inactifs(self):
        Fournisseur.creer('Actif')
        Fournisseur.creer('Inactif')
        fid = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'Inactif'")['id']
        Fournisseur.supprimer(fid)
        rows = list(Fournisseur.lister())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['nom'], 'Actif')


class TestCommandeFournisseurCreer(unittest.TestCase):
    def setUp(self):
        reset_db()
        _clear_fournisseurs()
        Fournisseur.creer('TestFourn')
        self.fid = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'TestFourn'")['id']
        self.p1 = _creer_produit('Prod1', 'C1', 500, 10)
        self.p2 = _creer_produit('Prod2', 'C2', 800, 5)

    def test_creer_commande(self):
        lignes = [
            {'produit_id': self.p1, 'quantite': 10, 'prix_unitaire': 400},
            {'produit_id': self.p2, 'quantite': 5, 'prix_unitaire': 700},
        ]
        cid = CommandeFournisseur.creer(self.fid, lignes)
        self.assertIsNotNone(cid)
        self.assertIsInstance(cid, int)

    def test_total_calcule(self):
        lignes = [{'produit_id': self.p1, 'quantite': 10, 'prix_unitaire': 400}]
        cid = CommandeFournisseur.creer(self.fid, lignes)
        c = CommandeFournisseur.obtenir(cid)
        self.assertEqual(c['total'], 4000)

    def test_total_plusieurs_lignes(self):
        lignes = [
            {'produit_id': self.p1, 'quantite': 10, 'prix_unitaire': 400},
            {'produit_id': self.p2, 'quantite': 5, 'prix_unitaire': 600},
        ]
        cid = CommandeFournisseur.creer(self.fid, lignes)
        c = CommandeFournisseur.obtenir(cid)
        self.assertEqual(c['total'], 7000)

    def test_statut_initial_en_attente(self):
        cid = CommandeFournisseur.creer(self.fid, [{'produit_id': self.p1, 'quantite': 5, 'prix_unitaire': 400}])
        c = CommandeFournisseur.obtenir(cid)
        self.assertEqual(c['statut'], 'en_attente')

    def test_notes_enregistrees(self):
        cid = CommandeFournisseur.creer(self.fid, [{'produit_id': self.p1, 'quantite': 1, 'prix_unitaire': 0}],
                                        notes='Urgence')
        c = CommandeFournisseur.obtenir(cid)
        self.assertEqual(c['notes'], 'Urgence')


class TestCommandeFournisseurLister(unittest.TestCase):
    def setUp(self):
        reset_db()
        _clear_fournisseurs()
        Fournisseur.creer('F1')
        Fournisseur.creer('F2')
        self.fid1 = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'F1'")['id']
        self.fid2 = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'F2'")['id']
        self.p = _creer_produit()

    def test_lister_toutes(self):
        CommandeFournisseur.creer(self.fid1, [{'produit_id': self.p, 'quantite': 1, 'prix_unitaire': 0}])
        CommandeFournisseur.creer(self.fid2, [{'produit_id': self.p, 'quantite': 1, 'prix_unitaire': 0}])
        self.assertEqual(len(list(CommandeFournisseur.lister())), 2)

    def test_lister_par_fournisseur(self):
        CommandeFournisseur.creer(self.fid1, [{'produit_id': self.p, 'quantite': 1, 'prix_unitaire': 0}])
        CommandeFournisseur.creer(self.fid2, [{'produit_id': self.p, 'quantite': 1, 'prix_unitaire': 0}])
        rows = list(CommandeFournisseur.lister(self.fid1))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['fournisseur_nom'], 'F1')

    def test_lister_vide(self):
        self.assertEqual(list(CommandeFournisseur.lister()), [])

    def test_obtenir_details(self):
        lignes = [
            {'produit_id': self.p, 'quantite': 3, 'prix_unitaire': 400},
        ]
        cid = CommandeFournisseur.creer(self.fid1, lignes)
        details = list(CommandeFournisseur.obtenir_details(cid))
        self.assertEqual(len(details), 1)
        self.assertEqual(details[0]['quantite_commandee'], 3)

    def test_obtenir_details_plusieurs_lignes(self):
        p2 = _creer_produit('Prod2', 'C2')
        lignes = [
            {'produit_id': self.p, 'quantite': 3, 'prix_unitaire': 400},
            {'produit_id': p2, 'quantite': 2, 'prix_unitaire': 700},
        ]
        cid = CommandeFournisseur.creer(self.fid1, lignes)
        details = list(CommandeFournisseur.obtenir_details(cid))
        self.assertEqual(len(details), 2)


class TestRecevoir(unittest.TestCase):
    def setUp(self):
        reset_db()
        _clear_fournisseurs()
        Fournisseur.creer('TestFourn')
        self.fid = database.db.fetch_one("SELECT id FROM fournisseurs WHERE nom = 'TestFourn'")['id']
        self.p1 = _creer_produit('Prod1', 'C1', 500, 10)
        self.p2 = _creer_produit('Prod2', 'C2', 800, 5)

    def _creer_commande(self, qte1=10, qte2=6):
        lignes = [
            {'produit_id': self.p1, 'quantite': qte1, 'prix_unitaire': 400},
            {'produit_id': self.p2, 'quantite': qte2, 'prix_unitaire': 700},
        ]
        cid = CommandeFournisseur.creer(self.fid, lignes)
        details = list(CommandeFournisseur.obtenir_details(cid))
        return cid, details

    def test_reception_totale_statut_recue(self):
        cid, details = self._creer_commande()
        d1 = next(d for d in details if d['code_barre'] == 'C1')
        d2 = next(d for d in details if d['code_barre'] == 'C2')
        CommandeFournisseur.recevoir(cid, [
            {'detail_id': d1['id'], 'quantite_recue': 10},
            {'detail_id': d2['id'], 'quantite_recue': 6},
        ])
        self.assertEqual(CommandeFournisseur.obtenir(cid)['statut'], 'recue')

    def test_reception_partielle_statut_partielle(self):
        cid, details = self._creer_commande()
        d1 = next(d for d in details if d['code_barre'] == 'C1')
        CommandeFournisseur.recevoir(cid, [{'detail_id': d1['id'], 'quantite_recue': 5}])
        self.assertEqual(CommandeFournisseur.obtenir(cid)['statut'], 'partielle')

    def test_reception_nulle_statut_envoyee(self):
        cid, details = self._creer_commande()
        d1 = next(d for d in details if d['code_barre'] == 'C1')
        CommandeFournisseur.recevoir(cid, [{'detail_id': d1['id'], 'quantite_recue': 0}])
        self.assertEqual(CommandeFournisseur.obtenir(cid)['statut'], 'envoyee')

    def test_stock_mis_a_jour(self):
        cid, details = self._creer_commande()
        d1 = next(d for d in details if d['code_barre'] == 'C1')
        CommandeFournisseur.recevoir(cid, [{'detail_id': d1['id'], 'quantite_recue': 8}])
        stock = database.db.fetch_one(
            "SELECT stock_actuel FROM produits WHERE id = ?", (self.p1,)
        )['stock_actuel']
        self.assertEqual(stock, 18)  # 10 + 8

    def test_reception_incrementale(self):
        cid, details = self._creer_commande()
        d1 = next(d for d in details if d['code_barre'] == 'C1')
        CommandeFournisseur.recevoir(cid, [{'detail_id': d1['id'], 'quantite_recue': 4}])
        CommandeFournisseur.recevoir(cid, [{'detail_id': d1['id'], 'quantite_recue': 6}])
        stock = database.db.fetch_one(
            "SELECT stock_actuel FROM produits WHERE id = ?", (self.p1,)
        )['stock_actuel']
        self.assertEqual(stock, 20)  # 10 + 4 + 6

    def test_detail_inexistant_ignore(self):
        cid, details = self._creer_commande()
        CommandeFournisseur.recevoir(cid, [{'detail_id': 9999, 'quantite_recue': 5}])

    def test_reception_negative_ignoree(self):
        cid, details = self._creer_commande()
        d1 = next(d for d in details if d['code_barre'] == 'C1')
        CommandeFournisseur.recevoir(cid, [{'detail_id': d1['id'], 'quantite_recue': -3}])
        stock = database.db.fetch_one(
            "SELECT stock_actuel FROM produits WHERE id = ?", (self.p1,)
        )['stock_actuel']
        self.assertEqual(stock, 10)  # inchangé


if __name__ == '__main__':
    unittest.main()
