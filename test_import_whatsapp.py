"""
Script de test pour l'import WhatsApp
Usage: python test_import_whatsapp.py chemin/vers/export.zip
"""
import sys
import os

# Ajouter le dossier parent au path
sys.path.insert(0, os.path.dirname(__file__))

from modules.ia_extraction import IAExtraction


def tester_import(zip_path):
    """Tester l'import d'un fichier WhatsApp"""
    print(f"📂 Test import: {zip_path}")
    print("-" * 60)

    if not os.path.exists(zip_path):
        print(f"❌ Fichier introuvable: {zip_path}")
        return

    # Traiter l'export
    produits, erreur = IAExtraction.traiter_export_whatsapp(zip_path)

    if erreur != "OK":
        print(f"❌ Erreur: {erreur}")
        return

    print(f"\n✅ {len(produits)} produits extraits:\n")

    for i, p in enumerate(produits, 1):
        print(f"{i}. {p['nom']}")
        print(f"   Prix: {p['prix']} FCFA")
        print(f"   Catégorie: {p['categorie_suggeree']}")
        print(f"   Code-barre: {p.get('code_barre', '(auto)')}")
        print(f"   Confiance: {p['confiance']:.0%}")
        print()

    print("-" * 60)
    print(f"📊 Total: {len(produits)} produits")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_import_whatsapp.py chemin/vers/export.zip")
        print("\nExemple fourni:")
        exemple = "/tmp/claude-1000/-mnt-d-Projects-Python-GestionBoutique-v2/f5b31ef1-e4a2-4b52-8dbc-05441ed9cd60/scratchpad/exemple_whatsapp_v2.zip"
        if os.path.exists(exemple):
            tester_import(exemple)
        else:
            print(f"Fichier exemple introuvable: {exemple}")
    else:
        tester_import(sys.argv[1])
