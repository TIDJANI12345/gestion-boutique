# Cahier des charges — POS Professionnel Mono-Poste
## HISHIpos v2.0 — Boutique Bénin / Afrique de l'Ouest

> Référentiel établi le 2026-05-04.
> Contraintes : SQLite offline, 1 PC Celeron 4 Go RAM, 1–3 employés, extensible.

---

## PARTIE 1 : CE QU'UN POS PRO DOIT AVOIR

| # | Fonctionnalité | Utilité concrète Bénin | Priorité |
|---|---|---|---|
| **VENTES** | | | |
| 1 | Vente rapide (panier) | Encaisser vite, file d'attente courte | Critique |
| 2 | Scan code-barres | Éviter erreurs de prix, accélérer | Critique |
| 3 | Recherche produit | Trouver sans code-barres | Critique |
| 4 | Calcul monnaie à rendre | Éviter erreurs caissier | Critique |
| 5 | Modes de paiement multiples | Espèces + Orange Money + Wave + MTN | Critique |
| 6 | Paiement mixte (split) | Client paie moitié espèces, moitié mobile | Important |
| 7 | Remise manuelle | Négociation courante en boutique | Important |
| 8 | Annulation de vente | Erreur caissier | Critique |
| 9 | Reçu imprimé (thermique) | Preuve d'achat client | Critique |
| 10 | Reçu PDF | Envoi WhatsApp, archivage | Important |
| 11 | Prix de gros automatique | Grossiste paie moins dès X unités | Important |
| 12 | Unité de mesure par produit | Vente au kg, litre, sachet | Important |
| **SESSION DE CAISSE** | | | |
| 13 | Ouverture de caisse (fond) | Déclarer le cash disponible en début de journée | Critique |
| 14 | Clôture Z (rapport fin journée) | Vérifier si la caisse est juste | Critique |
| 15 | Rapport X (état intermédiaire) | Contrôle en cours de journée sans clôturer | Important |
| 16 | Comptage espèces à la clôture | Détecter les écarts caisse | Critique |
| 17 | Historique des clôtures | Traçabilité comptable | Important |
| **PRODUITS & STOCK** | | | |
| 18 | CRUD produits | Ajouter, modifier, supprimer | Critique |
| 19 | Catégories | Ranger : Alimentaire, Hygiène, etc. | Important |
| 20 | Alertes stock bas | Savoir quoi réapprovisionner | Critique |
| 21 | Historique mouvements stock | Tracer entrées/sorties | Important |
| 22 | Ajustement stock manuel | Correction inventaire, pertes, casse | Critique |
| 23 | Inventaire physique (comptage) | Vérification périodique réel vs système | Important |
| 24 | Images produit | Identifier visuellement | Confort |
| 25 | Code-barres multiples types | EAN-13, Code128 selon fournisseur | Important |
| 26 | Import produits (CSV/Excel) | Éviter saisie manuelle de 500 produits | Important |
| 27 | Prix d'achat + marge | Savoir si on est rentable | Critique |
| **CLIENTS** | | | |
| 28 | Fiche client | Nom, téléphone, historique achats | Important |
| 29 | Fidélité (points) | Récompenser les clients réguliers | Confort |
| 30 | Historique achats client | Voir ce qu'il a acheté | Important |
| 31 | Crédit client (ardoise) | Pratique courante Afrique : "noter" | Critique |
| **RAPPORTS** | | | |
| 32 | CA du jour / semaine / mois | Savoir combien on a gagné | Critique |
| 33 | Top produits vendus | Savoir quoi stocker en priorité | Important |
| 34 | Rapport par caissier | Contrôler chaque employé | Important |
| 35 | Rapport par mode paiement | Séparer espèces vs mobile money | Important |
| 36 | Rapport TVA mensuel | Déclaration fiscale DGI Bénin | Important |
| 37 | Bénéfice brut | Prix vente - Prix achat | Critique |
| 38 | Rapport stock valorisé | Valeur du stock en FCFA | Important |
| 39 | Export rapport (Excel/PDF) | Envoyer au comptable | Important |
| **FISCALITÉ BÉNIN** | | | |
| 40 | TVA 18% paramétrable | Obligation DGI pour commerçants formels | Important |
| 41 | IFU + RCCM sur reçus | Obligation légale Bénin | Important |
| 42 | Devise FCFA | Affichage sans décimales | Critique |
| **UTILISATEURS** | | | |
| 43 | Multi-utilisateurs + rôles | Patron / Gestionnaire / Caissier | Critique |
| 44 | Mot de passe sécurisé | Empêcher accès non autorisé | Critique |
| 45 | Logs d'audit | Voir qui a fait quoi | Important |
| 46 | Timeout session | Déconnexion auto si inactivité | Important |
| **SYSTÈME** | | | |
| 47 | Sauvegarde automatique | Ne pas perdre les données | Critique |
| 48 | Restauration | Récupérer après crash | Critique |
| 49 | Export ZIP complet | Transférer vers nouveau PC | Important |
| 50 | Fonctionne offline | Bénin = coupures réseau fréquentes | Critique |
| 51 | Rapide sur PC bas de gamme | Celeron 4 Go RAM | Critique |
| 52 | Mise à jour automatique | Recevoir les nouvelles versions | Confort |
| **IMPRESSION** | | | |
| 53 | Imprimante thermique 58mm/80mm | Standard boutique Bénin | Critique |
| 54 | Test d'impression | Vérifier la config | Important |
| 55 | Logo boutique sur ticket | Image de marque | Confort |
| 56 | QR code sur ticket | Vérification reçu | Confort |

