# Plan de Migration : Tkinter → PySide6 (Qt6)

## Objectifs

1. **Migrer l'interface** de Tkinter vers PySide6 (Qt6)
2. **Rendre l'application multiplateforme** : Windows, Linux, macOS

## Analyse honnete de la situation actuelle

### Ce qui fonctionne bien (a garder tel quel)
- **`modules/`** : 18 modules de logique metier **independants du framework UI**. Ils font des requetes DB et retournent des donnees. Aucun import tkinter. **Zero modification necessaire.**
- **`database.py`** : Couche DB propre avec singleton, transactions, migrations. **Reutilisable tel quel.**

### Ce qui doit etre reecrit
- **`interface/`** : 19 fichiers Tkinter (fenetres). **Reecriture complete.**
- **`main.py`** : Flux de demarrage lie a `tk.Tk()`. **Reecriture.**
- **`config.py`** : Chemins codes en dur pour Windows (`APPDATA`). **Adaptation multiplateforme.**
- **`qt_utils.py`** : Deja commence mais incomplet. **A completer et utiliser.**

### Ce qui est actuellement Windows-only (a corriger)
- **`config.py:18-21`** : `os.getenv('APPDATA')` → n'existe pas sur Linux/macOS
- **Inno Setup** : Installateur Windows uniquement
- **PyInstaller** : Configure pour `.exe` seulement
- **`modules/imprimante.py`** : Les chemins USB vendor/product sont les memes, mais les ports serie different (`COM3` vs `/dev/ttyUSB0`)
- **Encodage** : `sys.stdout.reconfigure(encoding='utf-8')` specifique aux problemes Windows cp1252

### Pourquoi cette migration est faisable
La separation interface/logique metier est deja faite. Les modules ne connaissent pas Tkinter. On reecrit **seulement la couche UI** et on adapte les chemins, pas la logique.

---

## Strategie : Cohabitation dans le meme projet

### Structure cible pendant la migration

```
GestionBoutique_v2/
├── main.py                    # Ancien point d'entree (Tkinter) - GARDE temporairement
├── main_qt.py                 # Nouveau point d'entree (PySide6) - CREE
├── config.py                  # Adapte pour supporter les deux
├── database.py                # INCHANGE
│
├── interface/                 # Ancien code Tkinter - SUPPRIME a la fin
│   ├── fenetre_principale.py
│   ├── fenetre_ventes.py
│   ├── ... (19 fichiers)
│   └── qt_utils.py            # DEPLACE vers ui/
│
├── ui/                        # NOUVEAU - Interface PySide6
│   ├── __init__.py
│   ├── theme.py               # Systeme de theme Qt (couleurs, styles QSS)
│   ├── components/            # Composants reutilisables
│   │   ├── __init__.py
│   │   ├── table.py           # QTableView configure pour l'app
│   │   ├── toolbar.py         # Barre d'outils standard
│   │   ├── dialogs.py         # Dialogues communs (confirmation, saisie)
│   │   └── scanner.py         # Widget scanner code-barres
│   │
│   ├── windows/               # Fenetres de l'application
│   │   ├── __init__.py
│   │   ├── login.py
│   │   ├── premier_lancement.py
│   │   ├── licence.py
│   │   ├── principale.py
│   │   ├── principale_caissier.py
│   │   ├── ventes.py
│   │   ├── paiement.py
│   │   ├── confirmation_vente.py
│   │   ├── produits.py
│   │   ├── clients.py
│   │   ├── utilisateurs.py
│   │   ├── rapports.py
│   │   ├── liste_ventes.py
│   │   ├── parametres_fiscaux.py
│   │   ├── config_sync.py
│   │   ├── whatsapp.py
│   │   └── a_propos.py
│   │
│   └── resources/             # Icones, images
│       └── icons/
│
├── modules/                   # INCHANGE - logique metier
├── tests/                     # Tests adaptes
└── tests_qt/                  # Nouveaux tests pour l'UI Qt
```

### Structure cible finale (apres migration)

```
GestionBoutique_v2/
├── main.py                    # Point d'entree PySide6
├── config.py                  # Multiplateforme (Windows/Linux/macOS)
├── database.py                # INCHANGE
├── ui/                        # Interface PySide6
│   ├── ...
├── modules/                   # INCHANGE
├── tests/
├── packaging/                 # NOUVEAU - Scripts d'installation par OS
│   ├── windows/
│   │   └── gestion_boutique.iss   # Inno Setup (Windows)
│   ├── linux/
│   │   └── gestion_boutique.desktop  # Fichier .desktop (Linux)
│   └── build.py               # Script PyInstaller multiplateforme
└── requirements.txt
```

