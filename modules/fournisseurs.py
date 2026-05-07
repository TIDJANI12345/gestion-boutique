"""
Gestion des fournisseurs et commandes d'approvisionnement.
"""
from database import db
from modules.logger import get_logger

logger = get_logger('fournisseurs')


class Fournisseur:

    @staticmethod
    def lister():
        return db.fetch_all(
            "SELECT * FROM fournisseurs WHERE actif = 1 ORDER BY nom"
        )

    @staticmethod
    def obtenir(fournisseur_id: int):
        return db.fetch_one(
            "SELECT * FROM fournisseurs WHERE id = ?", (fournisseur_id,)
        )

    @staticmethod
    def creer(nom, telephone='', email='', adresse='', contact_nom=''):
        db.execute_query(
            """INSERT INTO fournisseurs (nom, telephone, email, adresse, contact_nom)
               VALUES (?, ?, ?, ?, ?)""",
            (nom, telephone, email, adresse, contact_nom)
        )
        logger.info(f"Fournisseur créé : {nom}")

    @staticmethod
    def modifier(fournisseur_id, nom, telephone='', email='', adresse='', contact_nom=''):
        db.execute_query(
            """UPDATE fournisseurs SET nom=?, telephone=?, email=?, adresse=?, contact_nom=?
               WHERE id=?""",
            (nom, telephone, email, adresse, contact_nom, fournisseur_id)
        )

    @staticmethod
    def supprimer(fournisseur_id):
        db.execute_query(
            "UPDATE fournisseurs SET actif = 0 WHERE id = ?", (fournisseur_id,)
        )


class CommandeFournisseur:

    STATUTS = {
        'en_attente':  'En attente',
        'envoyee':     'Envoyée',
        'recue':       'Reçue',
        'partielle':   'Partiellement reçue',
        'annulee':     'Annulée',
    }

    @staticmethod
    def lister(fournisseur_id=None):
        if fournisseur_id:
            return db.fetch_all(
                """SELECT c.*, f.nom as fournisseur_nom
                   FROM commandes_fournisseurs c
                   JOIN fournisseurs f ON f.id = c.fournisseur_id
                   WHERE c.fournisseur_id = ?
                   ORDER BY c.date_commande DESC""",
                (fournisseur_id,)
            )
        return db.fetch_all(
            """SELECT c.*, f.nom as fournisseur_nom
               FROM commandes_fournisseurs c
               JOIN fournisseurs f ON f.id = c.fournisseur_id
               ORDER BY c.date_commande DESC"""
        )

    @staticmethod
    def obtenir(commande_id: int):
        return db.fetch_one(
            """SELECT c.*, f.nom as fournisseur_nom
               FROM commandes_fournisseurs c
               JOIN fournisseurs f ON f.id = c.fournisseur_id
               WHERE c.id = ?""",
            (commande_id,)
        )

    @staticmethod
    def obtenir_details(commande_id: int):
        return db.fetch_all(
            """SELECT d.*, p.nom as produit_nom, p.code_barre, p.stock_actuel
               FROM details_commandes_fournisseurs d
               JOIN produits p ON p.id = d.produit_id
               WHERE d.commande_id = ?""",
            (commande_id,)
        )

    @staticmethod
    def creer(fournisseur_id, lignes: list, date_livraison=None, notes='') -> int:
        """
        Crée une commande avec ses lignes.
        lignes = [{'produit_id': x, 'quantite': x, 'prix_unitaire': x}, ...]
        Retourne l'id de la commande créée.
        """
        total = sum(l['quantite'] * l.get('prix_unitaire', 0) for l in lignes)
        commande_id = db.execute_query(
            """INSERT INTO commandes_fournisseurs
               (fournisseur_id, date_livraison_prevue, total, notes)
               VALUES (?, ?, ?, ?)""",
            (fournisseur_id, date_livraison, total, notes)
        )
        for l in lignes:
            db.execute_query(
                """INSERT INTO details_commandes_fournisseurs
                   (commande_id, produit_id, quantite_commandee, prix_unitaire)
                   VALUES (?, ?, ?, ?)""",
                (commande_id, l['produit_id'], l['quantite'], l.get('prix_unitaire', 0))
            )
        logger.info(f"Commande fournisseur #{commande_id} créée ({len(lignes)} produits)")
        return commande_id

    @staticmethod
    def recevoir(commande_id: int, receptions: list):
        """
        Enregistre la réception des marchandises et met à jour le stock.
        receptions = [{'detail_id': x, 'quantite_recue': x}, ...]
        """
        for r in receptions:
            detail = db.fetch_one(
                "SELECT * FROM details_commandes_fournisseurs WHERE id = ?",
                (r['detail_id'],)
            )
            if not detail:
                continue
            qte = r['quantite_recue']
            if qte <= 0:
                continue
            db.execute_query(
                "UPDATE details_commandes_fournisseurs SET quantite_recue = quantite_recue + ? WHERE id = ?",
                (qte, r['detail_id'])
            )
            db.execute_query(
                "UPDATE produits SET stock_actuel = stock_actuel + ? WHERE id = ?",
                (qte, detail['produit_id'])
            )

        # Mettre à jour le statut de la commande
        details = db.fetch_all(
            "SELECT quantite_commandee, quantite_recue FROM details_commandes_fournisseurs WHERE commande_id = ?",
            (commande_id,)
        )
        total_cmd = sum(d['quantite_commandee'] for d in details)
        total_recu = sum(d['quantite_recue'] for d in details)

        if total_recu == 0:
            statut = 'envoyee'
        elif total_recu >= total_cmd:
            statut = 'recue'
        else:
            statut = 'partielle'

        db.execute_query(
            "UPDATE commandes_fournisseurs SET statut = ? WHERE id = ?",
            (statut, commande_id)
        )
        logger.info(f"Réception commande #{commande_id} : {total_recu}/{total_cmd} articles — statut={statut}")
