"""Tests pour serveur_local/api_locale.py."""
import json
import unittest
from tests.conftest import reset_db
import database
from serveur_local.api_locale import app, _terminaux, _terminaux_lock, get_token


class ApiTestBase(unittest.TestCase):
    def setUp(self):
        reset_db()
        with _terminaux_lock:
            _terminaux.clear()
        self.client = app.test_client()
        self.token = get_token()

    def hdr(self, machine_id=None, json_ct=True):
        h = {'X-Local-Token': self.token}
        if json_ct:
            h['Content-Type'] = 'application/json'
        if machine_id:
            h['X-Machine-Id'] = machine_id
        return h


class TestPing(ApiTestBase):
    def test_ping_sans_auth(self):
        r = self.client.get('/ping')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['status'], 'ok')

    def test_ping_timestamp_present(self):
        r = self.client.get('/ping')
        self.assertIn('timestamp', r.get_json())


class TestAuth(ApiTestBase):
    def test_sans_token_401(self):
        r = self.client.get('/produits')
        self.assertEqual(r.status_code, 401)

    def test_mauvais_token_401(self):
        r = self.client.get('/produits', headers={'X-Local-Token': 'mauvais'})
        self.assertEqual(r.status_code, 401)

    def test_bon_token_passe(self):
        r = self.client.get('/produits', headers=self.hdr())
        self.assertEqual(r.status_code, 200)


