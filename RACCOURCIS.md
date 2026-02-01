# Guide des Raccourcis Clavier

## Fenêtre Ventes (Caisse)

| Raccourci | Action | Description |
|-----------|--------|-------------|
| **F5** | Focus scan | Place le curseur dans le champ de scan |
| **F6** | Ouvrir caméra popup | Lance le scanner par webcam (popup) |
| **F2** | Valider vente | Procède au paiement |
| **F8** | Annuler vente | Annule la vente en cours |
| **F9** | Mode scan | Bascule AUTO/MANUEL (supermarché ou avec quantité) |
| **Ctrl+Entrée** | Valider vente | Alternative à F2 |
| **Entrée** | Scanner produit | Valide le code-barres saisi |

**Note :** Un widget caméra intégré est aussi disponible dans la fenêtre Ventes (coin supérieur droit). Activer pour scan continu sans popup.

---

## Mode de Scan

### Mode AUTOMATIQUE (supermarché) - Par défaut ✨
- Scan → ajout direct quantité 1
- Re-scan même produit → quantité s'incrémente
- **Aucune popup** de confirmation
- Flux ultra-rapide comme en supermarché

### Mode MANUEL (avec quantité)
- Scan → popup demande quantité
- Confirmation à chaque scan
- Plus sûr pour éviter les erreurs

**Basculer :** F9 ou Menu Administration → Paramètres caisse

---

## Productivité Caisse

### Flux rapide avec clavier uniquement

#### Scénario 1 : Scan manuel
```
1. F5          → Focus sur scan
2. 123456789   → Saisir code-barres
3. Entrée      → Valider
4. 2 Entrée    → Quantité (si demandée)
5. F2          → Valider vente
```

#### Scénario 2 : Scan caméra
```
1. F6          → Ouvrir caméra
2. [Présenter code devant caméra]
3. 2 Entrée    → Quantité (si demandée)
4. F2          → Valider vente
```

#### Scénario 3 : Annulation rapide
```
F8             → Annuler tout et recommencer
```

---

## Autres fenêtres (futures)

### Dashboard
| Raccourci | Action |
|-----------|--------|
| **Ctrl+N** | Nouvelle vente |
| **Ctrl+P** | Produits |
| **Ctrl+R** | Rapports |

### Produits
| Raccourci | Action |
|-----------|--------|
| **Ctrl+F** | Rechercher |
| **Ctrl+N** | Nouveau produit |
| **F5** | Actualiser |

### Rapports
| Raccourci | Action |
|-----------|--------|
| **Ctrl+E** | Exporter Excel |
| **Ctrl+P** | Imprimer |

---

## Raccourcis Windows universels

| Raccourci | Action |
|-----------|--------|
| **Alt+F4** | Fermer fenêtre |
| **Échap** | Fermer dialogue |
| **Tab** | Champ suivant |
| **Shift+Tab** | Champ précédent |

---

## Configuration

Les raccourcis sont définis dans :
- `ui/windows/ventes.py` → méthode `_setup_raccourcis()`
- Modifiables selon vos besoins

### Ajouter un raccourci

```python
QShortcut(QKeySequence("F7"), self).activated.connect(
    self._ma_fonction
)
```

---

## Affichage dans l'interface

Les raccourcis actifs sont affichés en bas de la fenêtre Ventes :

```
⌨️ Raccourcis : F5=Focus scan | F6=Caméra | F2=Valider | F8=Annuler | Ctrl+Entrée=Valider
```

---

## Conseils

### Pour caissiers débutants
Commencer par :
1. **F5** pour scanner
2. **F2** pour valider

### Pour caissiers expérimentés
- **F6** pour scan caméra (produits sans code)
- **F8** pour annulation rapide
- **Ctrl+Entrée** pour valider (main droite sur pavé numérique)

### Impression
- Après validation, le reçu s'ouvre automatiquement
- Imprimer avec **Ctrl+P** dans le PDF

---

## Personnalisation (avancé)

Modifier les raccourcis dans `ventes.py` :

```python
# Exemple : Changer F6 en F7
QShortcut(QKeySequence("F7"), self).activated.connect(
    self._ouvrir_scanner_camera
)
```

**Note :** Éviter les conflits avec raccourcis système (Ctrl+C, Ctrl+V, etc.)