### Pourquoi cette structure et pas une autre

**L'idee de creer dans le meme projet est bonne.** Voici pourquoi :
- On peut tester `main_qt.py` pendant que `main.py` (Tkinter) reste fonctionnel
- Pas de risque de casser le logiciel en production
- Git suit tout l'historique
- Quand la migration est terminee : `rm -rf interface/` et renommer `main_qt.py` → `main.py`

**Ce que j'aurais deconseille :**
- Creer un projet separe (perte du contexte Git, duplication des modules)
- Modifier les fichiers Tkinter en place (risque de tout casser)
- Utiliser un adaptateur/bridge Tkinter↔Qt (complexite inutile)

---

## Ordre de migration (par priorite)

### Phase 0 : Fondation (FAIRE EN PREMIER)

**Objectif :** Infrastructure Qt de base, sans toucher au code existant.

| Etape | Fichier | Description |
|-------|---------|-------------|
| 0.1 | `ui/__init__.py` | Package init |
| 0.2 | `ui/theme.py` | Couleurs, polices, stylesheet QSS globale |
| 0.3 | `ui/components/table.py` | `BoutiqueTableView` : QTableView + QSortFilterProxyModel preconfigure |
| 0.4 | `ui/components/dialogs.py` | Dialogues standard : confirmation, saisie quantite, erreur |
| 0.5 | `ui/components/toolbar.py` | Barre d'outils avec raccourcis clavier |
| 0.6 | `main_qt.py` | Point d'entree minimal : QApplication + une fenetre vide |
| 0.7 | Adapter `config.py` | **Rendre multiplateforme** + ajouter constantes Qt sans casser Tkinter |
| 0.8 | `ui/platform.py` | Detection OS et chemins specifiques par plateforme |

**Validation :** `python main_qt.py` affiche une fenetre vide avec le bon theme sur Windows ET Linux.

### Phase 1 : Authentification

**Objectif :** Pouvoir se connecter via Qt.

| Etape | Fichier | Remplace |
|-------|---------|----------|
| 1.1 | `ui/windows/licence.py` | `interface/fenetre_licence.py` |
| 1.2 | `ui/windows/premier_lancement.py` | `interface/fenetre_premier_lancement.py` |
| 1.3 | `ui/windows/login.py` | `interface/fenetre_login.py` |
| 1.4 | Mettre a jour `main_qt.py` | Flux complet : licence → premier lancement → login |

**Validation :** On peut se connecter de A a Z via `main_qt.py`.

**Pourquoi commencer par la :** C'est le flux d'entree. Sans login, on ne peut rien tester d'autre. Et ces fenetres sont simples (formulaires).

### Phase 2 : Dashboard principal

| Etape | Fichier | Remplace |
|-------|---------|----------|
| 2.1 | `ui/windows/principale.py` | `interface/fenetre_principale.py` |
| 2.2 | `ui/windows/principale_caissier.py` | `interface/fenetre_principale_caissier.py` |

**Points critiques :**
- Statistiques temps reel (QTimer remplace `root.after()`)
- Graphiques matplotlib : remplacer backend TkAgg par backend Qt5Agg
- Session timeout : QTimer + evenements Qt
- Raccourcis clavier : QShortcut (F1=Ventes, F2=Produits, etc.)

**Validation :** Dashboard complet avec stats, graphiques, boutons de navigation.

### Phase 3 : Ventes (le coeur du logiciel)

**C'est la phase la plus critique. A faire avec le plus de soin.**

| Etape | Fichier | Remplace |
|-------|---------|----------|
| 3.1 | `ui/components/scanner.py` | Widget scanner integre |
| 3.2 | `ui/windows/ventes.py` | `interface/fenetre_ventes.py` |
| 3.3 | `ui/windows/paiement.py` | `interface/fenetre_paiement.py` |
| 3.4 | `ui/windows/confirmation_vente.py` | `interface/fenetre_confirmation_vente.py` |

**Ameliorations Qt vs Tkinter :**
- Panier : QTableView au lieu de Treeview (tri, edition inline de quantite)
- Scanner : QCamera au lieu d'OpenCV dans un Toplevel
- Paiement : QDialog modal propre (pas de `grab_set` fragile)
- Raccourcis : F5=scanner, Entree=ajouter, Suppr=retirer du panier

**Validation :** Faire une vente complete : scan → panier → paiement → recu → confirmation.

### Phase 4 : Gestion (produits, clients, utilisateurs)

