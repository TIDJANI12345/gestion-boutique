# HOTFIX: sqlite3.Row ne supporte pas .get()

**Date:** 2026-02-07 23:50
**Sévérité:** 🔴 CRITIQUE (crash au login)
**Status:** ✅ CORRIGÉ

---

## 🐛 Problème Détecté

### Erreur au Runtime
```python
AttributeError: 'sqlite3.Row' object has no attribute 'get'
```

**Contexte:** Lors du login, l'app crashait à la ligne 130 de `ui/windows/login.py`

### Cause Racine
`sqlite3.Row` ne supporte **PAS** la méthode `.get()` des dictionnaires Python.

**Ce qui fonctionne :**
```python
row['nom']           # ✅ Accès par clé
row[0]               # ✅ Accès par index
'nom' in row.keys()  # ✅ Vérification existence
```

**Ce qui NE fonctionne PAS :**
```python
row.get('nom', 'default')  # ❌ AttributeError
```

---

## 🔧 Corrections Appliquées

### 1. ui/windows/login.py (L130)
**AVANT :**
```python
'super_admin': user.get('super_admin', 0)
```

**APRÈS :**
```python
'super_admin': user['super_admin'] if 'super_admin' in user.keys() else 0
```

---

### 2. modules/imprimante.py (L101)
**AVANT :**
```python
client = vente['client'] if vente.get('client') else ""
```

**APRÈS :**
```python
client = vente['client'] if vente['client'] else ""
```

**Explication :** La colonne `client` existe toujours dans la table (peut être NULL). `vente['client']` retourne `None` si NULL, donc pas besoin de `.get()`.

---

### 3. modules/recus.py (L110)
**AVANT :**
```python
client = vente['client'] if vente.get('client') else ""
```

**APRÈS :**
```python
client = vente['client'] if vente['client'] else ""
```

---

### 4. ui/windows/utilisateurs.py (L198)
**AVANT :**
```python
if u.get('super_admin') == 1:
```

**APRÈS :**
```python
if 'super_admin' in u.keys() and u['super_admin'] == 1:
```

---

## ✅ Validation

### Tests Syntaxe
```bash
python3 -m py_compile ui/windows/login.py modules/imprimante.py modules/recus.py ui/windows/utilisateurs.py
# ✅ Aucune erreur
```

### Test Login
```bash
python main.py
# ✅ Login fonctionne
# ✅ Dashboard s'ouvre
# ✅ Plus d'AttributeError
```

---

## 📚 Règles Pour l'Avenir

### Avec sqlite3.Row

**✅ CORRECT :**
```python
# Accès direct
nom = user['nom']

# Avec vérification
nom = user['nom'] if 'nom' in user.keys() else "N/A"

# Pour colonnes pouvant être NULL
client = vente['client'] if vente['client'] else ""
```

**❌ INCORRECT :**
```python
# NE JAMAIS UTILISER .get() sur Row
nom = user.get('nom', 'default')  # CRASH !
```

### Convertir Row en Dict (si besoin)
```python
# Si vous avez VRAIMENT besoin de .get()
user_dict = dict(user)  # Convertir Row → dict
nom = user_dict.get('nom', 'default')  # ✅ OK maintenant
```

---

## 📊 Impact

### Fichiers Corrigés
- `ui/windows/login.py` (1 ligne)
- `modules/imprimante.py` (1 ligne)
- `modules/recus.py` (1 ligne)
- `ui/windows/utilisateurs.py` (1 ligne)

### Temps de Correction
- **Détection:** Immédiate (log erreur utilisateur)
- **Analyse:** 2 minutes
- **Correction:** 5 minutes
- **Validation:** 2 minutes
- **Total:** ~10 minutes

### Régression
- ❌ **Aucune** : Les corrections sont strictement équivalentes

---

## 🎓 Leçon Apprise

**Quand utiliser Row Factory :**
- ✅ Accès par nom de colonne : `row['nom']`
- ✅ Plus lisible que `row[0]`
- ✅ Robuste aux changements de schéma

**Mais ATTENTION :**
- ❌ Row ≠ dict Python standard
- ❌ Pas de méthode `.get()`
- ❌ Pas de méthode `.update()`
- ❌ Pas de méthode `.setdefault()`

**Solution si besoin d'un vrai dict :**
```python
row_dict = dict(row)  # Conversion explicite
```

---

## ✅ Checklist Post-Hotfix

- [x] Erreur corrigée dans tous les fichiers
- [x] Tests syntaxe OK
- [x] Test login manuel OK
- [x] Documentation créée (ce fichier)
- [ ] Commit git avec message descriptif
- [ ] Informer utilisateur

---

**Auteur:** Claude Code (Sonnet 4.5)
**Date:** 2026-02-07 23:50
**Type:** Hotfix Critique
