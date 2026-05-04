# Guide : Imprimante Thermique

## Matériel recommandé

| Modèle | Largeur | Prix indicatif | Connexion |
|--------|---------|----------------|-----------|
| **Xprinter XP-58IIH** | 58 mm | ~15 000 FCFA | USB |
| **Xprinter XP-80C** | 80 mm | ~25 000 FCFA | USB + Réseau |
| **EPSON TM-T20III** | 80 mm | ~60 000 FCFA | USB + Réseau |

**Recommandé pour démarrer :** Xprinter XP-58IIH (USB, 58 mm). Simple, robuste, courante au Bénin.

---

## Connexion USB (le plus simple)

### 1. Installer le pilote

Télécharger le pilote sur le site du fabricant (ex. xprinter.net) ou utiliser le CD fourni.  
Sous Windows 10/11, l'imprimante est souvent reconnue automatiquement.

### 2. Trouver le Vendor ID et Product ID

Brancher l'imprimante via USB, puis ouvrir **Gestionnaire de périphériques** → **Contrôleurs de bus USB**.  
Clic droit sur l'imprimante → Propriétés → Détails → ID matériel.  
On voit quelque chose comme : `USB\VID_0483&PID_5720`  
- `VID_0483` → Vendor ID = `0x0483`
- `PID_5720` → Product ID = `0x5720`

### 3. Configurer dans l'application

Aller dans **Paramètres Caisse** → section **Impression thermique** :
- Mode : `USB`
- Enregistrer

Puis aller dans **Paramètres avancés** (base de données) ou directement via la DB :
```
imprimante_usb_vendor = 0x0483
imprimante_usb_product = 0x5720
imprimante_format = 58mm   (ou 80mm selon votre modèle)
```

> Pour modifier directement : ouvrir `boutique.db` avec DB Browser for SQLite,  
> table `parametres`, modifier les lignes correspondantes.

### 4. Tester

Cliquer **"Imprimer ticket de test"** dans Paramètres Caisse.  
Un ticket doit sortir avec le nom de la boutique, la date et "Imprimante OK !".

---

## Connexion Réseau (IP)

Utile si l'imprimante est partagée entre plusieurs postes.

### 1. Connecter l'imprimante au réseau

Via câble Ethernet (RJ45) ou WiFi selon le modèle.  
Imprimer la page de configuration (maintenir le bouton FEED à l'allumage) pour voir l'IP assignée.

### 2. Configurer dans l'application (DB)

```
imprimante_mode = reseau
imprimante_ip = 192.168.1.50    (l'IP de votre imprimante)
imprimante_port = 9100           (port standard ESC/POS)
imprimante_format = 80mm
```

### 3. Tester la connectivité réseau (optionnel)

Depuis le PC, ouvrir un terminal et taper :
```
ping 192.168.1.50
```
Si la réponse arrive → l'imprimante est joignable.

---

## Connexion Série (COM) — rare

Pour les vieilles imprimantes avec port RS-232.

```
imprimante_mode = serie
imprimante_serie_port = COM3      (vérifier dans Gestionnaire de périphériques)
imprimante_serie_baudrate = 9600
```

---

## Modifier les paramètres avancés (DB)

Pour les paramètres non exposés dans l'interface (Vendor ID, IP, port...) :

1. Télécharger **DB Browser for SQLite** (gratuit) : https://sqlitebrowser.org
2. Ouvrir `%APPDATA%\GestionBoutique\data\boutique.db`
3. Onglet **Parcourir les données** → table `parametres`
4. Modifier les valeurs directement
5. Cliquer **Écrire les modifications**

---

## Dépannage

| Symptôme | Cause probable | Solution |
|----------|---------------|----------|
| "Impossible de se connecter" (USB) | Mauvais Vendor/Product ID | Vérifier dans Gestionnaire de périphériques |
| "Impossible de se connecter" (USB) | Pilote non installé | Installer le pilote du fabricant |
| Ticket vide / blanc | Papier thermique à l'envers | Retourner le rouleau (face brillante vers le bas) |
| Caractères illisibles | Mauvais baudrate (série) | Essayer 19200 ou 115200 |
| "python-escpos non installé" | Dépendance manquante | `pip install python-escpos==3.1` |
| Ticket coupé à mi-chemin | Format papier mal configuré | Vérifier `imprimante_format` (58mm vs 80mm) |

---

## Format papier

| Paramètre `imprimante_format` | Largeur caractères | Adapté à |
|-------------------------------|-------------------|----------|
| `58mm` | 32 caractères | Petites boutiques, reçus courts |
| `80mm` | 48 caractères | Tickets détaillés, plus lisible |