| Etape | Fichier | Remplace |
|-------|---------|----------|
| 4.1 | `ui/windows/produits.py` | `interface/fenetre_produits.py` |
| 4.2 | `ui/windows/clients.py` | `interface/fenetre_clients.py` |
| 4.3 | `ui/windows/utilisateurs.py` | `interface/fenetre_utilisateurs.py` |

**Ameliorations Qt :**
- Recherche en temps reel avec QSortFilterProxyModel
- Edition inline dans le tableau
- Import/export Excel via QFileDialog

### Phase 5 : Rapports et outils

| Etape | Fichier | Remplace |
|-------|---------|----------|
| 5.1 | `ui/windows/rapports.py` | `interface/fenetre_rapports.py` |
| 5.2 | `ui/windows/liste_ventes.py` | `interface/fenetre_liste_ventes.py` |
| 5.3 | `ui/windows/parametres_fiscaux.py` | `interface/fenetre_parametres_fiscaux.py` |
| 5.4 | `ui/windows/config_sync.py` | `interface/fenetre_config_sync.py` |
| 5.5 | `ui/windows/whatsapp.py` | `interface/fenetre_whatsapp.py` |
| 5.6 | `ui/windows/a_propos.py` | `interface/fenetre_a_propos.py` |

### Phase 6 : Nettoyage final

| Etape | Action |
|-------|--------|
| 6.1 | Supprimer `interface/` (tout le dossier) |
| 6.2 | Renommer `main_qt.py` → `main.py` |
| 6.3 | Supprimer `ttkthemes` des dependances |
| 6.4 | Ajouter `PySide6` aux dependances |
| 6.5 | Adapter PyInstaller pour Qt |
| 6.6 | Adapter l'installateur Inno Setup |
| 6.7 | Mettre a jour `requirements.txt` |
| 6.8 | Supprimer `qt_utils.py` de `interface/` |

---

## Support multiplateforme (integre dans la migration)

### Adaptation de `config.py` (Phase 0, etape 0.7)

Le code actuel :
```python
# AVANT - Windows seulement
APPDATA = os.getenv('APPDATA') or os.path.expanduser('~')
BASE_DIR = os.path.join(APPDATA, 'GestionBoutique')
```

Le code cible :
```python
# APRES - Multiplateforme
import platform

def _get_base_dir():
    """Retourne le dossier de donnees selon l'OS."""
    if getattr(sys, 'frozen', False):
        # Mode .exe / binaire compile
        systeme = platform.system()
        if systeme == 'Windows':
            base = os.getenv('APPDATA', os.path.expanduser('~'))
        elif systeme == 'Darwin':  # macOS
            base = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support')
        else:  # Linux et autres
            base = os.environ.get('XDG_DATA_HOME', os.path.join(os.path.expanduser('~'), '.local', 'share'))
        return os.path.join(base, 'GestionBoutique')
    else:
        # Mode dev - dossier projet
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = _get_base_dir()
```

### Chemins des donnees par OS

| Donnees | Windows | Linux | macOS |
|---------|---------|-------|-------|
| Base | `%APPDATA%/GestionBoutique/` | `~/.local/share/GestionBoutique/` | `~/Library/Application Support/GestionBoutique/` |
| DB | `data/boutique.db` | idem (relatif a Base) | idem |
| Recus | `recus/` | idem | idem |
| Logs | `data/logs/` | idem | idem |
| Sauvegardes | `sauvegardes/` | idem | idem |

### Adaptation de l'imprimante (Phase 3)

| Parametre | Windows | Linux | macOS |
|-----------|---------|-------|-------|
| Port serie | `COM3`, `COM4` | `/dev/ttyUSB0`, `/dev/ttyACM0` | `/dev/tty.usbserial-*` |
| USB (python-escpos) | Identique (vendor_id/product_id) | Identique | Identique |
| Reseau | Identique (IP:port) | Identique | Identique |
| Permissions USB | Aucune config | Ajouter user au groupe `lp` ou regle udev | Aucune config |

Le module `modules/imprimante.py` n'importe pas Tkinter, donc **pas de reecriture**.
Seule adaptation : proposer les bons ports serie dans l'UI selon l'OS.

### Encodage (Phase 0)

```python
# AVANT - Fix specifique Windows
if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# APRES - Appliquer seulement sur Windows
if platform.system() == 'Windows' and sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
```

### Packaging par OS (Phase 6)

