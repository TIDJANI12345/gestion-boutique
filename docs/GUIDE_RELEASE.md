# 📦 Guide de Release - Gestion Boutique

Guide complet pour créer et publier une nouvelle version avec système de mise à jour automatique.

---

## 🎯 Prérequis

- [x] Compte GitHub (pour releases) OU Dropbox/Google Drive
- [x] PyInstaller installé (`pip install pyinstaller`)
- [x] Git installé
- [x] Accès au dépôt du projet

---

## 📋 Checklist Avant Release

### 1. Code et Tests

- [ ] Tous les commits sont poussés sur `main`
- [ ] Tous les tests passent (`pytest tests/`)
- [ ] Pas d'erreurs de syntaxe (`python -m py_compile *.py`)
- [ ] CHANGELOG.md à jour avec les changements
- [ ] Documentation mise à jour si nécessaire

### 2. Version

- [ ] Incrémenter `APP_VERSION` dans `config.py`
  ```python
  # Format: MAJEUR.MINEUR.PATCH
  APP_VERSION = "2.1.0"  # Exemple
  ```

**Règles Semantic Versioning :**
- **MAJEUR** : Changements incompatibles (breaking changes)
- **MINEUR** : Nouvelles fonctionnalités (rétrocompatible)
- **PATCH** : Corrections de bugs

**Exemples :**
- `2.0.0` → `2.0.1` : Bug fixes uniquement
- `2.0.0` → `2.1.0` : Nouvelles fonctionnalités + bug fixes
- `2.0.0` → `3.0.0` : Changements majeurs (DB migration, etc.)

---

## 🛠️ Étapes de Release

### Étape 1 : Préparer le Code

```bash
# 1. Mettre à jour la version
cd /mnt/d/Projects/Python/GestionBoutique_v2
nano config.py  # Modifier APP_VERSION

# 2. Mettre à jour CHANGELOG.md
nano CHANGELOG.md

# 3. Commit et tag
git add config.py CHANGELOG.md
git commit -m "chore: Bump version to 2.1.0"
git tag -a v2.1.0 -m "Release 2.1.0 - Système audit trail complet"
git push origin main --tags
```

### Étape 2 : Compiler l'Application

#### Windows (depuis WSL ou PowerShell)

```bash
# Depuis WSL avec Python Windows
/mnt/c/Users/hp/AppData/Local/Programs/Python/Python311/python.exe -m PyInstaller GestionBoutique.spec

# OU depuis PowerShell Windows
python -m PyInstaller GestionBoutique.spec

# Fichier .exe généré dans :
# dist/GestionBoutique.exe
```

#### Linux

```bash
python3 -m PyInstaller GestionBoutique.spec

# Fichier généré dans :
# dist/GestionBoutique
```

### Étape 3 : Tester le .exe

```bash
# Tester l'exécutable
cd dist/
./GestionBoutique.exe  # Windows
./GestionBoutique      # Linux

# Tests critiques :
# ✅ Login fonctionne
# ✅ Dashboard s'ouvre
# ✅ Vente complète (scan → paiement → reçu)
# ✅ Gestion utilisateurs
# ✅ Rapports
# ✅ Sauvegarde/Restauration
```

### Étape 4 : Calculer SHA256 (Optionnel mais Recommandé)

```bash
# Windows PowerShell
Get-FileHash dist/GestionBoutique.exe -Algorithm SHA256

# Linux/WSL
sha256sum dist/GestionBoutique.exe

# Sortie exemple :
# abc123def456789... dist/GestionBoutique.exe
```

Copier le hash pour `version.json`.

### Étape 5 : Créer version.json

```bash
cd /mnt/d/Projects/Python/GestionBoutique_v2
cp version.json.template version.json
nano version.json
```

**Remplir les informations :**

```json
{
  "version": "2.1.0",
  "date": "2026-02-08",
  "url_download": "https://github.com/USERNAME/REPO/releases/download/v2.1.0/GestionBoutique.exe",
  "url_changelog": "https://github.com/USERNAME/REPO/releases/download/v2.1.0/CHANGELOG.md",
  "sha256": "abc123def456...",
  "taille_mb": 105,
  "critique": false,
  "message": "Nouvelle version avec système d'audit trail complet"
}
```

