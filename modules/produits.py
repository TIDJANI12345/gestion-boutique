"""
Module de gestion des produits - Version 2.0
Avec choix manuel/auto pour les codes-barres
"""
from database import db
from datetime import datetime
import random
import string

class Produit:
    
    @staticmethod
    def generer_code_barre(type_code='code128', prefixe='PRD'):
        """Générer un code-barres selon le type"""
        if type_code == 'ean13':
            # EAN-13 : 12 chiffres + 1 checksum
            code = ''.join(random.choices(string.digits, k=12))
            checksum = Produit.calculer_checksum_ean13(code)
            return code + str(checksum)
        elif type_code == 'ean8':
            # EAN-8 : 7 chiffres + 1 checksum
            code = ''.join(random.choices(string.digits, k=7))
            checksum = Produit.calculer_checksum_ean13(code)
            return code + str(checksum)
        else:
            # Code128 ou autres : préfixe + 6 chiffres
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
            return False, "Le code-barres ne peut pas être vide"
        
        if type_code == 'ean13':
            if len(code) != 13 or not code.isdigit():
                return False, "EAN-13 doit contenir exactement 13 chiffres"
            # Vérifier le checksum
            checksum_calcule = Produit.calculer_checksum_ean13(code[:-1])
            if int(code[-1]) != checksum_calcule:
                return False, "Checksum EAN-13 invalide"
        elif type_code == 'ean8':
            if len(code) != 8 or not code.isdigit():
                return False, "EAN-8 doit contenir exactement 8 chiffres"
            checksum_calcule = Produit.calculer_checksum_ean13(code[:-1])
            if int(code[-1]) != checksum_calcule:
                return False, "Checksum EAN-8 invalide"
        
        # Vérifier l'unicité
        if Produit.code_barre_existe(code):
            return False, "Ce code-barres existe déjà"
        
        return True, "Code-barres valide"
    
    @staticmethod
    def code_barre_existe(code_barre):
        """Vérifier si un code-barres existe déjà"""
        result = db.fetch_one("SELECT id FROM produits WHERE code_barre = ?", (code_barre,))
        return result is not None
    
    @staticmethod
    def ajouter(nom, categorie, prix_achat, prix_vente, stock_actuel, stock_alerte, 
                code_barre=None, type_code_barre='code128', description=""):
        """Ajouter un nouveau produit"""
        
        # Générer ou valider le code-barres
        if not code_barre:
            code_barre = Produit.generer_code_barre(type_code_barre)
        else:
            valide, message = Produit.valider_code_barre(code_barre, type_code_barre)
            if not valide:
                print(f"❌ {message}")
                return None
        
        query = """
            INSERT INTO produits 
            (nom, categorie, prix_achat, prix_vente, stock_actuel, stock_alerte, 
             code_barre, type_code_barre, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        if db.execute_query(query, (nom, categorie, prix_achat, prix_vente, stock_actuel, 
                                     stock_alerte, code_barre, type_code_barre, description)):
            print(f"✅ Produit '{nom}' ajouté avec code-barres: {code_barre}")
            return code_barre
        return None
    
    @staticmethod
    def modifier(id_produit, nom, categorie, prix_achat, prix_vente, stock_actuel, 
                 stock_alerte, description=""):
        """Modifier un produit existant"""
        query = """
            UPDATE produits 
            SET nom = ?, categorie = ?, prix_achat = ?, prix_vente = ?, 
                stock_actuel = ?, stock_alerte = ?, description = ?
            WHERE id = ?
        """
        if db.execute_query(query, (nom, categorie, prix_achat, prix_vente, stock_actuel, 
                                     stock_alerte, description, id_produit)):
            print(f"✅ Produit ID {id_produit} modifié")
            return True
        return False
    
    @staticmethod
    def supprimer(id_produit):
        """Supprimer un produit"""
        query = "DELETE FROM produits WHERE id = ?"
        if db.execute_query(query, (id_produit,)):
            print(f"✅ Produit ID {id_produit} supprimé")
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
        """Rechercher des produits par nom ou catégorie"""
        query = "SELECT * FROM produits WHERE nom LIKE ? OR categorie LIKE ? OR code_barre LIKE ?"
        terme = f"%{terme}%"
        return db.fetch_all(query, (terme, terme, terme))
    
    @staticmethod
    def mettre_a_jour_stock(id_produit, nouvelle_quantite, operation="Mise à jour"):
        """Mettre à jour le stock d'un produit"""
        ancien = db.fetch_one("SELECT stock_actuel FROM produits WHERE id = ?", (id_produit,))
        if ancien:
            ancien_stock = ancien[0]
            query = "UPDATE produits SET stock_actuel = ? WHERE id = ?"
            if db.execute_query(query, (nouvelle_quantite, id_produit)):
                query_historique = """
                    INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation)
                    VALUES (?, ?, ?, ?)
                """
                db.execute_query(query_historique, (id_produit, ancien_stock, nouvelle_quantite, operation))
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
        """Obtenir toutes les catégories distinctes"""
        query = "SELECT DISTINCT categorie FROM produits WHERE categorie IS NOT NULL AND categorie != '' ORDER BY categorie"
        results = db.fetch_all(query)
        return [r[0] for r in results]
    
    @staticmethod
    def obtenir_par_categorie():
        """Obtenir tous les produits groupés par catégorie"""
        categories = {}
        produits = Produit.obtenir_tous()
        
        for produit in produits:
            categorie = produit[2] if produit[2] else "Sans catégorie"
            if categorie not in categories:
                categories[categorie] = []
            categories[categorie].append(produit)
        
        return categories
