"""Tests pour modules/licence.py."""
import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from tests.conftest import reset_db
import database
from modules.licence import GestionLicence


class TestGetMachineId(unittest.TestCase):
    def test_retourne_string(self):
        gl = GestionLicence()
        mid = gl.get_machine_id()
        self.assertIsInstance(mid, str)

    def test_longueur_sha256(self):
        gl = GestionLicence()
        mid = gl.get_machine_id()
        self.assertEqual(len(mid), 64)

    def test_deterministe(self):
        gl = GestionLicence()
        self.assertEqual(gl.get_machine_id(), gl.get_machine_id())

    def test_deux_instances_meme_machine(self):
        self.assertEqual(GestionLicence().get_machine_id(), GestionLicence().get_machine_id())


class TestObtenirInfoLocale(unittest.TestCase):
    def setUp(self):
        self.gl = GestionLicence()
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.key')
        self.tmp.close()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def test_sans_fichier_retourne_none(self):
        with patch('modules.licence.FICHIER_LICENCE', '/chemin/inexistant/licence.key'):
            self.assertIsNone(self.gl.obtenir_info_locale())

    def test_avec_fichier_valide(self):
        data = {
            'cle': 'TEST-CLE-001',
            'machine_id': self.gl.get_machine_id(),
            'expiration': '2099-12-31',
            'type': 'pro',
        }
        encrypted = self.gl.cipher.encrypt(json.dumps(data).encode())
        with open(self.tmp.name, 'wb') as f:
            f.write(encrypted)

        with patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            info = self.gl.obtenir_info_locale()

        self.assertIsNotNone(info)
        self.assertEqual(info['cle_licence'], 'TEST-CLE-001')
        self.assertEqual(info['type_licence'], 'pro')

    def test_fichier_corrompu_retourne_none(self):
        with open(self.tmp.name, 'wb') as f:
            f.write(b'DONNEES_CORROMPUES_PAS_FERNET')

        with patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            self.assertIsNone(self.gl.obtenir_info_locale())


class TestVerifierLocale(unittest.TestCase):
    def setUp(self):
        self.gl = GestionLicence()
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.key')
        self.tmp.close()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def _ecrire_licence(self, machine_id=None, expiration='2099-12-31'):
        data = {
            'cle': 'TEST-001',
            'machine_id': machine_id or self.gl.get_machine_id(),
            'expiration': expiration,
            'type': 'standard',
        }
        encrypted = self.gl.cipher.encrypt(json.dumps(data).encode())
        with open(self.tmp.name, 'wb') as f:
            f.write(encrypted)

    def test_sans_fichier(self):
        with patch('modules.licence.FICHIER_LICENCE', '/inexistant.key'):
            ok, msg = self.gl.verifier_locale()
        self.assertFalse(ok)

    def test_licence_valide(self):
        self._ecrire_licence()
        with patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            ok, msg = self.gl.verifier_locale()
        self.assertTrue(ok)
        self.assertIn('valide', msg.lower())

    def test_licence_expiree(self):
        self._ecrire_licence(expiration='2000-01-01')
        with patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            ok, msg = self.gl.verifier_locale()
        self.assertFalse(ok)
        self.assertIn('expir', msg.lower())

    def test_licence_autre_machine(self):
        self._ecrire_licence(machine_id='autre_machine_id_' + 'x' * 50)
        with patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            ok, msg = self.gl.verifier_locale()
        self.assertFalse(ok)
        self.assertIn('autre ordinateur', msg.lower())


class TestActiverDemo(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.gl = GestionLicence()

    def test_activer_demo(self):
        ok = self.gl.activer_demo()
        self.assertTrue(ok)
        self.assertEqual(database.db.get_parametre('licence_plan_enc'), '__demo__')
        self.assertEqual(database.db.get_parametre('licence_features_enc'), '__none__')

    def test_activer_demo_enregistre_debut(self):
        self.gl.activer_demo()
        debut = database.db.get_parametre('licence_demo_debut', '')
        self.assertNotEqual(debut, '')

    def test_activer_demo_preserve_debut_existant(self):
        database.db.set_parametre('licence_demo_debut', '12345.0')
        self.gl.activer_demo()
        debut = database.db.get_parametre('licence_demo_debut', '')
        self.assertEqual(debut, '12345.0')


class TestActiverEnLigne(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.gl = GestionLicence()
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.key')
        self.tmp.close()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except Exception:
            pass

    def test_activation_succes(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'succes': True,
            'expiration': '2099-12-31',
            'type': 'pro',
            'plan': 'pro',
            'features_extra': '',
        }
        with patch('requests.post', return_value=mock_response), \
             patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            ok, msg = self.gl.activer_en_ligne('TEST-CLE-001')
        self.assertTrue(ok)
        self.assertIn('reussie', msg.lower())

    def test_activation_cle_invalide(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'succes': False,
            'message': 'Clé invalide',
        }
        with patch('requests.post', return_value=mock_response), \
             patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            ok, msg = self.gl.activer_en_ligne('MAUVAISE-CLE')
        self.assertFalse(ok)
        self.assertIn('invalide', msg.lower())

    def test_activation_sans_connexion(self):
        import requests as req_mod
        with patch('requests.post', side_effect=req_mod.exceptions.ConnectionError()):
            ok, msg = self.gl.activer_en_ligne('TEST-CLE')
        self.assertFalse(ok)
        self.assertIn('serveur', msg.lower())

    def test_activation_erreur_serveur(self):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.side_effect = Exception('no json')
        with patch('requests.post', return_value=mock_response), \
             patch('modules.licence.FICHIER_LICENCE', self.tmp.name):
            ok, msg = self.gl.activer_en_ligne('TEST-CLE')
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
