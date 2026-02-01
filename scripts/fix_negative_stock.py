#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de correction des stocks négatifs existants

USAGE:
    python scripts/fix_negative_stock.py

Ce script:
1. Trouve tous les produits avec un stock négatif
2. Affiche la liste
3. Réinitialise le stock à 0 pour chaque produit

IMPORTANT: Exécuter AVANT d'ajouter le TRIGGER de validation du stock.
"""
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db
from modules.logger import get_logger

logger = get_logger(__name__)


def corriger_stocks_negatifs():
    """Corriger tous les stocks négatifs en les mettant à 0"""
    print("=" * 60)
    print("CORRECTION DES STOCKS NÉGATIFS")
    print("=" * 60)
    print()

    # Trouver stocks négatifs
    negatifs = db.fetch_all(
        "SELECT id, nom, stock_actuel, code_barre FROM produits WHERE stock_actuel < 0"
    )

    if not negatifs:
        print("✓ Aucun stock négatif trouvé")
        print("  La base de données est propre!")
        return 0

    print(f"⚠️  ATTENTION: {len(negatifs)} produit(s) avec stock négatif détecté(s):")
    print()

    for prod in negatifs:
        id_produit, nom, stock, code_barre = prod
        print(f"  - ID {id_produit}: {nom}")
        print(f"    Code-barres: {code_barre}")
        print(f"    Stock actuel: {stock}")
        print()

    # Demander confirmation
    reponse = input("Voulez-vous réinitialiser ces stocks à 0 ? (oui/non): ")

    if reponse.lower() not in ['oui', 'o', 'yes', 'y']:
        print("\nOpération annulée")
        return 1

    print("\nCorrection en cours...")

    # Corriger chaque produit
    corriges = 0
    for prod in negatifs:
        id_produit = prod[0]
        try:
            # Mettre à jour le stock à 0
            db.execute_query(
                "UPDATE produits SET stock_actuel = 0, updated_at = datetime('now') WHERE id = ?",
                (id_produit,)
            )

            # Enregistrer dans l'historique
            db.execute_query(
                """INSERT INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation)
                   VALUES (?, ?, 0, 'Correction stock négatif')""",
                (id_produit, prod[2])
            )

            corriges += 1
            logger.info(f"Stock corrigé pour produit ID {id_produit}: {prod[2]} → 0")

        except Exception as e:
            logger.error(f"Erreur lors de la correction du produit ID {id_produit}: {e}")
            print(f"✗ Erreur pour produit ID {id_produit}")

    print(f"\n✓ {corriges} produit(s) corrigé(s)")
    print("\nLa base de données est maintenant propre.")
    print("\nVous pouvez maintenant activer le TRIGGER de validation du stock.")

    return 0


if __name__ == "__main__":
    try:
        exit_code = corriger_stocks_negatifs()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Erreur fatale: {e}")
        print(f"\n✗ Erreur fatale: {e}")
        sys.exit(1)
