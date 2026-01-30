"""Configuration partagee pour les tests.
Doit etre importe en premier dans chaque fichier de test.

IMPORTANT: Ce module modifie config.DB_PATH AVANT que database.py soit importe,
pour que l'instance globale db utilise :memory: des le depart.
"""
import os
import sys

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configurer les chemins AVANT tout import de database
import config
config.DB_PATH = ':memory:'
config.DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data')
os.makedirs(config.DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(config.DATA_DIR, 'logs'), exist_ok=True)

# Maintenant importer database - l'instance db sera creee avec :memory:
# Grace a config.DB_PATH = ':memory:' ci-dessus
import database


def reset_db():
    """Vider toutes les tables pour un test propre.
    Reutilise la meme instance db (et donc la meme connexion :memory:)."""
    db = database.db
    for table in ['paiements', 'details_ventes', 'historique_stock', 'logs_actions',
                  'sync_queue', 'ventes', 'produits', 'utilisateurs', 'parametres',
                  'taux_tva', 'devises']:
        try:
            db.execute_query(f"DELETE FROM {table}")
        except Exception:
            pass
    db.init_parametres()
    return db