class TestTerminaux(ApiTestBase):
    def test_connect_premier_terminal(self):
        r = self.client.post('/connect',
            data=json.dumps({'machine_id': 'T1', 'nom': 'Caisse 1'}),
            headers=self.hdr('T1'))
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertEqual(d['status'], 'ok')
        self.assertEqual(d['terminaux_connectes'], 1)

    def test_connect_deuxieme_terminal_quota_depasse(self):
        # Plan démo : max 1 terminal
        self.client.post('/connect',
            data=json.dumps({'machine_id': 'T1', 'nom': 'Caisse 1'}),
            headers=self.hdr('T1'))
        r = self.client.post('/connect',
            data=json.dumps({'machine_id': 'T2', 'nom': 'Caisse 2'}),
            headers=self.hdr('T2'))
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.get_json()['code'], 'QUOTA_DEPASSE')

    def test_reconnect_terminal_connu_autorise(self):
        self.client.post('/connect',
            data=json.dumps({'machine_id': 'T1', 'nom': 'Caisse 1'}),
            headers=self.hdr('T1'))
        r = self.client.post('/connect',
            data=json.dumps({'machine_id': 'T1', 'nom': 'Caisse 1'}),
            headers=self.hdr('T1'))
        self.assertEqual(r.status_code, 200)

    def test_connect_sans_machine_id(self):
        r = self.client.post('/connect',
            data=json.dumps({'nom': 'Caisse ?'}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 400)

    def test_liste_terminaux_vide(self):
        r = self.client.get('/terminaux', headers=self.hdr())
        d = r.get_json()
        self.assertEqual(d['nb'], 0)

    def test_liste_terminaux_apres_connect(self):
        self.client.post('/connect',
            data=json.dumps({'machine_id': 'T1', 'nom': 'Caisse 1'}),
            headers=self.hdr('T1'))
        r = self.client.get('/terminaux', headers=self.hdr())
        self.assertEqual(r.get_json()['nb'], 1)

    def test_deconnecter_terminal(self):
        self.client.post('/connect',
            data=json.dumps({'machine_id': 'T1', 'nom': 'Caisse 1'}),
            headers=self.hdr('T1'))
        r = self.client.post('/deconnecter',
            data=json.dumps({'machine_id': 'T1'}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        with _terminaux_lock:
            self.assertNotIn('T1', _terminaux)

    def test_deconnecter_terminal_inconnu_ok(self):
        r = self.client.post('/deconnecter',
            data=json.dumps({'machine_id': 'INCONNU'}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 200)


class TestProduits(ApiTestBase):
    def test_liste_vide(self):
        r = self.client.get('/produits', headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [])

    def test_creer_produit(self):
        payload = {'nom': 'Sucre', 'prix_vente': 500, 'code_barre': 'SUC001'}
        r = self.client.post('/produits', data=json.dumps(payload), headers=self.hdr())
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()['status'], 'ok')

    def test_creer_champs_manquants(self):
        r = self.client.post('/produits',
            data=json.dumps({'nom': 'Sucre'}), headers=self.hdr())
        self.assertEqual(r.status_code, 400)

    def test_get_produit(self):
        self.client.post('/produits',
            data=json.dumps({'nom': 'Sel', 'prix_vente': 200, 'code_barre': 'SEL001'}),
            headers=self.hdr())
        r = self.client.get('/produits/SEL001', headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()['nom'], 'Sel')

    def test_get_produit_inexistant(self):
        r = self.client.get('/produits/NOPE', headers=self.hdr())
        self.assertEqual(r.status_code, 404)

    def test_modifier_produit(self):
        self.client.post('/produits',
            data=json.dumps({'nom': 'Huile', 'prix_vente': 1000, 'code_barre': 'HUI001'}),
            headers=self.hdr())
        r = self.client.put('/produits/HUI001',
            data=json.dumps({'nom': 'Huile Premium', 'prix_vente': 1200}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 200)

    def test_liste_apres_creation(self):
        self.client.post('/produits',
            data=json.dumps({'nom': 'Lait', 'prix_vente': 750, 'code_barre': 'LAI001'}),
            headers=self.hdr())
        produits = self.client.get('/produits', headers=self.hdr()).get_json()
        self.assertEqual(len(produits), 1)
        self.assertEqual(produits[0]['nom'], 'Lait')

    def test_stock_alerte_defaut(self):
        self.client.post('/produits',
            data=json.dumps({'nom': 'Test', 'prix_vente': 100, 'code_barre': 'TST001'}),
            headers=self.hdr())
        p = self.client.get('/produits/TST001', headers=self.hdr()).get_json()
        self.assertEqual(p['stock_alerte'], 5)


class TestVentes(ApiTestBase):
    def setUp(self):
        super().setUp()
        database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
            ('TestProd', 'TP001', 1000, 50)
        )
        self.produit_id = database.db.fetch_one(
            "SELECT id FROM produits WHERE code_barre = 'TP001'"
        )['id']

    def test_liste_vide(self):
        r = self.client.get('/ventes', headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [])

    def test_enregistrer_vente(self):
        payload = {
            'numero_vente': 'V001',
            'total': 1000,
            'details': [{'produit_id': self.produit_id, 'quantite': 1,
                         'prix_unitaire': 1000, 'sous_total': 1000}],
        }
        r = self.client.post('/ventes', data=json.dumps(payload), headers=self.hdr())
        self.assertEqual(r.status_code, 201)
        self.assertIn('vente_id', r.get_json())

    def test_vente_champs_manquants(self):
        r = self.client.post('/ventes',
            data=json.dumps({'numero_vente': 'V002'}), headers=self.hdr())
        self.assertEqual(r.status_code, 400)

    def test_liste_apres_vente(self):
        payload = {
            'numero_vente': 'V003',
            'total': 500,
            'details': [{'produit_id': self.produit_id, 'quantite': 1,
                         'prix_unitaire': 500, 'sous_total': 500}],
        }
        self.client.post('/ventes', data=json.dumps(payload), headers=self.hdr())
        ventes = self.client.get('/ventes', headers=self.hdr()).get_json()
        self.assertEqual(len(ventes), 1)

    def test_stock_mis_a_jour(self):
        payload = {
            'numero_vente': 'V004',
            'total': 3000,
            'details': [{'produit_id': self.produit_id, 'quantite': 3,
                         'prix_unitaire': 1000, 'sous_total': 3000}],
        }
        self.client.post('/ventes', data=json.dumps(payload), headers=self.hdr())
        p = database.db.fetch_one(
            "SELECT stock_actuel FROM produits WHERE id = ?", (self.produit_id,)
        )
        self.assertEqual(p['stock_actuel'], 47)


class TestStatsDashboard(ApiTestBase):
    def test_dashboard_vide(self):
        r = self.client.get('/stats/dashboard', headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        for k in ('ventes_jour', 'stock_alerte', 'total_produits'):
            self.assertIn(k, d)
        self.assertEqual(d['ventes_jour']['nb'], 0)

    def test_dashboard_compte_produits(self):
        database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente) VALUES (?, ?, ?)",
            ('P1', 'CB1', 100)
        )
        d = self.client.get('/stats/dashboard', headers=self.hdr()).get_json()
        self.assertEqual(d['total_produits'], 1)


class TestStockAlertes(ApiTestBase):
    def test_alertes_vide(self):
        r = self.client.get('/stock/alertes', headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [])

    def test_alerte_detectee(self):
        database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel, stock_alerte) VALUES (?, ?, ?, ?, ?)",
            ('ProdAlerte', 'PA001', 500, 2, 5)
        )
        alertes = self.client.get('/stock/alertes', headers=self.hdr()).get_json()
        self.assertEqual(len(alertes), 1)
        self.assertEqual(alertes[0]['code_barre'], 'PA001')

    def test_stock_suffisant_non_signale(self):
        database.db.execute_query(
            "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel, stock_alerte) VALUES (?, ?, ?, ?, ?)",
            ('ProdOK', 'PO001', 500, 20, 5)
        )
        alertes = self.client.get('/stock/alertes', headers=self.hdr()).get_json()
        self.assertEqual(len(alertes), 0)


