"""
Module de gestion des produits
"""
from database import db
from datetime import datetime
from modules.logger import get_logger
import random
import string

logger = get_logger('produits')


class Produit:

    @staticmethod
    def generer_code_barre(type_code='code128', prefixe='PRD'):
        """Generer un code-barres selon le type"""
        if type_code == 'ean13':
            code = ''.join(random.choices(string.digits, k=12))
            checksum = Produit.calculer_checksum_ean13(code)
            return code + str(checksum)
        elif type_code == 'ean8':
            code = ''.join(random.choices(string.digits, k=7))
            checksum = Produit.calculer_checksum_ean13(code)
            return code + str(checksum)
        else:
            while True:
                nombre = ''.join(random.choices(string.digits, k=6))
                code = f"{prefixe}{nombre}"
                if not Produit.code_barre_existe(code):
                    return code

    @staticmethod
    def calculer_checksum_ean13(code):
        """Calculer le checksum pour EAN-13/EAN-8"""
        somme = 0
        for i, digit in enumerate(code):
            if i % 2 == 0:
                somme += int(digit)
            else:
                somme += int(digit) * 3
        return (10 - (somme % 10)) % 10

    @staticmethod
    def valider_code_barre(code, type_code='code128'):
        """Valider un code-barres selon son type"""
        if not code:
            return False, "Le code-barres ne peut pas etre vide"

        if type_code == 'ean13':
            if len(code) != 13 or not code.isdigit():
                return False, "EAN-13 doit contenir exactement 13 chiffres"
            checksum_calcule = Produit.calculer_checksum_ean13(code[:-1])
            if int(code[-1]) != checksum_calcule:
                return False, "Checksum EAN-13 invalide"
        elif type_code == 'ean8':
            if len(code) != 8 or not code.isdigit():
                return False, "EAN-8 doit contenir exactement 8 chiffres"
            checksum_calcule = Produit.calculer_checksum_ean13(code[:-1])
            if int(code[-1]) != checksum_calcule:
                return False, "Checksum EAN-8 invalide"

        if Produit.code_barre_existe(code):
            return False, "Ce code-barres existe deja"

        return True, "Code-barres valide"

    @staticmethod
    def code_barre_existe(code_barre):
        """Verifier si un code-barres existe deja"""
        result = db.fetch_one("SELECT id FROM produits WHERE code_barre = ?", (code_barre,))
        return result is not None

    @staticmethod
    def ajouter(nom, categorie, prix_achat, prix_vente, stock_actuel, stock_alerte,
                code_barre=None, type_code_barre='code128', description=""):
        """Ajouter un nouveau produit avec validation"""

        # Validation des donnees
        if prix_vente is not None and prix_vente < 0:
            logger.warning(f"Ajout refuse : prix_vente negatif ({prix_vente})")
            return None
        if prix_achat is not None and prix_achat < 0:
            logger.warning(f"Ajout refuse : prix_achat negatif ({prix_achat})")
            return None
        if stock_actuel is not None and stock_actuel < 0:
            logger.warning(f"Ajout refuse : stock negatif ({stock_actuel})")
            return None

        # Generer ou valider le code-barres
        if not code_barre:
            code_barre = Produit.generer_code_barre(type_code_barre)
        else:
            valide, message = Produit.valider_code_barre(code_barre, type_code_barre)
            if not valide:
                logger.warning(f"Code-barres invalide : {message}")
                return None

        query = """
            INSERT INTO produits
            (nom, categorie, prix_achat, prix_vente, stock_actuel, stock_alerte,
             code_barre, type_code_barre, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        result = db.execute_query(query, (nom, categorie, prix_achat, prix_vente, stock_actuel,
                                          stock_alerte, code_barre, type_code_barre, description))
        if result:
            logger.info(f"Produit ajoute : '{nom}' (code: {code_barre})")
            return code_barre
        return None

    @staticmethod
    def modifier(id_produit, nom, categorie, prix_achat, prix_vente, stock_actuel,
                 stock_alerte, description=""):
        """Modifier un produit existant avec validation"""

        if prix_vente is not None and prix_vente < 0:
            logger.warning(f"Modification refusee : prix_vente negatif ({prix_vente})")
            return False
        if prix_achat is not None and prix_achat < 0:
            logger.warning(f"Modification refusee : prix_achat negatif ({prix_achat})")
            return False
        if stock_actuel is not None and stock_actuel < 0:
            logger.warning(f"Modification refusee : stock negatif ({stock_actuel})")
            return False

        query = """
            UPDATE produits
            SET nom = ?, categorie = ?, prix_achat = ?, prix_vente = ?,
                stock_actuel = ?, stock_alerte = ?, description = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """
        result = db.execute_query(query, (nom, categorie, prix_achat, prix_vente, stock_actuel,
                                          stock_alerte, description, id_produit))
        if result:
            logger.info(f"Produit modifie : ID {id_produit}")
            return True
        return False

    @staticmethod
    def supprimer(id_produit, user_id=None):
        """Supprimer un produit"""
        query = "DELETE FROM produits WHERE id = ?"
        result = db.execute_query(query, (id_produit,))
        if result:
            logger.info(f"Produit supprime : ID {id_produit}")
            if user_id:
                from modules.utilisateurs import Utilisateur
                Utilisateur.logger_action(user_id, 'suppression_produit',
                                          f"Produit {id_produit} supprimé")
            return True
        return False

    @staticmethod
    def obtenir_tous():
        """Obtenir tous les produits"""
        query = "SELECT * FROM produits ORDER BY id ASC"
        return db.fetch_all(query)

    @staticmethod
    def obtenir_par_id(id_produit):
        """Obtenir un produit par son ID"""
        query = "SELECT * FROM produits WHERE id = ?"
        return db.fetch_one(query, (id_produit,))

    @staticmethod
    def obtenir_par_code_barre(code_barre):
        """Obtenir un produit par son code-barres"""
        query = "SELECT * FROM produits WHERE code_barre = ?"
        return db.fetch_one(query, (code_barre,))

    @staticmethod
    def rechercher(terme):
        """Rechercher des produits par nom ou categorie"""
        query = "SELECT * FROM produits WHERE nom LIKE ? OR categorie LIKE ? OR code_barre LIKE ?"
        terme = f"%{terme}%"
        return db.fetch_all(query, (terme, terme, terme))

    @staticmethod
    def mettre_a_jour_stock(id_produit, nouvelle_quantite, operation="Mise a jour", user_id=None):
        """Mettre a jour le stock d'un produit"""
        # VALIDATION : Stock ne peut pas être négatif
        if nouvelle_quantite < 0:
            logger.error(f"Tentative de mise à jour stock négatif: {nouvelle_quantite} pour produit {id_produit}")
            return False

        ancien = db.fetch_one("SELECT stock_actuel FROM produits WHERE id = ?", (id_produit,))
        if ancien:
            ancien_stock = ancien['stock_actuel']
            query = "UPDATE produits SET stock_actuel = ?, updated_at = datetime('now') WHERE id = ?"
            if db.execute_query(query, (nouvelle_quantite, id_produit)):
                query_historique = """
                    INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation)
                    VALUES (?, ?, ?, ?)
                """
                db.execute_query(query_historique, (id_produit, ancien_stock, nouvelle_quantite, operation))
                if user_id and operation == "Ajustement":
                    from modules.utilisateurs import Utilisateur
                    Utilisateur.logger_action(user_id, 'ajustement_stock',
                                              f"Produit {id_produit}: stock ajusté ({operation})")
                return True
        return False

    @staticmethod
    def obtenir_stock_faible(seuil=None):
        """Obtenir les produits avec un stock faible"""
        if seuil is None:
            query = "SELECT * FROM produits WHERE stock_actuel < stock_alerte ORDER BY stock_actuel"
            return db.fetch_all(query)
        else:
            query = "SELECT * FROM produits WHERE stock_actuel < ? ORDER BY stock_actuel"
            return db.fetch_all(query, (seuil,))

    @staticmethod
    def obtenir_categories():
        """Obtenir toutes les categories distinctes"""
        query = "SELECT DISTINCT categorie FROM produits WHERE categorie IS NOT NULL AND categorie != '' ORDER BY categorie"
        results = db.fetch_all(query)
        return [r['categorie'] for r in results]

    @staticmethod
    def obtenir_par_categorie():
        """Obtenir tous les produits groupes par categorie"""
        categories = {}
        produits = Produit.obtenir_tous()

        for produit in produits:
            categorie = produit['categorie'] if produit['categorie'] else "Sans categorie"
            if categorie not in categories:
                categories[categorie] = []
            categories[categorie].append(produit)

        return categories

    @staticmethod
    def rechercher_filtre(terme="", categorie=None, stock_filter=None,
                          prix_min=None, prix_max=None, limit=50, offset=0):
        """Rechercher des produits avec filtres multiples et pagination"""
        conditions = []
        params = []

        if terme:
            conditions.append("(nom LIKE ? OR categorie LIKE ? OR code_barre LIKE ?)")
            t = f"%{terme}%"
            params.extend([t, t, t])

        if categorie and categorie != "Toutes":
            conditions.append("categorie = ?")
            params.append(categorie)

        if stock_filter == "Stock faible":
            conditions.append("stock_actuel <= stock_alerte AND stock_actuel > 0")
        elif stock_filter == "Rupture":
            conditions.append("stock_actuel = 0")
        elif stock_filter == "Stock négatif":
            conditions.append("stock_actuel < 0")

        if prix_min is not None:
            conditions.append("prix_vente >= ?")
            params.append(prix_min)
        if prix_max is not None:
            conditions.append("prix_vente <= ?")
            params.append(prix_max)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT * FROM produits WHERE {where} ORDER BY id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        return db.fetch_all(query, tuple(params))

    @staticmethod
    def compter_filtre(terme="", categorie=None, stock_filter=None,
                       prix_min=None, prix_max=None):
        """Compter les produits correspondant aux filtres (pour pagination)"""
        conditions = []
        params = []

        if terme:
            conditions.append("(nom LIKE ? OR categorie LIKE ? OR code_barre LIKE ?)")
            t = f"%{terme}%"
            params.extend([t, t, t])

        if categorie and categorie != "Toutes":
            conditions.append("categorie = ?")
            params.append(categorie)

        if stock_filter == "Stock faible":
            conditions.append("stock_actuel <= stock_alerte AND stock_actuel > 0")
        elif stock_filter == "Rupture":
            conditions.append("stock_actuel = 0")
        elif stock_filter == "Stock négatif":
            conditions.append("stock_actuel < 0")

        if prix_min is not None:
            conditions.append("prix_vente >= ?")
            params.append(prix_min)
        if prix_max is not None:
            conditions.append("prix_vente <= ?")
            params.append(prix_max)

        where = " AND ".join(conditions) if conditions else "1=1"
        query = f"SELECT COUNT(*) as count FROM produits WHERE {where}"

        result = db.fetch_one(query, tuple(params))
        return result['count'] if result else 0
