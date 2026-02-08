# 🔄 Système de Mise à Jour Automatique - Documentation Technique

Documentation technique du système de notification et téléchargement de mises à jour.

---

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Serveur (GitHub/Dropbox/Drive)                              │
│  ├─ version.json (2-3 KB)                                   │
│  ├─ GestionBoutique_v2.1.0.exe (100-150 MB)                │
│  └─ CHANGELOG.md                                            │
└─────────────────────────────────────────────────────────────┘
                        │
                        │ HTTP GET (lightweight)
                        ▼
┌─────────────────────────────────────────────────────────────┐
│  Application PySide6                                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ main.py                                                │  │
│  │ ├─ Au démarrage (+ 3 sec)                            │  │
│  │ └─ verifier_mises_a_jour_auto()                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ modules/updater.py                                     │  │
│  │ ├─ Updater.verifier_mise_a_jour()                    │  │
│  │ ├─ Compare versions (packaging.version)              │  │
│  │ └─ Return (bool, dict)                                │  │
│  └───────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ ui/dialogs/update_notification.py                     │  │
│  │ ├─ UpdateNotificationDialog                           │  │
│  │ ├─ Affiche infos (version, taille, message)          │  │
│  │ └─ Actions : Télécharger / Plus tard / Ignorer       │  │
│  └───────────────────────────────────────────────────────┘  │
│                        │                                     │
│                        ▼                                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ webbrowser.open(url_download)                         │  │
│  │ → Ouvre navigateur pour téléchargement               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Fichiers Créés

### 1. `modules/updater.py`

**Responsabilités :**
- Vérifier version distante (HTTP GET vers version.json)
- Comparer versions (Semantic Versioning)
- Gérer versions ignorées (DB parametres)
- Ouvrir navigateur pour téléchargement
- Logger toutes les opérations

**API Publique :**
```python
class Updater:
    @staticmethod
    def verifier_mise_a_jour(version_actuelle: str) -> tuple[bool, dict | None]
        """Retourne (nouvelle_dispo, infos) ou (False, None)"""

    @staticmethod
    def ouvrir_page_telechargement(url: str) -> None
        """Ouvre navigateur avec URL"""

    @staticmethod
    def ignorer_version(version: str) -> None
        """Marque version comme ignorée"""

    @staticmethod
    def est_ignoree(version: str) -> bool
        """Vérifie si version ignorée"""
```

**Configuration :**
```python
# Ligne 10 - À MODIFIER après déploiement
UPDATE_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/version.json"

# Timeouts adaptés aux réseaux africains
TIMEOUT_VERIFICATION = 10  # secondes
RETRY_ATTEMPTS = 2
```

### 2. `ui/dialogs/update_notification.py`

**Responsabilités :**
- Afficher dialog personnalisé
- Présenter informations de version
- Gérer actions utilisateur (4 boutons)
- Afficher instructions post-téléchargement

**Composants UI :**
```python
class UpdateNotificationDialog(QDialog):
    def __init__(self, infos_update: dict, parent=None)

    # Boutons
    - _telecharger() → Ouvre navigateur + Instructions
    - _voir_changelog() → Ouvre URL changelog
    - _ignorer_version() → Marque comme ignorée
    - reject() → Ferme dialog (Plus tard)
```

### 3. Modifications `main.py`

**Ajouts :**
```python
# Ligne 63-78
def verifier_mises_a_jour_auto(fenetre_parent):
    """Vérification automatique 3 sec après dashboard"""
    nouvelle_dispo, infos = Updater.verifier_mise_a_jour(APP_VERSION)
    if nouvelle_dispo and not Updater.est_ignoree(infos['version']):
        UpdateNotificationDialog(infos, fenetre_parent).exec()

# Ligne 107
QTimer.singleShot(3000, lambda: verifier_mises_a_jour_auto(fenetre))
```

### 4. Modifications `config.py`

