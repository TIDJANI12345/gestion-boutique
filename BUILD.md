# Guide de Build - Gestion Boutique v2.0

## ⚠️ Important : Premier lancement

L'exe distribué **NE DOIT PAS** contenir la base de données de développement !

- ✅ L'application crée une DB vierge au premier lancement
- ✅ L'utilisateur voit "Premier lancement" → "Licence" → "Login"
- ❌ NE PAS copier `data/boutique.db` dans le build

---

## Prérequis

- Python 3.11+
- Toutes les dépendances installées (`pip install -r requirements.txt`)
- PyInstaller 6.3.0+
- Inno Setup 6.x (pour l'installateur Windows)

---

## Build Windows

### Méthode automatique (Recommandée)

```cmd
creer_exe.bat
```

Ce script :
1. ✅ Nettoie les anciens builds
2. ✅ Installe les dépendances
3. ✅ Compile avec PyInstaller (mode onedir)
4. ✅ Copie uniquement logo.ico, logo.png, images/

**Résultat :** `dist\GestionBoutique\`

### Méthode manuelle

```cmd
# 1. Nettoyer
rmdir /s /q build dist

# 2. Build
pyinstaller --clean --noconfirm GestionBoutique.spec

# 3. Copier fichiers (SANS data/)
copy logo.ico dist\GestionBoutique\
copy logo.png dist\GestionBoutique\
xcopy /E /I /Y images dist\GestionBoutique\images
```

---

## Structure du build

```
dist/GestionBoutique/
├── GestionBoutique.exe          ← Exécutable principal
├── _internal/                   ← Dépendances PySide6, Python, DLL
├── logo.ico
├── logo.png
└── images/                      ← Images produits (optionnel)
```

**Au premier lancement, l'application crée automatiquement :**
- `%APPDATA%\GestionBoutique\data\boutique.db` (DB vierge)
- `%APPDATA%\GestionBoutique\recus\`
- `%APPDATA%\GestionBoutique\exports\`
- `%APPDATA%\GestionBoutique\images\`

---

## Créer l'installateur Windows

```cmd
# Avec Inno Setup Compiler (GUI)
1. Ouvrir installer_script.iss
2. Build > Compile

# Ou en ligne de commande
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer_script.iss
```

**Sortie :** `output\GestionBoutique_Setup_v2.0.0.exe` (~80-120 MB)

---

## Flux de premier lancement

Quand un utilisateur installe et lance l'exe :

```
1. Splash screen (2.5s)
2. Création automatique de %APPDATA%\GestionBoutique\data\
3. Création DB vierge avec tables
4. Fenêtre "Premier lancement" (créer compte admin)
5. Fenêtre "Licence" (activer avec clé)
6. Login
7. Dashboard
```

---

## Configuration PyInstaller

### Mode : onedir ✅
- Démarrage plus rapide que onefile
- Meilleur pour PySide6 (Qt6 est volumineux)
- Dossier `dist\GestionBoutique\` avec exe + `_internal\`

### Exclusions
```python
excludes=['tkinter', 'ttkthemes', '_tkinter', 'Tkinter']
```

### Hidden imports
```python
hiddenimports=['PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets']
```

---

## Test du build

### 1. Test rapide (dev)
```cmd
cd dist\GestionBoutique
GestionBoutique.exe
```

### 2. Test réaliste (utilisateur final)

```cmd
# Supprimer les données de test
rmdir /s /q %APPDATA%\GestionBoutique

# Lancer l'exe
dist\GestionBoutique\GestionBoutique.exe
```

**Vous devez voir :**
1. ✅ Splash screen
2. ✅ "Premier lancement" → créer compte
3. ✅ "Licence" → entrer clé
4. ✅ Login
5. ✅ Dashboard

### 3. Checklist complète

- [ ] Splash screen s'affiche
- [ ] Premier lancement demande de créer un compte
- [ ] Fenêtre licence demande une clé
- [ ] Login fonctionne avec le compte créé
- [ ] Dashboard s'affiche
- [ ] Toutes les fenêtres s'ouvrent (ventes, produits, rapports...)
- [ ] Scanner fonctionne (si caméra disponible)
- [ ] Vente complète : scan → paiement → reçu PDF
- [ ] Reçu se crée dans `%APPDATA%\GestionBoutique\recus\`
- [ ] Pas d'erreur dans les logs

---

## Tailles

- **Build complet (dist/):** ~150-200 MB
- **Installateur (.exe):** ~80-120 MB (LZMA compressé)
- **Installé sur PC:** ~180-220 MB

**Pourquoi si gros ?** PySide6 inclut tout Qt6 (framework complet).

---

## Problèmes courants

### ❌ L'exe montre directement le login
**Cause :** La base de données dev a été copiée dans le build.
**Solution :** Vérifier que `creer_exe.bat` ne copie PAS `data/`

### ❌ Module not found: PySide6
```cmd
pip install PySide6>=6.6.0
```

### ❌ "Failed to execute script"
1. Lancer depuis cmd pour voir l'erreur :
   ```cmd
   cd dist\GestionBoutique
   GestionBoutique.exe
   ```
2. Vérifier les logs dans `_internal\`

### ❌ UPX warnings pendant le build
Normal. UPX compresse certains fichiers Qt, peut échouer sur d'autres. Le build fonctionne quand même.

### ❌ Antivirus bloque l'exe
- Soumettre l'exe à l'antivirus (faux positif)
- Signer l'exe avec un certificat de code

---

## Distribution

### Option 1 : Installateur (Recommandé)
```
output\GestionBoutique_Setup_v2.0.0.exe
```
- Installation dans Program Files
- Raccourcis bureau/menu démarrer
- Désinstallation propre

### Option 2 : Portable (Zip)
```cmd
# Créer une archive
cd dist
7z a GestionBoutique_v2.0.0_Portable.zip GestionBoutique\
```
- Extraire et lancer GestionBoutique.exe
- Pas d'installation requise
- Données dans %APPDATA%

---

## Multiplateforme

### Linux
```bash
pyinstaller --clean --noconfirm GestionBoutique.spec
# Résultat : dist/GestionBoutique/GestionBoutique (binaire Linux)
```

Données créées dans : `~/.local/share/GestionBoutique/`

### macOS
```bash
pyinstaller --clean --noconfirm GestionBoutique.spec
# Résultat : dist/GestionBoutique.app
```

Données créées dans : `~/Library/Application Support/GestionBoutique/`

---

## Notes de version

### v2.0.0 - Migration PySide6

**Changements :**
- Migration complète Tkinter → PySide6
- Nouveau système de thème moderne
- Architecture multiplateforme
- Composants réutilisables

**Impact build :**
- Taille +100 MB (Qt6 vs Tkinter)
- Démarrage ~2-3s (chargement Qt)
- Compatibilité Windows 10/11, Linux, macOS

---

## Support

- GitHub: https://github.com/TIDJANI12345/gestion-boutique
- Email: contact@votreentreprise.bj
