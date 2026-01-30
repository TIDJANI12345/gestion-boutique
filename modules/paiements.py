"""
Module de gestion des paiements
"""
from database import db
from modules.logger import get_logger

logger = get_logger('paiements')

# Labels d'affichage pour les modes de paiement
MODE_LABELS = {
    'especes': 'Especes',
    'orange_money': 'Orange Money',
    'mtn_momo': 'MTN MoMo',
    'moov_money': 'Moov Money',
}


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
            'total_orange_money': 0,
            'total_mtn_momo': 0,
            'total_moov_money': 0,
            'total_general': 0,
            'nb_transactions': 0,
            'details_par_mode': [],
        }

        totaux = Paiement.total_par_mode_jour(date)
        for mode, total, nb in totaux:
            rapport['details_par_mode'].append({
                'mode': mode,
                'label': MODE_LABELS.get(mode, mode),
                'total': total,
                'nb': nb,
            })
            rapport['total_general'] += total
            rapport['nb_transactions'] += nb

            if mode == 'especes':
                rapport['total_especes'] = total
            elif mode == 'orange_money':
                rapport['total_orange_money'] = total
            elif mode == 'mtn_momo':
                rapport['total_mtn_momo'] = total
            elif mode == 'moov_money':
                rapport['total_moov_money'] = total

        return rapport
