"""
Module de gestion de l'ardoise (crédit client).
"""
from datetime import datetime
from database import db
from modules.logger import get_logger

logger = get_logger('ardoise')


def creer_ardoise(client_id: int, montant: float, vente_id: int = None,
                  notes: str = None, date_echeance: str = None) -> int | None:
    """
    Créer une ligne d'ardoise pour un client.
    Returns: ardoise_id ou None
    """
    if montant <= 0:
        logger.warning(f"creer_ardoise refusé : montant={montant}")
        return None
    if not client_id:
        logger.warning("creer_ardoise refusé : client_id requis")
        return None

    ardoise_id = db.execute_query(
        """INSERT INTO ardoise
           (client_id, vente_id, montant_initial, montant_restant, notes, date_echeance, statut)
           VALUES (?, ?, ?, ?, ?, ?, 'en_cours')""",
        (client_id, vente_id, montant, montant, notes, date_echeance)
    )
    if ardoise_id:
        logger.info(f"Ardoise créée : ID={ardoise_id}, client={client_id}, montant={montant}")
    return ardoise_id


def encaisser(ardoise_id: int, montant: float, mode: str = 'especes',
              reference: str = None, notes: str = None,
              session_id: int = None) -> tuple[bool, str, int | None]:
    """
    Encaisser un paiement sur une ardoise (partiel ou total).
    Returns: (succes, message, encaissement_id)
    """
    ardoise = db.fetch_one("SELECT * FROM ardoise WHERE id = ?", (ardoise_id,))
    if not ardoise:
        return False, "Ardoise introuvable.", None
    if ardoise['statut'] == 'solde':
        return False, "Cette ardoise est déjà soldée.", None

    restant = ardoise['montant_restant']
    if montant <= 0:
        return False, "Montant invalide.", None
    if montant > restant:
        montant = restant

    enc_id = db.execute_query(
        """INSERT INTO encaissements_ardoise
           (ardoise_id, montant, mode_paiement, reference, notes, id_session)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (ardoise_id, montant, mode, reference, notes, session_id)
    )

    nouveau_restant = restant - montant
    nouveau_statut = 'solde' if nouveau_restant <= 0.01 else 'partiel'

    db.execute_query(
        "UPDATE ardoise SET montant_restant = ?, statut = ? WHERE id = ?",
        (max(0, nouveau_restant), nouveau_statut, ardoise_id)
    )

    logger.info(f"Encaissement ardoise {ardoise_id}: {montant}, restant={nouveau_restant}")
    if nouveau_statut == 'solde':
        return True, "Ardoise soldée.", enc_id
    return True, f"Paiement enregistré. Reste : {nouveau_restant:,.0f} FCFA", enc_id


def solde_client(client_id: int) -> float:
    """Retourne le total dû par un client (toutes ardoises en cours)."""
    result = db.fetch_one(
        """SELECT COALESCE(SUM(montant_restant), 0) as total
           FROM ardoise WHERE client_id = ? AND statut != 'solde'""",
        (client_id,)
    )
    return float(result['total']) if result else 0.0


def liste_ardoise_client(client_id: int) -> list:
    """Toutes les ardoises d'un client avec le détail des encaissements."""
    rows = db.fetch_all(
        """SELECT a.*, v.numero_vente
           FROM ardoise a
           LEFT JOIN ventes v ON a.vente_id = v.id
           WHERE a.client_id = ?
           ORDER BY a.date_creation DESC""",
        (client_id,)
    )
    return [dict(r) for r in rows] if rows else []


def encaissements_ardoise(ardoise_id: int) -> list:
    """Historique des paiements d'une ardoise."""
    rows = db.fetch_all(
        "SELECT * FROM encaissements_ardoise WHERE ardoise_id = ? ORDER BY date_encaissement DESC",
        (ardoise_id,)
    )
    return [dict(r) for r in rows] if rows else []


def liste_debiteurs() -> list:
    """
    Tous les clients ayant une ardoise en cours, triés par solde décroissant.
    Returns: list of dicts {client_id, client_nom, client_telephone, nb_ardoises, solde_total}
    """
    rows = db.fetch_all(
        """SELECT c.id as client_id, c.nom as client_nom,
                  c.telephone as client_telephone,
                  COUNT(a.id) as nb_ardoises,
                  SUM(a.montant_restant) as solde_total
           FROM ardoise a
           JOIN clients c ON a.client_id = c.id
           WHERE a.statut != 'solde'
           GROUP BY c.id
           ORDER BY solde_total DESC"""
    )
    return [dict(r) for r in rows] if rows else []


def stats_ardoise() -> dict:
    """Statistiques globales de l'ardoise."""
    total = db.fetch_one(
        "SELECT COALESCE(SUM(montant_restant), 0) as t FROM ardoise WHERE statut != 'solde'"
    )
    nb = db.fetch_one(
        "SELECT COUNT(DISTINCT client_id) as n FROM ardoise WHERE statut != 'solde'"
    )
    return {
        'total_du': float(total['t']) if total else 0.0,
        'nb_debiteurs': int(nb['n']) if nb else 0,
    }
