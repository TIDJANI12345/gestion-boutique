"""
Module de gestion des clients
"""
from database import db
from modules.logger import get_logger

logger = get_logger('clients')


class Client:

    @staticmethod
    def ajouter(nom, telephone=None, email=None, notes=None):
        """Ajouter un nouveau client. Retourne client_id ou None."""
        if not nom or not nom.strip():
            logger.warning("Ajout refuse : nom vide")
            return None

        query = """
            INSERT INTO clients (nom, telephone, email, notes)
            VALUES (?, ?, ?, ?)
        """
        result = db.execute_query(query, (nom.strip(), telephone, email, notes))
        if result:
            logger.info(f"Client ajoute : '{nom}' (ID {result})")
            return result
        return None

    @staticmethod
    def modifier(client_id, nom, telephone=None, email=None, notes=None):
        """Modifier un client existant. Retourne True/False."""
        if not nom or not nom.strip():
            logger.warning("Modification refusee : nom vide")
            return False

        query = """
            UPDATE clients
            SET nom = ?, telephone = ?, email = ?, notes = ?
            WHERE id = ?
        """
        result = db.execute_query(query, (nom.strip(), telephone, email, notes, client_id))
        if result:
            logger.info(f"Client modifie : ID {client_id}")
            return True
        return False

    @staticmethod
    def supprimer(client_id):
        """Supprimer un client. Met ventes.client_id a NULL."""
        db.execute_query("UPDATE ventes SET client_id = NULL WHERE client_id = ?", (client_id,))
        result = db.execute_query("DELETE FROM clients WHERE id = ?", (client_id,))
        if result:
            logger.info(f"Client supprime : ID {client_id}")
            return True
        return False

    @staticmethod
    def obtenir_par_id(client_id):
        """Obtenir un client par son ID"""
        return db.fetch_one("SELECT * FROM clients WHERE id = ?", (client_id,))

    @staticmethod
    def obtenir_tous():
        """Obtenir tous les clients"""
        return db.fetch_all("SELECT * FROM clients ORDER BY nom ASC")

    @staticmethod
    def rechercher(terme):
        """Rechercher des clients par nom, telephone ou email"""
        t = f"%{terme}%"
        return db.fetch_all(
            "SELECT * FROM clients WHERE nom LIKE ? OR telephone LIKE ? OR email LIKE ? ORDER BY nom ASC",
            (t, t, t)
        )

    @staticmethod
    def rechercher_filtre(terme="", limit=50, offset=0):
        """Rechercher des clients avec pagination"""
        if terme:
            t = f"%{terme}%"
            return db.fetch_all(
                "SELECT * FROM clients WHERE nom LIKE ? OR telephone LIKE ? OR email LIKE ? "
                "ORDER BY nom ASC LIMIT ? OFFSET ?",
                (t, t, t, limit, offset)
            )
        return db.fetch_all(
            "SELECT * FROM clients ORDER BY nom ASC LIMIT ? OFFSET ?",
            (limit, offset)
        )

    @staticmethod
    def compter_filtre(terme=""):
        """Compter les clients correspondant au filtre"""
        if terme:
            t = f"%{terme}%"
            result = db.fetch_one(
                "SELECT COUNT(*) FROM clients WHERE nom LIKE ? OR telephone LIKE ? OR email LIKE ?",
                (t, t, t)
            )
        else:
            result = db.fetch_one("SELECT COUNT(*) FROM clients")
        return result[0] if result else 0

    # --- Historique ---

    @staticmethod
    def obtenir_historique_achats(client_id, limit=50, offset=0):
        """Obtenir l'historique des achats d'un client"""
        return db.fetch_all(
            "SELECT id, numero_vente, date_vente, total, statut "
            "FROM ventes WHERE client_id = ? AND deleted_at IS NULL "
            "ORDER BY date_vente DESC LIMIT ? OFFSET ?",
            (client_id, limit, offset)
        )

    @staticmethod
    def compter_achats(client_id):
        """Compter le nombre d'achats d'un client"""
        result = db.fetch_one(
            "SELECT COUNT(*) FROM ventes WHERE client_id = ? AND deleted_at IS NULL",
            (client_id,)
        )
        return result[0] if result else 0

    @staticmethod
    def calculer_total_achats(client_id):
        """Calculer le total des achats d'un client"""
        result = db.fetch_one(
            "SELECT COALESCE(SUM(total), 0) FROM ventes WHERE client_id = ? AND deleted_at IS NULL",
            (client_id,)
        )
        return result[0] if result else 0.0

    # --- Fidelite ---

    @staticmethod
    def ajouter_points(client_id, montant_vente):
        """Ajouter des points de fidelite apres un achat. Retourne les points gagnes."""
        fidelite_active = db.get_parametre('fidelite_active', '1')
        if fidelite_active != '1':
            return 0

        try:
            points_par_fcfa = int(db.get_parametre('fidelite_points_par_fcfa', '1000'))
        except (ValueError, TypeError):
            points_par_fcfa = 1000

        if points_par_fcfa <= 0:
            return 0

        points_gagnes = int(montant_vente // points_par_fcfa)
        if points_gagnes > 0:
            db.execute_query(
                "UPDATE clients SET points_fidelite = points_fidelite + ?, "
                "total_achats = total_achats + ?, nombre_achats = nombre_achats + 1 "
                "WHERE id = ?",
                (points_gagnes, montant_vente, client_id)
            )
            logger.info(f"Client {client_id}: +{points_gagnes} points fidelite")
        else:
            db.execute_query(
                "UPDATE clients SET total_achats = total_achats + ?, "
                "nombre_achats = nombre_achats + 1 WHERE id = ?",
                (montant_vente, client_id)
            )
        return points_gagnes

    @staticmethod
    def obtenir_points(client_id):
        """Obtenir les points de fidelite d'un client"""
        result = db.fetch_one("SELECT points_fidelite FROM clients WHERE id = ?", (client_id,))
        return result[0] if result else 0

    @staticmethod
    def calculer_remise_fidelite(client_id):
        """Calculer la remise applicable. Retourne (remise_pct, points_a_utiliser) ou (0, 0)."""
        try:
            seuil = int(db.get_parametre('fidelite_remise_seuil', '100'))
            remise_pct = int(db.get_parametre('fidelite_remise_pct', '5'))
        except (ValueError, TypeError):
            return 0, 0

        points = Client.obtenir_points(client_id)
        if points >= seuil:
            return remise_pct, seuil
        return 0, 0

    @staticmethod
    def utiliser_points(client_id, points):
        """Utiliser des points de fidelite. Retourne True si succes."""
        points_actuels = Client.obtenir_points(client_id)
        if points_actuels < points:
            return False

        result = db.execute_query(
            "UPDATE clients SET points_fidelite = points_fidelite - ? WHERE id = ?",
            (points, client_id)
        )
        if result:
            logger.info(f"Client {client_id}: -{points} points utilises")
            return True
        return False

    # --- Utilitaire ---

    @staticmethod
    def obtenir_clients_avec_telephone():
        """Obtenir les clients ayant un telephone (pour SMS/WhatsApp)"""
        return db.fetch_all(
            "SELECT * FROM clients WHERE telephone IS NOT NULL AND telephone != '' ORDER BY nom ASC"
        )
