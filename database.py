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
            self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Activer Row Factory pour accès par clé
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
            self.create_tables()  # Restaure le schéma (critique pour :memory:)

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
                date_ajout TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                description TEXT
            )
        ''')

        # Table Ventes
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ventes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_vente TEXT UNIQUE NOT NULL,
                date_vente TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                total REAL NOT NULL,
                client TEXT,
                utilisateur_id INTEGER,
                statut TEXT DEFAULT 'terminee',
                deleted_at TIMESTAMP DEFAULT NULL,
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
            )
        ''')

        # Migration : Ajouter colonne utilisateur_id si absente
        try:
            self.cursor.execute("SELECT utilisateur_id FROM ventes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne utilisateur_id à table ventes")
            self.cursor.execute("ALTER TABLE ventes ADD COLUMN utilisateur_id INTEGER")
            self.conn.commit()

        # Migration : Ajouter colonne client_id si absente
        try:
            self.cursor.execute("SELECT client_id FROM ventes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne client_id à table ventes")
            self.cursor.execute("ALTER TABLE ventes ADD COLUMN client_id INTEGER")
            self.conn.commit()

        # Migration : Ajouter colonne remise si absente
        try:
            self.cursor.execute("SELECT remise FROM ventes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne remise à table ventes")
            self.cursor.execute("ALTER TABLE ventes ADD COLUMN remise REAL DEFAULT 0")
            self.conn.commit()

        # Migration : Ajouter colonne nom_caisse si absente
        try:
            self.cursor.execute("SELECT nom_caisse FROM ventes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne nom_caisse à table ventes")
            self.cursor.execute("ALTER TABLE ventes ADD COLUMN nom_caisse TEXT DEFAULT NULL")
            self.conn.commit()

        # Migrations : colonnes paiement sur ventes (requises par api_locale)
        for col, definition in [
            ('total_ttc',      'REAL DEFAULT 0'),
            ('montant_recu',   'REAL DEFAULT 0'),
            ('monnaie',        'REAL DEFAULT 0'),
            ('mode_paiement',  "TEXT DEFAULT 'especes'"),
        ]:
            try:
                self.cursor.execute(f"SELECT {col} FROM ventes LIMIT 1")
            except sqlite3.OperationalError:
                logger.info(f"Migration: Ajout colonne {col} à table ventes")
                self.cursor.execute(f"ALTER TABLE ventes ADD COLUMN {col} {definition}")
                self.conn.commit()

        # Migration : Ajouter colonnes prix_gros / seuil_gros à produits
        try:
            self.cursor.execute("SELECT prix_gros FROM produits LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonnes prix_gros / seuil_gros à table produits")
            self.cursor.execute("ALTER TABLE produits ADD COLUMN prix_gros REAL DEFAULT 0")
            self.cursor.execute("ALTER TABLE produits ADD COLUMN seuil_gros INTEGER DEFAULT 0")
            self.conn.commit()

        # Migration : Ajouter colonne unite_mesure à produits
        try:
            self.cursor.execute("SELECT unite_mesure FROM produits LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne unite_mesure à table produits")
            self.cursor.execute("ALTER TABLE produits ADD COLUMN unite_mesure TEXT DEFAULT 'pièce'")
            self.conn.commit()

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

        # Migration : Ajouter colonne is_prix_gros à details_ventes
        try:
            self.cursor.execute("SELECT is_prix_gros FROM details_ventes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne is_prix_gros à table details_ventes")
            self.cursor.execute("ALTER TABLE details_ventes ADD COLUMN is_prix_gros INTEGER DEFAULT 0")
            self.conn.commit()

        # Table Historique du stock
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS historique_stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produit_id INTEGER,
                quantite_avant INTEGER,
                quantite_apres INTEGER,
                operation TEXT,
                date_operation TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
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
                date_creation TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                dernier_login TIMESTAMP,
                super_admin BOOLEAN DEFAULT 0
            )
        ''')

        # Migration: Ajouter colonne super_admin a la table utilisateurs si elle n'existe pas
        try:
            self.cursor.execute("SELECT super_admin FROM utilisateurs LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne super_admin a table utilisateurs")
            self.cursor.execute("ALTER TABLE utilisateurs ADD COLUMN super_admin BOOLEAN DEFAULT 0")
            self.conn.commit()

        # Si aucun super-admin n'existe, marquer le premier utilisateur comme super-admin
        result = self.fetch_one("SELECT COUNT(*) FROM utilisateurs WHERE super_admin = 1")
        if result and result[0] == 0:
            # Marquer le premier utilisateur actif comme super-admin
            self.execute_query("""
                UPDATE utilisateurs
                SET super_admin = 1, role = 'patron'
                WHERE id = (SELECT id FROM utilisateurs ORDER BY id LIMIT 1)
            """)
            logger.info("Le premier utilisateur a ete marque comme Super-Admin.")

        # Table Logs d'actions
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                utilisateur_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                date_action TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
            )
        ''')

        # Table Clients
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                telephone TEXT,
                email TEXT,
                points_fidelite INTEGER DEFAULT 0,
                total_achats REAL DEFAULT 0,
                nombre_achats INTEGER DEFAULT 0,
                date_creation TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                notes TEXT
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
                date_paiement TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
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

        # Migration : ajouter client_id aux ventes
        self.migrer_clients()

        # Migration : ajouter sync_done à historique_stock
        self.migrer_sync()

        # Inserer parametres par defaut
        self.init_parametres()

        # TRIGGER : Empêcher stock négatif (sécurité supplémentaire)
        self.cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS verifier_stock_positif
            BEFORE UPDATE ON produits
            FOR EACH ROW
            WHEN NEW.stock_actuel < 0
            BEGIN
                SELECT RAISE(ABORT, 'Le stock ne peut pas être négatif');
            END
        ''')

        # Table Ardoise (crédits clients)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ardoise (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                vente_id INTEGER,
                montant_initial REAL NOT NULL,
                montant_restant REAL NOT NULL,
                date_creation TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                date_echeance TIMESTAMP NULL,
                statut TEXT DEFAULT 'en_cours',
                notes TEXT,
                FOREIGN KEY (client_id) REFERENCES clients(id),
                FOREIGN KEY (vente_id) REFERENCES ventes(id)
            )
        ''')

        # Table Encaissements ardoise
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS encaissements_ardoise (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ardoise_id INTEGER NOT NULL,
                montant REAL NOT NULL,
                mode_paiement TEXT DEFAULT 'especes',
                reference TEXT,
                date_encaissement TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                notes TEXT,
                id_session INTEGER NULL,
                FOREIGN KEY (ardoise_id) REFERENCES ardoise(id)
            )
        ''')

        # Table Sessions de caisse
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions_caisse (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_caisse TEXT DEFAULT 'C1',
                id_caissier INTEGER NOT NULL,
                date_ouverture TIMESTAMP NOT NULL,
                fond_ouverture INTEGER NOT NULL DEFAULT 0,
                date_cloture TIMESTAMP NULL,
                fond_cloture_declare INTEGER NULL,
                fond_cloture_calcule INTEGER DEFAULT 0,
                ecart INTEGER DEFAULT 0,
                total_especes INTEGER DEFAULT 0,
                total_mobile INTEGER DEFAULT 0,
                total_credit INTEGER DEFAULT 0,
                total_annule INTEGER DEFAULT 0,
                nb_ventes INTEGER DEFAULT 0,
                statut TEXT DEFAULT 'ouverte',
                hash_cloture TEXT NULL,
                FOREIGN KEY (id_caissier) REFERENCES utilisateurs(id)
            )
        ''')

        # Migration : id_session dans ventes
        try:
            self.cursor.execute("SELECT id_session FROM ventes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne id_session à table ventes")
            self.cursor.execute("ALTER TABLE ventes ADD COLUMN id_session INTEGER NULL")
            self.conn.commit()

        # Migration : motif_annulation dans ventes
        try:
            self.cursor.execute("SELECT motif_annulation FROM ventes LIMIT 1")
        except sqlite3.OperationalError:
            logger.info("Migration: Ajout colonne motif_annulation à table ventes")
            self.cursor.execute("ALTER TABLE ventes ADD COLUMN motif_annulation TEXT NULL")
            self.conn.commit()

        # Migration : colonnes de paiement détaillées dans sessions_caisse
        for col in ('total_virement', 'total_cheque', 'total_carte', 'total_autre'):
            try:
                self.cursor.execute(f"SELECT {col} FROM sessions_caisse LIMIT 1")
            except sqlite3.OperationalError:
                logger.info(f"Migration: Ajout colonne {col} à sessions_caisse")
                self.cursor.execute(f"ALTER TABLE sessions_caisse ADD COLUMN {col} INTEGER DEFAULT 0")
                self.conn.commit()

        # Tables fournisseurs
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS fournisseurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                telephone TEXT,
                email TEXT,
                adresse TEXT,
                contact_nom TEXT,
                actif INTEGER DEFAULT 1,
                date_creation TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS commandes_fournisseurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fournisseur_id INTEGER NOT NULL,
                date_commande TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime')),
                date_livraison_prevue DATE,
                statut TEXT DEFAULT 'en_attente',
                total REAL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (fournisseur_id) REFERENCES fournisseurs(id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS details_commandes_fournisseurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                commande_id INTEGER NOT NULL,
                produit_id INTEGER NOT NULL,
                quantite_commandee INTEGER NOT NULL,
                prix_unitaire REAL DEFAULT 0,
                quantite_recue INTEGER DEFAULT 0,
                FOREIGN KEY (commande_id) REFERENCES commandes_fournisseurs(id),
                FOREIGN KEY (produit_id) REFERENCES produits(id)
            )
        ''')

        self.conn.commit()
        logger.info("Tables creees/verifiees avec succes")

    def migrer_updated_at(self):
        """Ajouter la colonne updated_at aux tables produits et utilisateurs si absente"""
        for table in ('produits', 'utilisateurs'):
            try:
                colonnes = [row[1] for row in self.cursor.execute(f"PRAGMA table_info({table})").fetchall()]
                if 'updated_at' not in colonnes:
                    self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMP")
                    self.cursor.execute(f"UPDATE {table} SET updated_at = strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime') WHERE updated_at IS NULL")
                    logger.info(f"Colonne updated_at ajoutee a {table}")
            except Exception as e:
                logger.warning(f"Migration updated_at pour {table}: {e}")

    def migrer_clients(self):
        """Ajouter la colonne client_id a la table ventes et migrer les noms existants"""
        try:
            colonnes = [row[1] for row in self.cursor.execute("PRAGMA table_info(ventes)").fetchall()]
            if 'client_id' not in colonnes:
                self.cursor.execute("ALTER TABLE ventes ADD COLUMN client_id INTEGER REFERENCES clients(id)")
                # Migrer les noms existants vers la table clients
                noms = self.cursor.execute(
                    "SELECT DISTINCT client FROM ventes WHERE client IS NOT NULL AND client != ''"
                ).fetchall()
                for (nom,) in noms:
                    self.cursor.execute(
                        "INSERT INTO clients (nom) VALUES (?)", (nom,)
                    )
                    client_id = self.cursor.lastrowid
                    self.cursor.execute(
                        "UPDATE ventes SET client_id = ? WHERE client = ?", (client_id, nom)
                    )
                logger.info("Migration client_id effectuee sur la table ventes")
        except Exception as e:
            logger.warning(f"Migration clients: {e}")

    def migrer_sync(self):
        """Ajouter sync_done à historique_stock pour le suivi de synchronisation"""
        try:
            colonnes = [row[1] for row in self.cursor.execute("PRAGMA table_info(historique_stock)").fetchall()]
            if 'sync_done' not in colonnes:
                self.cursor.execute("ALTER TABLE historique_stock ADD COLUMN sync_done INTEGER DEFAULT 0")
                self.conn.commit()
                logger.info("Migration: sync_done ajouté à historique_stock")
        except Exception as e:
            logger.warning(f"Migration sync_done: {e}")

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
            # Parametres fidelite
            ('fidelite_active', '1', 'Programme fidelite actif: 0 ou 1'),
            ('fidelite_points_par_fcfa', '1000', '1 point par X FCFA depenses'),
            ('fidelite_remise_seuil', '100', 'Nombre de points pour une remise'),
            ('fidelite_remise_pct', '5', 'Pourcentage de remise fidelite'),
            ('gestionnaire_peut_vendre', '1', 'Permettre aux gestionnaires d\'effectuer des ventes: 0=non, 1=oui'),
            ('camera_auto_start', '0', 'Démarrer la caméra automatiquement: 0=non, 1=oui'),
            ('mode_scan_auto', '1', 'Mode de scan automatique (sans demander la quantité): 0=non, 1=oui'),
            ('son_scan_actif', '1', 'Activer le son lors du scan: 0=non, 1=oui'),
            ('son_scan_type', 'beep', 'Type de son de scan: beep ou fichier'),
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

    def fetch_one_dict(self, query, params=()):
        """Recuperer un seul resultat en dict explicite"""
        row = self.fetch_one(query, params)
        return dict(row) if row else None

    def fetch_all_dicts(self, query, params=()):
        """Recuperer tous les resultats en liste de dicts"""
        rows = self.fetch_all(query, params)
        return [dict(row) for row in rows] if rows else []

    def get_parametre(self, cle, defaut=""):
        """Recuperer un parametre"""
        result = self.fetch_one("SELECT valeur FROM parametres WHERE cle = ?", (cle,))
        return result['valeur'] if result else defaut

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
