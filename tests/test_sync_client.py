"""Tests pour modules/sync_client.py."""
import unittest
from unittest.mock import patch, MagicMock
from tests.conftest import reset_db
import database
from modules.sync_client import SyncClient, _operation_to_event_type


class TestOperationToEventType(unittest.TestCase):
    def test_vente(self):
        self.assertEqual(_operation_to_event_type('Vente #V001'), 'vente')

    def test_reappro(self):
        self.assertEqual(_operation_to_event_type('Réapprovisionnement'), 'reappro')
        self.assertEqual(_operation_to_event_type('Reception marchandise'), 'reappro')

    def test_correction(self):
        self.assertEqual(_operation_to_event_type('Correction inventaire'), 'correction')
        self.assertEqual(_operation_to_event_type('Ajustement stock'), 'correction')

    def test_perte(self):
        self.assertEqual(_operation_to_event_type('Perte/casse'), 'perte')
        self.assertEqual(_operation_to_event_type('Vol détecté'), 'perte')

    def test_autre(self):
        self.assertEqual(_operation_to_event_type('Opération inconnue'), 'autre')

    def test_none(self):
        self.assertEqual(_operation_to_event_type(None), 'vente')

    def test_vide(self):
        self.assertEqual(_operation_to_event_type(''), 'vente')


class TestConfigurer(unittest.TestCase):
    def test_non_configure_par_defaut(self):
        sc = SyncClient()
        self.assertFalse(sc.configure)

    def test_configure_apres_parametres(self):
        sc = SyncClient()
        sc.configurer('http://localhost:5000', 'CLE123', 'MACHINE1')
        self.assertTrue(sc.configure)

    def test_configure_url_avec_slash(self):
        sc = SyncClient()
        sc.configurer('http://localhost:5000/', 'CLE', 'MID')
        self.assertFalse(sc._url.endswith('/'))

    def test_non_configure_si_url_vide(self):
        sc = SyncClient()
        sc.configurer('', 'CLE', 'MID')
        self.assertFalse(sc.configure)


class TestPing(unittest.TestCase):
    def setUp(self):
        self.sc = SyncClient()
        self.sc.configurer('http://srv:5000', 'CLE', 'MID')

    def test_ping_succes(self):
        mock_r = MagicMock()
        mock_r.ok = True
        with patch('requests.get', return_value=mock_r) as mock_get:
            result = self.sc.ping()
        self.assertTrue(result)
        mock_get.assert_called_once_with('http://srv:5000/api/sync/ping', timeout=5)

    def test_ping_echec(self):
        mock_r = MagicMock()
        mock_r.ok = False
        with patch('requests.get', return_value=mock_r):
            self.assertFalse(self.sc.ping())

    def test_ping_exception_reseau(self):
        with patch('requests.get', side_effect=ConnectionError()):
            self.assertFalse(self.sc.ping())

    def test_ping_non_configure(self):
        sc = SyncClient()
        self.assertFalse(sc.ping())


class TestCollecterPayload(unittest.TestCase):
    def setUp(self):
        reset_db()
        database.db.migrer_sync()
        self.sc = SyncClient()
        self.sc.configurer('http://srv:5000', 'CLE', 'MID')

    def test_payload_vide_sans_donnees(self):
        payload = self.sc._collecter_payload()
        self.assertIn('produits', payload)
        self.assertIn('ventes', payload)
        self.assertIn('stock_events', payload)
        self.assertIn('utilisateurs', payload)

    def test_stock_events_depuis_historique(self):
        pid = database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
            ('Test', 'CB001', 500, 10)
        )
        database.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation, sync_done) VALUES (?, ?, ?, ?, ?)",
            (pid, 10, 7, 'Vente #V001', 0)
        )
        payload = self.sc._collecter_payload()
        events = payload['stock_events']
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]['delta'], -3)
        self.assertEqual(events[0]['event_type'], 'vente')
        self.assertTrue(events[0]['event_uuid'].startswith('MID:'))

    def test_event_delta_zero_exclu(self):
        pid = database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
            ('Test2', 'CB002', 500, 10)
        )
        database.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation, sync_done) VALUES (?, ?, ?, ?, ?)",
            (pid, 5, 5, 'Opération', 0)
        )
        payload = self.sc._collecter_payload()
        self.assertEqual(len(payload['stock_events']), 0)

    def test_deja_synced_exclu(self):
        pid = database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
            ('Test3', 'CB003', 500, 10)
        )
        database.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation, sync_done) VALUES (?, ?, ?, ?, 1)",
            (pid, 10, 5, 'Vente', 1, )
        )
        payload = self.sc._collecter_payload()
        self.assertEqual(len(payload['stock_events']), 0)


