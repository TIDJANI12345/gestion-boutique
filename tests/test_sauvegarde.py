"""Tests unitaires pour le module Sauvegarde (Phase 2.3)"""
import unittest
import os
import tempfile
import shutil
import sqlite3
from tests.conftest import reset_db

import config
import database


def _creer_temp_db(temp_dir):
    """Creer un vrai fichier SQLite de test"""
    temp_db = os.path.join(temp_dir, 'boutique.db')
    conn = sqlite3.connect(temp_db)
    conn.execute("CREATE TABLE IF NOT EXISTS test_data (id INTEGER, valeur TEXT)")
    conn.execute("INSERT INTO test_data VALUES (1, 'test')")
    conn.commit()
    conn.close()
    return temp_db


class TestSauvegardeLocale(unittest.TestCase):
    """Test sauvegarde et restauration locale"""

    def setUp(self):
        reset_db()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = _creer_temp_db(self.temp_dir)
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)

        import modules.sauvegarde as mod
        self._orig_backup_dir = mod.BACKUP_DIR
        self._orig_db_path = config.DB_PATH
        mod.BACKUP_DIR = self.backup_dir
        config.DB_PATH = self.temp_db

    def tearDown(self):
        import modules.sauvegarde as mod
        mod.BACKUP_DIR = self._orig_backup_dir
        config.DB_PATH = self._orig_db_path
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_sauvegarder_locale(self):
        """Creer une sauvegarde locale"""
        from modules.sauvegarde import sauvegarder_locale
        succes, message, chemin = sauvegarder_locale()
        self.assertTrue(succes, f"Echec: {message}")
        self.assertIsNotNone(chemin)
        self.assertTrue(os.path.exists(chemin))

    def test_lister_sauvegardes(self):
        """Lister les sauvegardes disponibles"""
        import time
        from modules.sauvegarde import sauvegarder_locale, lister_sauvegardes
        sauvegarder_locale()
        time.sleep(1.1)  # S'assurer d'un timestamp different
        sauvegarder_locale()

        sauvegardes = lister_sauvegardes()
        self.assertGreaterEqual(len(sauvegardes), 2)

        for s in sauvegardes:
            self.assertIn('nom', s)
            self.assertIn('chemin', s)
            self.assertIn('date', s)
            self.assertIn('taille', s)

    def test_sauvegardes_triees_par_date(self):
        """Les sauvegardes sont triees par date decroissante"""
        from modules.sauvegarde import sauvegarder_locale, lister_sauvegardes
        import time

        sauvegarder_locale()
        time.sleep(1.1)
        sauvegarder_locale()

        sauvegardes = lister_sauvegardes()
        if len(sauvegardes) >= 2:
            self.assertGreaterEqual(sauvegardes[0]['date'], sauvegardes[1]['date'])


class TestExportImportZip(unittest.TestCase):
    """Test export et import ZIP"""

    def setUp(self):
        reset_db()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = _creer_temp_db(self.temp_dir)
        self.backup_dir = os.path.join(self.temp_dir, 'backups')
        os.makedirs(self.backup_dir, exist_ok=True)

        import modules.sauvegarde as mod
        self._orig_backup_dir = mod.BACKUP_DIR
        self._orig_db_path = config.DB_PATH
        self._orig_images_dir = config.IMAGES_DIR
        self._orig_recus_dir = config.RECUS_DIR
        mod.BACKUP_DIR = self.backup_dir
        config.DB_PATH = self.temp_db
        # Creer des dossiers images/recus vides pour le test
        config.IMAGES_DIR = os.path.join(self.temp_dir, 'images')
        config.RECUS_DIR = os.path.join(self.temp_dir, 'recus')
        os.makedirs(config.IMAGES_DIR, exist_ok=True)
        os.makedirs(config.RECUS_DIR, exist_ok=True)

    def tearDown(self):
        import modules.sauvegarde as mod
        mod.BACKUP_DIR = self._orig_backup_dir
        config.DB_PATH = self._orig_db_path
        config.IMAGES_DIR = self._orig_images_dir
        config.RECUS_DIR = self._orig_recus_dir
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_exporter_zip(self):
        """Exporter un ZIP"""
        from modules.sauvegarde import exporter_zip
        succes, message, chemin = exporter_zip()
        self.assertTrue(succes, f"Echec: {message}")
        self.assertTrue(chemin.endswith('.zip'))
        self.assertTrue(os.path.exists(chemin))

    def test_zip_contient_db(self):
        """Le ZIP contient le fichier boutique.db"""
        from modules.sauvegarde import exporter_zip
        import zipfile

        _, _, chemin = exporter_zip()
        with zipfile.ZipFile(chemin, 'r') as zf:
            noms = zf.namelist()
            db_files = [n for n in noms if 'boutique.db' in n]
            self.assertGreater(len(db_files), 0, f"DB absente du ZIP. Contenu: {noms}")

    def test_importer_zip_invalide(self):
        """Importer un fichier non-ZIP echoue proprement"""
        from modules.sauvegarde import importer_zip

        fake_path = os.path.join(self.temp_dir, "fake.zip")
        with open(fake_path, 'w') as f:
            f.write("pas un zip")

        succes, message = importer_zip(fake_path)
        self.assertFalse(succes)

    def test_importer_zip_inexistant(self):
        """Importer un fichier inexistant echoue proprement"""
        from modules.sauvegarde import importer_zip

        succes, message = importer_zip("/chemin/inexistant.zip")
        self.assertFalse(succes)
        self.assertIn("introuvable", message.lower())


class TestNettoyageSauvegardes(unittest.TestCase):
    """Test nettoyage des anciennes sauvegardes"""

    def test_nettoyage_anciennes(self):
        """Les sauvegardes au-dela du max sont supprimees"""
        import modules.sauvegarde as mod
        from modules.sauvegarde import sauvegarder_locale, lister_sauvegardes

        temp_dir = tempfile.mkdtemp()
        temp_db = _creer_temp_db(temp_dir)
        backup_dir = os.path.join(temp_dir, 'backups')
        os.makedirs(backup_dir, exist_ok=True)

        orig_backup = mod.BACKUP_DIR
        orig_max = mod.MAX_BACKUPS
        orig_db = config.DB_PATH

        try:
            mod.BACKUP_DIR = backup_dir
            mod.MAX_BACKUPS = 3
            config.DB_PATH = temp_db

            for _ in range(5):
                sauvegarder_locale()

            sauvegardes = lister_sauvegardes()
            self.assertLessEqual(len(sauvegardes), 3)
        finally:
            mod.BACKUP_DIR = orig_backup
            mod.MAX_BACKUPS = orig_max
            config.DB_PATH = orig_db
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
