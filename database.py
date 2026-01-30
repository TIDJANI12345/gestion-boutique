"""
Gestion de la base de données SQLite
Structure inspirée du projet PHP
"""
import sqlite3
from config import DB_PATH
from datetime import datetime

class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connexion à la base de données"""
        try:
            self.conn = sqlite3.connect(DB_PATH)
            self.cursor = self.conn.cursor()
            print("✅ Connexion à la base de données réussie")
        except Exception as e:
            print(f"❌ Erreur de connexion : {e}")
    
    def create_tables(self):
        """Création des tables avec support du Soft Delete"""
        
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
                statut TEXT DEFAULT 'terminée',
                deleted_at TIMESTAMP DEFAULT NULL
            )
        ''')
        
        # Table Détails des ventes
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
        
        # Table Paramètres (nouvelle)
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

        # --- AJOUTEZ CECI POUR L'ADMIN PAR DÉFAUT ---
        # On vérifie si la table est vide pour créer le premier patron
        self.cursor.execute("SELECT COUNT(*) FROM utilisateurs")
        if self.cursor.fetchone()[0] == 0:
            import bcrypt # Assurez-vous d'avoir fait pip install bcrypt
            mdp_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            self.cursor.execute('''
                INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ('Admin', 'Principal', 'admin@boutique.com', mdp_hash, 'patron'))
        
        # Migration : ajouter updated_at aux tables existantes
        self.migrer_updated_at()

        # Insérer paramètres par défaut
        self.init_parametres()

        self.conn.commit()
        print("✅ Tables créées avec succès")
    
    def migrer_updated_at(self):
        """Ajouter la colonne updated_at aux tables produits et utilisateurs si absente"""
        for table in ('produits', 'utilisateurs'):
            try:
                colonnes = [row[1] for row in self.cursor.execute(f"PRAGMA table_info({table})").fetchall()]
                if 'updated_at' not in colonnes:
                    self.cursor.execute(f"ALTER TABLE {table} ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    self.cursor.execute(f"UPDATE {table} SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
                    print(f"✅ Colonne updated_at ajoutée à {table}")
            except Exception as e:
                print(f"⚠️ Migration updated_at pour {table}: {e}")

    def init_parametres(self):
        """Initialiser les paramètres par défaut"""
        from config import BOUTIQUE_NOM, BOUTIQUE_ADRESSE, BOUTIQUE_TELEPHONE, BOUTIQUE_EMAIL
        
        parametres_defaut = [
            ('boutique_nom', BOUTIQUE_NOM, 'Nom de la boutique'),
            ('boutique_adresse', BOUTIQUE_ADRESSE, 'Adresse de la boutique'),
            ('boutique_telephone', BOUTIQUE_TELEPHONE, 'Téléphone de la boutique'),
            ('boutique_email', BOUTIQUE_EMAIL, 'Email de la boutique'),
        ]
        
        for cle, valeur, description in parametres_defaut:
            self.cursor.execute(
                'INSERT OR IGNORE INTO parametres (cle, valeur, description) VALUES (?, ?, ?)',
                (cle, valeur, description)
            )
        self.conn.commit()
    
    def execute_query(self, query, params=()):
        """
        Exécuter une requête INSERT/UPDATE/DELETE
        Retourne lastrowid pour les INSERT, True/False sinon
        """
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
            
            # ✅ CORRECTION : Retourner lastrowid pour les INSERT
            if query.strip().upper().startswith('INSERT'):
                return self.cursor.lastrowid
            return True
            
        except Exception as e:
            print(f"❌ Erreur SQL : {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def fetch_all(self, query, params=()):
        """Récupérer tous les résultats"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            print(f"❌ Erreur : {e}")
            return []
    
    def fetch_one(self, query, params=()):
        """Récupérer un seul résultat"""
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchone()
        except Exception as e:
            print(f"❌ Erreur : {e}")
            return None
    
    def get_parametre(self, cle, defaut=""):
        """Récupérer un paramètre"""
        result = self.fetch_one("SELECT valeur FROM parametres WHERE cle = ?", (cle,))
        return result[0] if result else defaut
    
    def set_parametre(self, cle, valeur):
        """Définir un paramètre"""
        query = "INSERT OR REPLACE INTO parametres (cle, valeur) VALUES (?, ?)"
        return self.execute_query(query, (cle, valeur))
    
    def close(self):
        """Fermer la connexion"""
        if self.conn:
            self.conn.close()
            print("✅ Connexion fermée")

# Instance globale de la base de données
db = Database()