---

## PARTIE 2 : ÉTAT DES LIEUX HISHIpos v2.0

| # | Fonctionnalité | Priorité | Statut | Fichier |
|---|---|---|---|---|
| **VENTES** | | | | |
| 1 | Vente rapide (panier) | Critique | ✅ FAIT | `ui/windows/ventes.py` |
| 2 | Scan code-barres (caméra) | Critique | ✅ FAIT | `modules/scanner_camera.py` |
| 3 | Recherche produit | Critique | ✅ FAIT | `ui/windows/ventes.py` |
| 4 | Calcul monnaie à rendre | Critique | ✅ FAIT | `ui/windows/paiement.py` |
| 5 | Modes de paiement multiples | Critique | ✅ FAIT | `modules/paiements.py` (espèces, Orange, Wave, MTN, carte…) |
| 6 | Paiement mixte (split) | Important | ✅ FAIT | `modules/paiements.py::enregistrer_paiement_mixte()` |
| 7 | Remise manuelle | Important | ✅ FAIT | `ui/windows/ventes.py` + colonne `remise` |
| 8 | Annulation de vente | Critique | 🟡 PARTIEL | `modules/ventes.py` (soft-delete) — pas d'UI dédiée |
| 9 | Reçu thermique | Critique | ✅ FAIT | `modules/imprimante.py` |
| 10 | Reçu PDF | Important | ✅ FAIT | `modules/recus.py` |
| 11 | Prix de gros auto | Important | ✅ FAIT | `modules/ventes.py` + `prix_gros` / `seuil_gros` |
| 12 | Unité de mesure | Important | ✅ FAIT | `modules/produits.py` + migration `database.py` |
| **SESSION DE CAISSE** | | | | |
| 13 | Ouverture de caisse (fond) | Critique | ❌ À FAIRE | — |
| 14 | Clôture Z | Critique | ❌ À FAIRE | — |
| 15 | Rapport X (intermédiaire) | Important | ❌ À FAIRE | — |
| 16 | Comptage espèces clôture | Critique | ❌ À FAIRE | — |
| 17 | Historique clôtures | Important | ❌ À FAIRE | — |
| **PRODUITS & STOCK** | | | | |
| 18 | CRUD produits | Critique | ✅ FAIT | `ui/windows/produits.py` |
| 19 | Catégories | Important | ✅ FAIT | `ui/windows/gestion_categories.py` |
| 20 | Alertes stock bas | Critique | ✅ FAIT | `modules/produits.py` + `stock_alerte` |
| 21 | Historique mouvements stock | Important | ✅ FAIT | table `historique_stock` |
| 22 | Ajustement stock manuel | Critique | 🟡 PARTIEL | Via modifier produit — pas d'UI dédiée avec motif |
| 23 | Inventaire physique | Important | ❌ À FAIRE | — |
| 24 | Images produit | Confort | 🟡 PARTIEL | `config.IMAGES_DIR` + code-barres — pas d'upload photo produit |
| 25 | Code-barres multiples types | Important | ✅ FAIT | `modules/codebarres.py` (EAN-13, EAN-8, Code128) |
| 26 | Import CSV/Excel | Important | ❌ À FAIRE | — |
| 27 | Prix achat + marge | Critique | ✅ FAIT | colonne `prix_achat` + `modules/rapports.py` |
| **CLIENTS** | | | | |
| 28 | Fiche client | Important | ✅ FAIT | `modules/clients.py` + `ui/windows/clients.py` |
| 29 | Fidélité (points) | Confort | ✅ FAIT | colonne `points_fidelite` dans `clients` |
| 30 | Historique achats client | Important | ✅ FAIT | `total_achats`, `nombre_achats` |
| 31 | **Crédit client (ardoise)** | **Critique** | ❌ **À FAIRE** | — |
| **RAPPORTS** | | | | |
| 32 | CA jour / semaine / mois | Critique | ✅ FAIT | `modules/rapports.py` |
| 33 | Top produits | Important | ✅ FAIT | `modules/rapports.py::top_produits()` |
| 34 | Rapport par caissier | Important | ✅ FAIT | filtrage par `utilisateur_id` |
| 35 | Rapport par mode paiement | Important | ✅ FAIT | `modules/paiements.py::rapport_caisse_jour()` |
| 36 | Rapport TVA mensuel | Important | ✅ FAIT | `modules/fiscalite.py::rapport_tva_mensuel()` |
| 37 | Bénéfice brut | Critique | 🟡 PARTIEL | `prix_achat` présent — pas affiché en dashboard |
| 38 | Stock valorisé | Important | ✅ FAIT | `modules/produits.py::valeur_stock_total()` |
| 39 | Export rapport Excel/PDF | Important | 🟡 PARTIEL | Export ZIP OK — pas d'export rapport Excel |
| **FISCALITÉ** | | | | |
| 40 | TVA 18% | Important | ✅ FAIT | `modules/fiscalite.py` |
| 41 | IFU + RCCM sur reçus | Important | ✅ FAIT | paramètres + `modules/recus.py` |
| 42 | Devise FCFA | Critique | ✅ FAIT | `modules/fiscalite.py::get_devise()` |
| **UTILISATEURS** | | | | |
| 43 | Multi-utilisateurs + rôles | Critique | ✅ FAIT | `modules/utilisateurs.py` + `modules/permissions.py` |
| 44 | Mot de passe (bcrypt) | Critique | ✅ FAIT | `modules/utilisateurs.py` |
| 45 | Logs d'audit | Important | ✅ FAIT | `ui/windows/logs_audit.py` |
| 46 | Timeout session | Important | ✅ FAIT | paramètre `session_timeout` |
| **SYSTÈME** | | | | |
| 47 | Sauvegarde auto | Critique | ✅ FAIT | `modules/sauvegarde.py::sauvegarde_auto_si_necessaire()` |
| 48 | Restauration | Critique | ✅ FAIT | `ui/windows/sauvegarde.py` |
| 49 | Export ZIP | Important | ✅ FAIT | `modules/sauvegarde.py::exporter_zip()` |
| 50 | Offline total | Critique | ✅ FAIT | SQLite, aucune dépendance réseau |
| 51 | Léger (PC bas de gamme) | Critique | ✅ FAIT | PySide6 + SQLite |
| 52 | Mise à jour auto | Confort | ✅ FAIT | `modules/updater.py` + GitHub Releases API |
| **IMPRESSION** | | | | |
| 53 | Thermique 58mm / 80mm | Critique | ✅ FAIT | `modules/imprimante.py` |
| 54 | Test d'impression | Important | ✅ FAIT | `ImprimanteThermique.imprimer_test()` |
| 55 | Logo sur ticket | Confort | ✅ FAIT | `modules/imprimante.py` (PIL) |
| 56 | QR code ticket | Confort | ✅ FAIT | `modules/imprimante.py` (qrcode) |

