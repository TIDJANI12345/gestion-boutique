"""
Gestion des sessions de caisse — ouverture, clôture Z, rapport X.
"""
import hashlib
from datetime import datetime
from database import db
from modules.logger import get_logger

logger = get_logger('sessions')


def session_actuelle() -> dict | None:
    """Retourne la session ouverte ou None."""
    return db.fetch_one(
        "SELECT * FROM sessions_caisse WHERE statut = 'ouverte' ORDER BY id DESC LIMIT 1"
    )


def ouvrir_session(id_caissier: int, fond: int, id_caisse: str = 'C1') -> tuple[bool, str, int | None]:
    """
    Ouvrir une nouvelle session de caisse.
    Refuse si une session est déjà ouverte.

    Returns: (succes, message, session_id)
    """
    if session_actuelle():
        return False, "Une session est déjà ouverte. Clôturez-la d'abord.", None

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    session_id = db.execute_query(
        """INSERT INTO sessions_caisse
           (id_caisse, id_caissier, date_ouverture, fond_ouverture, statut)
           VALUES (?, ?, ?, ?, 'ouverte')""",
        (id_caisse, id_caissier, now, fond)
    )
    if session_id:
        logger.info(f"Session ouverte: ID={session_id}, caissier={id_caissier}, fond={fond}")
        return True, "Session ouverte.", session_id
    return False, "Erreur lors de l'ouverture de session.", None


def _calculer_totaux(session_id: int) -> dict:
    """Calculer les totaux de la session depuis les ventes et paiements."""
    # Ventes actives (non annulées) liées à cette session
    ventes = db.fetch_all(
        "SELECT id, total FROM ventes WHERE id_session = ? AND statut != 'annulee'",
        (session_id,)
    )
    vente_ids = [v['id'] for v in ventes]
    nb_ventes = len(vente_ids)
    total_general = sum(v['total'] for v in ventes)

    # Ventes annulées
    annulees = db.fetch_all(
        "SELECT COALESCE(SUM(total), 0) as s FROM ventes WHERE id_session = ? AND statut = 'annulee'",
        (session_id,)
    )
    total_annule = int(annulees[0]['s']) if annulees else 0

    # Totaux par mode de paiement
    total_especes = 0
    total_mobile = 0
    modes_mobile = ('orange_money', 'mtn_momo', 'moov_money', 'wave',
                    'mobile_money', 'virement', 'carte', 'cheque')

    if vente_ids:
        placeholders = ','.join('?' * len(vente_ids))
        paiements = db.fetch_all(
            f"SELECT mode, COALESCE(SUM(montant), 0) as s "
            f"FROM paiements WHERE vente_id IN ({placeholders}) GROUP BY mode",
            vente_ids
        )
        for p in paiements:
            if p['mode'] == 'especes':
                total_especes += int(p['s'])
            elif p['mode'] in modes_mobile:
                total_mobile += int(p['s'])
            # mixte : déjà décomposé par ligne

    return {
        'nb_ventes': nb_ventes,
        'total_general': int(total_general),
        'total_especes': total_especes,
        'total_mobile': total_mobile,
        'total_credit': 0,   # ardoise — implémenté en Phase J5
        'total_annule': total_annule,
    }


def rapport_x(session_id: int | None = None) -> dict | None:
    """
    Rapport X : état intermédiaire sans clôturer.
    Utilise la session ouverte si session_id non fourni.
    """
    if session_id is None:
        s = session_actuelle()
        if not s:
            return None
        session_id = s['id']
    else:
        s = db.fetch_one("SELECT * FROM sessions_caisse WHERE id = ?", (session_id,))
        if not s:
            return None

    totaux = _calculer_totaux(session_id)
    return {
        'session': dict(s),
        **totaux,
    }


def cloturer_session(fond_declare: int) -> tuple[bool, str, dict | None]:
    """
    Clôture Z : calcule les totaux, génère le hash, ferme la session.

    Returns: (succes, message, rapport_dict)
    """
    s = session_actuelle()
    if not s:
        return False, "Aucune session ouverte.", None

    session_id = s['id']
    totaux = _calculer_totaux(session_id)

    fond_calcule = totaux['total_especes'] + s['fond_ouverture']
    ecart = fond_declare - fond_calcule

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Hash Z = SHA256(date_ouverture + date_cloture + total_especes + fond_ouverture + id_caissier)
    raw = (
        f"{s['date_ouverture']}"
        f"{now}"
        f"{totaux['total_especes']}"
        f"{s['fond_ouverture']}"
        f"{s['id_caissier']}"
    )
    hash_z = hashlib.sha256(raw.encode()).hexdigest()[:16].upper()

    db.execute_query(
        """UPDATE sessions_caisse SET
               date_cloture = ?,
               fond_cloture_declare = ?,
               fond_cloture_calcule = ?,
               ecart = ?,
               total_especes = ?,
               total_mobile = ?,
               total_credit = ?,
               total_annule = ?,
               nb_ventes = ?,
               statut = 'cloturee',
               hash_cloture = ?
           WHERE id = ?""",
        (now, fond_declare, fond_calcule, ecart,
         totaux['total_especes'], totaux['total_mobile'],
         totaux['total_credit'], totaux['total_annule'],
         totaux['nb_ventes'], hash_z, session_id)
    )

    rapport = {
        'session_id': session_id,
        'id_caisse': s['id_caisse'],
        'date_ouverture': s['date_ouverture'],
        'date_cloture': now,
        'fond_ouverture': s['fond_ouverture'],
        'fond_cloture_declare': fond_declare,
        'fond_cloture_calcule': fond_calcule,
        'ecart': ecart,
        'hash_cloture': hash_z,
        **totaux,
    }

    logger.info(f"Session {session_id} clôturée. Hash={hash_z}, écart={ecart}")
    return True, "Session clôturée.", rapport


def historique_clotures(limit: int = 30) -> list:
    """Liste des sessions clôturées pour l'audit."""
    rows = db.fetch_all(
        """SELECT sc.*, u.nom || ' ' || u.prenom as caissier_nom
           FROM sessions_caisse sc
           LEFT JOIN utilisateurs u ON sc.id_caissier = u.id
           WHERE sc.statut = 'cloturee'
           ORDER BY sc.date_cloture DESC
           LIMIT ?""",
        (limit,)
    )
    return [dict(r) for r in rows] if rows else []