class TestMarquerSyncDone(unittest.TestCase):
    def setUp(self):
        reset_db()
        database.db.migrer_sync()
        self.sc = SyncClient()
        self.sc.configurer('http://srv:5000', 'CLE', 'MID')

    def test_marque_sync_done(self):
        pid = database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente) VALUES (?, ?, ?)",
            ('T', 'CB001', 100)
        )
        hid = database.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation, sync_done) VALUES (?, ?, ?, ?, ?)",
            (pid, 10, 5, 'Vente', 0)
        )
        events = [{'event_uuid': f'MID:{hid}'}]
        self.sc._marquer_sync_done(events)
        row = database.db.fetch_one("SELECT sync_done FROM historique_stock WHERE id = ?", (hid,))
        self.assertEqual(row['sync_done'], 1)

    def test_ignore_event_autre_machine(self):
        pid = database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente) VALUES (?, ?, ?)",
            ('T', 'CB002', 100)
        )
        hid = database.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation, sync_done) VALUES (?, ?, ?, ?, ?)",
            (pid, 10, 5, 'Vente', 0)
        )
        events = [{'event_uuid': f'AUTRE_MACHINE:{hid}'}]
        self.sc._marquer_sync_done(events)
        row = database.db.fetch_one("SELECT sync_done FROM historique_stock WHERE id = ?", (hid,))
        self.assertEqual(row['sync_done'], 0)


class TestAppliquerPull(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.sc = SyncClient()
        self.sc.configurer('http://srv:5000', 'CLE', 'MID')

    def test_appliquer_stock_events(self):
        database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
            ('Prod', 'CB001', 500, 10)
        )
        data = {
            'stock_events': [{'code_barre': 'CB001', 'delta': -3}],
            'last_event_id': 42,
            'produits': [],
            'ventes': [],
            'utilisateurs': [],
        }
        self.sc._appliquer_pull(data)
        p = database.db.fetch_one("SELECT stock_actuel FROM produits WHERE code_barre = 'CB001'")
        self.assertEqual(p['stock_actuel'], 7)

    def test_stock_ne_descend_pas_sous_zero(self):
        database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
            ('Prod', 'CB002', 500, 2)
        )
        data = {
            'stock_events': [{'code_barre': 'CB002', 'delta': -10}],
            'last_event_id': 1,
            'produits': [], 'ventes': [], 'utilisateurs': [],
        }
        self.sc._appliquer_pull(data)
        p = database.db.fetch_one("SELECT stock_actuel FROM produits WHERE code_barre = 'CB002'")
        self.assertEqual(p['stock_actuel'], 0)

    def test_last_event_id_mis_a_jour(self):
        data = {
            'stock_events': [],
            'last_event_id': 99,
            'produits': [], 'ventes': [], 'utilisateurs': [],
        }
        self.sc._appliquer_pull(data)
        self.assertEqual(database.db.get_parametre('sync_last_event_id'), '99')

    def test_produits_mis_a_jour(self):
        database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente) VALUES (?, ?, ?)",
            ('Ancien Nom', 'CB003', 500)
        )
        data = {
            'stock_events': [],
            'last_event_id': 0,
            'produits': [{'code_barre': 'CB003', 'nom': 'Nouveau Nom', 'prix_vente': 750}],
            'ventes': [],
            'utilisateurs': [],
        }
        self.sc._appliquer_pull(data)
        p = database.db.fetch_one("SELECT nom, prix_vente FROM produits WHERE code_barre = 'CB003'")
        self.assertEqual(p['nom'], 'Nouveau Nom')
        self.assertEqual(p['prix_vente'], 750)

    def test_ventes_insertees(self):
        data = {
            'stock_events': [],
            'last_event_id': 0,
            'produits': [],
            'ventes': [{'numero_vente': 'V999', 'date_vente': '2026-01-01', 'total': 5000, 'statut': 'terminee'}],
            'utilisateurs': [],
        }
        self.sc._appliquer_pull(data)
        v = database.db.fetch_one("SELECT * FROM ventes WHERE numero_vente = 'V999'")
        self.assertIsNotNone(v)

    def test_utilisateurs_inseres(self):
        data = {
            'stock_events': [],
            'last_event_id': 0,
            'produits': [],
            'ventes': [],
            'utilisateurs': [{'nom': 'Bob', 'prenom': 'Test', 'email': 'bob@t.com',
                               'mot_de_passe': 'hash', 'role': 'caissier', 'actif': 1}],
        }
        self.sc._appliquer_pull(data)
        u = database.db.fetch_one("SELECT * FROM utilisateurs WHERE email = 'bob@t.com'")
        self.assertIsNotNone(u)


