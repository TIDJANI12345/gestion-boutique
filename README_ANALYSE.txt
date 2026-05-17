================================================================================
   GESTION BOUTIQUE v2 — ANALYSE COMPLÈTE DU SYSTÈME EXISTANT
   Préparée pour reconstruction en Electron.js + React + SQLite
   Date d'analyse : 2026-05-17
   Analyste : Contexte métier & fonctionnel pour refactorisation complète
================================================================================

IMPORTANT : Ce document sert de référence métier/fonctionnelle uniquement.
Le code source Python/PySide6 ne doit PAS être converti directement.
L'objectif est une reconstruction moderne from scratch.

--------------------------------------------------------------------------------
TABLE DES MATIÈRES
--------------------------------------------------------------------------------
  1. PRÉSENTATION DU LOGICIEL
  2. MODULES EXISTANTS (18 modules métier)
  3. ARCHITECTURE ACTUELLE
  4. TECHNOLOGIES UTILISÉES
  5. WORKFLOWS MÉTIER
  6. FONCTIONNALITÉS DÉTAILLÉES
  7. LIMITATIONS TECHNIQUES
  8. PROBLÈMES ACTUELS
  9. PISTES D'AMÉLIORATION
 10. RECOMMANDATIONS POUR ELECTRON.JS + REACT + SQLITE
 11. RÉSUMÉ GLOBAL (contexte pour reconstruction)

================================================================================
 1. PRÉSENTATION DU LOGICIEL
================================================================================

