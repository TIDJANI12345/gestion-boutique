"""
Module de gestion des ventes
"""
from database import db
from datetime import datetime
from modules.produits import Produit
from modules.logger import get_logger
import random
import string

logger = get_logger('ventes')


class Vente:

    @staticmethod
    def generer_numero_vente():
        """Generer un numero de vente unique"""
        date_str = datetime.now().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"V{date_str}-{random_str}"

    @staticmethod
    def creer_vente(client="", utilisateur_id=None):
        """Creer une nouvelle vente"""
        numero_vente = Vente.generer_numero_vente()
        query = "INSERT INTO ventes (numero_vente, client, total, utilisateur_id) VALUES (?, ?, 0, ?)"
        vente_id = db.execute_query(query, (numero_vente, client, utilisateur_id))

        if vente_id:
            logger.info(f"Vente creee : ID={vente_id}, numero={numero_vente}, utilisateur={utilisateur_id}")
        return vente_id

    @staticmethod
    def ajouter_produit(vente_id, produit_id, quantite):
        """Ajouter un produit a une vente avec validation"""

        # Validation quantite
        if quantite <= 0:
            logger.warning(f"Quantite invalide : {quantite}")
            return False

        # Verifier le stock
        produit = Produit.obtenir_par_id(produit_id)
        if not produit:
            logger.warning(f"Produit introuvable : ID {produit_id}")
            return False

        stock_actuel = produit[5]
        if stock_actuel < quantite:
            logger.warning(f"Stock insuffisant pour produit {produit_id} : {stock_actuel} < {quantite}")
            return False

        prix_unitaire = produit[4]
        sous_total = prix_unitaire * quantite

        query = """
            INSERT INTO details_ventes (vente_id, produit_id, quantite, prix_unitaire, sous_total)
            VALUES (?, ?, ?, ?, ?)
        """
        if db.execute_query(query, (vente_id, produit_id, quantite, prix_unitaire, sous_total)):
            # Mettre a jour le stock
            nouveau_stock = stock_actuel - quantite
            Produit.mettre_a_jour_stock(produit_id, nouveau_stock, "Vente")

            # Mettre a jour le total de la vente
            Vente.calculer_total(vente_id)
            logger.info(f"Produit {produit_id} ajoute a vente {vente_id} (qte: {quantite})")
            return True

        return False

    @staticmethod
    def calculer_total(vente_id):
        """Calculer le total d'une vente"""
        query = "SELECT SUM(sous_total) FROM details_ventes WHERE vente_id = ?"
        result = db.fetch_one(query, (vente_id,))
        total = result[0] if result and result[0] else 0

        query_update = "UPDATE ventes SET total = ? WHERE id = ?"
        db.execute_query(query_update, (total, vente_id))
        return total

    @staticmethod
    def obtenir_details_vente(vente_id):
        """Obtenir les details d'une vente"""
        query = """
            SELECT dv.id, p.nom, dv.quantite, dv.prix_unitaire, dv.sous_total, p.code_barre
            FROM details_ventes dv
            JOIN produits p ON dv.produit_id = p.id
            WHERE dv.vente_id = ?
        """
        return db.fetch_all(query, (vente_id,))

    @staticmethod
    def obtenir_vente(vente_id):
        """Obtenir les informations d'une vente"""
        query = "SELECT * FROM ventes WHERE id = ?"
        return db.fetch_one(query, (vente_id,))

    @staticmethod
    def obtenir_toutes_ventes(date_debut=None, date_fin=None, utilisateur_id=None):
        """Obtenir toutes les ventes (avec filtre optionnel utilisateur)"""
        if date_debut and date_fin:
            if utilisateur_id is not None:
                query = "SELECT * FROM ventes WHERE date_vente BETWEEN ? AND ? AND utilisateur_id = ? ORDER BY date_vente DESC"
                return db.fetch_all(query, (date_debut, date_fin, utilisateur_id))
            else:
                query = "SELECT * FROM ventes WHERE date_vente BETWEEN ? AND ? ORDER BY date_vente DESC"
                return db.fetch_all(query, (date_debut, date_fin))
        else:
            if utilisateur_id is not None:
                query = "SELECT * FROM ventes WHERE utilisateur_id = ? ORDER BY date_vente DESC"
                return db.fetch_all(query, (utilisateur_id,))
            else:
                query = "SELECT * FROM ventes ORDER BY date_vente DESC"
                return db.fetch_all(query)

    @staticmethod
    def supprimer_ligne_vente(detail_id, vente_id):
        """Supprimer une ligne d'une vente"""
        query = "SELECT produit_id, quantite FROM details_ventes WHERE id = ?"
        detail = db.fetch_one(query, (detail_id,))

        if detail:
            produit_id, quantite = detail

            query_delete = "DELETE FROM details_ventes WHERE id = ?"
            if db.execute_query(query_delete, (detail_id,)):
                produit = Produit.obtenir_par_id(produit_id)
                if produit:
                    nouveau_stock = produit[5] + quantite
                    Produit.mettre_a_jour_stock(produit_id, nouveau_stock, "Annulation ligne")

                Vente.calculer_total(vente_id)
                logger.info(f"Ligne {detail_id} supprimee de vente {vente_id}")
                return True

        return False

    @staticmethod
    def annuler_vente(vente_id):
        """Annuler une vente complete"""
        query = "SELECT produit_id, quantite FROM details_ventes WHERE vente_id = ?"
        details = db.fetch_all(query, (vente_id,))

        for detail in details:
            produit_id, quantite = detail
            produit = Produit.obtenir_par_id(produit_id)
            if produit:
                nouveau_stock = produit[5] + quantite
                Produit.mettre_a_jour_stock(produit_id, nouveau_stock, "Annulation vente")

        query_details = "DELETE FROM details_ventes WHERE vente_id = ?"
        db.execute_query(query_details, (vente_id,))

        query_vente = "DELETE FROM ventes WHERE id = ?"
        result = db.execute_query(query_vente, (vente_id,))

        if result:
            logger.info(f"Vente {vente_id} annulee")
        return result

    @staticmethod
    def obtenir_ventes_du_jour():
        """Obtenir les ventes du jour"""
        aujourd_hui = datetime.now().strftime("%Y-%m-%d")
        query = "SELECT * FROM ventes WHERE DATE(date_vente) = ? ORDER BY date_vente DESC"
        return db.fetch_all(query, (aujourd_hui,))

    @staticmethod
    def obtenir_chiffre_affaires(date_debut=None, date_fin=None):
        """Calculer le chiffre d'affaires"""
        if date_debut and date_fin:
            query = "SELECT SUM(total) FROM ventes WHERE date_vente BETWEEN ? AND ?"
            result = db.fetch_one(query, (date_debut, date_fin))
        else:
            query = "SELECT SUM(total) FROM ventes"
            result = db.fetch_one(query)

        return result[0] if result and result[0] else 0