class TestUtilisateurs(ApiTestBase):
    def test_liste_vide(self):
        r = self.client.get('/utilisateurs', headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), [])

    def test_liste_avec_utilisateur(self):
        database.db.execute_query(
            "INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role, actif) VALUES (?, ?, ?, ?, ?, 1)",
            ('Jean', 'Dupont', 'jean@test.com', 'hash', 'caissier')
        )
        r = self.client.get('/utilisateurs', headers=self.hdr())
        users = r.get_json()
        self.assertEqual(len(users), 1)
        self.assertNotIn('mot_de_passe', users[0])


class TestLogin(ApiTestBase):
    def setUp(self):
        super().setUp()
        import bcrypt
        hashed = bcrypt.hashpw(b'secret123', bcrypt.gensalt()).decode()
        database.db.execute_query(
            "INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role, actif) VALUES (?, ?, ?, ?, ?, 1)",
            ('Jean', 'Dupont', 'jean@test.com', hashed, 'caissier')
        )

    def test_login_succes(self):
        r = self.client.post('/login',
            data=json.dumps({'email': 'jean@test.com', 'mot_de_passe': 'secret123'}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 200)
        d = r.get_json()
        self.assertTrue(d['succes'])
        self.assertNotIn('mot_de_passe', d['utilisateur'])

    def test_login_mauvais_mot_de_passe(self):
        r = self.client.post('/login',
            data=json.dumps({'email': 'jean@test.com', 'mot_de_passe': 'mauvais'}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 401)
        self.assertFalse(r.get_json()['succes'])

    def test_login_champs_manquants(self):
        r = self.client.post('/login',
            data=json.dumps({'email': 'jean@test.com'}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 400)

    def test_login_email_inexistant(self):
        r = self.client.post('/login',
            data=json.dumps({'email': 'nope@test.com', 'mot_de_passe': 'secret123'}),
            headers=self.hdr())
        self.assertEqual(r.status_code, 401)


if __name__ == '__main__':
    unittest.main()