**Ajouts :**
```python
# Lignes 9-11
APP_VERSION = "2.0.0"  # À incrémenter à chaque release
APP_NAME = "Gestion Boutique"
```

### 5. Modifications `ui/windows/principale.py`

**Menu Aide :**
```python
# Ligne 174-183
action_verifier_maj = QAction("🔄 Vérifier les mises à jour", self)
action_verifier_maj.triggered.connect(self.verifier_mises_a_jour_manuel)

# Ligne 620-650
def verifier_mises_a_jour_manuel(self):
    """Vérification manuelle (menu Aide)"""
    # Affiche "Vérification en cours..."
    # Appelle Updater.verifier_mise_a_jour()
    # Affiche dialog si MAJ dispo OU "À jour"
```

### 6. `requirements.txt`

**Dépendances ajoutées :**
```python
packaging>=21.0  # Pour comparaison versions semver
# requests déjà présent
```

---

## 🔢 Format version.json

**Structure :**
```json
{
  "version": "2.1.0",           # REQUIRED - Format x.y.z
  "date": "2026-02-08",         # REQUIRED - ISO 8601
  "url_download": "https://...", # REQUIRED - URL .exe
  "url_changelog": "https://...",# OPTIONAL - URL changelog
  "sha256": "abc123...",        # OPTIONAL - Hash integrity
  "taille_mb": 105,             # OPTIONAL - Taille en MB
  "critique": false,            # OPTIONAL - Badge rouge
  "message": "Descriptif..."    # OPTIONAL - Description courte
}
```

**Validation :**
- `version` : Doit être format Semantic Versioning (x.y.z)
- `url_download` : Doit être URL accessible publiquement
- `sha256` : Si présent, sera vérifié (future feature)
- `critique` : Si `true`, affiche badge rouge "⚠️ CRITIQUE"

---

## 🔐 Sécurité

### Vérification Intégrité (Planifié)

**Actuellement :** Non implémenté
**Future :** Vérifier SHA256 avant installation

```python
# modules/updater.py - À implémenter
def verifier_sha256(fichier, sha256_attendu):
    import hashlib
    sha256_hash = hashlib.sha256()
    with open(fichier, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest() == sha256_attendu
```

### HTTPS Obligatoire

**Toutes les URLs doivent être HTTPS** (pas HTTP)
- GitHub Releases : ✅ HTTPS par défaut
- Dropbox Public : ✅ HTTPS par défaut
- Google Drive : ✅ HTTPS par défaut

---

## 📊 Logs

**Fichier :** `data/logs/updater.log`

**Exemples :**
```
2026-02-08 14:30:15 [INFO] updater: Vérification des mises à jour (tentative 1/2)...
2026-02-08 14:30:16 [INFO] updater: Version actuelle: 2.0.0, Version distante: 2.1.0
2026-02-08 14:30:16 [INFO] updater: ✅ Nouvelle version disponible : 2.1.0
2026-02-08 14:30:45 [INFO] updater: Ouverture du navigateur : https://github.com/...
2026-02-08 14:31:02 [INFO] updater: Version 2.1.0 marquée comme ignorée
```

**Erreurs courantes :**
```
⏱️ Timeout lors de la vérification (tentative 1/2)
❌ Pas de connexion internet pour vérifier les MAJ
❌ Erreur HTTP lors de la vérification : 404
❌ Erreur de parsing JSON : ...
```

---

## 🧪 Tests

### Test Unitaire (modules/updater.py)

```python
# tests/test_updater.py - À créer
import pytest
from modules.updater import Updater

def test_verifier_version_superieure():
    """2.1.0 > 2.0.0"""
    # Mock requests.get
    # Assert True, infos

def test_verifier_version_egale():
    """2.0.0 == 2.0.0"""
    # Assert False, None

def test_verifier_timeout():
    """Timeout réseau"""
    # Mock timeout
    # Assert False, None

def test_ignorer_version():
    """Ignorer version fonctionne"""
    # Updater.ignorer_version("2.1.0")
    # Assert Updater.est_ignoree("2.1.0") == True
```

