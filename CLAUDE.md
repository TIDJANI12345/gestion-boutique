# CLAUDE.md

Ce fichier fournit des directives à Claude Code (claude.ai/code) pour travailler avec le code de ce dépôt.

## Mode de Réponse
- Concis. Code uniquement. Pas d'explications bavardes.
- Utiliser des blocs rechercher/remplacer pour les modifications. NE PAS afficher les fichiers complets.
- Pas de commentaires évidents.
- Usage minimal de tokens.

---

## Aperçu du Projet

Système de point de vente (POS) pour commerces de détail. Déployé au Bénin (devise : FCFA, TVA : 18%).
Fonctionnalités : ventes, inventaire, clients, reçus, intégration imprimante thermique.

**Migration :** Tkinter → PySide6 **TERMINÉE** ✅

---

## Architecture

### Principe Fondamental : Séparation des Responsabilités
- **`modules/`** - Logique métier (18 modules). **NE JAMAIS** importer de frameworks UI (tkinter/PySide6)
- **`database.py`** - Singleton SQLite. Tous les accès DB passent par ici
- **`ui/`** - Couche d'interface PySide6
- **`config.py`** - Configuration multiplateforme (Windows/Linux/macOS)

### Fichiers Clés
```
main.py                    # Point d'entrée PySide6
database.py                # Singleton DB : db.execute_query(), db.fetch_*()
config.py                  # BASE_DIR, DB_PATH (détection OS)
modules/                   # Logique métier (indépendant UI)
  ventes.py                # Moteur de ventes
  produits.py              # Produits
  utilisateurs.py          # Utilisateurs + hiérarchie des rôles
  permissions.py           # Système de rôles à 3 niveaux
  imprimante.py            # Imprimante thermique (ESC/POS)
  recus.py                 # Reçus PDF (ReportLab)
ui/
  theme.py                 # Styles QSS
  platform.py              # Détection OS, chemins
  components/              # Composants réutilisables (table, dialogs, toolbar, scanner)
  windows/                 # Fenêtres de l'application
    ventes.py              # Fenêtre ventes (CRITIQUE)
    paiement.py            # Modal de paiement
    principale*.py         # 3 dashboards (patron/gestionnaire/caissier)
```

### Base de Données
- SQLite : `{BASE_DIR}/data/boutique.db`
- Pattern singleton : `from database import db`
- Accès : `db.execute_query(sql, params)`, `db.fetch_one()`, `db.fetch_all()`
- Config clé-valeur : `db.get_parametre(key)`, `db.set_parametre(key, val)`

### Hiérarchie des Rôles (3 niveaux)
1. **Super-Admin (patron)** - 1 seul compte, accès total
2. **Gestionnaire** - Gestion produits/stocks, ne peut pas gérer les utilisateurs
3. **Caissier** - Ventes uniquement, dashboard limité

Appliqué via `modules/permissions.py` et `modules/utilisateurs.py::est_super_admin()`

---

## Flux Critiques

### Flux de Vente
```
Scanner/saisie manuelle → Panier (mémoire) → Modal paiement → Transaction DB atomique
→ MAJ stock → Reçu PDF → Confirmation → Callback rafraîchissement dashboard
```

**Fichiers :** `ui/windows/ventes.py`, `ui/windows/paiement.py`, `modules/ventes.py`

### Flux d'Authentification
```
Splash → Vérif licence → Premier lancement (si aucun utilisateur) → Login → Dashboard selon rôle
```

**Fichiers :** `main.py`, `ui/windows/{licence,premier_lancement,login}.py`

### Routage Dashboard (main.py)
```python
if role == 'patron' or user.get('super_admin') == 1:
    → PrincipaleWindow
elif role == 'gestionnaire':
    → PrincipaleGestionnaireWindow
elif role == 'caissier':
    → PrincipaleCaissierWindow
```

---

## Commandes de Développement

### Exécution
```bash
python main.py                          # Lancer l'app PySide6
python main_tkinter_backup.py          # Ancienne version Tkinter (backup)
```

### Python Windows depuis WSL
```bash
/mnt/c/Users/hp/AppData/Local/Programs/Python/Python311/python.exe main.py
```

### Tests
```bash
python -m pytest tests/                 # Tous les tests
python -m pytest tests/test_ventes.py   # Fichier de test unique
python -m pytest -v -k "test_name"      # Test spécifique
```

