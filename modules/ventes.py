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

        stock_actuel = produit['stock_actuel']
        if stock_actuel < quantite:
            logger.warning(f"Stock insuffisant pour produit {produit_id} : {stock_actuel} < {quantite}")
            return False

        prix_unitaire = produit['prix_vente']
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
        query = "SELECT SUM(sous_total) as total FROM details_ventes WHERE vente_id = ?"
        result = db.fetch_one(query, (vente_id,))
        total = result['total'] if result and result['total'] else 0

        query_update = "UPDATE ventes SET total = ? WHERE id = ?"
        db.execute_query(query_update, (total, vente_id))
        return total

    @staticmethod
    def obtenir_details_vente(vente_id):
        """Obtenir les details d'une vente"""
        query = """
            SELECT dv.id, p.nom, dv.quantite, dv.prix_unitaire, dv.sous_total,
                   p.code_barre, COALESCE(dv.is_prix_gros, 0) as is_prix_gros,
                   COALESCE(p.unite_mesure, 'pièce') as unite_mesure
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
    def obtenir_ventes_annulees(date_debut=None, date_fin=None, utilisateur_id=None):
        """Retourne uniquement les ventes annulées (pour UI annulation)."""
        base = "SELECT v.*, u.nom as caissier_nom FROM ventes v LEFT JOIN utilisateurs u ON v.utilisateur_id = u.id WHERE v.statut = 'annulee'"
        params = []
        if date_debut and date_fin:
            base += " AND DATE(v.date_vente) BETWEEN ? AND ?"
            params += [date_debut, date_fin]
        if utilisateur_id:
            base += " AND v.utilisateur_id = ?"
            params.append(utilisateur_id)
        base += " ORDER BY v.deleted_at DESC"
        return db.fetch_all(base, tuple(params)) if params else db.fetch_all(base)

    @staticmethod
    def obtenir_toutes_ventes(date_debut=None, date_fin=None, utilisateur_id=None):
        """Obtenir toutes les ventes actives (hors annulées)."""
        base = "SELECT * FROM ventes WHERE statut != 'annulee'"
        params = []
        if date_debut and date_fin:
            base += " AND date_vente BETWEEN ? AND ?"
            params += [date_debut, date_fin]
        if utilisateur_id is not None:
            base += " AND utilisateur_id = ?"
            params.append(utilisateur_id)
        base += " ORDER BY date_vente DESC"
        return db.fetch_all(base, tuple(params)) if params else db.fetch_all(base)

    @staticmethod
    def supprimer_ligne_vente(detail_id, vente_id):
        """Supprimer une ligne d'une vente"""
        query = "SELECT produit_id, quantite FROM details_ventes WHERE id = ?"
        detail = db.fetch_one(query, (detail_id,))

        if detail:
            produit_id = detail['produit_id']
            quantite = detail['quantite']

            query_delete = "DELETE FROM details_ventes WHERE id = ?"
            if db.execute_query(query_delete, (detail_id,)):
                produit = Produit.obtenir_par_id(produit_id)
                if produit:
                    nouveau_stock = produit['stock_actuel'] + quantite
                    Produit.mettre_a_jour_stock(produit_id, nouveau_stock, "Annulation ligne")

                Vente.calculer_total(vente_id)
                logger.info(f"Ligne {detail_id} supprimee de vente {vente_id}")
                return True

        return False

    @staticmethod
    def annuler_vente(vente_id, user_id=None, motif=None):
        """Annulation douce d'une vente : restaure le stock, marque statut='annulee'."""
        vente = db.fetch_one("SELECT * FROM ventes WHERE id = ? AND statut != 'annulee'", (vente_id,))
        if not vente:
            return False

        details = db.fetch_all(
            "SELECT produit_id, quantite FROM details_ventes WHERE vente_id = ?", (vente_id,)
        )
        for d in details:
            produit = Produit.obtenir_par_id(d['produit_id'])
            if produit:
                Produit.mettre_a_jour_stock(
                    d['produit_id'], produit['stock_actuel'] + d['quantite'], "Annulation vente"
                )

        from datetime import datetime as _dt
        result = db.execute_query(
            """UPDATE ventes
               SET statut = 'annulee', deleted_at = ?, motif_annulation = ?
               WHERE id = ?""",
            (_dt.now().strftime("%Y-%m-%d %H:%M:%S"), motif, vente_id)
        )
        if result:
            logger.info(f"Vente {vente_id} annulée (soft-delete)")
            if user_id:
                from modules.utilisateurs import Utilisateur
                Utilisateur.logger_action(user_id, 'annulation_vente',
                                          f"Vente {vente_id} annulée — {motif or ''}")
        return bool(result)

    @staticmethod
    def obtenir_ventes_du_jour():
        """Obtenir les ventes actives du jour."""
        aujourd_hui = datetime.now().strftime("%Y-%m-%d")
        query = "SELECT * FROM ventes WHERE DATE(date_vente) = ? AND statut != 'annulee' ORDER BY date_vente DESC"
        return db.fetch_all(query, (aujourd_hui,))

    @staticmethod
    def obtenir_chiffre_affaires(date_debut=None, date_fin=None):
        """Calculer le chiffre d'affaires (ventes actives uniquement)."""
        if date_debut and date_fin:
            query = "SELECT SUM(total) FROM ventes WHERE statut != 'annulee' AND date_vente BETWEEN ? AND ?"
            result = db.fetch_one(query, (date_debut, date_fin))
        else:
            query = "SELECT SUM(total) FROM ventes WHERE statut != 'annulee'"
            result = db.fetch_one(query)

        return result[0] if result and result[0] else 0