class TestPush(unittest.TestCase):
    def setUp(self):
        reset_db()
        database.db.migrer_sync()
        self.sc = SyncClient()
        self.sc.configurer('http://srv:5000', 'CLE', 'MID')

    def test_push_succes(self):
        mock_r = MagicMock()
        mock_r.ok = True
        with patch('requests.post', return_value=mock_r):
            result = self.sc.push()
        self.assertTrue(result)
        self.assertIsNotNone(database.db.get_parametre('sync_last_push'))

    def test_push_echec_serveur(self):
        mock_r = MagicMock()
        mock_r.ok = False
        mock_r.status_code = 500
        mock_r.text = 'Internal error'
        with patch('requests.post', return_value=mock_r):
            result = self.sc.push()
        self.assertFalse(result)

    def test_push_non_configure(self):
        sc = SyncClient()
        self.assertFalse(sc.push())

    def test_push_marque_sync_done(self):
        pid = database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
            ('T', 'CB001', 100, 10)
        )
        hid = database.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation, sync_done) VALUES (?, ?, ?, ?, ?)",
            (pid, 10, 7, 'Vente', 0)
        )
        mock_r = MagicMock()
        mock_r.ok = True
        with patch('requests.post', return_value=mock_r):
            self.sc.push()
        row = database.db.fetch_one("SELECT sync_done FROM historique_stock WHERE id = ?", (hid,))
        self.assertEqual(row['sync_done'], 1)


class TestPull(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.sc = SyncClient()
        self.sc.configurer('http://srv:5000', 'CLE', 'MID')

    def test_pull_succes(self):
        mock_r = MagicMock()
        mock_r.ok = True
        mock_r.json.return_value = {
            'stock_events': [], 'last_event_id': 10,
            'produits': [], 'ventes': [], 'utilisateurs': [],
        }
        with patch('requests.post', return_value=mock_r):
            result = self.sc.pull()
        self.assertTrue(result)
        self.assertIsNotNone(database.db.get_parametre('sync_last_pull'))

    def test_pull_echec(self):
        mock_r = MagicMock()
        mock_r.ok = False
        mock_r.status_code = 403
        mock_r.text = 'Forbidden'
        with patch('requests.post', return_value=mock_r):
            self.assertFalse(self.sc.pull())

    def test_pull_non_configure(self):
        sc = SyncClient()
        self.assertFalse(sc.pull())


class TestBootstrap(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.sc = SyncClient()
        self.sc.configurer('http://srv:5000', 'CLE', 'MID')

    def test_bootstrap_succes(self):
        mock_r = MagicMock()
        mock_r.ok = True
        mock_r.json.return_value = {
            'produits': [
                {'code_barre': 'CB001', 'nom': 'Prod1', 'prix_vente': 500,
                 'stock_actuel': 20, 'stock_alerte': 5},
            ],
            'last_event_id': 15,
        }
        with patch('requests.get', return_value=mock_r):
            result = self.sc.bootstrap()
        self.assertTrue(result)
        p = database.db.fetch_one("SELECT * FROM produits WHERE code_barre = 'CB001'")
        self.assertIsNotNone(p)
        self.assertEqual(p['stock_actuel'], 20)
        self.assertEqual(database.db.get_parametre('sync_last_event_id'), '15')

    def test_bootstrap_idempotent(self):
        mock_r = MagicMock()
        mock_r.ok = True
        mock_r.json.return_value = {
            'produits': [{'code_barre': 'CB001', 'nom': 'Prod1', 'prix_vente': 500, 'stock_actuel': 20}],
            'last_event_id': 1,
        }
        with patch('requests.get', return_value=mock_r):
            self.sc.bootstrap()
            self.sc.bootstrap()  # deuxième appel ne doit pas dupliquer
        count = database.db.fetch_one("SELECT COUNT(*) as n FROM produits WHERE code_barre = 'CB001'")['n']
        self.assertEqual(count, 1)

    def test_bootstrap_echec(self):
        mock_r = MagicMock()
        mock_r.ok = False
        mock_r.status_code = 403
        mock_r.text = 'Forbidden'
        with patch('requests.get', return_value=mock_r):
            self.assertFalse(self.sc.bootstrap())


if __name__ == '__main__':
    unittest.main()