**Config tests :** `tests/conftest.py` configure la DB en mémoire (`:memory:`) pour isoler les tests

### Compilation
```bash
pyinstaller GestionBoutique.spec        # Créer l'exécutable
```

---

## Conventions

### Naming
- **Qt windows:** `XxxWindow` (class), `xxx.py` (file) in `ui/windows/`
- **Tkinter (legacy):** `FenetreXxx` (class), `fenetre_xxx.py` in `interface/`
- **UI language:** French (end-user facing)
- **Code/comments:** French or English

### Qt Patterns
- Use **signals/slots**, not raw callbacks
- Dialogs: inherit `QDialog`, use `exec()` for modal
- Styling: QSS in `ui/theme.py`, not inline Python
- Shortcuts: `QShortcut` or `QKeySequence.StandardKey` (cross-platform)

### Business Logic Rules
- Modules in `modules/` **MUST NOT** import `tkinter` or `PySide6`
- All UI-agnostic code goes in `modules/`
- DB access only via `database.py` singleton

---

## Multiplatform Support

### Paths (handled by `config.py`)
| OS      | Data Dir                                              |
|---------|-------------------------------------------------------|
| Windows | `%APPDATA%/GestionBoutique/`                          |
| Linux   | `~/.local/share/GestionBoutique/`                     |
| macOS   | `~/Library/Application Support/GestionBoutique/`      |

### Serial Ports (thermal printer)
| OS      | Ports                                  |
|---------|----------------------------------------|
| Windows | `COM3`, `COM4`, ...                    |
| Linux   | `/dev/ttyUSB0`, `/dev/ttyACM0`, ...    |
| macOS   | `/dev/tty.usbserial-*`                 |

Detection: `ui/platform.py::get_serial_ports()`

### Packaging
- **Windows:** PyInstaller + Inno Setup
- **Linux:** PyInstaller → AppImage or `.deb`
- **macOS:** PyInstaller → `.app` + `.dmg`

---

## Common Patterns

### Database Transaction
```python
from database import db

# Single query
result = db.execute_query("INSERT INTO produits (nom, prix_vente) VALUES (?, ?)", ("Test", 100))

# Fetch
products = db.fetch_all("SELECT * FROM produits WHERE stock_actuel < ?", (10,))
product = db.fetch_one("SELECT * FROM produits WHERE id = ?", (1,))

# Transaction (auto-commit/rollback)
with db.conn:
    db.execute_query("UPDATE stock ...")
    db.execute_query("INSERT INTO historique ...")
```

### Qt Signal/Slot
```python
from PySide6.QtCore import Signal

class MyWindow(QDialog):
    data_changed = Signal(dict)  # Define signal

    def some_action(self):
        self.data_changed.emit({'key': 'value'})  # Emit

# Connect
window.data_changed.connect(self.on_data_changed)
```

### Permissions Check
```python
from modules.permissions import Permissions

if not Permissions.peut(user, 'gerer_produits'):
    erreur(self, "Accès refusé")
    return
```

---

## Important Files to Read First

When working on:
- **Sales:** Read `modules/ventes.py`, `ui/windows/ventes.py`, `ui/windows/paiement.py`
- **Users/Roles:** Read `modules/utilisateurs.py`, `modules/permissions.py`, `PLAN_HIERARCHIE_ROLES.md`
- **Database:** Read `database.py` (lines 1-200 for schema)
- **Theming:** Read `ui/theme.py`
- **Platform:** Read `ui/platform.py`, `config.py`

---

## Migration Notes

**Tkinter → PySide6 migration completed.**
- Backup Tkinter code: `main_tkinter_backup.py`, `interface/` (deprecated)
- **Do not modify** files in `interface/` - use `ui/` equivalents
- See `MIGRATION_PYSIDE6.md` for full migration plan (historical reference)

---

## Development Environment

- **Python:** 3.11+
- **WSL users:** Use Windows Python path for GUI testing
- **Dependencies:** See `requirements.txt`
  - Core: `PySide6>=6.6.0`, `platformdirs>=4.0.0`
  - Business: `reportlab`, `python-escpos`, `opencv-python`, `pyzbar`, `bcrypt`
  - Dev: `pytest>=7.0.0`, `pyinstaller==6.3.0`