**Champs à remplir :**
- `version` : Nouvelle version (ex: `"2.1.0"`)
- `date` : Date du jour (format `YYYY-MM-DD`)
- `url_download` : URL GitHub Release (voir étape 6)
- `url_changelog` : URL du CHANGELOG
- `sha256` : Hash calculé à l'étape 4 (optionnel)
- `taille_mb` : Taille du .exe en MB (voir avec `ls -lh dist/GestionBoutique.exe`)
- `critique` : `true` si MAJ critique (affiche badge rouge), `false` sinon
- `message` : Description courte des changements

---

## 🚀 Méthode A : Release sur GitHub (RECOMMANDÉE)

### 1. Créer la Release sur GitHub

#### Option 1 : Via Interface Web

1. Aller sur `https://github.com/USERNAME/REPO/releases`
2. Cliquer "Draft a new release"
3. **Tag version** : `v2.1.0` (correspond au tag git)
4. **Release title** : `Version 2.1.0 - Système Audit Trail`
5. **Description** : Copier-coller le CHANGELOG
6. **Attach binaries** :
   - `dist/GestionBoutique.exe`
   - `CHANGELOG.md`
   - `version.json`
7. Cocher "Set as the latest release"
8. Cliquer "Publish release"

#### Option 2 : Via GitHub CLI (gh)

```bash
# Installer gh (si pas déjà fait)
# https://cli.github.com/

# Créer la release
gh release create v2.1.0 \
  --title "Version 2.1.0 - Système Audit Trail" \
  --notes-file CHANGELOG.md \
  dist/GestionBoutique.exe \
  version.json \
  CHANGELOG.md

# Vérifier
gh release view v2.1.0
```

### 2. Récupérer les URLs

Après la création, les URLs seront :

```
# Téléchargement .exe
https://github.com/USERNAME/REPO/releases/download/v2.1.0/GestionBoutique.exe

# Changelog
https://github.com/USERNAME/REPO/releases/download/v2.1.0/CHANGELOG.md

# version.json (à mettre à la racine du repo)
https://raw.githubusercontent.com/USERNAME/REPO/main/version.json
```

### 3. Mettre à jour modules/updater.py

```python
# Dans modules/updater.py, ligne 10
UPDATE_URL = "https://raw.githubusercontent.com/USERNAME/REPO/main/version.json"
```

Remplacer `USERNAME` et `REPO` par vos valeurs.

### 4. Commiter version.json dans le repo

```bash
git add version.json modules/updater.py
git commit -m "chore: Update version.json for v2.1.0"
git push origin main
```

---

## 📦 Méthode B : Release sur Dropbox

### 1. Upload sur Dropbox

1. Créer dossier `GestionBoutique_Releases/v2.1.0/`
2. Uploader :
   - `GestionBoutique.exe`
   - `CHANGELOG.md`
   - `version.json`

### 2. Créer Lien de Partage

1. Clic droit sur `GestionBoutique.exe` → "Share" → "Create link"
2. Copier le lien (ex: `https://www.dropbox.com/s/XXXX/GestionBoutique.exe?dl=0`)
3. **Important** : Remplacer `?dl=0` par `?dl=1` pour téléchargement direct

```
URL originale :
https://www.dropbox.com/s/XXXX/GestionBoutique.exe?dl=0

URL de téléchargement :
https://www.dropbox.com/s/XXXX/GestionBoutique.exe?dl=1
```

### 3. Mettre à jour version.json

```json
{
  "url_download": "https://www.dropbox.com/s/XXXX/GestionBoutique.exe?dl=1",
  "url_changelog": "https://www.dropbox.com/s/YYYY/CHANGELOG.md?dl=1"
}
```

### 4. Héberger version.json

**Option 1 : GitHub (même si .exe ailleurs)**
```bash
git add version.json
git commit -m "Update version.json for v2.1.0"
git push origin main
```

**Option 2 : Dropbox Public Folder**
```
Mettre version.json dans dossier Public de Dropbox
URL : https://dl.dropboxusercontent.com/.../version.json
```

---

## 📦 Méthode C : Release sur Google Drive

### 1. Upload sur Drive

1. Créer dossier `GestionBoutique_Releases/v2.1.0/`
2. Uploader les fichiers
3. Clic droit → "Get link" → "Anyone with the link"

### 2. Créer URL de Téléchargement Direct