---

## RÉSUMÉ

| Statut | Critique | Important | Confort | Total |
|---|---|---|---|---|
| ✅ FAIT | 16 | 20 | 4 | **40** |
| 🟡 PARTIEL | 2 | 3 | 1 | **6** |
| ❌ À FAIRE | 5 | 4 | 0 | **9** |

---

## LACUNES PRIORITAIRES (ordre d'implémentation recommandé)

### Critiques manquantes
1. **Session de caisse** — ouverture (fond de caisse) + clôture Z + comptage espèces + historique (5 features d'un coup)
2. **Crédit client / ardoise** — pratique incontournable en Afrique de l'Ouest
3. **Annulation de vente** — UI dédiée (le soft-delete existe en base, il manque juste l'interface)
4. **Ajustement stock avec motif** — UI dédiée (Perte / Casse / Correction / Entrée fournisseur)

### Importantes manquantes
5. **Import CSV produits** — indispensable pour les boutiques avec catalogue existant
6. **Inventaire physique** — comptage réel vs système, rapport d'écart
7. **Bénéfice brut en dashboard** — visible d'un coup d'œil
8. **Export rapport Excel** — pour le comptable

---

*Référentiel basé sur Odoo POS, Lightspeed, Loyverse — version mono-poste offline.*
*Adapté au contexte Bénin : FCFA, TVA 18%, IFU/RCCM, mobile money (Orange/Wave/MTN).*
