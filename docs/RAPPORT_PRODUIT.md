# Gestion Boutique Pro — Rapport Produit

> Version 2.2.0 · Logiciel de caisse et gestion commerciale  
> Éditeur : Hisham Digital · [hishamdigital.com](https://hishamdigital.com/boutique/gestion-boutique-pro-perpetuelle)

---

## Table des matières

1. [Présentation](#1-présentation)
2. [Fonctionnalités détaillées](#2-fonctionnalités-détaillées)
3. [Pourquoi acheter ce logiciel](#3-pourquoi-acheter-ce-logiciel)
4. [Grille tarifaire recommandée](#4-grille-tarifaire-recommandée)
5. [État de qualité & honnêteté](#5-état-de-qualité--honnêteté)
6. [Roadmap suggérée](#6-roadmap-suggérée)

---

## 1. Présentation

**Gestion Boutique Pro** est un logiciel de point de vente (POS) conçu spécifiquement pour les commerces de détail en Afrique de l'Ouest. Il fonctionne **entièrement hors ligne**, sans abonnement mensuel, et s'installe sur n'importe quel PC Windows.

### Pour qui ?

| Type de commerce | Adapté ? |
|---|---|
| Épiceries, alimentations générales | ✅ |
| Boutiques de vêtements / chaussures | ✅ |
| Pharmacies / cosmétiques | ✅ |
| Quincailleries | ✅ |
| Supérettes et minimarchés | ✅ |
| Grossistes avec revendeurs | ✅ |

### Contexte technique

- **Plateforme** : Windows 10/11 (64-bit)
- **Installation** : Exécutable `.exe` — aucune installation Python requise
- **Base de données** : SQLite locale (données sur le PC du client)
- **Connexion internet** : Requise uniquement pour l'activation de la licence
- **Devise par défaut** : FCFA (XOF) — modifiable

---

## 2. Fonctionnalités détaillées

### 2.1 Point de vente (Caisse)

- Saisie produits par **scan code-barres** (scanner USB/Bluetooth) ou recherche manuelle
- Panier en temps réel avec calcul automatique du total
- **4 modes de paiement** : Espèces, Mobile Money, Virement bancaire, Chèque
- **Paiement mixte** : combiner plusieurs modes pour une même vente
- Calcul automatique de la **monnaie à rendre** (mode espèces)
- Référence de transaction pour Mobile Money (Orange Money, MTN MoMo, Wave, Moov)
- Validation du stock avant validation de la vente
- Raccourcis clavier pour une caisse rapide (F1, Ctrl+P, Ctrl+A…)

### 2.2 Gestion des produits

- Ajout, modification, suppression de produits
- **Génération automatique de codes-barres** (EAN-13, EAN-8, Code 128)
- Validation du checksum EAN (intégrité des codes)
- Suivi du **stock en temps réel** avec seuil d'alerte configurable
- Historique de chaque mouvement de stock (qui, quand, combien)
- Catégorisation libre des produits
- Recherche et filtres avancés (catégorie, stock faible, rupture, fourchette de prix)
- Pagination (10 produits par page)

### 2.3 Gestion des clients & fidélité

- Fiche client complète (nom, téléphone, email, notes)
- **Programme de fidélité** : accumulation de points à chaque achat
- Remise automatique au franchissement d'un seuil de points
- Consultation de l'historique d'achats par client
- Recherche client (nom, téléphone, email)

### 2.4 Reçus et impressions

**Reçu PDF (professionnel) :**
- Logo de la boutique en en-tête et filigrane
- QR code unique par vente (scannable)
- Décomposition TVA (HT / TVA / TTC) si activée
- Détail du paiement (mode, montant reçu, monnaie rendue)
- Points de fidélité du client
- Informations boutique personnalisables (adresse, téléphone, email)

**Ticket thermique ESC/POS :**
- Compatible imprimantes 58 mm et 80 mm
- Connexion USB, réseau (TCP/IP) ou port série (COM)
- Format adapté automatiquement à la largeur du papier
- QR code sur ticket (optionnel)
- Impression automatique après chaque vente (configurable)

### 2.5 Rapports et statistiques

| Rapport | Contenu |
|---|---|
| **Vue d'ensemble** | Ventes du jour, CA jour/mois/total, valeur du stock |
| **Top produits** | 20 produits les plus vendus (quantité + CA) |
| **Rapprochement caisse** | Totaux par mode de paiement, nb transactions |
| **TVA mensuelle** | Total TTC, HT, TVA collectée — sélecteur mois/année |
| **Stock faible** | Produits sous le seuil d'alerte |
| **Comparaison** | Variation CA vs jour précédent (%) |

Export **Excel** disponible depuis l'onglet rapports.

### 2.6 Fiscalité et devises

- TVA activable/désactivable globalement
- Taux TVA par défaut configurable (18 % par défaut — Bénin)
- **Taux TVA différenciés par catégorie** de produits
- Multi-devises : FCFA, GNF, NGN, USD, EUR…
- Conversion de montants entre devises

### 2.7 Gestion des utilisateurs et accès

**3 niveaux de rôles :**

| Rôle | Droits |
|---|---|
| **Patron (Super-Admin)** | Accès total : utilisateurs, rapports, paramètres, sauvegarde, ventes |
| **Gestionnaire** | Produits, stocks, clients, ses ventes, catégories |
| **Caissier** | Ventes uniquement, consultation de ses propres ventes |

- Authentification par email + mot de passe (hachage bcrypt)
- Politique de mot de passe fort (8 caractères minimum, 1 chiffre)
- Activation / désactivation de comptes sans suppression
- Un seul compte patron possible (protection anti-fraude)

### 2.8 Audit et traçabilité

- Chaque action est enregistrée : qui, quoi, quand
- Journal consultable par le patron
- Traçabilité des connexions et déconnexions
- Historique des annulations de ventes

### 2.9 Sauvegarde et restauration

- Sauvegarde locale horodatée (10 dernières conservées)
- Sauvegarde automatique en arrière-plan toutes les 24 h
- Export complet en ZIP (base de données + images + reçus PDF)
- Restauration depuis un fichier de sauvegarde avec backup préalable automatique

### 2.10 Export WhatsApp catalogue

- Génération automatique d'un **message catalogue formaté** pour revendeurs
- Groupement par catégorie, affichage des stocks, filtrage produits disponibles
- Copie en un clic dans le presse-papiers → collage direct dans WhatsApp

### 2.11 Configuration avancée

- **Préférences caisse** : mode scan (auto / manuel / unique), impression auto, fidélité
- **Modes de paiement** : activer/désactiver chaque mode individuellement
- **Informations boutique** : nom, adresse, téléphone, email (apparaissent sur les reçus)
- **Thème** : mode clair / mode sombre avec persistance

### 2.12 Protection et licence

- Licence activée en ligne lors de la première installation
- Licence liée à la machine (anti-copie)
- Activation via serveur sécurisé (gbserver.pythonanywhere.com)
- Aucun abonnement mensuel — **licence perpétuelle**

---

## 3. Pourquoi acheter ce logiciel

### ✅ Fait pour l'Afrique de l'Ouest

La plupart des logiciels de caisse sur le marché sont conçus pour l'Europe ou l'Amérique. Gestion Boutique Pro intègre nativement la devise FCFA, la TVA à 18 % (taux béninois), les opérateurs Mobile Money locaux (Orange Money, MTN MoMo, Wave, Moov), et une interface entièrement en français.

### ✅ Aucun abonnement — licence à vie

Contrairement aux solutions cloud (Shopify POS, Lightspeed, Square) qui facturent entre 20 000 et 100 000 FCFA par mois, Gestion Boutique Pro s'achète une seule fois. Pas de frais récurrents, pas de dépendance à internet pour les ventes quotidiennes.

### ✅ Fonctionne sans internet

La caisse continue de fonctionner même en cas de coupure réseau. Internet n'est nécessaire qu'à l'activation initiale.

### ✅ Tout-en-un

Un seul logiciel couvre : la caisse, la gestion des stocks, les clients, la fidélité, les rapports, la comptabilité TVA, l'impression thermique, les PDF de reçus et l'export catalogue WhatsApp. Aucun module additionnel à acheter.

### ✅ Multi-utilisateurs avec contrôle des accès

Le patron garde le contrôle total. Les caissiers voient uniquement ce dont ils ont besoin. Les gestionnaires peuvent gérer les stocks sans accéder aux finances. Les données sont protégées.

### ✅ Rapports pour décider

Savoir quels produits se vendent le mieux, identifier les ruptures de stock avant qu'elles surviennent, rapprocher la caisse en fin de journée, générer le rapport TVA mensuel — tout est là, sans tableur Excel à remplir manuellement.

---

## 4. Grille tarifaire recommandée

### Principe : licence perpétuelle par poste

Le modèle recommandé est une **licence par installation** (par PC) à paiement unique, avec une option d'assistance.

| Formule | Prix recommandé | Contenu |
|---|---|---|
| **Licence Solo** | **35 000 FCFA** | 1 PC, 1 point de vente, licence à vie |
| **Licence Pro** | **55 000 FCFA** | 1 PC, 1 point de vente, licence à vie + 3 mois de support WhatsApp |
| **Licence Multi-poste** | **85 000 FCFA** | Jusqu'à 3 PC (même boutique), licence à vie + 6 mois support |

> **Équivalences** : 35 000 FCFA ≈ 53 € ≈ 58 USD

### Justification du positionnement

- **Logiciels cloud africains concurrents** (GestProf, Logicaisse…) : 10 000–25 000 FCFA/mois
- **En 2 mois**, le client récupère son investissement vs un abonnement
- **Prix accessible** pour les petits commerces tout en valorisant la qualité du produit
- Pas de dumping : un prix trop bas décrédibilise le logiciel

### Options additionnelles (à la carte)

| Service | Prix |
|---|---|
| Installation + formation sur site (Cotonou) | 15 000 FCFA |
| Support WhatsApp 1 an | 20 000 FCFA |
| Personnalisation logo sur reçus | Inclus |
| Migration données depuis Excel | 10 000 FCFA |

---

## 5. État de qualité & honnêteté

### Ce qui fonctionne bien ✅

| Domaine | État |
|---|---|
| Architecture du code | Propre — séparation modules/UI respectée |
| Flux de vente complet | Fonctionnel de bout en bout |
| Système de rôles et permissions | Robuste et bien pensé |
| Génération PDF | Professionnel |
| Système de licence | Opérationnel |
| Thème clair/sombre | Fonctionnel (corrections en cours) |
| Sauvegarde automatique | Fiable |
| Modes de paiement | Complets pour le contexte local |

### Ce qui est en cours d'amélioration ⚠️

| Point | Détail |
|---|---|
| Interface mode sombre | Quelques fenêtres avaient des couleurs hardcodées — corrigées progressivement |
| Cohérence visuelle boutons | Hiérarchie des couleurs (primaire/secondaire/danger) en cours d'uniformisation |
| Messages de debug | Des `print("DEBUG: …")` restent dans `ventes.py` — à supprimer avant livraison |
| Gestion des catégories | Logique améliorée (dropdown simple + bouton +) |

### Ce qui manque pour une v1.0 commerciale solide 🔲

| Fonctionnalité | Priorité |
|---|---|
| Suppression des `print` de debug | Haute |
| Tests automatisés complets | Moyenne |
| Manuel utilisateur PDF | Haute |
| Vidéo de démonstration | Haute |
| Page de téléchargement sécurisée sur le site | Haute |
| Gestion des retours produits | Moyenne |
| Tableaux de bord plus visuels (graphiques en camembert) | Basse |

### Note globale

> **7,5 / 10** — Logiciel fonctionnellement complet pour un commerce de détail standard. La base technique est saine. Les points à régler avant commercialisation intensive sont essentiellement cosmétiques et documentaires, pas structurels.

---

## 6. Roadmap suggérée

### Court terme (avant première vente)
- [ ] Supprimer tous les `print` de debug dans le code
- [ ] Tester le flux complet : activation licence → première vente → reçu PDF → rapport
- [ ] Rédiger un guide utilisateur d'une page (démarrage rapide)
- [ ] Préparer une vidéo démo de 3 minutes pour le site

### Moyen terme (après premières ventes)
- [ ] Gestion des retours / remboursements partiels
- [ ] Alertes stock par notification Windows
- [ ] Import produits depuis Excel (CSV)
- [ ] Dashboard graphique amélioré (courbes, camemberts)

### Long terme (v2.x)
- [ ] Application mobile compagnon (consultation stock à distance)
- [ ] Synchronisation multi-boutiques (pour les grossistes avec succursales)
- [ ] Module comptabilité simplifié (dépenses, bénéfice net)

---

*Rapport généré le 04/05/2026 · Gestion Boutique Pro v2.2.0*
