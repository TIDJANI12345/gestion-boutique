"""
Script de remplissage de la base de données de test.
Crée 14 produits + 49 ventes (juste sous la limite démo de 50).
"""
from database import db
from modules.produits import Produit
from modules.ventes import Vente

PRODUITS = [
    # (nom, catégorie, prix_achat, prix_vente, stock, alerte, code, description)
    ("Riz Uncle Ben 5kg",     "Alimentaire", 6000, 7500,  50,  5, "ALI001", "Riz premium"),
    ("Huile Dinor 1L",        "Alimentaire", 2000, 2500,  30,  5, "ALI002", "Huile végétale"),
    ("Sucre 1kg",             "Alimentaire",  600,  850, 100, 10, "ALI003", "Sucre blanc"),
    ("Farine 1kg",            "Alimentaire",  400,  600,  80, 10, "ALI004", "Farine de blé"),
    ("Lait Nido 400g",        "Alimentaire", 2500, 3200,  25,  5, "ALI005", "Lait en poudre"),
    ("Savon Lux",             "Hygiène",      150,  250, 100, 15, "HYG001", "Savon de toilette"),
    ("Dentifrice Colgate",    "Hygiène",      800, 1200,  45, 10, "HYG002", "Dentifrice"),
    ("Shampoing",             "Hygiène",     1500, 2000,  20,  5, "HYG003", "Shampoing"),
    ("Lessive OMO 1kg",       "Hygiène",     2000, 2800,  25,  5, "HYG004", "Lessive"),
    ("Coca-Cola 1.5L",        "Boissons",     600,  900,  48, 12, "BOI001", "Boisson gazeuse"),
    ("Fanta 1.5L",            "Boissons",     600,  900,  40, 12, "BOI002", "Fanta orange"),
    ("Eau Possotomè 1.5L",    "Boissons",     200,  350, 200, 20, "BOI003", "Eau minérale"),
    ("Produit Rupture",       "Test",        1000, 1500,   0,  5, "TEST001", "Stock épuisé"),
    ("Produit Stock Faible",  "Test",         500,  800,   3,  5, "TEST002", "Stock critique"),
]

