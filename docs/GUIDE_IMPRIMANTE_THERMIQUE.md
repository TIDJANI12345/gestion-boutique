# Guide : Imprimante Thermique & Lecteur de Codes-Barres

---

## 1. Imprimante Thermique

### ✅ Modèle recommandé : Xprinter 80mm — 35 000 FCFA (Sayen Electronics, Cotonou)

**Caractéristiques :** USB + RJ11, 80mm, cutter automatique, 300mm/s, 203 dpi  
**Contact vendeur :** +229 01 91 06 06 09 / 01 97 10 28 33

C'est le meilleur choix pour cette application :
- **USB** → plug and play, aucune configuration complexe
- **80mm** → tickets plus larges (48 caractères), plus lisibles
- **Cutter automatique** → le ticket se coupe seul après chaque impression
- **RJ11** → compatible tiroir-caisse si besoin plus tard
- **Vendeur physique local** → SAV possible

### Configuration dans l'application (Xprinter USB)

#### Étape 1 — Brancher et installer

Brancher l'imprimante en USB. Windows 10/11 installe le pilote automatiquement dans la plupart des cas. Sinon, télécharger le pilote sur xprinter.net.

#### Étape 2 — Trouver le Vendor ID et Product ID

Ouvrir **Gestionnaire de périphériques** → **Contrôleurs de bus USB** → clic droit sur l'imprimante → Propriétés → Détails → ID matériel.  
Exemple : `USB\VID_0483&PID_5720` → Vendor = `0x0483`, Product = `0x5720`

#### Étape 3 — Configurer dans la DB

Ouvrir `%APPDATA%\GestionBoutique\data\boutique.db` avec **DB Browser for SQLite** :

| Clé | Valeur |
|-----|--------|
| `imprimante_mode` | `usb` |
| `imprimante_usb_vendor` | `0x0483` *(adapter selon l'étape 2)* |
| `imprimante_usb_product` | `0x5720` *(adapter selon l'étape 2)* |
| `imprimante_format` | `80mm` |

#### Étape 4 — Tester

Dans **Paramètres Caisse** → sélectionner **USB** → **Enregistrer** → **Imprimer ticket de test**.

---

### Alternative budget : Imprimante Thermique Portable 58mm — 22 000 FCFA (Bluetooth)

> ⚠️ **C'est une imprimante Bluetooth, pas USB.**  
> `python-escpos` ne gère pas le Bluetooth directement sur Windows.  
> Elle fonctionne via un **port COM virtuel Bluetooth** (mode Série dans l'app).

### Connexion : Bluetooth → Port COM Virtuel

#### Étape 1 — Appairer l'imprimante

1. Allumer l'imprimante (maintenir le bouton power)
2. Windows → **Paramètres** → **Bluetooth et appareils** → **Ajouter un appareil**
3. Sélectionner l'imprimante dans la liste (nom type "MTP-II" ou "Thermal Printer")
4. Valider l'appairage

#### Étape 2 — Trouver le port COM attribué

1. Clic droit sur **Démarrer** → **Gestionnaire de périphériques**
2. Développer **Ports (COM et LPT)**
3. Repérer le port de l'imprimante Bluetooth (ex. `COM4` ou `COM5`)
4. Noter ce numéro — c'est celui à utiliser dans l'app

#### Étape 3 — Configurer dans l'application

Aller dans **Paramètres Caisse** → **Impression thermique** :
- Mode : `Série (COM)`
- Cliquer **Enregistrer**

Puis ouvrir `boutique.db` avec **DB Browser for SQLite** (gratuit) :
- Table `parametres`
- Modifier ou ajouter :

| Clé | Valeur |
|-----|--------|
| `imprimante_mode` | `serie` |
| `imprimante_serie_port` | `COM4` *(adapter selon ton gestionnaire de périphériques)* |
| `imprimante_serie_baudrate` | `9600` |
| `imprimante_format` | `58mm` |

#### Étape 4 — Tester

Dans **Paramètres Caisse** → cliquer **"Imprimer ticket de test"**.  
Un ticket doit sortir avec le nom de la boutique et "Imprimante OK !".

---

---

### Connexion Réseau (IP)

Pour une imprimante partagée entre plusieurs postes.

Imprimer la page de configuration (maintenir FEED à l'allumage) pour voir l'IP.

| Clé | Valeur |
|-----|--------|
| `imprimante_mode` | `reseau` |
| `imprimante_ip` | `192.168.1.50` *(l'IP de l'imprimante)* |
| `imprimante_port` | `9100` |
| `imprimante_format` | `80mm` |

---

### Modifier les paramètres via DB Browser for SQLite

1. Télécharger **DB Browser for SQLite** (gratuit) : https://sqlitebrowser.org
2. Ouvrir `%APPDATA%\GestionBoutique\data\boutique.db`
3. Onglet **Parcourir les données** → table `parametres`
4. Modifier les valeurs
5. Cliquer **Écrire les modifications**

---

### Format papier

| `imprimante_format` | Largeur | Caractères par ligne |
|---------------------|---------|----------------------|
| `58mm` | 58 mm | 32 |
| `80mm` | 80 mm | 48 |

---

### Dépannage imprimante

| Symptôme | Cause | Solution |
|----------|-------|----------|
| "Impossible de se connecter" (Série) | Mauvais port COM | Vérifier dans Gestionnaire de périphériques |
| "Impossible de se connecter" (Série) | Imprimante non appairée | Refaire l'appairage Bluetooth |
| Ticket vide / blanc | Papier à l'envers | Retourner le rouleau (face brillante vers le bas) |
| Caractères illisibles | Mauvais baudrate | Essayer `19200` |
| "python-escpos non installé" | Dépendance manquante | `pip install python-escpos==3.1` |
| Ticket coupé à mi-chemin | Mauvais format papier | Vérifier `imprimante_format` = `58mm` |

---

## 2. Lecteur de Codes-Barres

### Modèle disponible localement : 1D 2D Wired/Wireless Barcode Scanner

- **Avec fil (USB) :** 20 000 FCFA ✅ Recommandé
- **Sans fil :** 23 000 FCFA

### Pourquoi c'est le bon choix

| Critère | Détail |
|---------|--------|
| Type | HID (Human Interface Device) — se comporte comme un clavier |
| Codes supportés | 1D (Code128, EAN13, EAN8, Code39) + 2D (QR Code) |
| Configuration requise | **Aucune** — plug and play |
| Compatibilité avec l'app | **100%** — fonctionne nativement |

### Comment ça fonctionne avec l'application

Le lecteur tape automatiquement le code-barres dans le champ de saisie de la fenêtre **Ventes**, puis simule la touche Entrée. L'article est ajouté au panier instantanément.

En mode **AUTO** (Paramètres Caisse → Mode AUTOMATIQUE) : ajout direct, quantité 1, pas de popup.  
En mode **MANUEL** : une fenêtre demande la quantité à chaque scan.

### Conseil

Prendre le **filaire à 20 000 FCFA** pour démarrer — plus fiable, pas de batterie à gérer, aucune latence. Le sans fil est utile seulement si le caissier doit se déplacer dans la boutique.