### Test Manuel

**Scenario 1 : Notification Auto**
```
1. Modifier config.py : APP_VERSION = "1.0.0"
2. Créer version.json distant avec version = "2.0.0"
3. Lancer app
4. Attendre 3 secondes
5. ✅ Notification devrait apparaître
```

**Scenario 2 : Vérification Manuelle**
```
1. Menu Aide → Vérifier les mises à jour
2. ✅ Dialog "Vérification en cours..." apparaît
3. ✅ Soit notification, soit "À jour"
```

**Scenario 3 : Ignorer Version**
```
1. Notification apparaît
2. Cliquer "Ignorer cette version"
3. Relancer app
4. ✅ Notification ne devrait PAS apparaître
5. Menu Aide → Vérifier (manuel)
6. ✅ Notification devrait réapparaître
```

---

## 🚀 Déploiement

### 1. Configurer UPDATE_URL

```python
# modules/updater.py ligne 10
# AVANT (template)
UPDATE_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/version.json"

# APRÈS (production)
UPDATE_URL = "https://raw.githubusercontent.com/YourCompany/GestionBoutique/main/version.json"
```

### 2. Première Release

```bash
# Créer version.json initial
{
  "version": "2.0.0",
  "date": "2026-02-08",
  "url_download": "https://github.com/.../v2.0.0/GestionBoutique.exe",
  "message": "Version initiale avec système de MAJ"
}

# Commit et push
git add version.json modules/updater.py
git commit -m "feat: Configure update system for production"
git push origin main
```

### 3. Releases Suivantes

Suivre `GUIDE_RELEASE.md`

---

## 🔧 Maintenance

### Modifier UPDATE_URL

Si vous changez d'hébergement :

```python
# modules/updater.py
UPDATE_URL = "https://nouvelle-url.com/version.json"

# Recompiler et redistribuer
pyinstaller GestionBoutique.spec
```

### Désactiver Vérification Auto

Pour debug ou offline :

```python
# main.py ligne 107 - Commenter
# QTimer.singleShot(3000, lambda: verifier_mises_a_jour_auto(fenetre))
```

### Réinitialiser Versions Ignorées

```python
# Dans Python console ou script
from database import db
db.set_parametre('version_ignoree', '')

# OU SQL direct
sqlite3 data/boutique.db "UPDATE parametres SET valeur = '' WHERE cle = 'version_ignoree';"
```

---

## 📈 Métriques (Future)

### Tracking Optionnel

**À implémenter :**
- Nombre de vérifications
- Nombre de téléchargements
- Versions les plus utilisées
- Taux d'adoption des MAJ

**Solution simple :**
```python
# POST vers API analytics
requests.post("https://analytics.com/api/check", {
    "version": APP_VERSION,
    "timestamp": datetime.now(),
    "action": "check_update"  # ou "download"
})
```

---

## 🐛 Dépannage

### "URL incorrecte"

**Vérifier :**
1. `modules/updater.py` ligne 10
2. Tester URL dans navigateur
3. Vérifier HTTPS (pas HTTP)

### "Version non détectée"

**Vérifier :**
1. Format Semantic Versioning (x.y.z)
2. Pas d'espace ou caractère spécial
3. JSON valide (https://jsonlint.com/)

### "Notification ne s'affiche jamais"

**Vérifier :**
1. Connexion internet active
2. Logs dans `data/logs/updater.log`
3. Timer dans main.py pas commenté
4. Version distante > Version locale

---

## 📚 Références

- **Semantic Versioning :** https://semver.org/
- **packaging (Python) :** https://packaging.pypa.io/
- **GitHub Releases :** https://docs.github.com/en/repositories/releasing-projects-on-github
- **PySide6 QTimer :** https://doc.qt.io/qtforpython-6/PySide6/QtCore/QTimer.html

---

**Auteur:** Claude Code (Sonnet 4.5)
**Date:** 2026-02-08
**Version:** 1.0