| OS | Outil | Format | Script |
|----|-------|--------|--------|
| Windows | PyInstaller + Inno Setup | `.exe` + installateur `.exe` | `packaging/windows/gestion_boutique.iss` |
| Linux | PyInstaller | AppImage ou `.deb` | `packaging/linux/build_linux.sh` |
| macOS | PyInstaller | `.app` + `.dmg` | `packaging/macos/build_macos.sh` |

**Script PyInstaller unifie (`packaging/build.py`) :**
```python
import platform
import subprocess

systeme = platform.system()
common_args = [
    'pyinstaller',
    '--name=GestionBoutique',
    '--windowed',
    '--onedir',
    'main.py',
]

if systeme == 'Windows':
    common_args += ['--icon=ui/resources/icons/app.ico']
elif systeme == 'Darwin':
    common_args += ['--icon=ui/resources/icons/app.icns']
# Linux : pas d'icone intégrée au binaire

subprocess.run(common_args)
```

### Ce qui ne change PAS entre les OS

- **SQLite** : Fonctionne partout identiquement
- **Logique metier** (`modules/`) : Aucun code specifique a l'OS
- **PySide6** : Meme API sur tous les OS
- **ReportLab** (PDF) : Multiplateforme
- **python-barcode** : Multiplateforme
- **Synchronisation cloud** : HTTP, identique partout

---

## Regles de migration (a respecter pour chaque fenetre)

### 1. Correspondances Tkinter → Qt

| Tkinter | PySide6 | Notes |
|---------|---------|-------|
| `tk.Tk()` | `QMainWindow` | Fenetre racine |
| `tk.Toplevel()` | `QDialog` ou `QMainWindow` | Selon modal ou non |
| `ttk.Treeview` | `QTableView` + `QStandardItemModel` | Bien plus puissant |
| `ttk.Entry` | `QLineEdit` | Equivalent direct |
| `ttk.Button` | `QPushButton` | Equivalent direct |
| `ttk.Label` | `QLabel` | Equivalent direct |
| `ttk.Combobox` | `QComboBox` | Equivalent direct |
| `ttk.Frame` | `QWidget` + `QLayout` | Qt utilise des layouts |
| `messagebox.showinfo` | `QMessageBox.information` | Equivalent direct |
| `messagebox.askyesno` | `QMessageBox.question` | Equivalent direct |
| `filedialog.askopenfilename` | `QFileDialog.getOpenFileName` | Equivalent direct |
| `root.after(ms, func)` | `QTimer.singleShot(ms, func)` | Equivalent direct |
| `bind('<KeyPress>')` | `QShortcut` ou `keyPressEvent` | Plus propre en Qt |
| `grid(row, col)` | `QGridLayout` | Equivalent direct |
| `pack()` | `QVBoxLayout` / `QHBoxLayout` | Equivalent direct |
| `grab_set()` | `exec()` (QDialog modal) | Plus fiable en Qt |
| Callback functions | Signaux/Slots Qt | Paradigme Qt natif |

### 2. Pattern de conversion d'une fenetre

```python
# AVANT (Tkinter) - fenetre_login.py
class FenetreLogin:
    def __init__(self, callback_success):
        self.root = tk.Tk()
        self.callback = callback_success
        # ... setup widgets ...
        self.root.mainloop()

# APRES (PySide6) - ui/windows/login.py
class LoginWindow(QDialog):
    # Signal Qt au lieu de callback
    login_success = Signal(dict)  # emet les infos user

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        # ... setup widgets avec layouts ...
        pass

    def _on_login(self):
        # ... verification ...
        self.login_success.emit(user_info)
        self.accept()
```

### 3. Regles strictes

- **Ne jamais importer tkinter dans `ui/`**
- **Ne jamais importer PySide6 dans `interface/`**
- **Les modules metier (`modules/`) ne doivent importer ni l'un ni l'autre**
- **Chaque fenetre Qt doit etre testable independamment**
- **Utiliser les signaux/slots Qt, pas des callbacks bruts**
- **Utiliser QSS (Qt Style Sheets) pour le style, pas du code Python**

---

