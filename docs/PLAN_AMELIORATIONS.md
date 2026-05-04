# Plan d'améliorations — GestionBoutique Pro

Suivi des phases d'implémentation pour la version commerciale.

---

## Phase 1 — IFU / RCCM + Message pied de page
> Obligation légale + personnalisation reçus

- [x] Ajouter champs IFU et RCCM dans `Paramètres Caisse`
- [x] Sauvegarder en DB (`boutique_ifu`, `boutique_rccm`)
- [x] Afficher IFU/RCCM sur le reçu PDF (`modules/recus.py`)
- [x] Afficher IFU/RCCM sur le ticket thermique (`modules/imprimante.py`)
- [x] Ajouter champ "Message pied de page" dans `Paramètres Caisse`
- [x] Sauvegarder en DB (`recu_message_pied`)
- [x] Afficher le message en bas du PDF
- [x] Afficher le message en bas du ticket thermique

**Statut : ✅ Terminé**

---

## Phase 2 — Remises / Rabais
> Fonctionnalité métier demandée par tous les commerçants

- [x] Ajouter champ remise (% ou montant fixe) sur le panier dans `ventes.py`
- [x] Calculer et afficher la remise dans le récapitulatif panier
- [x] Sauvegarder la remise dans la table `ventes` (nouvelle colonne `remise`)
- [x] Afficher la remise sur le reçu PDF
- [x] Afficher la remise sur le ticket thermique
- [ ] Remise par article (optionnel — phase ultérieure)

**Statut : ✅ Terminé**

---

## Phase 3 — Logo boutique sur le PDF
> Impact visuel fort pour la démo commerciale

- [x] Ajouter bouton "Choisir un logo" dans `Paramètres Caisse`
- [x] Copier et stocker le logo dans le dossier de l'app (`logo_boutique.png`)
- [x] Sauvegarder le chemin en DB (`boutique_logo_path`)
- [x] Intégrer le logo en en-tête du PDF (`modules/recus.py`)
- [x] Ajouter option filigrane (logo en transparence au centre du PDF)
- [x] Afficher un aperçu du logo dans `Paramètres Caisse`

**Statut : ✅ Terminé**

---

## Phase 4 — Logo sur le ticket thermique
> Impression image via ESC/POS

- [ ] Redimensionner le logo en noir & blanc (max 384px de large pour 80mm)
- [ ] Utiliser `printer.image()` dans `modules/imprimante.py`
- [ ] Gérer les erreurs (imprimante sans support image → ignorer silencieusement)
- [ ] Tester avec Xprinter 80mm

**Statut : ⬜ À faire**  
**Dépend de : Phase 3**

---

## Phase 5 — Couleur primaire personnalisable
> Donner l'impression d'un logiciel sur mesure à chaque client

- [ ] Ajouter un sélecteur de couleur dans `Paramètres Caisse`
- [ ] Sauvegarder la couleur en DB (`theme_couleur_primaire`)
- [ ] Modifier `ui/theme.py` pour utiliser la couleur DB au lieu de la couleur fixe
- [ ] Appliquer sans redémarrage (rechargement du style à la sauvegarde)

**Statut : ⬜ À faire**

---

## Phase 6 — Réseaux sociaux sur les reçus
> Publicité gratuite à chaque ticket imprimé

- [ ] Ajouter champs Facebook, Instagram, WhatsApp dans `Paramètres Caisse`
- [ ] Sauvegarder en DB (`boutique_facebook`, `boutique_instagram`, `boutique_whatsapp`)
- [ ] Afficher les réseaux non vides en pied de page du PDF
- [ ] Afficher les réseaux non vides en pied de page du ticket thermique

**Statut : ⬜ À faire**

---

## Phase 7 — Sauvegarde automatique
> Sécurité des données — argument de vente fort

- [ ] Sauvegarde manuelle : bouton "Sauvegarder maintenant" (copie de `boutique.db`)
- [ ] Sauvegarde automatique quotidienne au démarrage de l'app
- [ ] Conserver les 7 dernières sauvegardes (rotation)
- [ ] Choisir le dossier de sauvegarde (local, clé USB, réseau)
- [ ] Restauration : bouton "Restaurer une sauvegarde"
- [ ] Notification visuelle à chaque sauvegarde réussie

**Statut : ⬜ À faire**

---

## Phase 8 — Unité de mesure par produit
> Utile pour épicerie, quincaillerie, pharmacie

- [ ] Ajouter colonne `unite` dans la table `produits` (`pièce`, `kg`, `litre`, `carton`...)
- [ ] Ajouter sélecteur unité dans le formulaire produit
- [ ] Afficher l'unité dans le panier et sur les reçus
- [ ] Permettre des quantités décimales si unité = kg ou litre

**Statut : ⬜ À faire**

---

## Phase 9 — Multi-caisse
> Pour les boutiques avec plusieurs postes de vente

- [ ] Partager `boutique.db` sur un dossier réseau (NAS ou partage Windows)
- [ ] Configurer le chemin DB dans `Paramètres` (au lieu de `%APPDATA%`)
- [ ] Gérer les accès concurrents SQLite (WAL mode)
- [ ] Identifier chaque transaction par le nom du poste

**Statut : ⬜ À faire**

---

## Phase 10 — Prix de gros (tarif dégressif par quantité)
> Vendu à partir d'un certain nombre → prix réduit automatique

- [x] Migration DB : colonnes `prix_gros` et `seuil_gros` sur table `produits`
- [x] Fiche produit : champs "Prix gros" + "À partir de (qté)"
- [x] Panier : bascule automatique vers `prix_gros` si `quantité ≥ seuil_gros`
- [x] Indicateur visuel **[Prix gros]** sur la ligne panier
- [x] Recalcul en temps réel (boutons +/−)

**Statut : ✅ Terminé**

---

## Légende
- ⬜ À faire
- 🔄 En cours
- ✅ Terminé
- ⏸ En attente (dépendance)
