"""
Gestion des utilisateurs et authentification
"""
import bcrypt
import sqlite3
from database import db
from datetime import datetime

class Utilisateur:
    @staticmethod
    def initialiser_tables():
        """Créer les tables utilisateurs et logs si elles n'existent pas"""
        # Table Utilisateurs
        sql_users = """
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
        );
        """
        db.execute_query(sql_users)

        # Table Logs
        sql_logs = """
        CREATE TABLE IF NOT EXISTS logs_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        );
        """
        db.execute_query(sql_logs)

        # Créer l'admin par défaut s'il n'existe pas
        if not db.fetch_one("SELECT * FROM utilisateurs"):
            # Mot de passe par défaut : admin123
            mdp_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
            sql_admin = """
            INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role)
            VALUES (?, ?, ?, ?, ?)
            """
            db.execute_query(sql_admin, ('Admin', 'Principal', 'admin@boutique.com', mdp_hash.decode(), 'patron'))
            print("✅ Utilisateur Admin créé par défaut (admin@boutique.com / admin123)")

    @staticmethod
    def creer_utilisateur(nom, prenom, email, mot_de_passe, role='caissier'):
        """Créer un nouvel utilisateur"""
        try:
            hashed = bcrypt.hashpw(mot_de_passe.encode(), bcrypt.gensalt())
            query = """
                INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role)
                VALUES (?, ?, ?, ?, ?)
            """
            return db.execute_query(query, (nom, prenom, email, hashed.decode(), role))
        except sqlite3.IntegrityError:
            return False # Email déjà existant

    @staticmethod
    def authentifier(email, mot_de_passe):
        """Vérifier les identifiants"""
        query = "SELECT * FROM utilisateurs WHERE email = ? AND actif = 1"
        user = db.fetch_one(query, (email,))
        
        # user structure: 0:id, 1:nom, 2:prenom, 3:email, 4:hash, 5:role
        if user and bcrypt.checkpw(mot_de_passe.encode(), user[4].encode()):
            # Mettre à jour dernier login
            db.execute_query(
                "UPDATE utilisateurs SET dernier_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user[0],)
            )
            return user
        return None

    @staticmethod
    def obtenir_tous():
        """Liste de tous les utilisateurs"""
        return db.fetch_all("SELECT * FROM utilisateurs ORDER BY nom")

    @staticmethod
    def modifier_role(user_id, nouveau_role):
        """Changer le rôle d'un utilisateur"""
        return db.execute_query(
            "UPDATE utilisateurs SET role = ? WHERE id = ?",
            (nouveau_role, user_id)
        )

    @staticmethod
    def changer_statut(user_id, actif):
        """Activer/Désactiver un utilisateur"""
        return db.execute_query(
            "UPDATE utilisateurs SET actif = ? WHERE id = ?",
            (1 if actif else 0, user_id)
        )

    @staticmethod
    def logger_action(user_id, action, details=""):
        """Enregistrer une action dans les logs"""
        query = """
            INSERT INTO logs_actions (utilisateur_id, action, details)
            VALUES (?, ?, ?)
        """
        # On utilise try/except au cas où l'ID utilisateur est None (ex: système)
        try:
            if user_id:
                db.execute_query(query, (user_id, action, details))
        except Exception as e:
            print(f"Erreur log: {e}")