Nom            : GestionBoutique v2
Type           : Système de Point de Vente (POS) pour commerce de détail
Version        : 2.5.0
Marché cible   : Bénin (Afrique de l'Ouest)
Devise         : FCFA (Franc CFA)
TVA            : 18% (configurable par catégorie)
Framework UI   : PySide6 (migration depuis Tkinter — terminée)
Base de données: SQLite (fichier local)
Langage        : Python 3.11+

Déploiement    :
  - Windows : EXE via PyInstaller + Inno Setup
  - Linux   : AppImage / .deb
  - macOS   : .app + .dmg

Le logiciel gère un commerce de détail complet : ventes, stock, clients,
crédits (ardoise), fournisseurs, reçus PDF, impression thermique, rapports,
multi-utilisateurs avec rôles, mode réseau multi-caisses.

--------------------------------------------------------------------------------
Contexte commercial :
  - Boutiques physiques (alimentaire, textile, électronique, etc.)
  - 1 à N caisses simultanées sur réseau local (selon le plan)
  - Paiements multiples : espèces + Mobile Money Bénin
  - Système de licences par plan (Demo/Standard/Pro/White Label)

================================================================================
 2. MODULES EXISTANTS (18 modules métier)
================================================================================

Tous les modules sont dans /modules/ et sont INDÉPENDANTS de l'UI.
Principe respecté : aucun import PySide6 dans ces modules.

MODULE              | TAILLE  | RÔLE
--------------------|---------|------------------------------------------------------
ventes.py           | ~203 l  | Moteur des ventes — création, annulation, calculs
produits.py         | ~351 l  | CRUD produits, codes-barres, stock, prix gros/détail
clients.py          | ~211 l  | Profils clients, points de fidélité, historique
utilisateurs.py     | ~213 l  | Auth bcrypt, hiérarchie des rôles, gestion comptes
permissions.py      | ~150 l  | Système RBAC (3 niveaux) — vérification des droits
rapports.py         | ~289 l  | Statistiques, analyses, données pour graphiques
imprimante.py       | ~387 l  | Impression thermique ESC/POS (USB/série/réseau)
recus.py            | ~926 l  | Génération reçus PDF via ReportLab
sessions.py         | ~229 l  | Sessions de caisse (ouverture/clôture Z)
ardoise.py          | ~200 l  | Crédits clients — suivi, encaissements partiels
paiements.py        | ~172 l  | Modes de paiement, Mobile Money Bénin
codebarres.py       | ~150 l  | Génération codes-barres (Code128, EAN-13, QR)
fournisseurs.py     | ~164 l  | Répertoire fournisseurs, commandes, réceptions
import_csv.py       | ~163 l  | Import produits en lot depuis CSV (validation)
features.py         | ~336 l  | Feature flags par plan — chiffrement Fernet
licence.py          | ~194 l  | Validation/activation licences (machine binding)
sync_client.py      | ~339 l  | Synchronisation réseau local (client multi-caisse)
sauvegarde.py       | ~280 l  | Backup/restore automatique et manuel (ZIP)
logger.py           | ~80 l   | Logging centralisé (rotating file handler)
fiscalite.py        | ~120 l  | Gestion TVA par catégorie, multi-devises
updater.py          | ~191 l  | Vérification MAJ depuis GitHub Releases API
whatsapp.py         | ~162 l  | Envoi catalogues/messages WhatsApp Web
ia_extraction.py    | ~338 l  | Extraction IA via Google Generative AI (optionnel)
scanner_camera.py   | ~100 l  | Scan codes-barres via caméra (OpenCV + pyzbar)
reseau.py           | ~100 l  | Abstraction réseau local (module facade)
client_reseau.py    | ~120 l  | Communication HTTP avec serveur local

================================================================================
 3. ARCHITECTURE ACTUELLE
================================================================================

3.1 STRUCTURE GLOBALE
---------------------

GestionBoutique_v2/
├── main.py                       # Orchestrateur : Splash → Licence → Login → Dashboard
├── config.py                     # Configuration multiplateforme (chemins, ports)
├── database.py                   # Singleton SQLite (~608 lignes)
├── requirements.txt              # Dépendances pip
├── modules/                      # 18+ modules logique métier (sans UI)
├── ui/
│   ├── theme.py                  # Styles QSS globaux (dark/light mode)
│   ├── platform.py               # Détection OS, ports série
│   ├── components/               # Composants réutilisables (table, dialogs, etc.)
│   └── windows/                  # 35 fenêtres PySide6
├── serveur_local/
│   ├── api_locale.py             # API Flask (mode multi-caisse serveur)
│   └── discovery.py             # Découverte automatique du serveur
├── serveur_licence/              # Back-end licence (PythonAnywhere)
├── serveur_sync/                 # API sync cloud
├── tests/                        # Suite pytest (15+ fichiers)
├── docs/                         # Documentation extensive (20+ fichiers MD)
└── scripts/                      # Scripts utilitaires

3.2 COUCHE BASE DE DONNÉES — 15 TABLES SQLite
----------------------------------------------

TABLE                         | DESCRIPTION
------------------------------|----------------------------------------------------
produits                      | Catalogue produits (nom, prix, stock, code-barres)
ventes                        | En-tête des ventes (numéro, total, date, statut)
details_ventes                | Lignes de vente (produit, qté, prix, sous-total)
paiements                     | Paiements par vente (mode, montant, référence)
clients                       | Profils clients (nom, tel, email, fidélité)
utilisateurs                  | Comptes utilisateurs (role, bcrypt, super_admin)
sessions_caisse               | Sessions caisse (fond, totaux par mode, clôture Z)
ardoise                       | Crédits clients (montant initial/restant, statut)
encaissements_ardoise         | Paiements partiels d'ardoise
fournisseurs                  | Répertoire fournisseurs
commandes_fournisseurs        | En-têtes commandes fournisseur
details_commandes_fournisseurs| Lignes commandes fournisseur
historique_stock              | Journal des mouvements de stock
taux_tva                      | Taux TVA par catégorie
devises                       | Multi-devises avec taux de change
logs_actions                  | Audit trail (toutes actions utilisateurs)
parametres                    | Config clé-valeur (boutique, réseau, etc.)

COLONNES TABLE VENTES (toutes colonnes) :
  id, numero_vente, date_vente, total, client, utilisateur_id, statut,
  deleted_at, client_id, remise, nom_caisse, montant_recu, monnaie,
  mode_paiement, note, is_ardoise, id_session, motif_annulation

COLONNES TABLE PRODUITS :
  id, nom, categorie, prix_achat, prix_vente, stock_actuel, stock_alerte,
  code_barre, type_code_barre, date_ajout, description, image_path,
  prix_gros, seuil_gros, unite_mesure, actif, is_lot, quantite_lot

3.3 COUCHE UI — 35 FENÊTRES PYSIDE6
-------------------------------------

Dashboards (3) :
  principale.py              → Dashboard Patron/Admin (accès total)
  principale_gestionnaire.py → Dashboard Gestionnaire (stocks/produits)
  principale_caissier.py     → Dashboard Caissier (ventes uniquement)

Ventes (5) :
  ventes.py                  → Interface de vente principale (55K — la plus complexe)
  paiement.py                → Modal paiement (21K)
  confirmation_vente.py      → Confirmation après vente
  annulation_vente.py        → Annulation avec motif
  liste_ventes.py            → Historique des ventes (16K)

Catalogue (3) :
  produits.py                → CRUD produits (31K)
  gestion_categories.py      → Catégories produits
  import_csv.py              → Import lot depuis CSV

Clients & Crédit (2) :
  clients.py                 → Gestion clients (17K)
  ardoise.py                 → Gestion crédits clients (14K)

Fournisseurs (1) :
  fournisseurs.py            → Fournisseurs + commandes (21K)

Rapports (1) :
  rapports.py                → Statistiques et analyses (23K)

Paramètres (5) :
  parametres_boutique.py     → Nom, logo, coordonnées boutique
  parametres_paiement.py     → Modes de paiement actifs
  parametres_fiscaux.py      → TVA, devises
  preferences_caisse.py      → Préférences caissier (20K)
  config_reseau.py           → Mode standalone/serveur/client

Auth & Système (8) :
  login.py, licence.py, premier_lancement.py,
  splash.py, a_propos.py, plans.py,
  sauvegarde.py, utilisateurs.py

Avancé (6) :
  whatsapp.py, import_whatsapp.py, ecran_client.py,
  historique_clotures.py, logs_audit.py, plans.py

3.4 SYSTÈME DE LICENCES PAR PLAN
----------------------------------

PLAN        | CAISSES | TERMINAUX | FONCTIONNALITÉS
------------|---------|-----------|------------------------------------------
Demo        |    1    |     1     | Limité (30 jours), watermark reçus
Standard    |    1    |     1     | Fonctionnalités core
Pro         |   N     |    N      | Multi-caisse, toutes fonctionnalités
White Label |   N     |    N      | Logo personnalisé, branding custom

Machine binding : SHA256(node + OS + machine + uuid)
Serveur licence : PythonAnywhere (API REST)
Chiffrement feature flags : Fernet (cryptography)

================================================================================
 4. TECHNOLOGIES UTILISÉES
================================================================================

COUCHE          | TECHNOLOGIE          | VERSION    | USAGE
----------------|----------------------|------------|----------------------------
UI              | PySide6              | >=6.6.0    | Widgets Qt6 cross-platform
Styling         | QSS                  | —          | CSS-like theming
DB              | SQLite               | built-in   | Persistance locale
PDF             | ReportLab            | 4.0.7      | Génération reçus PDF
Auth            | bcrypt               | >=4.0.0    | Hachage mots de passe
Crypto          | cryptography         | 41.0.7     | Fernet (feature flags)
Impression      | python-escpos        | 3.1        | Thermique ESC/POS
Codes-barres    | python-barcode       | 0.15.1     | Code128, EAN-13, EAN-8
QR Codes        | qrcode               | 7.4.2      | QR sur reçus
Caméra/Scan     | opencv-python        | 4.8.1.78   | Scan via webcam
Lecture CB      | pyzbar               | 0.1.9      | Décodage codes-barres
Images          | Pillow               | 10.1.0     | Manipulation images
Graphiques      | matplotlib           | 3.8.2      | Charts rapports
Data            | pandas               | 2.1.4      | Analyses, export
Excel           | openpyxl             | 3.1.2      | Export .xlsx
HTTP            | requests             | 2.31.0     | Appels API externes
WebSocket       | websockets           | >=12.0     | Sync temps réel
Tunnel          | pyngrok              | >=7.0      | Tunnel HTTP dev
Réseau local    | Flask                | (dépend.)  | API multi-caisse
Packaging       | PyInstaller          | 6.3.0      | EXE Windows/Linux/macOS
Tests           | pytest               | >=7.0.0    | Tests unitaires/intégration
IA (optionnel)  | google-generativeai  | >=0.8.0    | Extraction données

================================================================================
 5. WORKFLOWS MÉTIER
================================================================================

5.1 FLUX D'AUTHENTIFICATION ET DÉMARRAGE
-----------------------------------------

  Lancement App
       ↓
  Splash screen (2.5s)
       ↓
  Démarrage serveur local (si mode=serveur)
       ↓
  Connexion serveur distant (si mode=client)
       ↓
  Vérification licence (standalone uniquement)
  [Si invalide → fenêtre activation → code licence]
       ↓
  Vérification premier lancement
  [Si aucun compte → création super-admin obligatoire]
       ↓
  Login (saisie email + mot de passe → bcrypt)
       ↓
  Routage dashboard selon rôle :
    super_admin=1 ou role='patron'   → PrincipaleWindow
    role='gestionnaire'              → PrincipaleGestionnaireWindow
    role='caissier'                  → PrincipaleCaissierWindow

5.2 FLUX DE VENTE (ATOMIQUE)
-----------------------------

  1. CONSTITUTION DU PANIER (en mémoire, liste Python)
     • Scanner code-barre → lookup produit → ajout au panier
     • Saisie manuelle → recherche par nom/code → ajout
     • Modification quantité dans panier
     • Application remise (% ou montant fixe)
     • Sélection client (optionnel → fidélité)

  2. AFFICHAGE TOTAUX EN TEMPS RÉEL
     • Sous-totaux par ligne
     • Total HT + TVA + Total TTC
     • Remise globale

  3. MODAL PAIEMENT (ui/windows/paiement.py)
     • Choix mode(s) de paiement :
       → Espèces, Orange Money, MTN MoMo, Moov Money, Wave, Virement, Chèque
     • Paiement mixte (ex: 50% espèces + 50% Mobile Money)
     • Saisie montant reçu → calcul monnaie automatique
     • Option ardoise (vente à crédit)

  4. VALIDATION → TRANSACTION SQL ATOMIQUE
     BEGIN TRANSACTION
       INSERT ventes (numero_vente, total, utilisateur_id, client_id, id_session)
       INSERT details_ventes (vente_id, produit_id, quantite, prix_unitaire)
       INSERT paiements (vente_id, mode, montant, reference)
       UPDATE produits SET stock_actuel = stock_actuel - quantite (par article)
       INSERT historique_stock (produit_id, quantite_avant/apres, operation)
     COMMIT

  5. POST-VENTE
     • Génération reçu PDF (ReportLab)
     • Impression thermique ESC/POS (si imprimante configurée)
     • Ajout points fidélité client
     • Callback rafraîchissement dashboard (totaux du jour)
     • Confirmation visuelle avec option d'impression

  Numérotation ventes : V{YYYYMMDD}-{séquence_journalière} (ex: V20260517-001)

5.3 FLUX SESSION DE CAISSE
----------------------------

  Ouverture de caisse :
    • Caissier saisit le fond de caisse initial (espèces disponibles)
    • Création session_caisse en DB (id_session attaché à toutes les ventes)

  En cours de journée :
    • Rapport X (lecture seule) : totaux en cours par mode de paiement

  Clôture Z (fin de journée) :
    • Calcul automatique : total espèces, total Mobile Money, total autre
    • Caissier saisit le fond de clôture déclaré (espèces comptées)
    • Calcul écart = fond_calculé - fond_déclaré
    • Génération rapport Z PDF + impression
    • Hash de session (intégrité, non modifiable après clôture)
    • Statut session → 'cloturee'

5.4 FLUX ARDOISE (CRÉDIT CLIENT)
----------------------------------

  Création ardoise :
    • Lors d'une vente → mode paiement = ardoise
    • Montant initial = total vente
    • Statut initial = 'en_cours'

  Suivi ardoise :
    • Affichage solde dû par client
    • Historique de tous les encaissements

  Encaissement partiel ou total :
    • Saisie montant payé + mode de paiement
    • Mise à jour montant_restant
    • Statut = 'partiel' si encore dû, 'solde' si réglé

5.5 FLUX COMMANDE FOURNISSEUR
-------------------------------

  1. Création commande (sélection fournisseur)
  2. Ajout lignes produits (qté commandée, prix unitaire)
  3. Statuts : 'en_attente' → 'envoyee' → 'recue' / 'partielle' / 'annulee'
  4. Réception : saisie quantité reçue → mise à jour stock automatique
  5. Historique des commandes par fournisseur

5.6 FLUX RÉSEAU MULTI-CAISSES
-------------------------------

  MODE SERVEUR (PC principal) :
    • API Flask locale sur port 5050
    • Gère le stock centralisé
    • Autorise/refuse les connexions clients
    • Synchronise les événements de stock

  MODE CLIENT (PC caisse secondaire) :
    • Se connecte au serveur via token
    • Sync initiale du catalogue produits
    • Envoie les événements de vente
    • Reçoit les mises à jour stock en temps réel

================================================================================
 6. FONCTIONNALITÉS DÉTAILLÉES
================================================================================

6.1 GESTION DES VENTES
  ✓ Panier avec quantités modifiables
  ✓ Scanner code-barre (USB ou caméra)
  ✓ Saisie manuelle avec recherche autocomplete
  ✓ Prix de gros automatique (si seuil de quantité atteint)
  ✓ Remise par article ou globale (% ou montant)
  ✓ Paiement multimode (espèces + Mobile Money + etc.)
  ✓ Paiement mixte (plusieurs modes sur une vente)
  ✓ Vente à crédit (ardoise)
  ✓ Association client pour fidélité
  ✓ Reçu PDF imprimable
  ✓ Impression thermique (58mm et 80mm)
  ✓ QR code sur reçu
  ✓ Annulation vente avec motif (rétablissement stock)
  ✓ Historique complet des ventes

6.2 GESTION DES PRODUITS
  ✓ CRUD complet (création, modification, suppression)
  ✓ Code-barre automatique ou manuel (Code128, EAN-13, EAN-8, QR)
  ✓ Impression étiquettes codes-barres
  ✓ Stock actuel + seuil d'alerte
  ✓ Prix détail + prix de gros (avec seuil quantité)
  ✓ Catégories personnalisables
  ✓ Images produits
  ✓ Unité de mesure (pièce, kg, litre, etc.)
  ✓ Gestion des lots
  ✓ Import en masse via CSV
  ✓ Filtre/recherche multicritère
  ✓ Produits actifs/inactifs (soft delete)

6.3 GESTION DES CLIENTS
  ✓ Profil : nom, téléphone, email, notes
  ✓ Points de fidélité (accumulation à chaque achat)
  ✓ Historique des achats (total dépensé, nb transactions)
  ✓ Recherche par nom / téléphone / email
  ✓ Solde ardoise en temps réel
  ✓ Pagination (50 clients par page)

6.4 GESTION DES FOURNISSEURS
  ✓ Répertoire fournisseurs (nom, contact, email, adresse)
  ✓ Commandes fournisseurs avec lignes de détail
  ✓ Suivi statut commandes
  ✓ Réception partielle ou totale (avec mise à jour stock)
  ✓ Historique des commandes par fournisseur

6.5 RAPPORTS ET STATISTIQUES
  ✓ Tableau de bord : CA du jour, du mois, total
  ✓ Nb ventes, vente moyenne
  ✓ Top produits les plus vendus
  ✓ Analyses par période
  ✓ Rapport de stock (valeur, ruptures, alertes)
  ✓ Graphiques (barres, courbes via matplotlib)
  ✓ Export PDF + Excel (pandas/openpyxl)
  ✓ Rapport Z (clôture de caisse journalière)
  ✓ Audit trail (toutes les actions utilisateurs)
  ✓ Historique des clôtures Z

6.6 GESTION DES UTILISATEURS
  ✓ 3 niveaux de rôles : patron / gestionnaire / caissier
  ✓ 1 seul super-admin (patron)
  ✓ CRUD comptes utilisateurs
  ✓ Mots de passe hachés bcrypt
  ✓ Reset mot de passe admin
  ✓ Activation/désactivation compte
  ✓ Historique des connexions

6.7 PARAMÈTRES ET CONFIGURATION
  ✓ Informations boutique (nom, adresse, téléphone, logo)
  ✓ TVA globale ou par catégorie
  ✓ Multi-devises avec taux de change
  ✓ Modes de paiement activables (par boutique)
  ✓ Préférences imprimante thermique (port, format)
  ✓ Mode réseau (standalone / serveur / client)
  ✓ Paramètres de fidélité (taux d'accumulation)
  ✓ Sauvegarde automatique programmable

6.8 FONCTIONNALITÉS AVANCÉES
  ✓ Mode réseau multi-caisses (jusqu'à N terminaux selon plan)
  ✓ Écran client secondaire (affichage articles/totaux)
  ✓ Envoi catalogues via WhatsApp Web
  ✓ Import CSV produits avec validation
  ✓ Mise à jour automatique (GitHub Releases API)
  ✓ Sauvegardes automatiques + restauration
  ✓ Extraction IA (Google Generative AI, optionnel)
  ✓ Scan caméra pour codes-barres
  ✓ Logs d'audit complets

================================================================================
 7. LIMITATIONS TECHNIQUES
================================================================================

7.1 BASE DE DONNÉES
  • Pas de système de migration formel (versioning)
    → Migrations ad-hoc dans create_tables() avec try/except
    → Risque de divergence de schéma entre installations
  • SQLite mono-fichier → pas de concurrence simultanée haute charge
  • Pas de cache applicatif → requêtes DB répétées
  • Pas de soft-delete systématique (mélange de patterns)
  • Accès SQL brut → pas de ORM, risque d'erreurs si colonnes renommées
  • Reconnexion automatique fragile (ping "SELECT 1" bloquant)

7.2 ARCHITECTURE
  • Pas de couche service/repository explicite → logique métier en partie
    dispersée entre modules/ et ui/windows/
  • Pas de DTO (Data Transfer Objects) → passage de dicts non typés
  • Pas d'enum pour les statuts (strings directes)
  • Pas de validation centralisée des formulaires
  • Feature flags déchiffrés à chaque appel (performance)
  • État de l'application géré de façon ad-hoc (pas de state management)

7.3 MULTI-THREADING
  • Certaines opérations bloquent le thread UI (requêtes réseau, génération PDF)
  • Pas de worker threads génériques → implémentation cas par cas
  • Flask serveur local → pas de rate limiting, pas de HTTPS

7.4 SÉCURITÉ
  • Machine binding licence faible (SHA256 prédictible)
  • Clé de chiffrement Fernet hardcodée en fallback dans le code
  • API locale Flask sans HTTPS (réseau local uniquement, mais risque)
  • Pas de token JWT pour l'API réseau → token statique

7.5 UI/UX
  • Fenêtres PySide6 lourdes (55K pour ventes.py)
  • Pagination manuelle implémentée dans chaque fenêtre (pas de composant réutilisable)
  • Dark mode partiel (non systématique dans certaines fenêtres)
  • Pas de responsive design (taille fixe ou semi-fixe)
  • Shortcut clavier limités (pas de navigation complète au clavier)

7.6 DEVOPS
  • Pas de CI/CD
  • Tests non exhaustifs (couverture incomplète)
  • Pas de versioning des sauvegardes (N dernières uniquement)
  • Packaging PyInstaller lourd (~150MB pour l'EXE)
  • Pas de logging structuré (format texte libre)

================================================================================
 8. PROBLÈMES ACTUELS IDENTIFIÉS
================================================================================

  P1. Migrations DB non versionnées
      → Chaque déploiement exécute create_tables() avec try/except
      → Aucun fichier de migration numérotée
      → Impossible de rollback proprement

  P2. Thread UI bloqué
      → Génération PDF, impression, appels API réseau → peuvent geler l'UI
      → Workaround : QTimer.singleShot() pour déporter certains appels

  P3. Couplage indirect UI ↔ DB
      → Certaines fenêtres accèdent directement à `db` au lieu de passer
        par les modules métier

  P4. Gestion d'erreurs incohérente
      → Certains modules retournent (bool, message), d'autres lèvent des exceptions,
        d'autres encore retournent None silencieusement

  P5. Clé de chiffrement Fernet exposée
      → _CLE_DEFAUT hardcodé dans modules/features.py (fallback dangereux)

  P6. Pas de pagination côté DB
      → La pagination UI charge tous les enregistrements puis découpe en Python
      → Problème de performance avec grands volumes

  P7. Synchronisation réseau fragile
      → Pas de mécanisme de conflict resolution
      → Si le serveur est coupé pendant une vente → état incohérent

  P8. Numéro de vente non séquentiel garanti
      → Basé sur comptage de la journée → risque de collision en mode multi-caisse

================================================================================
 9. PISTES D'AMÉLIORATION
================================================================================

  A. Système de migration DB versionné (Alembic ou custom)
  B. Architecture CQRS pour les rapports (séparation lecture/écriture)
  C. Event sourcing pour le stock (déjà amorcé avec historique_stock)
  D. API REST interne complète (plus cohérent que modules appelés directement)
  E. Worker threads dédiés pour les I/O lourds (PDF, impression, sync)
  F. State management centralisé (Redux pattern ou équivalent)
  G. Validation des données avec schémas (Pydantic ou équivalent)
  H. WebSocket pour sync temps réel multi-caisse (vs polling HTTP)
  I. Logging structuré (JSON) pour analyse et monitoring
  J. Tests de bout-en-bout (E2E) pour les workflows critiques
  K. HTTPS pour l'API réseau local (certificat auto-signé)
  L. Pagination SQL (LIMIT/OFFSET) plutôt que côté application
  M. Fingerprinting machine plus robuste pour les licences

================================================================================
 10. RECOMMANDATIONS POUR ELECTRON.JS + REACT + SQLITE
================================================================================

10.1 STACK RECOMMANDÉE
-----------------------

COUCHE              | TECHNOLOGIE              | JUSTIFICATION
--------------------|--------------------------|----------------------------------
Framework app       | Electron 28+             | Cross-platform, accès OS natif
UI                  | React 18 + TypeScript    | Composants réutilisables, typage
State management    | Zustand                  | Simple, léger, pas de boilerplate
UI components       | Shadcn/ui + Tailwind CSS | Design system professionnel
DB                  | better-sqlite3           | SQLite synchrone, rapide, natif
Migration DB        | Drizzle ORM              | TypeScript-first, migration versionnée
PDF                 | pdf-lib ou @react-pdf    | Génération PDF côté Node
ESC/POS             | node-escpos ou escpos    | Module Node natif
Codes-barres        | jsbarcode + zxing        | Génération et lecture
Auth                | argon2 (Node)            | Plus sécurisé que bcrypt
Chiffrement         | libsodium.js             | Feature flags chiffrés
Réseau local        | Socket.io + Express      | Multi-caisse temps réel
HTTP client         | axios                    | Requêtes API licence
Validation          | Zod                      | Schémas TypeScript-native
Logging             | winston + winston-daily  | Logging structuré JSON
Tests               | Vitest + Playwright      | Unit + E2E
Packaging           | electron-builder         | Windows/Linux/macOS
Auto-update         | electron-updater         | Basé GitHub Releases
Excel export        | exceljs                  | Compatible avec l'existant
Graphiques          | Recharts                 | React-native, léger

10.2 ARCHITECTURE RECOMMANDÉE
-------------------------------

electron-app/
├── src/
│   ├── main/                   # Electron Main Process (Node.js)
│   │   ├── index.ts            # Point d'entrée Electron
│   │   ├── database/
│   │   │   ├── schema.ts       # Drizzle schema (toutes les tables)
│   │   │   ├── migrations/     # Migrations versionnées
│   │   │   └── db.ts           # Instance better-sqlite3
│   │   ├── services/           # Logique métier (équivalent modules/)
│   │   │   ├── ventes.ts
│   │   │   ├── produits.ts
│   │   │   ├── clients.ts
│   │   │   ├── utilisateurs.ts
│   │   │   ├── sessions.ts
│   │   │   ├── ardoise.ts
│   │   │   ├── fournisseurs.ts
│   │   │   ├── rapports.ts
│   │   │   ├── imprimante.ts
│   │   │   ├── licence.ts
│   │   │   ├── sauvegarde.ts
│   │   │   └── features.ts
│   │   ├── ipc/                # IPC handlers (pont Main ↔ Renderer)
│   │   │   ├── ventes.ipc.ts
│   │   │   ├── produits.ipc.ts
│   │   │   └── ...
│   │   └── server/             # Serveur local multi-caisse (Express + Socket.io)
│   │       ├── api.ts
│   │       └── sync.ts
│   └── renderer/               # React App (UI)
│       ├── App.tsx
│       ├── pages/              # Équivalent ui/windows/
│       │   ├── DashboardPatron.tsx
│       │   ├── Ventes.tsx      # La plus complexe — priorité
│       │   ├── Paiement.tsx
│       │   ├── Produits.tsx
│       │   ├── Clients.tsx
│       │   ├── Ardoise.tsx
│       │   ├── Rapports.tsx
│       │   ├── Fournisseurs.tsx
│       │   └── Parametres/
│       ├── components/         # Composants réutilisables
│       │   ├── PanierVente.tsx
│       │   ├── ModalPaiement.tsx
│       │   ├── TableProduits.tsx
│       │   ├── SearchBar.tsx
│       │   └── BarcodeScanner.tsx
│       ├── stores/             # Zustand stores
│       │   ├── ventesStore.ts
│       │   ├── produitStore.ts
│       │   └── authStore.ts
│       └── hooks/              # Custom hooks
│           ├── useVentes.ts
│           └── useBarcode.ts

10.3 CORRESPONDANCE MODULES (Python → TypeScript)
--------------------------------------------------

Python module          | TypeScript service        | Priorité
-----------------------|---------------------------|----------
modules/ventes.py      | services/ventes.ts        | CRITIQUE
modules/produits.py    | services/produits.ts      | CRITIQUE
modules/utilisateurs.py| services/auth.ts          | CRITIQUE
modules/sessions.py    | services/sessions.ts      | CRITIQUE
modules/permissions.py | middleware/permissions.ts | HAUTE
modules/clients.py     | services/clients.ts       | HAUTE
modules/ardoise.py     | services/ardoise.ts       | HAUTE
modules/paiements.py   | services/paiements.ts     | HAUTE
modules/rapports.py    | services/rapports.ts      | HAUTE
modules/imprimante.py  | services/imprimante.ts    | HAUTE
modules/recus.py       | services/recus.ts         | HAUTE
modules/fournisseurs.py| services/fournisseurs.ts  | MOYENNE
modules/features.py    | services/features.ts      | MOYENNE
modules/licence.py     | services/licence.ts       | MOYENNE
modules/sauvegarde.py  | services/sauvegarde.ts    | MOYENNE
modules/codebarres.py  | services/codebarres.ts    | MOYENNE
modules/import_csv.py  | services/importCsv.ts     | BASSE
modules/whatsapp.py    | services/whatsapp.ts      | BASSE
modules/updater.py     | services/updater.ts       | BASSE
modules/ia_extraction.py| services/ia.ts           | OPTIONNEL

10.4 SCHEMA DB RECOMMANDÉ (Drizzle, TypeScript)
------------------------------------------------

  Reprendre exactement les 15 tables de l'existant avec :
  - Types stricts (enum pour statuts, dates en ISO 8601)
  - Clés étrangères explicites avec ON DELETE
  - Index sur colonnes fréquemment requêtées
  - Contraintes CHECK pour les statuts
  - Colonnes created_at / updated_at systématiques
  - Soft delete via deleted_at (uniformiser)

10.5 WORKFLOW IPC ELECTRON
---------------------------

  React Component
      ↓  window.electronAPI.ventes.creer(panier)
  Preload (contextBridge)
      ↓  ipcRenderer.invoke('ventes:creer', panier)
  Main Process IPC Handler
      ↓  appelle services/ventes.ts
  Service métier (TypeScript pur)
      ↓  appelle database/db.ts
  better-sqlite3 (synchrone)
      ↓  résultat
  Retour vers React via Promise

10.6 POINTS D'ATTENTION CRITIQUES
-----------------------------------

  1. La fenêtre Ventes est la plus complexe (55K de code Python).
     Commencer par elle car elle définit l'architecture de l'IPC.

  2. Les transactions SQL atomiques sont CRUCIALES pour les ventes.
     better-sqlite3 supporte les transactions synchrones natives → parfait.

  3. Le mode multi-caisse nécessite un conflit de stock à résoudre.
     Recommandation : event sourcing + dernière écriture gagne + alertes

  4. L'impression thermique ESC/POS nécessite des permissions OS.
     Sur Windows : accès COM/USB depuis Electron Main Process.
     Sur Linux : groupe 'dialout' pour l'utilisateur.

  5. Le scan caméra peut se faire entièrement dans React avec jsQR
     (pas besoin d'OpenCV côté Electron).

  6. La génération PDF peut être faite via @react-pdf/renderer
     (côté Renderer) ou pdf-lib (côté Main Process).

================================================================================
 11. RÉSUMÉ GLOBAL (contexte pour reconstruction)
================================================================================

Ce document décrit un SYSTÈME POS COMPLET ET FONCTIONNEL pour le marché
Béninois (Afrique de l'Ouest). Voici les éléments clés à préserver dans la
reconstruction :

FORCES À CONSERVER :
  ✓ La séparation UI / logique métier (principe fondamental)
  ✓ L'architecture multi-rôles (patron / gestionnaire / caissier)
  ✓ Le flux de vente atomique (transaction DB complète ou rien)
  ✓ Le système d'ardoise (crédit client spécifique au marché)
  ✓ Le support Mobile Money Bénin (Orange, MTN, Moov, Wave)
  ✓ Les sessions de caisse avec clôture Z
  ✓ Le système de licences par plan avec feature flags
  ✓ Le mode réseau multi-caisses
  ✓ L'impression thermique ESC/POS
  ✓ Les prix de gros automatiques

FAIBLESSES À CORRIGER :
  ✗ Migrations DB non versionnées → Drizzle migrations
  ✗ Pas de state management → Zustand
  ✗ Thread UI bloqué → IPC asynchrone Electron
  ✗ Pas de validation schéma → Zod
  ✗ Logging non structuré → Winston JSON
  ✗ API réseau sans sécurité → HTTPS + JWT
  ✗ Pagination côté app → LIMIT/OFFSET SQL

SPÉCIFICITÉS MÉTIER À MODÉLISER SOIGNEUSEMENT :
  → Paiements Mobile Money avec référence de transaction
  → Ardoise (crédit client) avec encaissements partiels
  → Prix de gros (seuil quantité)
  → Clôture Z de caisse avec écart fond
  → Numérotation ventes séquentielle par caisse
  → Feature flags par plan de licence
  → Synchronisation stock multi-caisse sans conflit

--------------------------------------------------------------------------------
MODULES PRIORITAIRES POUR LA RECONSTRUCTION (ordre recommandé) :
  1. Base de données + schéma Drizzle
  2. Auth + permissions (RBAC)
  3. Produits + stock
  4. Interface ventes + panier
  5. Paiements + modes Mobile Money
  6. Session de caisse + clôture Z
  7. Clients + fidélité + ardoise
  8. Reçus PDF + impression thermique
  9. Fournisseurs + commandes
 10. Rapports + statistiques
 11. Multi-caisse réseau
 12. Licence + feature flags
 13. Sauvegarde + mise à jour

--------------------------------------------------------------------------------
FIN DU DOCUMENT D'ANALYSE
GestionBoutique v2 → Reconstruction Electron.js + React + SQLite
================================================================================