## Risques et mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Matplotlib backend | Les graphiques utilisent TkAgg | Changer pour QtAgg (`matplotlib.use('QtAgg')`) |
| OpenCV + Camera | Scanner utilise cv2 dans un Toplevel Tk | Utiliser QCamera ou cv2 avec QImage |
| PyInstaller | La config actuelle est pour Tkinter | Ajouter les hooks PySide6 pour PyInstaller |
| Taille de l'exe | PySide6 est plus lourd que Tkinter (~80MB) | Utiliser `--exclude-module` pour exclure les modules Qt inutiles |
| Impression thermique | python-escpos ne depend pas de Qt | Aucun changement necessaire |
| Double mainloop | Tk et Qt ne peuvent pas coexister dans le meme processus | Utiliser `main.py` OU `main_qt.py`, jamais les deux |
| Chemins Windows en dur | `APPDATA`, `COM3`, etc. ne marchent pas sur Linux/macOS | Utiliser `platform.system()` + chemins dynamiques (voir section multiplateforme) |
| Permissions USB Linux | L'utilisateur ne peut pas acceder a l'imprimante USB | Documenter : `sudo usermod -a -G lp $USER` + regle udev |
| Polices systeme | Les polices different entre OS | Utiliser des polices Qt generiques ou embarquer une police (ex: Roboto) |
| Raccourcis clavier | Ctrl vs Cmd sur macOS | Utiliser `QKeySequence.StandardKey` qui s'adapte automatiquement |

---

## Dependances a ajouter

```txt
PySide6>=6.6.0              # Framework Qt6 - multiplateforme
platformdirs>=4.0.0         # Chemins standard par OS (alternative robuste a notre _get_base_dir)
```

**A retirer (Phase 6) :**
```txt
ttkthemes==3.2.2            # Plus necessaire (Tkinter)
```

**A garder :**
```txt
# Tout le reste reste identique - les modules metier
# ne changent pas, donc leurs dependances non plus.
```

**Note sur `platformdirs` :** Cette librairie est le standard Python pour obtenir les bons chemins selon l'OS (`user_data_dir`, `user_config_dir`, `user_log_dir`). C'est plus fiable que notre propre detection. Exemple :
```python
from platformdirs import user_data_dir
BASE_DIR = user_data_dir("GestionBoutique", "GestionBoutique")
# Windows : C:\Users\X\AppData\Roaming\GestionBoutique
# Linux   : ~/.local/share/GestionBoutique
# macOS   : ~/Library/Application Support/GestionBoutique
```

---

## Comment valider chaque phase

Apres chaque phase :

1. **Lancer `main_qt.py`** et verifier que la phase fonctionne
2. **Lancer `main.py`** (Tkinter) et verifier que RIEN n'est casse
3. **Lancer les tests** : `python -m pytest tests/`
4. **Tester manuellement** le flux critique : connexion → vente → paiement → recu

Les deux versions doivent fonctionner en parallele jusqu'a la Phase 6.

---

## Estimation realiste

- **Phase 0 (Fondation)** : Base necessaire avant tout
- **Phase 1 (Auth)** : 3 fenetres simples (formulaires)
- **Phase 2 (Dashboard)** : 2 fenetres complexes (stats, graphiques, timers)
- **Phase 3 (Ventes)** : La plus critique, la plus complexe
- **Phase 4 (Gestion)** : 3 fenetres moyennes (CRUD avec tableaux)
- **Phase 5 (Outils)** : 6 fenetres simples a moyennes
- **Phase 6 (Nettoyage)** : Suppression et configuration

**Total : 19 fenetres + composants + main_qt.py + theme**

---

## Mon avis sincere

Cette migration est **le bon choix** pour un logiciel de caisse commercial. Mais soyons clairs :

**Ce qui va bien se passer :**
- Les modules metier ne bougent pas → pas de regression metier
- Qt est fait pour ce type d'application → les tableaux, dialogues, impression seront meilleurs
- Le resultat sera visuellement professionnel

**Ce qui demande de l'attention :**
- La Phase 3 (Ventes) est critique. C'est le coeur du logiciel. Il faut tester exhaustivement
- Le passage de callbacks a signaux/slots change le paradigme de communication entre fenetres
- PyInstaller + PySide6 produit un executable plus lourd (prevoir ~150MB vs ~50MB avec Tkinter)

**Sur le multiplateforme :**
- 90% du code est deja portable (SQLite, Python, logique metier)
- Les seuls points d'attention sont : chemins fichiers, ports serie imprimante, packaging
- `platformdirs` + `platform.system()` resolvent les chemins proprement
- PySide6 gere nativement le look natif sur chaque OS (pas de travail supplementaire)
- Le packaging necessite de tester sur chaque OS cible (ou utiliser un CI comme GitHub Actions)

**Ce que je recommande :**
- Faire Phase 0 + Phase 1 d'abord pour valider l'approche
- Si ca fonctionne bien, continuer avec confiance
- Ne pas supprimer le code Tkinter avant que TOUT soit migre et teste
- Tester sur Linux des la Phase 0 pour detecter les problemes tot
