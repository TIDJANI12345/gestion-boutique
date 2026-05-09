"""
Tests pour le système de synchronisation événementielle.
Couvre : serveur_sync/app.py (Flask) + modules/sync_client.py (client).
"""
import sys
import os
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Setup DB in-memory avant tout import ──────────────────────────────────────
import config
config.DB_PATH = ':memory:'
config.DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
os.makedirs(config.DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(config.DATA_DIR, 'logs'), exist_ok=True)

import database
from tests.conftest import reset_db


# =============================================================================
# Tests serveur (Flask test client, DB SQLite en mémoire séparée)
# =============================================================================

class TestServeurSyncPush(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import tempfile
        # mkstemp ferme immédiatement le fd → SQLite peut ouvrir le fichier sur Windows
        fd, cls.sync_db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        import serveur_sync.app as srv
        srv.SYNC_DB_PATH = cls.sync_db_path
        srv.init_sync_db()
        srv.app.config['TESTING'] = True
        srv.valider_licence = lambda k: True

        cls.client = srv.app.test_client()
        cls.headers = {
            'X-Licence-Key': 'LICENCE-TEST',
            'X-Machine-Id': 'TERMINAL-A',
        }

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls.sync_db_path)
        except (PermissionError, OSError):
            pass  # Windows : connexions SQLite encore ouvertes

    def _get_db(self):
        import sqlite3
        conn = sqlite3.connect(self.sync_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _push(self, payload):
        return self.client.post(
            '/api/sync/push',
            data=json.dumps(payload),
            content_type='application/json',
            headers=self.headers,
        )

    # ── Ping ──────────────────────────────────────────────────────────────────

    def test_ping(self):
        r = self.client.get('/api/sync/ping')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['status'], 'ok')

    # ── Push : authentification ───────────────────────────────────────────────

    def test_push_sans_auth_rejete(self):
        r = self.client.post('/api/sync/push', json={})
        self.assertEqual(r.status_code, 401)

    # ── Push : événement de stock ─────────────────────────────────────────────

    def test_push_event_insere_et_stock_mis_a_jour(self):
        # Créer le produit sur le serveur d'abord
        self._push({'produits': [{
            'code_barre': 'CB001', 'nom': 'Savon', 'prix_vente': 500,
            'stock_alerte': 5,
        }]})
        # Simuler stock initial via correction
        self._push({'stock_events': [{
            'event_uuid': 'init-CB001', 'code_barre': 'CB001',
            'delta': 20, 'event_type': 'correction',
        }]})

        # Vente de 3 unités
        r = self._push({'stock_events': [{
            'event_uuid': 'vente-001', 'code_barre': 'CB001',
            'delta': -3, 'event_type': 'vente', 'reference': 'V2026-001',
        }]})
        self.assertEqual(r.status_code, 200)

        conn = self._get_db()
        row = conn.execute(
            "SELECT stock_actuel FROM sync_produits WHERE code_barre = 'CB001'"
        ).fetchone()
        conn.close()
        self.assertEqual(row['stock_actuel'], 17)  # 20 - 3

    def test_push_event_idempotent(self):
        """Le même event_uuid poussé deux fois ne double pas le delta."""
        self._push({'produits': [{'code_barre': 'CB002', 'nom': 'Lait', 'prix_vente': 300, 'stock_alerte': 2}]})
        self._push({'stock_events': [{'event_uuid': 'init-CB002', 'code_barre': 'CB002', 'delta': 10, 'event_type': 'correction'}]})

        payload = {'stock_events': [{'event_uuid': 'vente-002', 'code_barre': 'CB002', 'delta': -2, 'event_type': 'vente'}]}
        self._push(payload)
        self._push(payload)  # deuxième envoi identique

        conn = self._get_db()
        row = conn.execute("SELECT stock_actuel FROM sync_produits WHERE code_barre = 'CB002'").fetchone()
        count = conn.execute("SELECT COUNT(*) as n FROM stock_events WHERE event_uuid = 'vente-002'").fetchone()
        conn.close()

        self.assertEqual(count['n'], 1)      # une seule entrée
        self.assertEqual(row['stock_actuel'], 8)  # 10 - 2, pas 10 - 4

    def test_push_produit_ne_pas_ecraser_stock(self):
        """Pousser des infos produit ne doit pas toucher stock_actuel."""
        self._push({'produits': [{'code_barre': 'CB003', 'nom': 'Riz', 'prix_vente': 1000, 'stock_alerte': 3}]})
        self._push({'stock_events': [{'event_uuid': 'init-CB003', 'code_barre': 'CB003', 'delta': 50, 'event_type': 'correction'}]})

        # Push d'info produit (nouveau prix) — sans event de stock
        self._push({'produits': [{'code_barre': 'CB003', 'nom': 'Riz Premium', 'prix_vente': 1200, 'stock_alerte': 3}]})

        conn = self._get_db()
        row = conn.execute("SELECT stock_actuel, nom, prix_vente FROM sync_produits WHERE code_barre = 'CB003'").fetchone()
        conn.close()

        self.assertEqual(row['stock_actuel'], 50)    # inchangé
        self.assertEqual(row['nom'], 'Riz Premium')  # mis à jour
        self.assertEqual(row['prix_vente'], 1200)    # mis à jour

    def test_push_stock_ne_descend_pas_sous_zero(self):
        """MAX(0,...) : stock négatif impossible."""
        self._push({'produits': [{'code_barre': 'CB004', 'nom': 'Sel', 'prix_vente': 100, 'stock_alerte': 1}]})
        self._push({'stock_events': [{'event_uuid': 'init-CB004', 'code_barre': 'CB004', 'delta': 2, 'event_type': 'correction'}]})
        self._push({'stock_events': [{'event_uuid': 'vente-004', 'code_barre': 'CB004', 'delta': -10, 'event_type': 'vente'}]})

        conn = self._get_db()
        row = conn.execute("SELECT stock_actuel FROM sync_produits WHERE code_barre = 'CB004'").fetchone()
        conn.close()
        self.assertEqual(row['stock_actuel'], 0)

    def test_push_vente_sans_doublon(self):
        payload = {'ventes': [{'numero_vente': 'V-UNIQUE-01', 'date_vente': '2026-05-09 10:00:00', 'total': 1500}]}
        self._push(payload)
        self._push(payload)  # doublon
        conn = self._get_db()
        count = conn.execute("SELECT COUNT(*) as n FROM sync_ventes WHERE numero_vente = 'V-UNIQUE-01'").fetchone()
        conn.close()
        self.assertEqual(count['n'], 1)


