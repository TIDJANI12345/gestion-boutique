"""Tests pour modules/sessions.py."""
import unittest
from tests.conftest import reset_db
import database
from modules.sessions import (
    session_actuelle, ouvrir_session, cloturer_session,
    rapport_x, historique_clotures,
)


def _creer_caissier(email='caisse@test.com'):
    return database.db.execute_query(
        "INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role, actif) VALUES (?, ?, ?, ?, ?, 1)",
        ('Test', 'Caissier', email, 'hash', 'caissier')
    )


class TestSessionActuelle(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_aucune_session(self):
        self.assertIsNone(session_actuelle())

    def test_apres_ouverture(self):
        uid = _creer_caissier()
        ouvrir_session(uid, 5000)
        self.assertIsNotNone(session_actuelle())

    def test_apres_cloture_aucune(self):
        uid = _creer_caissier()
        ouvrir_session(uid, 5000)
        cloturer_session(5000)
        self.assertIsNone(session_actuelle())


class TestOuvrirSession(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.uid = _creer_caissier()

    def test_ouverture_valide(self):
        ok, msg, sid = ouvrir_session(self.uid, 5000)
        self.assertTrue(ok)
        self.assertIsNotNone(sid)
        self.assertIsInstance(sid, int)

    def test_double_ouverture_refusee(self):
        ouvrir_session(self.uid, 5000)
        ok, msg, sid = ouvrir_session(self.uid, 3000)
        self.assertFalse(ok)
        self.assertIsNone(sid)
        self.assertIn("déjà", msg.lower())

    def test_caisse_id_specifique(self):
        ok, msg, sid = ouvrir_session(self.uid, 1000, id_caisse='C2')
        self.assertTrue(ok)
        s = database.db.fetch_one("SELECT id_caisse FROM sessions_caisse WHERE id = ?", (sid,))
        self.assertEqual(s['id_caisse'], 'C2')

    def test_fond_enregistre(self):
        ok, msg, sid = ouvrir_session(self.uid, 7500)
        s = database.db.fetch_one("SELECT fond_ouverture, statut FROM sessions_caisse WHERE id = ?", (sid,))
        self.assertEqual(s['fond_ouverture'], 7500)
        self.assertEqual(s['statut'], 'ouverte')

    def test_apres_cloture_peut_ouvrir_nouveau(self):
        ouvrir_session(self.uid, 5000)
        cloturer_session(5000)
        ok, msg, sid = ouvrir_session(self.uid, 2000)
        self.assertTrue(ok)
        self.assertIsNotNone(sid)


class TestRapportX(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.uid = _creer_caissier()

    def test_sans_session_ouverte(self):
        self.assertIsNone(rapport_x())

    def test_avec_session_ouverte(self):
        ouvrir_session(self.uid, 5000)
        r = rapport_x()
        self.assertIsNotNone(r)
        self.assertIn('session', r)
        self.assertIn('nb_ventes', r)
        self.assertEqual(r['nb_ventes'], 0)
        self.assertEqual(r['total_general'], 0)

    def test_rapport_x_par_id(self):
        ok, msg, sid = ouvrir_session(self.uid, 5000)
        r = rapport_x(sid)
        self.assertIsNotNone(r)
        self.assertEqual(r['session']['id'], sid)

    def test_rapport_x_id_inexistant(self):
        self.assertIsNone(rapport_x(9999))

    def test_rapport_x_avec_ventes(self):
        ok, msg, sid = ouvrir_session(self.uid, 10000)
        # Créer une vente liée à cette session
        database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, id_session, statut) VALUES (?, datetime('now'), ?, ?, 'terminee')",
            ('VX01', 3000, sid)
        )
        r = rapport_x()
        self.assertEqual(r['nb_ventes'], 1)
        self.assertEqual(r['total_general'], 3000)


class TestCloturerSession(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.uid = _creer_caissier()

    def test_sans_session_ouverte(self):
        ok, msg, rapport = cloturer_session(5000)
        self.assertFalse(ok)
        self.assertIsNone(rapport)

    def test_cloture_valide(self):
        ouvrir_session(self.uid, 5000)
        ok, msg, rapport = cloturer_session(5000)
        self.assertTrue(ok)
        self.assertIsNotNone(rapport)

    def test_hash_cloture_format(self):
        ouvrir_session(self.uid, 0)
        ok, msg, rapport = cloturer_session(0)
        h = rapport['hash_cloture']
        self.assertEqual(len(h), 16)
        self.assertEqual(h, h.upper())

    def test_statut_devient_cloturee(self):
        ok, msg, sid = ouvrir_session(self.uid, 3000)
        cloturer_session(3000)
        s = database.db.fetch_one("SELECT statut FROM sessions_caisse WHERE id = ?", (sid,))
        self.assertEqual(s['statut'], 'cloturee')

    def test_double_cloture_refusee(self):
        ouvrir_session(self.uid, 5000)
        cloturer_session(5000)
        ok, msg, rapport = cloturer_session(5000)
        self.assertFalse(ok)
        self.assertIsNone(rapport)

    def test_fond_calcule_sans_ventes(self):
        # fond_calcule = total_especes (0) + fond_ouverture
        ouvrir_session(self.uid, 10000)
        ok, msg, rapport = cloturer_session(12000)
        self.assertTrue(ok)
        self.assertEqual(rapport['fond_ouverture'], 10000)
        self.assertEqual(rapport['fond_cloture_declare'], 12000)
        self.assertEqual(rapport['fond_cloture_calcule'], 10000)  # 0 especes + 10000 fond
        self.assertEqual(rapport['ecart'], 2000)

    def test_rapport_contient_champs_requis(self):
        ouvrir_session(self.uid, 5000)
        ok, msg, rapport = cloturer_session(5000)
        for k in ('session_id', 'hash_cloture', 'fond_ouverture',
                   'fond_cloture_declare', 'ecart', 'nb_ventes', 'total_general'):
            self.assertIn(k, rapport)

    def test_cloture_avec_ventes_especes(self):
        ok, msg, sid = ouvrir_session(self.uid, 5000)
        vid = database.db.execute_query(
            "INSERT INTO ventes (numero_vente, date_vente, total, id_session, statut) VALUES (?, datetime('now'), ?, ?, 'terminee')",
            ('VC01', 3000, sid)
        )
        database.db.execute_query(
            "INSERT INTO paiements (vente_id, mode, montant) VALUES (?, 'especes', ?)",
            (vid, 3000)
        )
        ok, msg, rapport = cloturer_session(8000)
        self.assertTrue(ok)
        self.assertEqual(rapport['total_especes'], 3000)
        # fond_calcule = 3000 (especes) + 5000 (fond_ouverture) = 8000
        self.assertEqual(rapport['fond_cloture_calcule'], 8000)
        self.assertEqual(rapport['ecart'], 0)


class TestHistoriqueClotures(unittest.TestCase):
    def setUp(self):
        reset_db()
        self.uid = _creer_caissier()

    def test_historique_vide(self):
        self.assertEqual(historique_clotures(), [])

    def test_historique_apres_cloture(self):
        ouvrir_session(self.uid, 5000)
        cloturer_session(5000)
        hist = historique_clotures()
        self.assertEqual(len(hist), 1)
        self.assertIn('hash_cloture', hist[0])

    def test_sessions_ouvertes_exclues(self):
        ouvrir_session(self.uid, 5000)
        # Session ouverte ne doit pas apparaître
        self.assertEqual(historique_clotures(), [])

    def test_limit_respecte(self):
        for i in range(4):
            ouvrir_session(self.uid, 1000)
            cloturer_session(1000)
        hist = historique_clotures(limit=2)
        self.assertEqual(len(hist), 2)

    def test_contient_nom_caissier(self):
        ouvrir_session(self.uid, 0)
        cloturer_session(0)
        hist = historique_clotures()
        self.assertIn('caissier_nom', hist[0])


if __name__ == '__main__':
    unittest.main()
