"""
Gestion de la base de donnees SQLite
"""
import sqlite3
from config import DB_PATH
from datetime import datetime
from modules.logger import get_logger

logger = get_logger('database')


class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connexion a la base de donnees"""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()
            logger.info("Connexion a la base de donnees reussie")
        except Exception as e:
            logger.error(f"Erreur de connexion : {e}")

    def _ensure_connection(self):
        """Reconnexion automatique si la connexion est perdue"""
        try:
            self.conn.execute("SELECT 1")
        except Exception:
            logger.warning("Connexion perdue, reconnexion...")
            self.connect()

    def create_tables(self):
        """Creation des tables"""

        # Table Produits
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS produits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                categorie TEXT,
                prix_achat REAL DEFAULT 0,
                prix_vente REAL NOT NULL,
                stock_actuel INTEGER DEFAULT 0,
                stock_alerte INTEGER DEFAULT 5,
                code_barre TEXT UNIQUE NOT NULL,
                type_code_barre TEXT DEFAULT 'code128',
                date_ajout TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')

        # Table Ventes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_vente TEXT UNIQUE NOT NULL,
                date_vente TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total REAL NOT NULL,
                client TEXT,
                statut TEXT DEFAULT 'terminee',
                deleted_at TIMESTAMP DEFAULT NULL
            )
        ''')

        # Table Details des ventes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS details_ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vente_id INTEGER,
                produit_id INTEGER,
                quantite INTEGER NOT NULL,
                prix_unitaire REAL NOT NULL,
                sous_total REAL NOT NULL,
                FOREIGN KEY (vente_id) REFERENCES ventes(id),
                FOREIGN KEY (produit_id) REFERENCES produits(id)
            )
        ''')

        # Table Historique du stock
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS historique_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produit_id INTEGER,
                quantite_avant INTEGER,
                quantite_apres INTEGER,
                operation TEXT,
                date_operation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (produit_id) REFERENCES produits(id)
            )
        ''')

        # Table Parametres
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS parametres (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cle TEXT UNIQUE NOT NULL,
                valeur TEXT,
                description TEXT
            )
        ''')

        # Table Utilisateurs
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS utilisateurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                mot_de_passe TEXT NOT NULL,
                role TEXT DEFAULT 'caissier',
                actif BOOLEAN DEFAULT 1,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                dernier_login TIMESTAMP
            )
        ''')

        # Table Logs d'actions
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utilisateur_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
            )
        ''')

        # Table file d'attente sync hors-ligne
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                table_name TEXT NOT NULL,
                data_json TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table Paiements
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS paiements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vente_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                montant REAL NOT NULL,
                reference TEXT,
                montant_recu REAL,
                monnaie_rendue REAL,
                date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vente_id) REFERENCES ventes(id)
            )
        ''')

        # Table Taux TVA par categorie
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS taux_tva (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categorie TEXT UNIQUE NOT NULL,
                taux REAL NOT NULL,
                description TEXT
            )
        ''')

        # Table Devises
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS devises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                symbole TEXT NOT NULL,
                taux_change REAL NOT NULL,
                actif BOOLEAN DEFAULT 1
            )
        ''')

        # Migration : ajouter updated_at aux tables existantes
        self.migrer_updated_at()

        # Inserer parametres par defaut
        self.init_parametres()

        self.conn.commit()
        logger.info("Tables creees/verifiees avec succes")

    def migrer_updated_at(self):
        """Ajouter la colonne updated_at aux tables produits et utilisateurs si absente"""
        for table in ('produits', 'utilisateurs'):
            try:
                colonnes = [row[1] for row in self.cursor.execute(f"PRAGMA table_info({table})").fetchall()]
                if 'updated_at' not in colonnes:
                    self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMP")
                    self.cursor.execute(f"UPDATE {table} SET updated_at = datetime('now') WHERE updated_at IS NULL")
                    logger.info(f"Colonne updated_at ajoutee a {table}")
            except Exception as e:
                logger.warning(f"Migration updated_at pour {table}: {e}")

    def init_parametres(self):
        """Initialiser les parametres par defaut"""
        from config import BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE, BOUTIQUE_EMAIL

        parametres_defaut = [
            ('boutique_nom', BOUTIQUE_NOM, 'Nom de la boutique'),
            ('boutique_adresse', BOUTIQUE_ADRESSE, 'Adresse de la boutique'),
            ('boutique_telephone', BOUTIQUE_TELEPHONE, 'Telephone de la boutique'),
            ('boutique_email', BOUTIQUE_EMAIL, 'Email de la boutique'),
            ('session_timeout', '900', 'Timeout session en secondes (defaut 15 min)'),
            # Parametres imprimante
            ('imprimante_mode', 'usb', 'Mode imprimante: usb, reseau, serie'),
            ('imprimante_format', '80mm', 'Format papier: 58mm ou 80mm'),
            ('imprimante_usb_vendor', '0x0', 'Vendor ID USB imprimante'),
            ('imprimante_usb_product', '0x0', 'Product ID USB imprimante'),
            ('imprimante_ip', '', 'Adresse IP imprimante reseau'),
            ('imprimante_port', '9100', 'Port imprimante reseau'),
            ('imprimante_serie_port', 'COM1', 'Port serie imprimante'),
            ('imprimante_serie_baudrate', '9600', 'Baudrate port serie'),
            # Parametres fiscaux
            ('tva_active', '0', 'TVA active: 0 ou 1'),
            ('tva_taux_defaut', '18', 'Taux TVA par defaut en %'),
            ('devise_principale', 'XOF', 'Code devise principale'),
            ('devise_symbole', 'FCFA', 'Symbole devise principale'),
        ]

        for cle, valeur, description in parametres_defaut:
            self.cursor.execute(
                'INSERT OR IGNORE INTO parametres (cle, valeur, description) VALUES (?, ?, ?)',
                (cle, valeur, description)
            )

        # Devises par defaut
        devises_defaut = [
            ('XOF', 'FCFA', 1.0),
            ('EUR', '€', 655.957),
            ('USD', '$', 600.0),
        ]
        for code, symbole, taux in devises_defaut:
            self.cursor.execute(
                'INSERT OR IGNORE INTO devises (code, symbole, taux_change, actif) VALUES (?, ?, ?, 1)',
                (code, symbole, taux)
            )

        self.conn.commit()

    def execute_query(self, query, params=()):
        """Executer une requete INSERT/UPDATE/DELETE avec rollback en cas d'erreur"""
        self._ensure_connection()
        try:
            self.cursor.execute(query, params)
            self.conn.commit()

            if query.strip().upper().startswith('INSERT'):
                return self.cursor.lastrowid
            return True

        except Exception as e:
            logger.error(f"Erreur SQL : {e} | Requete: {query[:100]}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return None

    def execute_transaction(self, queries_params_list):
        """Executer plusieurs requetes dans une transaction atomique"""
        self._ensure_connection()
        try:
            for query, params in queries_params_list:
                self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Erreur transaction : {e}")
            try:
                self.conn.rollback()
            except Exception:
                pass
            return None

    def fetch_all(self, query, params=()):
        """Recuperer tous les resultats"""
        self._ensure_connection()
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Erreur fetch_all : {e}")
            return []

    def fetch_one(self, query, params=()):
        """Recuperer un seul resultat"""
        self._ensure_connection()
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Erreur fetch_one : {e}")
            return None

    def get_parametre(self, cle, defaut=""):
        """Recuperer un parametre"""
        result = self.fetch_one("SELECT valeur FROM parametres WHERE cle = ?", (cle,))
        return result[0] if result else defaut

    def set_parametre(self, cle, valeur):
        """Definir un parametre"""
        query = "INSERT OR REPLACE INTO parametres (cle, valeur) VALUES (?, ?)"
        return self.execute_query(query, (cle, valeur))

    def close(self):
        """Fermer la connexion"""
        if self.conn:
            self.conn.close()
            logger.info("Connexion fermee")


# Instance globale de la base de donnees
db = Database()
