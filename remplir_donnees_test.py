"""
Script pour remplir la base de données - VERSION SIMPLIFIÉE
Uniquement Code128, codes fixes, CA prévisible
"""
from database import db
from modules.produits import Produit
from modules.ventes import Vente
from modules.codebarres import CodeBarre

def remplir_produits():
    """Ajouter des produits de test - CODES FIXES"""
    print("📦 Ajout des produits de test...")
    
    produits_test = [
        # (nom, catégorie, prix_achat, prix_vente, stock, alerte, CODE FIXE, description)
        
        # Alimentaire
        ("Riz Uncle Ben 5kg", "Alimentaire", 6000, 7500, 50, 5, "ALI001", "Riz de qualité premium"),
        ("Huile Dinor 1L", "Alimentaire", 2000, 2500, 30, 5, "ALI002", "Huile végétale"),
        ("Sucre 1kg", "Alimentaire", 600, 850, 100, 10, "ALI003", "Sucre blanc"),
        ("Farine 1kg", "Alimentaire", 400, 600, 80, 10, "ALI004", "Farine de blé"),
        ("Lait Nido 400g", "Alimentaire", 2500, 3200, 25, 5, "ALI005", "Lait en poudre"),
        
        # Hygiène
        ("Savon Lux", "Hygiène", 150, 250, 100, 15, "HYG001", "Savon de toilette"),
        ("Dentifrice Colgate", "Hygiène", 800, 1200, 45, 10, "HYG002", "Dentifrice"),
        ("Shampoing", "Hygiène", 1500, 2000, 20, 5, "HYG003", "Shampoing"),
        ("Lessive OMO 1kg", "Hygiène", 2000, 2800, 25, 5, "HYG004", "Lessive"),
        
        # Boissons
        ("Coca-Cola 1.5L", "Boissons", 600, 900, 48, 12, "BOI001", "Boisson gazeuse"),
        ("Fanta 1.5L", "Boissons", 600, 900, 40, 12, "BOI002", "Fanta orange"),
        ("Eau Possotomè 1.5L", "Boissons", 200, 350, 100, 20, "BOI003", "Eau minérale"),
        
        # Produits en alerte (pour tests)
        ("Produit Rupture", "Test", 1000, 1500, 0, 5, "TEST001", "Stock épuisé"),
        ("Produit Stock Faible", "Test", 500, 800, 3, 5, "TEST002", "Stock critique"),
    ]
    
    for nom, cat, pa, pv, stock, alerte, code, desc in produits_test:
        code_genere = Produit.ajouter(nom, cat, pa, pv, stock, alerte, code, 'code128', desc)
        if code_genere:
            CodeBarre.generer_image(code_genere, nom, pv, 'code128')
            print(f"  ✅ {nom} - {code_genere}")
        else:
            print(f"  ❌ Échec: {nom}")

def remplir_ventes():
    """Créer des ventes de test - CA PRÉVISIBLE"""
    print("\n💰 Création de ventes de test...")
    
    # Vente 1: Alimentaire (2 Riz + 3 Huile)
    # 2×7500 + 3×2500 = 15000 + 7500 = 22,500 FCFA
    vente1 = Vente.creer_vente("Client 1")
    p1 = Produit.obtenir_par_code_barre("ALI001")  # Riz
    p2 = Produit.obtenir_par_code_barre("ALI002")  # Huile
    if p1 and p2:
        Vente.ajouter_produit(vente1, p1[0], 2)
        Vente.ajouter_produit(vente1, p2[0], 3)
    print(f"  ✅ Vente 1: 22,500 FCFA")
    
    # Vente 2: Hygiène (5 Savon + 2 Dentifrice)
    # 5×250 + 2×1200 = 1250 + 2400 = 3,650 FCFA
    vente2 = Vente.creer_vente("Client 2")
    p3 = Produit.obtenir_par_code_barre("HYG001")  # Savon
    p4 = Produit.obtenir_par_code_barre("HYG002")  # Dentifrice
    if p3 and p4:
        Vente.ajouter_produit(vente2, p3[0], 5)
        Vente.ajouter_produit(vente2, p4[0], 2)
    print(f"  ✅ Vente 2: 3,650 FCFA")
    
    # Vente 3: Boissons (6 Coca + 10 Eau)
    # 6×900 + 10×350 = 5400 + 3500 = 8,900 FCFA
    vente3 = Vente.creer_vente("Client 3")
    p5 = Produit.obtenir_par_code_barre("BOI001")  # Coca
    p6 = Produit.obtenir_par_code_barre("BOI003")  # Eau
    if p5 and p6:
        Vente.ajouter_produit(vente3, p5[0], 6)
        Vente.ajouter_produit(vente3, p6[0], 10)
    print(f"  ✅ Vente 3: 8,900 FCFA")
    
    print(f"\n💰 TOTAL ATTENDU: 35,050 FCFA")

def afficher_statistiques():
    """Afficher un résumé"""
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DES DONNÉES")
    print("="*50)
    
    produits = Produit.obtenir_tous()
    print(f"\n✅ Produits : {len(produits)}")
    
    categories = {}
    for p in produits:
        cat = p[2] or "Sans catégorie"
        categories[cat] = categories.get(cat, 0) + 1
    
    for cat, nb in sorted(categories.items()):
        print(f"   - {cat}: {nb} produits")
    
    from modules.ventes import Vente
    ventes = Vente.obtenir_toutes_ventes()
    total_ca = sum(v[3] for v in ventes)
    
    print(f"\n💰 Ventes : {len(ventes)}")
    print(f"   - CA Total: {total_ca:,.0f} FCFA")
    
    for v in ventes:
        print(f"   - {v[1]}: {v[3]:,.0f} FCFA")
    
    stock_faible = Produit.obtenir_stock_faible()
    print(f"\n⚠️  Stock faible : {len(stock_faible)}")
    for p in stock_faible:
        print(f"   - {p[1]}: {p[5]}")
    
    print("\n" + "="*50)
    print(f"✅ CA ATTENDU: 35,050 FCFA")
    print(f"✅ CA OBTENU:  {total_ca:,.0f} FCFA")
    if total_ca == 35050:
        print("🎉 PARFAIT !")
    else:
        print("❌ INCOHÉRENCE !")
    print("="*50 + "\n")

def main():
    print("\n" + "="*50)
    print("🚀 REMPLISSAGE BASE DE DONNÉES")
    print("="*50 + "\n")
    
    try:
        remplir_produits()
        remplir_ventes()
        afficher_statistiques()
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()