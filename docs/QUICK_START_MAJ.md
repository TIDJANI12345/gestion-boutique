# 🚀 Quick Start - Système de Mise à Jour

Guide rapide pour démarrer avec le système de mise à jour automatique.

---

## ⚡ Installation (5 minutes)

### 1. Installer la Dépendance

```bash
cd /mnt/d/Projects/Python/GestionBoutique_v2
pip install packaging
```

### 2. Créer Compte GitHub

👉 https://github.com/signup (gratuit, 2 minutes)

### 3. Créer Dépôt

```bash
# Via GitHub CLI (recommandé)
gh repo create GestionBoutique --public

# OU via web : github.com/new
```

### 4. Configurer l'URL

```bash
# Ouvrir modules/updater.py
nano modules/updater.py

# Ligne 10, remplacer :
UPDATE_URL = "https://raw.githubusercontent.com/USERNAME/GestionBoutique/main/version.json"
#                                           ^^^^^^^^  ^^^^^^^^^^^^^^^^
#                                           Votre nom    Nom du dépôt
```

---

## 🧪 Test Local (2 minutes)

### Simuler une Mise à Jour

```bash
# 1. Modifier version actuelle
nano config.py
# APP_VERSION = "1.0.0"  # Mettre version basse

# 2. Créer version.json local
cp version.json.template version.json
nano version.json
# {
#   "version": "2.0.0",  # Version plus haute
#   "url_download": "https://google.com",  # N'importe quelle URL
#   "message": "Test MAJ"
# }

# 3. Servir localement
python3 -m http.server 8000 &

# 4. Modifier UPDATE_URL temporairement
nano modules/updater.py
# UPDATE_URL = "http://localhost:8000/version.json"

# 5. Lancer app
python main.py

# ✅ Notification devrait apparaître après 3 secondes !
```

---

## 📦 Première Release (10 minutes)

### Étape 1 : Préparer le Code

```bash
# Remettre vraie version
nano config.py
# APP_VERSION = "2.0.0"

# Remettre vraie URL
nano modules/updater.py
# UPDATE_URL = "https://raw.githubusercontent.com/USERNAME/GestionBoutique/main/version.json"
```

### Étape 2 : Compiler

```bash
pyinstaller GestionBoutique.spec
# Attendre 2-3 minutes
# ✅ dist/GestionBoutique.exe créé
```

### Étape 3 : Créer version.json

```bash
cp version.json.template version.json
nano version.json
```

**Remplir :**
```json
{
  "version": "2.0.0",
  "date": "2026-02-08",
  "url_download": "https://github.com/USERNAME/GestionBoutique/releases/download/v2.0.0/GestionBoutique.exe",
  "message": "Version initiale avec système de MAJ"
}
```

### Étape 4 : Release GitHub

```bash
# Créer release
gh release create v2.0.0 \
  --title "Version 2.0.0 - Système MAJ" \
  --notes "Première version avec notifications automatiques" \
  dist/GestionBoutique.exe \
  version.json \
  CHANGELOG.md

# ✅ Release créée !
# URL : https://github.com/TIDJANI12345/gestion-boutique/releases/tag/v2.0.0
```

### Étape 5 : Commit version.json

```bash
git add version.json modules/updater.py
git commit -m "feat: Configure update system"
git push origin main

# ✅ version.json accessible en ligne !
# URL :https://github.com/TIDJANI12345/gestion-boutique/releases/download/v2.0.0/GestionBoutique.exe
```

---

## ✅ Vérification

### Tester URL version.json

```bash
# Dans navigateur OU terminal
curl https://github.com/TIDJANI12345/gestion-boutique/releases/download/v2.0.0/GestionBoutique.exe

# Devrait afficher le JSON
```

### Tester Notification

```bash
# Lancer app
python main.py

# Si version actuelle < version distante :
# ✅ Notification après 3 secondes
```

---

## 🔄 Releases Suivantes (5 minutes)

```bash
# 1. Version
nano config.py  # APP_VERSION = "2.1.0"

# 2. Compile
pyinstaller GestionBoutique.spec

# 3. version.json
nano version.json  # version = "2.1.0", nouvelle URL

# 4. Release
gh release create v2.1.0 \
  --notes-file CHANGELOG.md \
  dist/GestionBoutique.exe \
  version.json

# 5. Push
git add version.json config.py CHANGELOG.md
git commit -m "Release v2.1.0"
git push origin main

# ✅ DONE !
```

---

## 🎯 Checklist Démarrage

- [ ] `pip install packaging` installé
- [ ] Compte GitHub créé
- [ ] Dépôt GitHub créé
- [ ] `UPDATE_URL` configuré dans `modules/updater.py`
- [ ] Test local effectué (notification apparaît)
- [ ] Première release créée sur GitHub
- [ ] `version.json` commité dans repo main
- [ ] URL `version.json` accessible en ligne (test curl)
- [ ] Test sur machine propre (téléchargement fonctionne)

---

## 📞 Aide Rapide

### Erreur "Module packaging not found"
```bash
pip install packaging
```

### Erreur "gh command not found"
```bash
# Installer GitHub CLI
# Windows : https://cli.github.com/
# Linux : sudo apt install gh
```

### Notification ne s'affiche jamais
```bash
# Vérifier URL accessible
curlhttps://github.com/TIDJANI12345/gestion-boutique/releases/download/v2.0.0/GestionBoutique.exe

# Vérifier logs
cat data/logs/updater.log
```

### Version pas détectée
```bash
# Format doit être x.y.z (Semantic Versioning)
# ✅ OK : "2.0.0", "2.1.0", "3.0.0"
# ❌ KO : "v2.0", "2.0", "version-2"
```

---

## 🎓 Ressources

- **Doc complète :** `IMPLEMENTATION_MAJ_COMPLETE.md`
- **Guide technique :** `SYSTEME_MAJ_README.md`
- **Workflow release :** `GUIDE_RELEASE.md`
- **Guide utilisateur :** `MISES_A_JOUR_UTILISATEUR.md`

---

## 🎉 C'est Parti !

Votre système de mise à jour est prêt !

**Prochaine étape :** Créer votre première release et partager avec vos utilisateurs 🚀

---

**Questions ?** Relire `IMPLEMENTATION_MAJ_COMPLETE.md`