# 49 ventes : (client, [(code, qté), ...])
VENTES = [
    ("Kouassi Aimé",    [("ALI001", 2), ("BOI003", 5)]),
    ("Fatou Diallo",    [("HYG001", 3), ("HYG002", 1)]),
    ("Moussa Koné",     [("BOI001", 4), ("BOI002", 2)]),
    ("Aïcha Traoré",    [("ALI002", 2), ("ALI003", 3)]),
    ("Koffi Mensah",    [("HYG004", 1), ("ALI004", 2)]),
    ("Aminata Bah",     [("ALI005", 2), ("BOI003", 10)]),
    ("Seydou Ouédraogo",[("BOI001", 6), ("BOI003", 10)]),
    ("Mariam Coulibaly",[("HYG001", 5), ("HYG002", 2)]),
    ("Ibrahim Sawadogo",[("ALI001", 1), ("ALI002", 1)]),
    ("Adjoa Annan",     [("ALI003", 4), ("ALI004", 4)]),
    ("Salif Diarra",    [("BOI002", 3), ("BOI003", 6)]),
    ("Ramatou Sow",     [("HYG003", 2), ("HYG004", 1)]),
    ("Lamine Ndiaye",   [("ALI005", 1), ("HYG001", 4)]),
    ("Bintou Kouyaté",  [("BOI001", 2), ("ALI003", 5)]),
    ("Dramane Sissoko", [("ALI002", 3), ("BOI003", 8)]),
    ("Oumou Camara",    [("HYG002", 3), ("ALI004", 3)]),
    ("Boubacar Barry",  [("ALI001", 3), ("BOI002", 4)]),
    ("Fanta Keïta",     [("HYG001", 6), ("BOI003", 4)]),
    ("Adama Touré",     [("ALI003", 6), ("ALI005", 1)]),
    ("Rokhaya Mbaye",   [("BOI001", 3), ("HYG004", 2)]),
    ("Mamadou Baldé",   [("ALI002", 4), ("ALI004", 5)]),
    ("Kadiatou Barry",  [("HYG003", 1), ("BOI002", 5)]),
    ("Ousmane Diop",    [("ALI001", 2), ("BOI003", 12)]),
    ("Hawa Traoré",     [("HYG002", 2), ("ALI003", 3)]),
    ("Souleymane Fall", [("BOI001", 5), ("HYG001", 3)]),
    ("Nafi Koné",       [("ALI005", 3), ("BOI003", 6)]),
    ("Cheikh Sall",     [("ALI002", 2), ("HYG004", 1)]),
    ("Mariame Sylla",   [("BOI002", 6), ("ALI004", 4)]),
    ("Bourama Doumbia", [("HYG001", 4), ("ALI003", 5)]),
    ("Yaye Diallo",     [("ALI001", 1), ("BOI001", 2)]),
    ("Issa Traoré",     [("HYG003", 3), ("BOI003", 8)]),
    ("Khady Ndiaye",    [("ALI002", 5), ("ALI005", 2)]),
    ("Modibo Samaké",   [("BOI001", 4), ("HYG002", 3)]),
    ("Astou Diallo",    [("ALI003", 8), ("BOI002", 3)]),
    ("Mamadou Koné",    [("HYG004", 2), ("BOI003", 15)]),
    ("Fatoumata Cissé", [("ALI001", 4), ("HYG001", 5)]),
    ("Sekou Camara",    [("ALI004", 6), ("BOI001", 3)]),
    ("Mariétou Diallo", [("HYG002", 4), ("ALI005", 1)]),
    ("Alpha Baldé",     [("BOI002", 4), ("ALI003", 6)]),
    ("Ndèye Sow",       [("HYG003", 2), ("BOI003", 10)]),
    ("Kalifa Kouyaté",  [("ALI002", 3), ("HYG004", 2)]),
    ("Bineta Sall",     [("BOI001", 6), ("ALI004", 3)]),
    ("Idrissa Diallo",  [("ALI001", 2), ("ALI003", 4)]),
    ("Dado Traoré",     [("HYG001", 7), ("BOI003", 5)]),
    ("Moustapha Diop",  [("ALI005", 2), ("BOI002", 3)]),
    ("Rokhia Fall",     [("HYG002", 5), ("ALI002", 2)]),
    ("Demba Koné",      [("BOI001", 3), ("ALI004", 5)]),
    ("Aminata Diallo",  [("HYG004", 3), ("BOI003", 12)]),
    ("Lassana Barry",   [("ALI001", 3), ("HYG003", 1)]),
]


def remplir_produits():
    print("Ajout des produits...")
    ids = {}
    for nom, cat, pa, pv, stock, alerte, code, desc in PRODUITS:
        result = Produit.ajouter(nom, cat, pa, pv, stock, alerte, code, 'code128', desc)
        if result:
            p = Produit.obtenir_par_code_barre(result)
            if p:
                ids[code] = p['id']
                print(f"  OK  {nom}")
        else:
            print(f"  --  {nom} (déjà existant ?)")
            p = Produit.obtenir_par_code_barre(code)
            if p:
                ids[code] = p['id']
    return ids


def remplir_ventes(ids: dict):
    print(f"\nCréation de {len(VENTES)} ventes...")
    ca_total = 0
    for i, (client, lignes) in enumerate(VENTES, 1):
        vente_id = Vente.creer_vente(client)
        for code, qte in lignes:
            pid = ids.get(code)
            if pid:
                Vente.ajouter_produit(vente_id, pid, qte)
        total = Vente.calculer_total(vente_id)
        ca_total += total
        print(f"  [{i:02d}/49] {client:<22} {total:>10,.0f} FCFA")
    return ca_total


def afficher_resume(ca_total: float):
    ventes = Vente.obtenir_toutes_ventes()
    print(f"\n{'='*50}")
    print(f"  Produits : {len(PRODUITS)}")
    print(f"  Ventes   : {len(ventes)}")
    print(f"  CA total : {ca_total:,.0f} FCFA")
    print(f"{'='*50}")
    print("  Démo : 49/50 ventes utilisées — limite presque atteinte.")
    print(f"{'='*50}\n")


def main():
    print(f"\n{'='*50}")
    print("  REMPLISSAGE BASE DE DONNÉES TEST")
    print(f"{'='*50}\n")
    try:
        ids = remplir_produits()
        ca = remplir_ventes(ids)
        afficher_resume(ca)
        # Synchroniser le compteur démo avec le nb de ventes créées
        db.set_parametre('licence_demo_ventes', str(len(VENTES)))
        print(f"  Compteur démo mis à jour : {len(VENTES)}/50")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    main()
