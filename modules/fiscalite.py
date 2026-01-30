"""
Module de gestion fiscale - TVA et devises
"""
from database import db
from modules.logger import get_logger

logger = get_logger('fiscalite')


class Fiscalite:

    @staticmethod
    def tva_active():
        """Verifier si la TVA est activee"""
        return db.get_parametre('tva_active', '0') == '1'

    @staticmethod
    def taux_tva_defaut():
        """Obtenir le taux de TVA par defaut"""
        try:
            return float(db.get_parametre('tva_taux_defaut', '18'))
        except ValueError:
            return 18.0

    @staticmethod
    def calculer_tva(montant_ttc, taux=None):
        """Calculer la decomposition HT/TVA/TTC a partir du prix TTC

        Les prix en base sont TTC. On decompose pour l'affichage.
        Formule: HT = TTC / (1 + taux/100)
        """
        if taux is None:
            taux = Fiscalite.taux_tva_defaut()

        if taux <= 0:
            return {'ht': montant_ttc, 'tva': 0, 'ttc': montant_ttc, 'taux': 0}

        ht = montant_ttc / (1 + taux / 100)
        tva = montant_ttc - ht

        return {
            'ht': round(ht, 2),
            'tva': round(tva, 2),
            'ttc': montant_ttc,
            'taux': taux,
        }

    @staticmethod
    def obtenir_taux_categorie(categorie):
        """Obtenir le taux TVA specifique a une categorie (si defini)"""
        result = db.fetch_one(
            "SELECT taux FROM taux_tva WHERE categorie = ?", (categorie,)
        )
        if result:
            return result[0]
        return Fiscalite.taux_tva_defaut()

    @staticmethod
    def definir_taux_categorie(categorie, taux, description=""):
        """Definir un taux TVA pour une categorie"""
        query = """
            INSERT OR REPLACE INTO taux_tva (categorie, taux, description)
            VALUES (?, ?, ?)
        """
        return db.execute_query(query, (categorie, taux, description))

    @staticmethod
    def supprimer_taux_categorie(categorie):
        """Supprimer le taux specifique d'une categorie"""
        return db.execute_query("DELETE FROM taux_tva WHERE categorie = ?", (categorie,))

    @staticmethod
    def lister_taux_tva():
        """Lister tous les taux TVA par categorie"""
        return db.fetch_all("SELECT id, categorie, taux, description FROM taux_tva ORDER BY categorie")

    # === DEVISES ===

    @staticmethod
    def devise_principale():
        """Obtenir la devise principale"""
        return {
            'code': db.get_parametre('devise_principale', 'XOF'),
            'symbole': db.get_parametre('devise_symbole', 'FCFA'),
        }

    @staticmethod
    def lister_devises():
        """Lister toutes les devises"""
        return db.fetch_all("SELECT id, code, symbole, taux_change, actif FROM devises ORDER BY code")

    @staticmethod
    def convertir(montant_xof, code_devise):
        """Convertir un montant XOF vers une autre devise"""
        result = db.fetch_one(
            "SELECT taux_change FROM devises WHERE code = ? AND actif = 1", (code_devise,)
        )
        if result and result[0] > 0:
            return round(montant_xof / result[0], 2)
        return montant_xof

    @staticmethod
    def maj_taux_change(code_devise, nouveau_taux):
        """Mettre a jour le taux de change d'une devise"""
        return db.execute_query(
            "UPDATE devises SET taux_change = ? WHERE code = ?",
            (nouveau_taux, code_devise)
        )

    @staticmethod
    def ajouter_devise(code, symbole, taux_change):
        """Ajouter une nouvelle devise"""
        return db.execute_query(
            "INSERT OR IGNORE INTO devises (code, symbole, taux_change, actif) VALUES (?, ?, ?, 1)",
            (code, symbole, taux_change)
        )

    @staticmethod
    def rapport_tva_mensuel(mois=None, annee=None):
        """Rapport TVA pour un mois donne"""
        from datetime import datetime
        if mois is None:
            mois = datetime.now().month
        if annee is None:
            annee = datetime.now().year

        date_debut = f"{annee}-{mois:02d}-01"
        if mois == 12:
            date_fin = f"{annee + 1}-01-01"
        else:
            date_fin = f"{annee}-{mois + 1:02d}-01"

        # Total des ventes du mois
        query = """
            SELECT COALESCE(SUM(total), 0)
            FROM ventes
            WHERE date_vente >= ? AND date_vente < ?
        """
        result = db.fetch_one(query, (date_debut, date_fin))
        total_ttc = result[0] if result else 0

        taux = Fiscalite.taux_tva_defaut()
        decomposition = Fiscalite.calculer_tva(total_ttc, taux)

        return {
            'mois': mois,
            'annee': annee,
            'total_ttc': total_ttc,
            'total_ht': decomposition['ht'],
            'total_tva': decomposition['tva'],
            'taux': taux,
        }
