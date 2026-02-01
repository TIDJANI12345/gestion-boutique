"""
Gestion des utilisateurs et authentification
"""
import bcrypt
import sqlite3
from database import db
from datetime import datetime
from modules.logger import get_logger

logger = get_logger('utilisateurs')


ROLES_DISPONIBLES = {
    'patron': 'Super-Admin (Patron)',
    'gestionnaire': 'Gestionnaire (Stocks)',
    'caissier': 'Caissier (Ventes)'
}


class Utilisateur:
    @staticmethod
    def initialiser_tables():
        """Creer les tables utilisateurs et logs si elles n'existent pas"""
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

    @staticmethod
    def compte_existe():
        """Verifier s'il existe au moins un utilisateur dans la base"""
        result = db.fetch_one("SELECT COUNT(*) FROM utilisateurs")
        return result and result[0] > 0

    @staticmethod
    def est_super_admin(user_id):
        """Vérifier si un utilisateur est super-admin"""
        result = db.fetch_one(
            "SELECT super_admin FROM utilisateurs WHERE id = ?",
            (user_id,)
        )
        return result and result[0] == 1

    @staticmethod
    def valider_mot_de_passe(mot_de_passe):
        """Valider la complexite du mot de passe. Retourne (bool, message)"""
        if len(mot_de_passe) < 8:
            return False, "Le mot de passe doit contenir au moins 8 caracteres"
        if not any(c.isdigit() for c in mot_de_passe):
            return False, "Le mot de passe doit contenir au moins 1 chiffre"
        return True, "Mot de passe valide"

    @staticmethod
    def creer_utilisateur(nom, prenom, email, mot_de_passe, role='caissier'):
        """Creer un nouvel utilisateur"""
        # Valider le mot de passe
        valide, message = Utilisateur.valider_mot_de_passe(mot_de_passe)
        if not valide:
            logger.warning(f"Creation utilisateur refusee : {message}")
            return False, message

        try:
            hashed = bcrypt.hashpw(mot_de_passe.encode(), bcrypt.gensalt())

            super_admin_flag = 0
            if role == 'patron':
                # Vérifier qu'il n'existe pas déjà un super-admin
                count_super_admin = db.fetch_one("SELECT COUNT(*) FROM utilisateurs WHERE super_admin = 1")
                if count_super_admin and count_super_admin[0] > 0:
                    return False, "Un super-admin existe déjà. Le rôle 'patron' ne peut être attribué qu'une seule fois."
                super_admin_flag = 1

            query = """
                INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role, super_admin)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            result = db.execute_query(query, (nom, prenom, email, hashed.decode(), role, super_admin_flag))
            if result:
                logger.info(f"Utilisateur cree : {email} ({role})")
                return True, "Utilisateur cree avec succes"
            return False, "Erreur lors de la creation"
        except sqlite3.IntegrityError:
            logger.warning(f"Email deja existant : {email}")
            return False, "Cet email existe deja"
        except Exception as e:
            logger.error(f"Erreur creation utilisateur : {e}")
            return False, f"Erreur : {e}"

    @staticmethod
    def authentifier(email, mot_de_passe):
        """Verifier les identifiants"""
        query = "SELECT * FROM utilisateurs WHERE email = ? AND actif = 1"
        user = db.fetch_one(query, (email,))

        if user and bcrypt.checkpw(mot_de_passe.encode(), user[4].encode()):
            db.execute_query(
                "UPDATE utilisateurs SET dernier_login = CURRENT_TIMESTAMP WHERE id = ?",
                (user[0],)
            )
            logger.info(f"Connexion reussie : {email}")
            return user

        logger.warning(f"Echec connexion pour : {email}")
        return None

    @staticmethod
    def obtenir_tous():
        """Liste de tous les utilisateurs"""
        return db.fetch_all("SELECT * FROM utilisateurs ORDER BY nom")

    @staticmethod
    def modifier_role(user_id, nouveau_role):
        """Changer le role d'un utilisateur"""
        # Vérifier si l'utilisateur est super-admin
        if Utilisateur.est_super_admin(user_id):
            return False, "Impossible de changer le rôle du Super-Admin."

        # Empêcher la promotion vers 'patron' si un super-admin existe déjà
        if nouveau_role == 'patron':
            count_super_admin = db.fetch_one("SELECT COUNT(*) FROM utilisateurs WHERE super_admin = 1")
            if count_super_admin and count_super_admin[0] > 0:
                return False, "Un super-admin existe déjà. Le rôle 'patron' ne peut être attribué qu'une seule fois."

        # Mettre à jour le rôle et potentiellement le flag super_admin
        super_admin_flag = 1 if nouveau_role == 'patron' else 0
        result = db.execute_query(
            "UPDATE utilisateurs SET role = ?, super_admin = ? WHERE id = ?",
            (nouveau_role, super_admin_flag, user_id)
        )
        if result:
            logger.info(f"Role modifie pour utilisateur {user_id} : {nouveau_role}")
            return True, "Rôle modifié avec succès."
        return False, "Erreur lors de la modification du rôle."

    @staticmethod
    def changer_statut(user_id, actif):
        """Activer/Desactiver un utilisateur"""
        result = db.execute_query(
            "UPDATE utilisateurs SET actif = ? WHERE id = ?",
            (1 if actif else 0, user_id)
        )
        if result:
            logger.info(f"Statut utilisateur {user_id} : {'actif' if actif else 'inactif'}")
        return result

    @staticmethod
    def modifier_mot_de_passe(user_id, nouveau_mot_de_passe):
        """Modifier le mot de passe d'un utilisateur (admin)"""
        import bcrypt
        hashed = bcrypt.hashpw(nouveau_mot_de_passe.encode('utf-8'), bcrypt.gensalt())
        result = db.execute_query(
            "UPDATE utilisateurs SET mot_de_passe = ? WHERE id = ?",
            (hashed.decode('utf-8'), user_id)
        )
        if result:
            logger.info(f"Mot de passe modifié pour utilisateur {user_id}")
        return result

    @staticmethod
    def logger_action(user_id, action, details=""):
        """Enregistrer une action dans les logs"""
        query = """
            INSERT INTO logs_actions (utilisateur_id, action, details)
            VALUES (?, ?, ?)
        """
        try:
            if user_id:
                db.execute_query(query, (user_id, action, details))
        except Exception as e:
            logger.error(f"Erreur log action: {e}")
