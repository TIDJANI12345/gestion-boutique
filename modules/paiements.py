"""
Module de gestion des paiements
"""
from database import db
from modules.logger import get_logger

logger = get_logger('paiements')

# Labels natifs (fallback si config non chargeable)
MODE_LABELS = {
    'especes':      'Espèces',
    'mobile_money': 'Mobile Money',
    'virement':     'Virement bancaire',
    'cheque':       'Chèque',
    'mixte':        'Paiement mixte',
    'orange_money': 'Orange Money',
    'mtn_momo':     'MTN MoMo',
    'moov_money':   'Moov Money',
    'wave':         'Wave',
}

# Modes Mobile Money natifs (fallback)
MODES_MOBILE_NATIFS = {'mobile_money', 'orange_money', 'mtn_momo', 'moov_money', 'wave'}


def _charger_type_map() -> dict:
    """Retourne {mode_key: type} depuis la config des modes de paiement."""
    try:
        from ui.windows.parametres_paiement import charger_config_paiement
        config = charger_config_paiement()
        return {k: v.get('type', 'autre') for k, v in config.items()}
    except Exception:
        return {}


def _get_label(mode: str) -> str:
    """Retourne le label d'affichage pour un mode, config ou fallback."""
    try:
        from ui.windows.parametres_paiement import charger_config_paiement
        config = charger_config_paiement()
        if mode in config:
            return config[mode]['label']
    except Exception:
        pass
    return MODE_LABELS.get(mode, mode)


def _get_type(mode: str, type_map: dict) -> str:
    """Retourne le type d'un mode avec fallback sur les natifs."""
    if mode in type_map:
        return type_map[mode]
    if mode in MODES_MOBILE_NATIFS:
        return 'mobile_money'
    if mode == 'especes':
        return 'especes'
    if mode == 'virement':
        return 'virement'
    if mode == 'cheque':
        return 'cheque'
    if mode == 'carte':
        return 'carte'
    return 'autre'


class Paiement:

    @staticmethod
    def enregistrer_paiement(vente_id, mode, montant, reference=None,
                             montant_recu=None, monnaie_rendue=None):
        """Enregistrer un paiement pour une vente"""
        query = """
            INSERT INTO paiements (vente_id, mode, montant, reference, montant_recu, monnaie_rendue)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        result = db.execute_query(
            query, (vente_id, mode, montant, reference, montant_recu, monnaie_rendue)
        )
        if result:
            logger.info(f"Paiement enregistre: vente={vente_id}, mode={mode}, montant={montant}")
        return result

    @staticmethod
    def enregistrer_paiement_mixte(vente_id, paiements_list):
        """Enregistrer plusieurs paiements pour une vente (paiement mixte)

        paiements_list: liste de dicts avec cles:
            mode, montant, reference, montant_recu, monnaie_rendue
        """
        queries = []
        for p in paiements_list:
            queries.append((
                """INSERT INTO paiements (vente_id, mode, montant, reference, montant_recu, monnaie_rendue)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (vente_id, p['mode'], p['montant'],
                 p.get('reference'), p.get('montant_recu'), p.get('monnaie_rendue'))
            ))
        result = db.execute_transaction(queries)
        if result:
            logger.info(f"Paiement mixte enregistre: vente={vente_id}, {len(paiements_list)} paiements")
        return result

    @staticmethod
    def obtenir_paiements_vente(vente_id):
        """Obtenir les paiements d'une vente"""
        query = """
            SELECT id, vente_id, mode, montant, reference, montant_recu, monnaie_rendue, date_paiement
            FROM paiements WHERE vente_id = ?
        """
        return db.fetch_all(query, (vente_id,))

    @staticmethod
    def total_par_mode_jour(date=None):
        """Totaux par mode de paiement pour une journee"""
        from datetime import datetime
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        query = """
            SELECT p.mode, SUM(p.montant) as total, COUNT(*) as nb
            FROM paiements p
            JOIN ventes v ON p.vente_id = v.id
            WHERE DATE(v.date_vente) = ?
            GROUP BY p.mode
        """
        return db.fetch_all(query, (date,))

    @staticmethod
    def rapport_caisse_jour(date=None):
        """Rapport de rapprochement de caisse"""
        from datetime import datetime
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        rapport = {
            'date': date,
            'total_especes': 0,
            'total_mobile_money': 0,
            'total_virement': 0,
            'total_cheque': 0,
            'total_mixte': 0,
            'total_autre': 0,
            'total_general': 0,
            'nb_transactions': 0,
            'details_par_mode': [],
        }

        type_map = _charger_type_map()
        totaux = Paiement.total_par_mode_jour(date)
        for mode, total, nb in totaux:
            rapport['details_par_mode'].append({
                'mode': mode,
                'label': _get_label(mode),
                'total': total,
                'nb': nb,
            })
            rapport['total_general'] += total
            rapport['nb_transactions'] += nb

            t = _get_type(mode, type_map)
            if t == 'especes':
                rapport['total_especes'] += total
            elif t == 'mobile_money':
                rapport['total_mobile_money'] += total
            elif t == 'virement':
                rapport['total_virement'] += total
            elif t == 'cheque':
                rapport['total_cheque'] += total
            elif mode == 'mixte':
                rapport['total_mixte'] += total
            elif t not in ('credit', 'mixte'):
                rapport['total_autre'] += total

        return rapport
