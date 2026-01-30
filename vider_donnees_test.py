"""
Script pour vider toutes les données de test
"""
from database import db
import os
from config import DB_PATH

def vider_base():
    """Supprimer toutes les données"""
    print("\n⚠️  ATTENTION: Suppression de toutes les données!")
    reponse = input("Voulez-vous continuer? (oui/non): ")
    
    if reponse.lower() != 'oui':
        print("❌ Annulé")
        return
    
    try:
        # Supprimer les données
        db.execute_query("DELETE FROM details_ventes")
        db.execute_query("DELETE FROM ventes")
        db.execute_query("DELETE FROM historique_stock")
        db.execute_query("DELETE FROM produits")
        
        print("✅ Toutes les données ont été supprimées")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    vider_base()