**Lien Drive :**
```
https://drive.google.com/file/d/FILE_ID/view?usp=sharing
```

**URL de téléchargement direct :**
```
https://drive.google.com/uc?export=download&id=FILE_ID
```

Remplacer `FILE_ID` par l'ID dans l'URL.

### 3. Mettre à jour version.json

```json
{
  "url_download": "https://drive.google.com/uc?export=download&id=FILE_ID"
}
```

---

## 🧪 Tester la Mise à Jour

### 1. Sur Machine de Test

```bash
# 1. Installer ancienne version (ex: 2.0.0)
# 2. Lancer l'app
# 3. Attendre 3 secondes → Notification devrait apparaître
# 4. Cliquer "Télécharger" → Navigateur s'ouvre
# 5. Télécharger nouvelle version
# 6. Fermer app
# 7. Remplacer .exe
# 8. Relancer → Vérifier version dans "À propos"
```

### 2. Test Menu Manuel

```bash
# 1. Menu Aide → Vérifier les mises à jour
# 2. Devrait afficher notification
```

### 3. Test "Ignorer cette version"

```bash
# 1. Cliquer "Ignorer cette version"
# 2. Relancer app
# 3. Notification ne devrait PAS apparaître
# 4. Vérifier manuellement → Notification réapparaît
```

---

## 📊 Statistiques d'Utilisation (Optionnel)

### Tracker les Téléchargements

**GitHub Releases :**
```bash
gh release view v2.1.0
# Affiche nombre de downloads
```

**Google Analytics :**
- Ajouter tracking sur URL de téléchargement
- Voir combien d'utilisateurs ont cliqué

---

## 🔄 Workflow Complet Résumé

```bash
# 1. Préparer
git checkout main
git pull origin main

# 2. Version
nano config.py  # APP_VERSION = "2.1.0"
nano CHANGELOG.md

# 3. Commit & Tag
git add .
git commit -m "chore: Bump to v2.1.0"
git tag -a v2.1.0 -m "Release 2.1.0"
git push origin main --tags

# 4. Compiler
pyinstaller GestionBoutique.spec

# 5. Tester
dist/GestionBoutique.exe

# 6. SHA256
sha256sum dist/GestionBoutique.exe

# 7. version.json
cp version.json.template version.json
nano version.json  # Remplir infos

# 8. Release GitHub
gh release create v2.1.0 \
  --title "Version 2.1.0" \
  --notes-file CHANGELOG.md \
  dist/GestionBoutique.exe \
  version.json \
  CHANGELOG.md

# 9. Commit version.json
git add version.json modules/updater.py
git commit -m "chore: Update version.json for v2.1.0"
git push origin main

# 10. Tester
# Lancer ancienne version → Vérifier notification
```

---

## 📝 Checklist Post-Release

- [ ] Release GitHub créée et publiée
- [ ] version.json à jour dans le repo
- [ ] modules/updater.py a la bonne URL
- [ ] Testé notification sur machine test
- [ ] Annoncé sur WhatsApp/Email aux clients
- [ ] Documentation mise à jour
- [ ] Tag git poussé

---

## 🆘 Troubleshooting

### Notification ne s'affiche pas

**Vérifier :**
1. `modules/updater.py` ligne 10 : URL correcte ?
2. `version.json` accessible en ligne ?
   ```bash
   curl https://raw.githubusercontent.com/.../version.json
   ```
3. Connexion internet active ?
4. Logs : `data/logs/updater.log`

### URL de téléchargement ne fonctionne pas

**Dropbox :** Vérifier `?dl=1` (pas `?dl=0`)
**Google Drive :** Vérifier lien "Anyone with the link"
**GitHub :** Vérifier release est "Published" (pas "Draft")

### Version ignorée par erreur

```bash
# Réinitialiser depuis l'app
# OU manuellement :
sqlite3 data/boutique.db "UPDATE parametres SET valeur = '' WHERE cle = 'version_ignoree';"
```

---

## 📞 Support

En cas de problème :
1. Consulter logs : `data/logs/updater.log`
2. Vérifier connectivité : `ping github.com`
3. Tester URL manuellement dans navigateur

---

**Auteur:** Claude Code (Sonnet 4.5)
**Date:** 2026-02-08
**Version:** 1.0
