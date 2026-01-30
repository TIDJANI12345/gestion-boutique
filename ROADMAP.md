# Roadmap - Gestion Boutique v2

Plan d'evolution pour rendre le logiciel pret a la vente.

---

## Phase 1 : Fiabilite et Securite (Priorite critique)

### 1.1 Securite
- [ ] Supprimer le mot de passe admin en dur (`admin123`) - forcer la creation au premier lancement
- [ ] Deplacer la cle de chiffrement licence hors du code source (variable d'environnement ou fichier separe)
- [ ] Hashage mot de passe avec salt unique par utilisateur (deja bcrypt, verifier la coherence)
- [ ] Timeout de session automatique apres inactivite
- [ ] Journalisation des connexions echouees (protection brute-force)
- [ ] Chiffrement de la base de donnees locale (SQLCipher)

### 1.2 Gestion d'erreurs
- [ ] Try/catch sur toutes les operations de vente (ne jamais crasher en pleine transaction)
- [ ] File d'attente locale pour les syncs echouees (retry automatique)
- [ ] Validation des donnees a chaque saisie (prix negatifs, stock negatif, etc.)
- [ ] Messages d'erreur clairs en francais pour l'utilisateur final
- [ ] Logging dans un fichier (`logs/app.log`) au lieu de `print()`

### 1.3 Tests automatises
- [ ] Tests unitaires : modules produits, ventes, utilisateurs, synchronisation
- [ ] Tests d'integration : cycle complet vente (ajout panier -> paiement -> stock mis a jour)
- [ ] Test sync : push/pull avec donnees de test
- [ ] Test hors-ligne : simuler coupure reseau pendant une vente

---

## Phase 2 : Fonctionnalites essentielles pour la vente

### 2.1 Impression de recus / tickets de caisse
- [ ] Support imprimante thermique (ESC/POS) - 58mm et 80mm
- [ ] Template de recu configurable (nom boutique, adresse, telephone)
- [ ] QR code sur le recu (lien vers recu numerique ou numero de vente)
- [ ] Recu en PDF exportable
- [ ] Option "Envoyer recu par WhatsApp" (deja un module WhatsApp existant)
 

### 2.2 Moyens de paiement
- [ ] Paiement en especes avec calcul du rendu de monnaie
- [ ] Paiement Mobile Money (Orange Money, MTN MoMo, Moov Money)
- [ ] Paiement mixte (une partie especes + une partie Mobile Money)
- [ ] Historique des paiements par type
- [ ] Rapprochement de caisse en fin de journee

### 2.3 Sauvegarde et restauration
- [ ] Sauvegarde automatique locale quotidienne (copie du .db avec date)
- [ ] Sauvegarde cloud automatique (via la sync deja en place)
- [ ] Bouton "Restaurer depuis une sauvegarde" dans les parametres
- [ ] Export complet de la base en ZIP (donnees + images produits)
- [ ] Import depuis un backup ZIP

### 2.4 Gestion fiscale basique
- [ ] Configuration TVA (taux par defaut, taux par categorie)
- [ ] Affichage HT / TVA / TTC sur les recus
- [ ] Rapport TVA mensuel pour comptabilite
- [ ] Multi-devises : FCFA (XOF), Euro, Dollar (avec taux configurable)

---

## Phase 3 : Experience utilisateur

### 3.1 Interface moderne
- [ ] Migrer de tkinter vers CustomTkinter (look moderne sans changer l'architecture)
- [ ] Theme sombre / theme clair (toggle)
- [ ] Icones vectorielles au lieu d'emojis (compatibilite Windows)
- [ ] Responsive : adaptation fenetre petits ecrans (laptop 13")
- [ ] Animations de transition entre les pages
- [ ] Raccourcis clavier pour les caissiers (F1=Nouvelle vente, F2=Rechercher produit, etc.)

### 3.2 Dashboard ameliore
- [ ] Graphique des ventes du jour / semaine / mois (matplotlib ou plotly)
- [ ] Top 10 produits les plus vendus
- [ ] Alertes stock bas en temps reel sur le dashboard
- [ ] Chiffre d'affaires du jour visible en permanence
- [ ] Comparaison jour precedent / semaine precedente

### 3.3 Recherche et navigation
- [ ] Recherche produit instantanee (au fur et a mesure de la frappe)
- [ ] Scanner code-barre via camera/webcam
- [ ] Filtres par categorie, par stock, par prix
- [ ] Pagination pour les grandes listes

---

## Phase 4 : Fonctionnalites avancees

### 4.1 Gestion clients
- [ ] Base de donnees clients (nom, telephone, email)
- [ ] Historique d'achats par client
- [ ] Programme de fidelite (points, remises)
- [ ] Envoi SMS/WhatsApp promotionnel aux clients

### 4.2 Gestion fournisseurs et achats
- [ ] Base de donnees fournisseurs
- [ ] Bons de commande fournisseur
- [ ] Reception de marchandise avec mise a jour auto du stock
- [ ] Historique des achats et prix fournisseur
- [ ] Alerte de reapprovisionnement automatique

### 4.3 Gestion des employes
- [ ] Pointage (heure arrivee / depart)
- [ ] Performance par caissier (CA genere, nombre de ventes)
- [ ] Permissions granulaires (qui peut modifier les prix, faire des remises, etc.)
- [ ] Historique des actions par utilisateur (deja logs_actions, a exploiter)

### 4.4 Rapports avances
- [ ] Rapport de cloture de caisse (Z de caisse)
- [ ] Rapport de marge beneficiaire par produit
- [ ] Rapport de rotation des stocks
- [ ] Export Excel/CSV des rapports
- [ ] Envoi automatique du rapport journalier par email au patron

---

## Phase 5 : Deploiement et distribution

### 5.1 Installateur professionnel
- [ ] Installateur Windows (.exe) avec NSIS ou Inno Setup (deja un .iss)
- [ ] Icone et splash screen professionnels
- [ ] Mise a jour automatique (verifier nouvelle version au demarrage)
- [ ] Desinstallation propre

### 5.2 Documentation
- [ ] Guide d'installation (1 page, avec captures d'ecran)
- [ ] Manuel utilisateur avec captures d'ecran (deja un fichier, a mettre a jour)
- [ ] Video tutoriel (3-5 minutes)
- [ ] FAQ / Troubleshooting

### 5.3 Support client
- [ ] Formulaire de contact integre dans l'app
- [ ] Numero WhatsApp support visible dans "A propos"
- [ ] Systeme de tickets basique (via email ou Google Form)
- [ ] Acces distant pour depannage (TeamViewer / AnyDesk)

---

## Phase 6 : Monetisation

### 6.1 Modele de prix
- [ ] Plan Mensuel : fonctionnalites de base (1 poste)
- [ ] Plan Annuel : multi-postes + sync cloud
- [ ] Plan Perpetuel : tout inclus
- [ ] Periode d'essai gratuite (14 jours)

### 6.2 Paiement en ligne
- [ ] Integration paiement via FedaPay ou Kkiapay (solutions beninoise)
- [ ] Activation automatique apres paiement (webhook)
- [ ] Page de vente / landing page

### 6.3 Marketing
- [ ] Page Facebook / Instagram avec demos
- [ ] Temoignages clients (apres premiers utilisateurs)
- [ ] Partenariats avec vendeurs de materiel POS au Benin

---

## Ordre de realisation recommande

| Etape | Phase | Impact |
|-------|-------|--------|
| 1 | Securite (1.1) | Obligatoire avant toute vente |
| 2 | Impression recus (2.1) | Fonctionnalite #1 demandee |
| 3 | Paiement especes + rendu monnaie (2.2) | Indispensable pour un caissier |
| 4 | Gestion erreurs (1.2) | Eviter les crashes en production |
| 5 | Sauvegarde/restauration (2.3) | Rassurer le client |
| 6 | Interface moderne (3.1) | Premiere impression = vente |
| 7 | Dashboard ameliore (3.2) | Valeur ajoutee visible |
| 8 | Gestion clients (4.1) | Differenciation concurrence |
| 9 | Rapports avances (4.4) | Aide a la decision pour le patron |
| 10 | Installateur pro (5.1) | Distribution facile |
