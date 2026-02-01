# Mode Supermarché - Guide Complet

## ✅ Implémenté !

Votre caisse fonctionne maintenant comme dans les supermarchés avec le **mode AUTOMATIQUE** par défaut.

---

## 🏪 Modes Disponibles

### Mode AUTOMATIQUE (supermarché) - PAR DÉFAUT

**Comportement :**
```
1. Scanner code-barres → ✓ Ajout direct quantité 1
2. Re-scanner même produit → ✓ Quantité s'incrémente (2, 3, 4...)
3. Scanner produit différent → ✓ Nouvelle ligne
4. Continuer à scanner → ✓ Flux rapide sans interruption
```

**Avantages :**
- ⚡ Ultra-rapide
- 🎯 Flux naturel comme en supermarché
- 🚫 Aucune popup qui ralentit
- ✅ Flash vert sur ligne ajoutée (feedback visuel)

**Idéal pour :**
- Supermarchés, épiceries
- Vente de produits unitaires
- Flux client important

---

### Mode MANUEL (avec quantité)

**Comportement :**
```
1. Scanner code-barres → Popup "Quantité ?"
2. Entrer quantité (ex: 5) → Validation
3. Produit ajouté avec quantité 5
```

**Avantages :**
- 🔒 Plus sûr (confirmation à chaque scan)
- ✏️ Quantité variable facilement
- 🛡️ Évite les erreurs

**Idéal pour :**
- Boutiques avec gros volumes par article
- Produits vendus par lots
- Formation de nouveaux caissiers

---

## ⚙️ Configuration

### Paramètres Caisse (Menu Administration)

**Accès :** Menu Administration → Paramètres caisse

**Options disponibles :**

1. **Mode de scan**
   - Mode AUTOMATIQUE (supermarché) - Par défaut
   - Mode MANUEL (avec quantité)

2. **Son de confirmation** 🔊
   - Activer/Désactiver le bip à chaque scan
   - Activé par défaut
   - Utile pour confirmer que le scan a été pris en compte

### Raccourci F9 (Rapide) ⭐

Dans la fenêtre **Ventes** :
```
1. Appuyez sur F9
2. Popup confirme le changement AUTO ↔ MANUEL
3. C'est tout !
```

---

## 🎮 Guide Pratique

### Scenario 1 : Client achète plusieurs produits différents (MODE AUTO)

```
Client prend : 1 pain, 1 lait, 2 œufs, 1 fromage

Caissier :
1. Scan pain     → ✓ Ajouté qte 1
2. Scan lait     → ✓ Ajouté qte 1
3. Scan œufs     → ✓ Ajouté qte 1
4. Scan œufs     → ✓ Qte devient 2 ✅
5. Scan fromage  → ✓ Ajouté qte 1
6. F2            → Paiement

Résultat : 4 lignes, 5 articles total
Temps : ~10 secondes
```

### Scenario 2 : Client achète gros volume (MODE MANUEL)

```
Client achète : 50 paquets de riz

Caissier :
1. F9                    → Bascule en mode MANUEL
2. Scan riz              → Popup "Quantité ?"
3. Entre 50 → Entrée     → ✓ Ajouté qte 50
4. F2                    → Paiement

Résultat : 1 ligne, 50 articles
Temps : ~5 secondes
```

### Scenario 3 : Mélange (Basculer selon besoin)

```
Client : 5 bouteilles d'eau + divers articles

Caissier :
1. Scan article A → ✓ Qte 1 (AUTO)
2. Scan article B → ✓ Qte 1 (AUTO)
3. F9             → Bascule MANUEL
4. Scan eau → 5 Entrée → ✓ Qte 5
5. F9             → Retour AUTO
6. Scan article C → ✓ Qte 1
7. F2             → Paiement
```

---

## 📊 Comparaison des Modes

| Critère | Mode AUTO | Mode MANUEL |
|---------|-----------|-------------|
| **Rapidité** | ⚡⚡⚡⚡⚡ | ⚡⚡⚡ |
| **Sécurité** | ⚡⚡⚡ | ⚡⚡⚡⚡⚡ |
| **Facilité** | ⚡⚡⚡⚡⚡ | ⚡⚡⚡⚡ |
| **Gros volumes** | ⚡⚡ | ⚡⚡⚡⚡⚡ |
| **Flux supermarché** | ⚡⚡⚡⚡⚡ | ⚡⚡ |

---

## 💡 Astuces Pro

### 1. Combiner les modes
- AUTO pour flux normal
- F9 → MANUEL pour gros volume ponctuel
- F9 → retour AUTO

### 2. Raccourcis caisse complète
```
F5  → Focus scan (démarrer)
F6  → Caméra (si pas de douchette)
F9  → Changer mode si besoin
F2  → Valider vente
F8  → Annuler si erreur
```

### 3. Formation caissier
- **Débutant :** Mode MANUEL (plus sûr)
- **Expérimenté :** Mode AUTO + F9 au besoin

---

## 🔧 Configuration Technique

### Paramètre DB
- **Clé :** `mode_scan_auto`
- **Valeurs :** `'1'` = AUTO, `'0'` = MANUEL
- **Défaut :** `'1'` (AUTO)

### Fichiers modifiés
- `ui/windows/ventes.py` - Logique scan + F9
- `ui/windows/preferences_caisse.py` - Interface paramètres
- `ui/windows/principale.py` - Menu Administration
- `RACCOURCIS.md` - Documentation

---

## 📱 Scanner : Options Disponibles

### 1. Caméra Intégrée ⭐ IMPLÉMENTÉE

**Widget caméra directement dans la fenêtre Ventes**
- Toujours visible (coin supérieur droit)
- Bouton Activer/Désactiver
- Scan en continu sans popup
- Cooldown 500ms entre scans
- **Gratuit, aucun matériel nécessaire**

**Comment l'utiliser :**
1. Ouvrir fenêtre Ventes
2. Cliquer "Activer" sur le widget caméra
3. Scanner continuellement
4. Produits ajoutés automatiquement
5. Désactiver quand terminé

### 2. Caméra Popup (F6)

**Dialogue modal pour scan occasionnel**
- F6 → ouvre popup caméra
- Scan → ferme automatiquement
- Répéter F6 pour chaque scan
- **Idéal pour scan ponctuel**

### 3. Scanner Bluetooth/USB (~15-30€)

**Solution professionnelle**
- Scanner USB filaire (~10-15€)
- Scanner Bluetooth (~30€)
- Se connecte comme un clavier
- Scan instantané
- Marques : Inateck, Tera, Eyoyo

### 4. Saisie Manuelle

**Pour produits sans code-barres**
- F5 → focus champ scan
- Taper code manuellement
- Entrée → valider

---

## ✅ Test de Validation

### Mode AUTO
```
1. Lancer application
2. Nouvelle vente
3. Scanner produit A → Ajouté direct ✓
4. Scanner produit A → Quantité = 2 ✓
5. Scanner produit B → Nouvelle ligne ✓
6. Flash vert sur lignes ajoutées ✓
```

### Mode MANUEL
```
1. F9 → Bascule MANUEL
2. Scanner produit → Popup quantité ✓
3. Entrer 5 → Ajouté qte 5 ✓
```

### Raccourci F9
```
1. F9 → Popup "Mode AUTO"
2. Scanner → Ajout direct
3. F9 → Popup "Mode MANUEL"
4. Scanner → Popup quantité
```

---

**🎉 Votre caisse est maintenant au niveau des supermarchés professionnels !**
