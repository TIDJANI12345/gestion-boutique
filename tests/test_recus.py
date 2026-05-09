"""Tests pour modules/recus.py — génération de reçus PDF."""
import os
import tempfile
import unittest
from unittest.mock import patch
from tests.conftest import reset_db
import database
from modules.recus import generer_recu_pdf, generer_recu_encaissement


_vente_counter = 0

def _creer_vente_complete(numero='V001', total=3000):
    """Crée une vente avec un produit et un détail, retourne (vente_id, produit_id)."""
    global _vente_counter
    _vente_counter += 1
    code = f'SUC{_vente_counter:03d}'
    pid = database.db.execute_query(
        "INSERT INTO produits (nom, code_barre, prix_vente, stock_actuel) VALUES (?, ?, ?, ?)",
        ('Sucre 1kg', code, 1500, 10)
    )
    vid = database.db.execute_query(
        "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, datetime('now'), ?, 'terminee')",
        (numero, total)
    )
    database.db.execute_query(
        "INSERT INTO details_ventes (vente_id, produit_id, quantite, prix_unitaire, sous_total) VALUES (?, ?, ?, ?, ?)",
        (vid, pid, 2, 1500, 3000)
    )
    return vid, pid


class TestGenererRecuPdf(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.tmp_dir)
        except Exception:
            pass

    def test_vente_inexistante_retourne_none(self):
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            result = generer_recu_pdf(9999)
        self.assertIsNone(result)

    def test_genere_fichier_pdf(self):
        vid, _ = _creer_vente_complete()
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            filepath = generer_recu_pdf(vid)
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))

    def test_fichier_est_pdf_valide(self):
        vid, _ = _creer_vente_complete()
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            filepath = generer_recu_pdf(vid)
        with open(filepath, 'rb') as f:
            header = f.read(4)
        self.assertEqual(header, b'%PDF')

    def test_nom_fichier_contient_numero_vente(self):
        vid, _ = _creer_vente_complete('V-TEST-42', 2000)
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            filepath = generer_recu_pdf(vid)
        self.assertIn('V-TEST-42', os.path.basename(filepath))

    def test_genere_plusieurs_ventes(self):
        vid1, _ = _creer_vente_complete('V001', 1000)
        vid2, _ = _creer_vente_complete('V002', 2000)
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            f1 = generer_recu_pdf(vid1)
            f2 = generer_recu_pdf(vid2)
        self.assertIsNotNone(f1)
        self.assertIsNotNone(f2)
        self.assertNotEqual(f1, f2)

    def test_avec_infos_boutique(self):
        database.db.set_parametre('boutique_nom', 'Ma Boutique Test')
        database.db.set_parametre('boutique_telephone', '00229 97000000')
        vid, _ = _creer_vente_complete()
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            filepath = generer_recu_pdf(vid)
        self.assertIsNotNone(filepath)
        # PDF généré sans erreur avec les infos boutique
        self.assertTrue(os.path.getsize(filepath) > 1000)

    def test_vente_sans_details_retourne_none(self):
        vid = database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, statut) VALUES (?, datetime('now'), ?, 'terminee')",
            ('V_VIDE', 0)
        )
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            result = generer_recu_pdf(vid)
        self.assertIsNone(result)


class TestGenererRecuEncaissement(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        try:
            shutil.rmtree(self.tmp_dir)
        except Exception:
            pass

    def _creer_ardoise_client(self):
        cid = database.db.execute_query(
            "INSERT INTO clients (nom, telephone) VALUES (?, ?)", ('Ali Diallo', '0601')
        )
        aid = database.db.execute_query(
            "INSERT INTO ardoise (client_id, montant_initial, montant_restant, statut) VALUES (?, ?, ?, 'en_cours')",
            (cid, 10000, 6000)
        )
        return aid, cid

    def test_ardoise_inexistante_retourne_none(self):
        encaissement = {'montant': 2000, 'date': '2026-05-09', 'reference': 'ENC001'}
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            result = generer_recu_encaissement(9999, encaissement)
        self.assertIsNone(result)

    def test_genere_pdf_encaissement(self):
        aid, _ = self._creer_ardoise_client()
        encaissement = {
            'montant': 4000,
            'date': '2026-05-09 10:00:00',
            'reference': 'ENC001',
            'mode': 'especes',
        }
        with patch('modules.recus.RECUS_DIR', self.tmp_dir):
            filepath = generer_recu_encaissement(aid, encaissement)
        self.assertIsNotNone(filepath)
        self.assertTrue(os.path.exists(filepath))
        with open(filepath, 'rb') as f:
            self.assertEqual(f.read(4), b'%PDF')


if __name__ == '__main__':
    unittest.main()
