"""Tests pour modules/features.py."""
import time
import unittest
from tests.conftest import reset_db
import database
from modules import features
from modules.features import (
    plan_actuel, peut, limite_caissiers, est_demo,
    statut_expiration, ventes_autorisees,
    demo_peut_vendre, demo_incrementer_ventes, demo_infos,
    PLANS, LIMITES,
)


class TestPlanActuel(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_plan_demo_par_defaut(self):
        # Aucun paramètre → demo
        self.assertEqual(plan_actuel(), 'demo')

    def test_plan_demo_explicite(self):
        database.db.set_parametre('licence_plan_enc', '__demo__')
        self.assertEqual(plan_actuel(), 'demo')

    def test_plan_reseau_standard(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_standard__')
        self.assertEqual(plan_actuel(), 'standard')

    def test_plan_reseau_pro(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        self.assertEqual(plan_actuel(), 'pro')

    def test_plan_reseau_inconnu_fallback_standard(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_inconnu__')
        self.assertEqual(plan_actuel(), 'standard')

    def test_plan_enc_invalide_fallback_standard(self):
        # Chiffrement invalide → fallback standard
        database.db.set_parametre('licence_plan_enc', 'DONNEES_CORROMPUES')
        self.assertIn(plan_actuel(), ('standard', 'demo'))


class TestPeut(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_demo_features_de_base(self):
        database.db.set_parametre('licence_plan_enc', '__demo__')
        self.assertTrue(peut('ventes'))
        self.assertTrue(peut('stock'))

    def test_demo_sans_reseau_local(self):
        database.db.set_parametre('licence_plan_enc', '__demo__')
        self.assertFalse(peut('reseau_local'))

    def test_standard_sans_multi_caissiers(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_standard__')
        self.assertFalse(peut('multi_caissiers'))

    def test_pro_avec_reseau_local(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        self.assertTrue(peut('reseau_local'))
        self.assertTrue(peut('multi_caissiers'))
        self.assertTrue(peut('session_caisse'))

    def test_feature_inexistante(self):
        self.assertFalse(peut('feature_qui_nexiste_pas'))

    def test_tous_plans_ont_ventes(self):
        for plan in PLANS:
            self.assertIn('ventes', PLANS[plan])


class TestLimiteCaissiers(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_demo_1_caissier(self):
        database.db.set_parametre('licence_plan_enc', '__demo__')
        self.assertEqual(limite_caissiers(), 1)

    def test_standard_1_caissier(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_standard__')
        self.assertEqual(limite_caissiers(), 1)

    def test_pro_caissiers_illimites(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        self.assertGreater(limite_caissiers(), 1)


class TestEstDemo(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_est_demo_par_defaut(self):
        self.assertTrue(est_demo())

    def test_pas_demo_en_pro(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        self.assertFalse(est_demo())


class TestStatutExpiration(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_demo_retourne_demo(self):
        self.assertEqual(statut_expiration(), 'demo')

    def test_pas_de_date_expiration_ok(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_expire', '')
        self.assertEqual(statut_expiration(), 'ok')

    def test_licence_future_ok(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_expire', '2099-12-31')
        self.assertEqual(statut_expiration(), 'ok')

    def test_licence_expiree_8j_expire(self):
        from datetime import date, timedelta
        exp = (date.today() - timedelta(days=10)).isoformat()
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_expire', exp)
        self.assertEqual(statut_expiration(), 'expire')

    def test_licence_expiree_grace(self):
        from datetime import date, timedelta
        exp = (date.today() - timedelta(days=3)).isoformat()
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_expire', exp)
        self.assertEqual(statut_expiration(), 'grace')


class TestVentesAutorisees(unittest.TestCase):
    def setUp(self):
        reset_db()

    def test_demo_autorisees(self):
        self.assertTrue(ventes_autorisees())

    def test_ok_autorisees(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_expire', '2099-12-31')
        self.assertTrue(ventes_autorisees())

    def test_expiree_bloquees(self):
        from datetime import date, timedelta
        exp = (date.today() - timedelta(days=10)).isoformat()
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_expire', exp)
        self.assertFalse(ventes_autorisees())

    def test_grace_autorisees(self):
        from datetime import date, timedelta
        exp = (date.today() - timedelta(days=3)).isoformat()
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_expire', exp)
        self.assertTrue(ventes_autorisees())


class TestDemo(unittest.TestCase):
    def setUp(self):
        reset_db()
        database.db.set_parametre('licence_plan_enc', '__demo__')

    def test_demo_peut_vendre_initial(self):
        ok, msg = demo_peut_vendre()
        self.assertTrue(ok)
        self.assertEqual(msg, '')

    def test_demo_limite_ventes(self):
        database.db.set_parametre('licence_demo_ventes', str(features.DEMO_MAX_VENTES))
        ok, msg = demo_peut_vendre()
        self.assertFalse(ok)
        self.assertIn('limite', msg.lower())

    def test_demo_incrementer(self):
        database.db.set_parametre('licence_demo_ventes', '5')
        demo_incrementer_ventes()
        nb = int(database.db.get_parametre('licence_demo_ventes', '0'))
        self.assertEqual(nb, 6)

    def test_demo_incrementer_hors_demo_sans_effet(self):
        database.db.set_parametre('licence_plan_enc', '__reseau_pro__')
        database.db.set_parametre('licence_demo_ventes', '5')
        demo_incrementer_ventes()
        nb = int(database.db.get_parametre('licence_demo_ventes', '0'))
        self.assertEqual(nb, 5)  # inchangé

    def test_demo_infos_structure(self):
        infos = demo_infos()
        self.assertIn('ventes_utilisees', infos)
        self.assertIn('ventes_max', infos)
        self.assertIn('jours_restants', infos)
        self.assertEqual(infos['ventes_max'], features.DEMO_MAX_VENTES)

    def test_demo_periode_expiree(self):
        debut_il_y_a_trop_longtemps = time.time() - (features.DEMO_MAX_JOURS + 2) * 86400
        database.db.set_parametre('licence_demo_debut', str(debut_il_y_a_trop_longtemps))
        ok, msg = demo_peut_vendre()
        self.assertFalse(ok)
        self.assertIn('période', msg.lower())

    def test_limites_plans_coherents(self):
        for plan in ('demo', 'standard', 'pro', 'white_label'):
            self.assertIn('terminaux', LIMITES[plan])
            self.assertIn('caissiers', LIMITES[plan])
            self.assertGreater(LIMITES[plan]['terminaux'], 0)


if __name__ == '__main__':
    unittest.main()
