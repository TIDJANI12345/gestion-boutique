# 🎯 GUIDE SIMPLIFIÉ - VOUS AVEZ DÉJÀ PYTHONANYWHERE !

---

## ✅ CE QUE VOUS AVEZ DÉJÀ

```
✅ PythonAnywhere configuré : gbserver.pythonanywhere.com
✅ Endpoint /api/activer fonctionne
✅ Logiciel Gestion Boutique avec licence.py
✅ Site easywebshop.wuaze.com
✅ Base de données MySQL avec structure professionnelle
```

**Vous êtes à 80% !** Il reste juste à connecter les 2 ! 🚀

---

## 🎯 CE QU'IL MANQUE

### **1 seule chose à faire sur PythonAnywhere :**

Ajouter la route `/api/enregistrer` pour que easywebshop puisse créer des licences.

### **2 choses à faire sur easywebshop :**

1. Modifier `webhook.php` pour générer licences
2. Modifier `success.php` pour afficher licences

---

## 📋 ÉTAPE 1 : MODIFIER L'API PYTHONANYWHERE

### **1.1 Se connecter à PythonAnywhere**

- Allez sur https://www.pythonanywhere.com
- Connectez-vous avec votre compte

### **1.2 Trouver votre fichier Flask**

1. Cliquez sur **"Files"**
2. Cherchez votre fichier d'API (probablement `flask_app.py` ou `app.py`)
3. Ouvrez-le

### **1.3 Ajouter la route `/api/enregistrer`**

Ajoutez ce code dans votre fichier Flask :

```python
@app.route('/api/enregistrer', methods=['POST'])
def enregistrer_licence():
    """
    Enregistrer une nouvelle licence
    Appelé par easywebshop après paiement
    """
    try:
        data = request.json
        
        cle_licence = data.get('cle_licence')
        type_licence = data.get('type_licence', 'annuelle')
        date_expiration = data.get('date_expiration')
        
        if not cle_licence:
            return jsonify({'error': 'Clé de licence requise'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Vérifier si déjà existe
        c.execute('SELECT id FROM licences WHERE cle_licence = ?', (cle_licence,))
        if c.fetchone():
            conn.close()
            return jsonify({'error': 'Licence déjà existante'}), 409
        
        # Insérer
        c.execute('''
            INSERT INTO licences 
            (cle_licence, type_licence, date_expiration, statut, source)
            VALUES (?, ?, ?, 'disponible', 'easywebshop')
        ''', (cle_licence, type_licence, date_expiration))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Licence enregistrée: {cle_licence}")
        
        return jsonify({
            'success': True,
            'cle_licence': cle_licence,
            'message': 'Licence enregistrée avec succès'
        })
    
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return jsonify({'error': str(e)}), 500
```

### **1.4 Ajouter colonne 'source' dans votre table licences**

Si votre table n'a pas la colonne `source`, ajoutez-la :

```python
# Dans votre fonction init_db() ou dans une console SQLite
c.execute("ALTER TABLE licences ADD COLUMN source TEXT DEFAULT 'manuel'")
```

### **1.5 Sauvegarder et recharger**

1. Cliquez **"Save"**
2. Allez dans l'onglet **"Web"**
3. Cliquez sur **"Reload gbserver.pythonanywhere.com"**

### **1.6 Tester la nouvelle route**

Ouvrez dans votre navigateur :

```
https://gbserver.pythonanywhere.com/api/ping
```

Vous devriez voir :
```json
{"status": "ok", "message": "..."}
```

✅ **Si ça marche, l'API est prête !**

---

## 📋 ÉTAPE 2 : MODIFIER LA BASE DE DONNÉES MYSQL

### **2.1 Ajouter colonnes à service_activations**

Connectez-vous à phpMyAdmin et exécutez :

```sql
ALTER TABLE service_activations 
  ADD COLUMN licence_key VARCHAR(255) UNIQUE DEFAULT NULL AFTER id,
  ADD COLUMN licence_type ENUM('mensuelle','trimestrielle','annuelle','perpetuelle') 
    DEFAULT 'annuelle' AFTER licence_key,
  ADD COLUMN machine_id VARCHAR(255) DEFAULT NULL AFTER status,
  ADD COLUMN activations_count INT DEFAULT 0 AFTER machine_id;
```

### **2.2 Vérifier le produit Gestion Boutique**

```sql
SELECT * FROM products WHERE slug = 'gestion-boutique';
```

Si existe → ✅ Parfait !  
Si n'existe pas → Exécutez l'INSERT du README.

---

## 📋 ÉTAPE 3 : MODIFIER EASYWEBSHOP

### **3.1 Sauvegarder les anciens fichiers**

```bash
cd /chemin/vers/easywebshop
cp webhook.php webhook_old.php
cp success.php success_old.php
```

### **3.2 Remplacer webhook.php**

Remplacez `webhook.php` par le fichier `webhook_GBSERVER.php` que je vous ai fourni.

**Renommez-le en `webhook.php`**

### **3.3 Remplacer success.php**

Remplacez `success.php` par le fichier `success_FINAL.php` que je vous ai fourni.

**Renommez-le en `success.php`**

### **3.4 Ajouter telechargement.php**

Copiez le fichier `telechargement.php` à la racine de easywebshop.

### **3.5 Créer dossier downloads**

```bash
mkdir downloads
```

Et y placer `GestionBoutique_Setup.exe`

---

## 📋 ÉTAPE 4 : TESTER LE SYSTÈME COMPLET

### **Test 1 : L'API répond**

