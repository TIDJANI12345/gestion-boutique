"""
Module de génération de rapports et statistiques
"""
from database import db
from datetime import datetime, timedelta

class Rapport:
        
    @staticmethod
    def statistiques_generales():
        """Obtenir les statistiques générales"""
        stats = {
            'nb_ventes': 0,
            'ca_jour': 0,
            'ca_mois': 0,
            'ca_total': 0,  # ✅ AJOUTÉ
            'nb_produits': 0,
            'valeur_stock': 0
        }
        
        try:
            # Ventes du jour
            aujourd_hui = datetime.now().strftime("%Y-%m-%d")
            query_jour = "SELECT COUNT(*), COALESCE(SUM(total), 0) FROM ventes WHERE DATE(date_vente) = ?"
            result = db.fetch_one(query_jour, (aujourd_hui,))
            if result:
                stats['nb_ventes'] = result[0] or 0
                stats['ca_jour'] = result[1] or 0
            
            # CA du mois
            debut_mois = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            query_mois = "SELECT COALESCE(SUM(total), 0) FROM ventes WHERE date_vente >= ?"
            result = db.fetch_one(query_mois, (debut_mois,))
            if result:
                stats['ca_mois'] = result[0] or 0
            
            # CA total ✅ AJOUTÉ
            query_total = "SELECT COALESCE(SUM(total), 0) FROM ventes"
            result = db.fetch_one(query_total)
            if result:
                stats['ca_total'] = result[0] or 0
            
            # Nombre de produits
            query_produits = "SELECT COUNT(*) FROM produits"
            result = db.fetch_one(query_produits)
            if result:
                stats['nb_produits'] = result[0] or 0
            
            # Valeur du stock
            query_valeur = "SELECT COALESCE(SUM(prix_vente * stock_actuel), 0) FROM produits"
            result = db.fetch_one(query_valeur)
            if result:
                stats['valeur_stock'] = result[0] or 0
                
        except Exception as e:
            print(f"❌ Erreur statistiques: {e}")
        
        return stats

    @staticmethod
    def statistiques_utilisateur(utilisateur_id):
        """Statistiques filtrées pour un utilisateur spécifique (caissier)"""
        stats = {
            'nb_ventes': 0,
            'ca_jour': 0,
        }

        try:
            # Ventes du jour pour cet utilisateur
            aujourd_hui = datetime.now().strftime("%Y-%m-%d")
            query_jour = """
                SELECT COUNT(*), COALESCE(SUM(total), 0)
                FROM ventes
                WHERE DATE(date_vente) = ? AND utilisateur_id = ?
            """
            result = db.fetch_one(query_jour, (aujourd_hui, utilisateur_id))
            if result:
                stats['nb_ventes'] = result[0] or 0
                stats['ca_jour'] = result[1] or 0

        except Exception as e:
            print(f"❌ Erreur statistiques utilisateur: {e}")

        return stats

    @staticmethod
    def top_produits(limite=20):
        """Obtenir les produits les plus vendus"""
        query = """
            SELECT p.nom, p.categorie, SUM(dv.quantite) as total_vendu, 
                   SUM(dv.sous_total) as ca_total
            FROM details_ventes dv
            JOIN produits p ON dv.produit_id = p.id
            GROUP BY p.id
            ORDER BY total_vendu DESC
            LIMIT ?
        """
        return db.fetch_all(query, (limite,))
    
    @staticmethod
    def ventes_par_periode(date_debut, date_fin):
        """Obtenir les ventes pour une période"""
        query = """
            SELECT DATE(date_vente) as jour, COUNT(*) as nb_ventes, 
                   SUM(total) as ca
            FROM ventes
            WHERE date_vente BETWEEN ? AND ?
            GROUP BY DATE(date_vente)
            ORDER BY jour DESC
        """
        return db.fetch_all(query, (date_debut, date_fin))
    
    @staticmethod
    def ca_par_categorie():
        """Chiffre d'affaires par catégorie"""
        query = """
            SELECT p.categorie, SUM(dv.sous_total) as ca_total
            FROM details_ventes dv
            JOIN produits p ON dv.produit_id = p.id
            GROUP BY p.categorie
            ORDER BY ca_total DESC
        """
        return db.fetch_all(query)
    
    @staticmethod
    def evolution_ventes_7_jours():
        """Évolution des ventes sur 7 jours"""
        il_y_a_7_jours = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        query = """
            SELECT DATE(date_vente) as jour, COUNT(*) as nb_ventes, 
                   COALESCE(SUM(total), 0) as ca
            FROM ventes
            WHERE date_vente >= ?
            GROUP BY DATE(date_vente)
            ORDER BY jour ASC
        """
        return db.fetch_all(query, (il_y_a_7_jours,))
    
    @staticmethod
    def rapport_journalier(date=None):
        """Rapport complet pour une journée"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        rapport = {
            'date': date,
            'nb_ventes': 0,
            'ca_total': 0,
            'nb_articles': 0,
            'ventes': [],
            'top_produits': []
        }
        
        try:
            # Stats globales du jour
            query_stats = """
                SELECT COUNT(*), COALESCE(SUM(total), 0)
                FROM ventes
                WHERE DATE(date_vente) = ?
            """
            result = db.fetch_one(query_stats, (date,))
            if result:
                rapport['nb_ventes'] = result[0] or 0
                rapport['ca_total'] = result[1] or 0
            
            # Nombre total d'articles vendus
            query_articles = """
                SELECT COALESCE(SUM(dv.quantite), 0)
                FROM details_ventes dv
                JOIN ventes v ON dv.vente_id = v.id
                WHERE DATE(v.date_vente) = ?
            """
            result = db.fetch_one(query_articles, (date,))
            if result:
                rapport['nb_articles'] = result[0] or 0
            
            # Liste des ventes
            query_ventes = """
                SELECT numero_vente, date_vente, total, client
                FROM ventes
                WHERE DATE(date_vente) = ?
                ORDER BY date_vente DESC
            """
            rapport['ventes'] = db.fetch_all(query_ventes, (date,))
            
            # Top produits du jour
            query_top = """
                SELECT p.nom, SUM(dv.quantite) as qte, SUM(dv.sous_total) as ca
                FROM details_ventes dv
                JOIN produits p ON dv.produit_id = p.id
                JOIN ventes v ON dv.vente_id = v.id
                WHERE DATE(v.date_vente) = ?
                GROUP BY p.id
                ORDER BY qte DESC
                LIMIT 10
            """
            rapport['top_produits'] = db.fetch_all(query_top, (date,))
            
        except Exception as e:
            print(f"❌ Erreur rapport journalier: {e}")

        return rapport

    @staticmethod
    def rapport_caisse_jour(date=None):
        """Rapport de rapprochement de caisse avec details par mode de paiement"""
        from modules.paiements import Paiement
        return Paiement.rapport_caisse_jour(date)

    @staticmethod
    def statistiques_paiements(date_debut=None, date_fin=None):
        """Statistiques des paiements par mode sur une periode"""
        if date_debut and date_fin:
            query = """
                SELECT p.mode, SUM(p.montant) as total, COUNT(*) as nb
                FROM paiements p
                JOIN ventes v ON p.vente_id = v.id
                WHERE v.date_vente BETWEEN ? AND ?
                GROUP BY p.mode
                ORDER BY total DESC
            """
            return db.fetch_all(query, (date_debut, date_fin))
        else:
            query = """
                SELECT p.mode, SUM(p.montant) as total, COUNT(*) as nb
                FROM paiements p
                GROUP BY p.mode
                ORDER BY total DESC
            """
            return db.fetch_all(query)

    @staticmethod
    def rapport_tva_mensuel(mois=None, annee=None):
        """Rapport TVA mensuel"""
        from modules.fiscalite import Fiscalite
        return Fiscalite.rapport_tva_mensuel(mois, annee)

    @staticmethod
    def comparaison_jour_precedent():
        """Comparer les ventes du jour avec celles d'hier"""
        aujourd_hui = datetime.now().strftime("%Y-%m-%d")
        hier = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        query = """
            SELECT DATE(date_vente) as jour, COUNT(*) as nb, COALESCE(SUM(total), 0) as ca
            FROM ventes
            WHERE DATE(date_vente) IN (?, ?)
            GROUP BY DATE(date_vente)
        """
        results = db.fetch_all(query, (aujourd_hui, hier))

        data = {'aujourd_hui': {'nb': 0, 'ca': 0}, 'hier': {'nb': 0, 'ca': 0}}
        for row in results:
            if row[0] == aujourd_hui:
                data['aujourd_hui'] = {'nb': row[1], 'ca': row[2]}
            elif row[0] == hier:
                data['hier'] = {'nb': row[1], 'ca': row[2]}

        if data['hier']['ca'] > 0:
            data['variation_ca_pct'] = ((data['aujourd_hui']['ca'] - data['hier']['ca']) / data['hier']['ca']) * 100
        else:
            data['variation_ca_pct'] = 100.0 if data['aujourd_hui']['ca'] > 0 else 0.0

        return data

    @staticmethod
    def donnees_graphique_ventes(periode='semaine'):
        """Donnees formatees pour graphique matplotlib: list de (label, ca)"""
        if periode == 'jour':
            aujourd_hui = datetime.now().strftime("%Y-%m-%d")
            query = """
                SELECT strftime('%H', date_vente) as heure, COALESCE(SUM(total), 0)
                FROM ventes WHERE DATE(date_vente) = ?
                GROUP BY heure ORDER BY heure
            """
            results = db.fetch_all(query, (aujourd_hui,))
            return [(f"{r[0]}h", r[1]) for r in results]
        elif periode == 'semaine':
            data = Rapport.evolution_ventes_7_jours()
            return [(r[0][-5:], r[2]) for r in data]
        elif periode == 'mois':
            debut_mois = datetime.now().replace(day=1).strftime("%Y-%m-%d")
            query = """
                SELECT DATE(date_vente), COALESCE(SUM(total), 0)
                FROM ventes WHERE date_vente >= ?
                GROUP BY DATE(date_vente) ORDER BY DATE(date_vente)
            """
            results = db.fetch_all(query, (debut_mois,))
            return [(r[0][-2:], r[1]) for r in results]
        return []