class TestServeurSyncPull(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        import tempfile
        fd, cls.sync_db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        import serveur_sync.app as srv
        srv.SYNC_DB_PATH = cls.sync_db_path
        srv.init_sync_db()
        srv.app.config['TESTING'] = True
        srv.valider_licence = lambda k: True

        cls.app = srv.app
        cls.headers_a = {'X-Licence-Key': 'LIC-PULL', 'X-Machine-Id': 'TERM-A'}
        cls.headers_b = {'X-Licence-Key': 'LIC-PULL', 'X-Machine-Id': 'TERM-B'}

        with srv.app.test_client() as c:
            c.post('/api/sync/push', json={
                'produits': [{'code_barre': 'PULL-CB', 'nom': 'Farine', 'prix_vente': 700, 'stock_alerte': 2}],
                'stock_events': [
                    {'event_uuid': 'pull-init', 'code_barre': 'PULL-CB', 'delta': 30, 'event_type': 'correction'},
                    {'event_uuid': 'pull-vente-1', 'code_barre': 'PULL-CB', 'delta': -5, 'event_type': 'vente'},
                ],
            }, headers=cls.headers_a, content_type='application/json')

    @classmethod
    def tearDownClass(cls):
        try:
            os.unlink(cls.sync_db_path)
        except (PermissionError, OSError):
            pass

    def test_pull_retourne_events_autres_terminaux(self):
        with self.app.test_client() as c:
            r = c.post('/api/sync/pull',
                       json={'depuis_event_id': 0},
                       headers=self.headers_b,
                       content_type='application/json')
        data = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertIn('stock_events', data)
        self.assertGreater(len(data['stock_events']), 0)

    def test_pull_exclut_propre_terminal(self):
        """Terminal A ne reçoit pas ses propres événements."""
        with self.app.test_client() as c:
            r = c.post('/api/sync/pull',
                       json={'depuis_event_id': 0},
                       headers=self.headers_a,
                       content_type='application/json')
        data = r.get_json()
        for e in data.get('stock_events', []):
            self.assertNotEqual(e['terminal_id'], 'TERM-A')

    def test_pull_depuis_event_id(self):
        """Avec depuis_event_id au max, aucun événement retourné."""
        with self.app.test_client() as c:
            r = c.post('/api/sync/pull',
                       json={'depuis_event_id': 9999999},
                       headers=self.headers_b,
                       content_type='application/json')
        data = r.get_json()
        self.assertEqual(data['stock_events'], [])

    def test_pull_last_event_id_avance(self):
        """last_event_id doit être >= depuis_event_id."""
        with self.app.test_client() as c:
            r = c.post('/api/sync/pull',
                       json={'depuis_event_id': 0},
                       headers=self.headers_b,
                       content_type='application/json')
        data = r.get_json()
        self.assertGreater(data['last_event_id'], 0)

    def test_bootstrap_retourne_snapshot(self):
        with self.app.test_client() as c:
            r = c.get('/api/sync/bootstrap', headers=self.headers_b)
        data = r.get_json()
        self.assertEqual(r.status_code, 200)
        self.assertIn('produits', data)
        self.assertIn('last_event_id', data)
        self.assertGreater(len(data['produits']), 0)
        produit = next((p for p in data['produits'] if p['code_barre'] == 'PULL-CB'), None)
        self.assertIsNotNone(produit)
        self.assertEqual(produit['stock_actuel'], 25)  # 30 - 5


# =============================================================================
# Tests client (sync_client.py, DB locale :memory:)
# =============================================================================

class TestSyncClientMigration(unittest.TestCase):

    def test_colonne_sync_done_existe(self):
        """migrer_sync() ajoute sync_done à historique_stock (idempotent)."""
        db = reset_db()
        db.migrer_sync()
        colonnes = [row[1] for row in db.conn.execute("PRAGMA table_info(historique_stock)").fetchall()]
        self.assertIn('sync_done', colonnes)


class TestSyncClientCollecte(unittest.TestCase):

    def setUp(self):
        self.db = reset_db()
        self.db.migrer_sync()  # Garantit sync_done présent quelle que soit l'init
        # Créer un produit avec historique de stock
        from modules.produits import Produit
        code = Produit.ajouter('Test', 'Cat', 100, 200, 15, 3)
        produit = Produit.obtenir_par_code_barre(code)
        self.produit_id = produit['id']
        self.code_barre = code

        # Insérer 2 entrées dans historique_stock (non synchronisées)
        self.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation) VALUES (?, ?, ?, ?)",
            (self.produit_id, 15, 12, 'vente_test')
        )
        self.db.execute_query(
            "INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation) VALUES (?, ?, ?, ?)",
            (self.produit_id, 12, 22, 'reappro_test')
        )

    def test_collecte_genere_events_depuis_historique(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')
        payload = client._collecter_payload()

        events = payload['stock_events']
        self.assertEqual(len(events), 2)

        deltas = [e['delta'] for e in events]
        self.assertIn(-3, deltas)   # 12 - 15
        self.assertIn(10, deltas)   # 22 - 12

    def test_collecte_event_uuid_unique_par_terminal(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')
        payload = client._collecter_payload()

        for e in payload['stock_events']:
            self.assertTrue(e['event_uuid'].startswith('MACHINE-X:'))

    def test_collecte_produits_sans_stock_actuel(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')
        payload = client._collecter_payload()

        for p in payload['produits']:
            self.assertNotIn('stock_actuel', p)

    def test_marquer_sync_done(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')
        payload = client._collecter_payload()
        client._marquer_sync_done(payload['stock_events'])

        rows = self.db.fetch_all("SELECT sync_done FROM historique_stock")
        for r in rows:
            self.assertEqual(r['sync_done'], 1)

    def test_seulement_sync_done_0_collecte(self):
        """Après sync_done=1, un nouveau push ne re-collecte pas les mêmes events."""
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')

        payload = client._collecter_payload()
        client._marquer_sync_done(payload['stock_events'])

        payload2 = client._collecter_payload()
        self.assertEqual(payload2['stock_events'], [])


class TestSyncClientAppliquerPull(unittest.TestCase):

    def setUp(self):
        self.db = reset_db()
        from modules.produits import Produit
        code = Produit.ajouter('Produit Pull', 'Cat', 100, 300, 20, 3)
        self.code_barre = code

    def test_appliquer_delta_negatif(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')

        client._appliquer_pull({
            'stock_events': [{'code_barre': self.code_barre, 'delta': -4, 'event_type': 'vente'}],
            'last_event_id': 42,
            'produits': [], 'ventes': [], 'utilisateurs': [],
        })

        row = self.db.fetch_one("SELECT stock_actuel FROM produits WHERE code_barre = ?", (self.code_barre,))
        self.assertEqual(row['stock_actuel'], 16)  # 20 - 4

    def test_appliquer_delta_positif(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')

        client._appliquer_pull({
            'stock_events': [{'code_barre': self.code_barre, 'delta': 10, 'event_type': 'reappro'}],
            'last_event_id': 43,
            'produits': [], 'ventes': [], 'utilisateurs': [],
        })

        row = self.db.fetch_one("SELECT stock_actuel FROM produits WHERE code_barre = ?", (self.code_barre,))
        self.assertEqual(row['stock_actuel'], 30)  # 20 + 10

    def test_appliquer_delta_ne_descend_pas_sous_zero(self):
        """MAX(0,...) protège contre les stocks négatifs malgré le trigger."""
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')

        client._appliquer_pull({
            'stock_events': [{'code_barre': self.code_barre, 'delta': -999, 'event_type': 'vente'}],
            'last_event_id': 44,
            'produits': [], 'ventes': [], 'utilisateurs': [],
        })

        row = self.db.fetch_one("SELECT stock_actuel FROM produits WHERE code_barre = ?", (self.code_barre,))
        self.assertEqual(row['stock_actuel'], 0)

    def test_appliquer_pull_met_a_jour_last_event_id(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')

        client._appliquer_pull({
            'stock_events': [], 'last_event_id': 77,
            'produits': [], 'ventes': [], 'utilisateurs': [],
        })

        val = self.db.get_parametre('sync_last_event_id')
        self.assertEqual(val, '77')

    def test_appliquer_pull_infos_produit_sans_toucher_stock(self):
        from modules.sync_client import SyncClient
        client = SyncClient()
        client.configurer('http://fake', 'LIC', 'MACHINE-X')

        client._appliquer_pull({
            'stock_events': [],
            'last_event_id': 0,
            'produits': [{'code_barre': self.code_barre, 'nom': 'Nouveau Nom', 'prix_vente': 999}],
            'ventes': [], 'utilisateurs': [],
        })

        row = self.db.fetch_one(
            "SELECT nom, prix_vente, stock_actuel FROM produits WHERE code_barre = ?",
            (self.code_barre,)
        )
        self.assertEqual(row['nom'], 'Nouveau Nom')
        self.assertEqual(row['prix_vente'], 999)
        self.assertEqual(row['stock_actuel'], 20)  # inchangé


class TestEventTypeMapping(unittest.TestCase):

    def test_vente(self):
        from modules.sync_client import _operation_to_event_type
        self.assertEqual(_operation_to_event_type('vente_caisse'), 'vente')

    def test_reappro(self):
        from modules.sync_client import _operation_to_event_type
        self.assertEqual(_operation_to_event_type('reappro fournisseur'), 'reappro')

    def test_correction(self):
        from modules.sync_client import _operation_to_event_type
        self.assertEqual(_operation_to_event_type('correction inventaire'), 'correction')

    def test_perte(self):
        from modules.sync_client import _operation_to_event_type
        self.assertEqual(_operation_to_event_type('perte casse'), 'perte')

    def test_vide(self):
        from modules.sync_client import _operation_to_event_type
        self.assertEqual(_operation_to_event_type(''), 'vente')

    def test_inconnu(self):
        from modules.sync_client import _operation_to_event_type
        self.assertEqual(_operation_to_event_type('xyz inconnu'), 'autre')


if __name__ == '__main__':
    unittest.main(verbosity=2)