```bash
curl https://gbserver.pythonanywhere.com/api/ping
```

Devrait retourner : `{"status": "ok", ...}`

### **Test 2 : Achat sur easywebshop (sandbox)**

1. Activez mode sandbox dans `.env` :
```
FEDAPAY_ENV=sandbox
```

2. Allez sur votre site
3. Achetez "Gestion Boutique"
4. Utilisez une carte test FedaPay

### **Test 3 : Vérifier les logs**

```bash
tail -f webhook.log
```

Vous devriez voir :
```
[2026-01-25 16:30:12] 💰 Paiement approuvé, traitement licences...
[2026-01-25 16:30:12] 🔑 Gestion Boutique détecté
[2026-01-25 16:30:12] ✅ Service activation créé: GB26-...
[2026-01-25 16:30:13] ✅ Licence enregistrée sur PythonAnywhere
```

### **Test 4 : Vérifier MySQL**

```sql
SELECT * FROM service_activations ORDER BY id DESC LIMIT 1;
```

Vous devriez voir la licence générée.

### **Test 5 : Vérifier PythonAnywhere**

Sur PythonAnywhere, dans la console Python :

```python
import sqlite3
conn = sqlite3.connect('/home/gbserver/gestion_boutique/licences.db')
c = conn.cursor()
c.execute("SELECT * FROM licences ORDER BY id DESC LIMIT 1")
print(c.fetchone())
```

Vous devriez voir la même licence.

### **Test 6 : Activer dans le logiciel**

1. Lancez `GestionBoutique.exe`
2. Entrez la clé reçue par email
3. Cliquez "Activer"

Devrait afficher : **"Activation réussie !"**

---

## 🎬 WORKFLOW FINAL

```
Client achète sur easywebshop.wuaze.com
    ↓
Paie 50,000 FCFA via Orange Money
    ↓
webhook.php génère: GB26-X7Y2-P9Q4-M3N8
    ↓
Enregistre dans MySQL (service_activations)
    ↓
Envoie à gbserver.pythonanywhere.com/api/enregistrer
    ↓
PythonAnywhere enregistre dans SQLite
    ↓
Email envoyé au client avec licence
    ↓
Client télécharge GestionBoutique.exe
    ↓
Client entre GB26-X7Y2-P9Q4-M3N8
    ↓
Logiciel appelle gbserver.pythonanywhere.com/api/activer
    ↓
PythonAnywhere vérifie et active
    ↓
Logiciel débloqué ✅
```

---

## 🔍 ARCHITECTURE COMPLÈTE

```
┌──────────────────────────────────────┐
│   EASYWEBSHOP.WUAZE.COM              │
│   (Site de vente)                    │
│                                      │
│   MySQL:                             │
│   - orders                           │
│   - order_items                      │
│   - service_activations ← LICENCES   │
│   - payments                         │
│                                      │
│   webhook.php:                       │
│   - Génère GB26-XXXX-YYYY-ZZZZ      │
│   - Enregistre dans MySQL            │
│   - Envoie à PythonAnywhere         │
└──────────────┬───────────────────────┘
               │
               ↓ POST /api/enregistrer
               │
┌──────────────────────────────────────┐
│   GBSERVER.PYTHONANYWHERE.COM        │
│   (API de validation)                │
│                                      │
│   SQLite:                            │
│   - licences                         │
│                                      │
│   Routes:                            │
│   - /api/enregistrer (easywebshop)   │
│   - /api/activer (logiciel)          │
└──────────────┬───────────────────────┘
               │
               ↓ POST /api/activer
               │
┌──────────────────────────────────────┐
│   GESTION BOUTIQUE (Client)          │
│   (Logiciel Windows)                 │
│                                      │
│   licence.py:                        │
│   - Demande clé au démarrage         │
│   - Vérifie sur PythonAnywhere       │
│   - Crypte localement                │
└──────────────────────────────────────┘
```

---

## ✅ CHECKLIST FINALE

### PythonAnywhere
- [ ] Route `/api/enregistrer` ajoutée
- [ ] Colonne `source` ajoutée à table licences
- [ ] Web app rechargée
- [ ] `/api/ping` fonctionne

### MySQL (easywebshop)
- [ ] Colonnes ajoutées à `service_activations`
- [ ] Produit "Gestion Boutique" existe

### Fichiers easywebshop
- [ ] `webhook.php` remplacé
- [ ] `success.php` remplacé
- [ ] `telechargement.php` ajouté
- [ ] Dossier `/downloads/` créé
- [ ] `.exe` uploadé

### Tests
- [ ] Achat test sandbox OK
- [ ] Licence dans MySQL
- [ ] Licence sur PythonAnywhere
- [ ] Email reçu
- [ ] Activation logiciel OK

---

## 🚀 LANCEMENT EN PRODUCTION

1. Mode production dans `.env` :
```
FEDAPAY_ENV=live
```

2. Configurer webhook FedaPay :
```
URL: https://easywebshop.wuaze.com/webhook.php
Events: transaction.approved
```

3. Faire un vrai achat test

---

## 💰 REVENUS

```
Prix : 50,000 FCFA
Commission FedaPay : ~1,500 FCFA (3%)
Net : 48,500 FCFA par vente

10 ventes/mois  = 485,000 FCFA
30 ventes/mois  = 1,455,000 FCFA
100 ventes/mois = 4,850,000 FCFA
```

---

## 📞 VOUS ÊTES PRÊT !

**Tout est connecté, suivez juste les étapes !** 🎉

Besoin d'aide ? Je suis là ! 😊
