"""
API Flask pour le système de licences Gestion Boutique
À déployer sur PythonAnywhere
"""
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta
import secrets
import os
from functools import wraps

# Clé secrète — à définir dans les variables d'environnement PythonAnywhere
API_SECRET_KEY = os.environ.get('PA_API_SECRET', 'changeme')
ADMIN_PASSWORD = os.environ.get('PA_ADMIN_PASSWORD', 'admin')

def require_api_key(f):
    """Décorateur : vérifie le header X-API-Key sur les endpoints sensibles"""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if not key or key != API_SECRET_KEY:
            return jsonify({'error': 'Non autorisé'}), 401
        return f(*args, **kwargs)
    return decorated

app = Flask(__name__)
app.secret_key = os.environ.get('PA_FLASK_SECRET', 'flask-secret-changeme')

# Base de données
DB_PATH = '/home/gbserver/boutique_licences.db'
SYNC_DB_PATH = '/home/gbserver/boutique_sync.db'

def init_db():
    """Initialiser la base de données"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS licences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cle_licence TEXT UNIQUE NOT NULL,
            type_licence TEXT NOT NULL,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            date_expiration TIMESTAMP,
            statut TEXT DEFAULT 'active',
            machine_id TEXT DEFAULT NULL,
            date_activation TIMESTAMP DEFAULT NULL,
            nb_activations INTEGER DEFAULT 0,
            source TEXT DEFAULT 'admin',
            plan TEXT DEFAULT 'standard',
            features_extra TEXT DEFAULT ''
        )
    ''')
    # Migrations
    for migration in [
        "ALTER TABLE licences ADD COLUMN source TEXT DEFAULT 'admin'",
        "ALTER TABLE licences ADD COLUMN plan TEXT DEFAULT 'standard'",
        "ALTER TABLE licences ADD COLUMN features_extra TEXT DEFAULT ''",
    ]:
        try:
            c.execute(migration)
            conn.commit()
        except Exception:
            pass
    
    conn.commit()
    conn.close()

# Initialiser au démarrage
init_db()


def get_sync_db():
    conn = sqlite3.connect(SYNC_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_sync_db():
    conn = get_sync_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            licence_key TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            code_barre TEXT NOT NULL,
            nom TEXT,
            categorie TEXT,
            prix_achat REAL DEFAULT 0,
            prix_vente REAL,
            stock_actuel INTEGER DEFAULT 0,
            stock_alerte INTEGER DEFAULT 5,
            type_code_barre TEXT DEFAULT 'code128',
            date_ajout TIMESTAMP,
            description TEXT,
            updated_at TIMESTAMP,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(licence_key, code_barre)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            licence_key TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            numero_vente TEXT NOT NULL,
            date_vente TIMESTAMP,
            total REAL,
            client TEXT,
            statut TEXT DEFAULT 'terminee',
            deleted_at TIMESTAMP,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(licence_key, numero_vente)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_details_ventes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            licence_key TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            numero_vente TEXT NOT NULL,
            produit_code_barre TEXT,
            quantite INTEGER,
            prix_unitaire REAL,
            sous_total REAL,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_historique_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            licence_key TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            produit_code_barre TEXT,
            quantite_avant INTEGER,
            quantite_apres INTEGER,
            operation TEXT,
            date_operation TIMESTAMP,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sync_utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            licence_key TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            nom TEXT,
            prenom TEXT,
            email TEXT NOT NULL,
            mot_de_passe TEXT,
            role TEXT DEFAULT 'caissier',
            actif BOOLEAN DEFAULT 1,
            date_creation TIMESTAMP,
            dernier_login TIMESTAMP,
            updated_at TIMESTAMP,
            synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(licence_key, email)
        )
    ''')
    conn.commit()
    conn.close()


init_sync_db()


def valider_licence(licence_key):
    """Vérifie qu'une licence est active et non expirée"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM licences WHERE cle_licence = ? AND statut = 'active'", (licence_key,))
        row = c.fetchone()
        conn.close()

        if not row:
            return False

        date_exp = row[4]  # date_expiration
        if date_exp:
            try:
                exp = datetime.fromisoformat(date_exp.replace('Z', '').split('+')[0])
            except ValueError:
                return True
            if datetime.now() > exp:
                return False
        return True
    except Exception:
        return False


def require_sync_auth(f):
    """Décorateur : valide X-Licence-Key + X-Machine-Id pour les routes sync"""
    @wraps(f)
    def decorated(*args, **kwargs):
        licence_key = request.headers.get('X-Licence-Key', '')
        machine_id = request.headers.get('X-Machine-Id', '')

        if not licence_key or not machine_id:
            return jsonify({'error': 'Authentification requise'}), 401

        if not valider_licence(licence_key):
            return jsonify({'error': 'Licence invalide ou expirée'}), 403

        return f(licence_key, machine_id, *args, **kwargs)
    return decorated

@app.route('/api/ping', methods=['GET'])
def ping():
    """Vérifier que l'API fonctionne"""
    return jsonify({
        'status': 'ok',
        'message': 'API Gestion Boutique opérationnelle',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/enregistrer-licence', methods=['POST'])
@require_api_key
def enregistrer_licence():
    """
    Enregistrer une nouvelle licence (appelé par easywebshop)
    """
    try:
        data = request.json
        
        cle_licence = data.get('cle_licence')
        type_licence = data.get('type_licence', 'annuelle')
        date_expiration = data.get('date_expiration')
        statut = data.get('statut', 'active')
        
        if not cle_licence:
            return jsonify({'error': 'Clé de licence requise'}), 400
        
        # Enregistrer dans la base
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            INSERT INTO licences (cle_licence, type_licence, date_expiration, statut, source)
            VALUES (?, ?, ?, ?, 'hishamdigital')
        ''', (cle_licence, type_licence, date_expiration, statut))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'cle_licence': cle_licence,
            'message': 'Licence enregistrée avec succès'
        })
    
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Licence déjà existante'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activer', methods=['POST'])
@app.route('/api/verifier', methods=['POST'])
def verifier_licence():
    """
    Activer/Vérifier une licence (appelé par le logiciel client)
    Endpoints: /api/activer (utilisé par Gestion Boutique) et /api/verifier
    """
    try:
        data = request.json
        
        cle = data.get('cle')
        machine_id = data.get('machine_id')
        
        if not cle or not machine_id:
            return jsonify({
                'valide': False,
                'message': 'Clé ou machine_id manquant'
            }), 400
        
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Récupérer la licence
        c.execute('''
            SELECT * FROM licences WHERE cle_licence = ?
        ''', (cle,))
        
        licence = c.fetchone()
        
        if not licence:
            conn.close()
            return jsonify({
                'valide': False,
                'message': 'Licence introuvable'
            })
        
        # Licence trouvée
        row = dict(zip([d[0] for d in c.description], licence)) if hasattr(c, 'description') else {}
        id_lic = licence[0]; cle_lic = licence[1]; type_lic = licence[2]
        date_creation = licence[3]; date_exp = licence[4]; statut = licence[5]
        machine_id_db = licence[6]; date_activ = licence[7]; nb_activ = licence[8]
        plan_lic = licence[10] if len(licence) > 10 else 'standard'
        features_extra_lic = licence[11] if len(licence) > 11 else ''
        
        # Vérifier si expirée
        if date_exp:
            exp_dt = datetime.fromisoformat(date_exp.replace('Z', '').split('+')[0])
            if datetime.now() > exp_dt:
                conn.close()
                return jsonify({
                    'valide': False,
                    'message': 'Licence expirée',
                    'date_expiration': date_exp
                })
        
        # Vérifier statut
        if statut != 'active':
            conn.close()
            return jsonify({
                'valide': False,
                'message': f'Licence {statut}'
            })
        
        # Première activation ?
        if not machine_id_db:
            # Première activation → Enregistrer machine_id
            c.execute('''
                UPDATE licences 
                SET machine_id = ?, 
                    date_activation = ?,
                    nb_activations = 1
                WHERE cle_licence = ?
            ''', (machine_id, datetime.now().isoformat(), cle))
            conn.commit()
            conn.close()
            
            return jsonify({
                'valide': True,
                'succes': True,
                'message': 'Première activation réussie',
                'type': type_lic,
                'type_licence': type_lic,
                'expiration': date_exp,
                'date_expiration': date_exp,
                'plan': plan_lic,
                'features_extra': features_extra_lic or '',
            })
        
        # Activation ultérieure → Vérifier machine_id
        if machine_id_db != machine_id:
            conn.close()
            return jsonify({
                'valide': False,
                'message': 'Cette licence est déjà activée sur un autre ordinateur'
            })
        
        # Tout est OK
        c.execute('''
            UPDATE licences 
            SET nb_activations = nb_activations + 1
            WHERE cle_licence = ?
        ''', (cle,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'valide': True,
            'succes': True,
            'message': 'Licence valide',
            'type': type_lic,
            'type_licence': type_lic,
            'expiration': date_exp,
            'date_expiration': date_exp,
            'plan': plan_lic,
            'features_extra': features_extra_lic or '',
        })
    
    except Exception as e:
        return jsonify({
            'valide': False,
            'message': f'Erreur serveur: {str(e)}'
        }), 500

@app.route('/api/stats', methods=['GET'])
def statistiques():
    """
    Statistiques des licences (pour admin)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Total licences
        c.execute("SELECT COUNT(*) FROM licences")
        total = c.fetchone()[0]
        
        # Licences actives
        c.execute("SELECT COUNT(*) FROM licences WHERE statut = 'active'")
        actives = c.fetchone()[0]
        
        # Licences expirées
        c.execute("""
            SELECT COUNT(*) FROM licences 
            WHERE date_expiration < datetime('now') AND date_expiration IS NOT NULL
        """)
        expirees = c.fetchone()[0]
        
        # Licences par type
        c.execute("SELECT type_licence, COUNT(*) FROM licences GROUP BY type_licence")
        par_type = dict(c.fetchall())
        
        conn.close()
        
        return jsonify({
            'total_licences': total,
            'licences_actives': actives,
            'licences_expirees': expirees,
            'par_type': par_type
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sync/ping', methods=['GET'])
def sync_ping():
    return jsonify({'status': 'ok', 'service': 'sync', 'timestamp': datetime.now().isoformat()})


@app.route('/api/sync/push', methods=['POST'])
@require_sync_auth
def sync_push(licence_key, machine_id):
    """Recevoir les changements d'un client"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Aucune donnée'}), 400

        conn = get_sync_db()
        now = datetime.now().isoformat()

        for p in data.get('produits', []):
            conn.execute('''
                INSERT INTO sync_produits
                    (licence_key, machine_id, code_barre, nom, categorie, prix_achat,
                     prix_vente, stock_actuel, stock_alerte, type_code_barre,
                     date_ajout, description, updated_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(licence_key, code_barre) DO UPDATE SET
                    machine_id=excluded.machine_id, nom=excluded.nom,
                    categorie=excluded.categorie, prix_achat=excluded.prix_achat,
                    prix_vente=excluded.prix_vente, stock_actuel=excluded.stock_actuel,
                    stock_alerte=excluded.stock_alerte, type_code_barre=excluded.type_code_barre,
                    description=excluded.description, updated_at=excluded.updated_at,
                    synced_at=excluded.synced_at
            ''', (
                licence_key, machine_id, p['code_barre'], p['nom'],
                p.get('categorie'), p.get('prix_achat', 0), p['prix_vente'],
                p.get('stock_actuel', 0), p.get('stock_alerte', 5),
                p.get('type_code_barre', 'code128'), p.get('date_ajout'),
                p.get('description'), p.get('updated_at', now), now
            ))

        for v in data.get('ventes', []):
            conn.execute('''
                INSERT OR IGNORE INTO sync_ventes
                    (licence_key, machine_id, numero_vente, date_vente, total,
                     client, statut, deleted_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                licence_key, machine_id, v['numero_vente'], v['date_vente'],
                v['total'], v.get('client'), v.get('statut', 'terminee'),
                v.get('deleted_at'), now
            ))

        for d in data.get('details_ventes', []):
            numero_vente = d.get('numero_vente', '')
            if not numero_vente:
                for v in data.get('ventes', []):
                    if v.get('id') == d.get('vente_id'):
                        numero_vente = v['numero_vente']
                        break
            conn.execute('''
                INSERT INTO sync_details_ventes
                    (licence_key, machine_id, numero_vente, produit_code_barre,
                     quantite, prix_unitaire, sous_total, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                licence_key, machine_id, numero_vente,
                d.get('produit_code_barre', ''), d['quantite'],
                d['prix_unitaire'], d['sous_total'], now
            ))

        for h in data.get('historique_stock', []):
            conn.execute('''
                INSERT INTO sync_historique_stock
                    (licence_key, machine_id, produit_code_barre, quantite_avant,
                     quantite_apres, operation, date_operation, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                licence_key, machine_id, h.get('produit_code_barre', ''),
                h.get('quantite_avant'), h.get('quantite_apres'),
                h.get('operation'), h.get('date_operation'), now
            ))

        for u in data.get('utilisateurs', []):
            conn.execute('''
                INSERT INTO sync_utilisateurs
                    (licence_key, machine_id, nom, prenom, email, mot_de_passe,
                     role, actif, date_creation, dernier_login, updated_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(licence_key, email) DO UPDATE SET
                    machine_id=excluded.machine_id, nom=excluded.nom,
                    prenom=excluded.prenom, mot_de_passe=excluded.mot_de_passe,
                    role=excluded.role, actif=excluded.actif,
                    dernier_login=excluded.dernier_login, updated_at=excluded.updated_at,
                    synced_at=excluded.synced_at
            ''', (
                licence_key, machine_id, u['nom'], u['prenom'],
                u['email'], u['mot_de_passe'], u.get('role', 'caissier'),
                u.get('actif', 1), u.get('date_creation'),
                u.get('dernier_login'), u.get('updated_at', now), now
            ))

        conn.commit()
        conn.close()
        return jsonify({'status': 'ok', 'message': 'Push reçu'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sync/pull', methods=['POST'])
@require_sync_auth
def sync_pull(licence_key, machine_id):
    """Renvoyer les changements depuis un timestamp, en excluant le même machine_id"""
    try:
        data = request.json or {}
        depuis = data.get('depuis', '2000-01-01T00:00:00')

        conn = get_sync_db()

        produits = conn.execute('''
            SELECT code_barre, nom, categorie, prix_achat, prix_vente,
                   stock_actuel, stock_alerte, type_code_barre, date_ajout,
                   description, updated_at
            FROM sync_produits
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        ventes = conn.execute('''
            SELECT numero_vente, date_vente, total, client, statut, deleted_at
            FROM sync_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        details = conn.execute('''
            SELECT numero_vente, produit_code_barre, quantite, prix_unitaire, sous_total
            FROM sync_details_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        historique = conn.execute('''
            SELECT produit_code_barre, quantite_avant, quantite_apres, operation, date_operation
            FROM sync_historique_stock
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        utilisateurs = conn.execute('''
            SELECT nom, prenom, email, mot_de_passe, role, actif,
                   date_creation, dernier_login, updated_at
            FROM sync_utilisateurs
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        conn.close()

        return jsonify({
            'produits': [dict(r) for r in produits],
            'ventes': [dict(r) for r in ventes],
            'details_ventes': [dict(r) for r in details],
            'historique_stock': [dict(r) for r in historique],
            'utilisateurs': [dict(r) for r in utilisateurs],
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Admin — Gestion Boutique Licences</title>
<style>
  body { font-family: sans-serif; max-width: 1100px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
  h1 { color: #333; }
  .card { background: #fff; border-radius: 8px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 4px rgba(0,0,0,.1); }
  label { display: block; margin-bottom: 4px; font-weight: bold; font-size: .9em; }
  input, select { width: 100%; padding: 8px; margin-bottom: 14px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
  button { background: #2563eb; color: #fff; border: none; padding: 10px 22px; border-radius: 4px; cursor: pointer; font-size: 1em; }
  button:hover { background: #1d4ed8; }
  .alert { padding: 12px 16px; border-radius: 4px; margin-bottom: 16px; }
  .alert-success { background: #d1fae5; color: #065f46; }
  .alert-error   { background: #fee2e2; color: #991b1b; }
  .cle { font-family: monospace; font-size: 1.2em; background: #f0fdf4; border: 1px solid #86efac; padding: 10px 14px; border-radius: 4px; letter-spacing: 2px; }
  table { width: 100%; border-collapse: collapse; font-size: .85em; }
  th, td { text-align: left; padding: 9px 10px; border-bottom: 1px solid #e5e7eb; vertical-align: top; }
  th { background: #f9fafb; font-size: .8em; text-transform: uppercase; color: #6b7280; }
  tr:hover td { background: #fafafa; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: .8em; font-weight: 600; }
  .badge-active    { background: #d1fae5; color: #065f46; }
  .badge-inactive  { background: #fee2e2; color: #991b1b; }
  .badge-dispo     { background: #dbeafe; color: #1e40af; }
  .badge-en-cours  { background: #fef9c3; color: #854d0e; }
  .badge-expire    { background: #f3f4f6; color: #6b7280; }
  .machine { font-size: .78em; color: #6b7280; font-family: monospace; word-break: break-all; max-width: 160px; }
  .logout { float: right; font-size: .85em; color: #6b7280; text-decoration: none; }
  .logout:hover { color: #111; }
  .stats { display: flex; gap: 16px; margin-bottom: 8px; flex-wrap: wrap; }
  .stat { flex: 1; min-width: 120px; background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 14px 18px; text-align: center; }
  .stat .val { font-size: 1.8em; font-weight: bold; color: #111; }
  .stat .lbl { font-size: .8em; color: #6b7280; margin-top: 2px; }
  .form-row { display: flex; gap: 16px; }
  .form-row > div { flex: 1; }
</style>
</head>
<body>
<h1>🔑 Gestion des Licences <a class="logout" href="/admin/logout">Se déconnecter</a></h1>

{% if message %}
<div class="alert alert-success">{{ message }}</div>
{% endif %}
{% if erreur %}
<div class="alert alert-error">{{ erreur }}</div>
{% endif %}

{% if nouvelle_cle %}
<div class="card">
  <strong>Nouvelle clé générée :</strong><br><br>
  <span class="cle">{{ nouvelle_cle }}</span>
</div>
{% endif %}

<div class="card">
  <div class="stats">
    <div class="stat"><div class="val">{{ stats.total }}</div><div class="lbl">Total</div></div>
    <div class="stat"><div class="val" style="color:#065f46">{{ stats.disponibles }}</div><div class="lbl">Disponibles</div></div>
    <div class="stat"><div class="val" style="color:#854d0e">{{ stats.en_cours }}</div><div class="lbl">En cours d'utilisation</div></div>
    <div class="stat"><div class="val" style="color:#6b7280">{{ stats.expirees }}</div><div class="lbl">Expirées</div></div>
    <div class="stat"><div class="val" style="color:#991b1b">{{ stats.inactives }}</div><div class="lbl">Désactivées</div></div>
  </div>
</div>

<div class="card">
  <h2 style="margin-top:0">Générer une licence</h2>
  <form method="post">
    <div class="form-row">
      <div>
        <label>Type de licence</label>
        <select name="type_licence">
          <option value="annuelle">Annuelle (1 an)</option>
          <option value="trimestrielle">Trimestrielle (90 jours)</option>
          <option value="mensuelle">Mensuelle (30 jours)</option>
          <option value="perpetuelle">Perpétuelle (sans expiration)</option>
        </select>
      </div>
      <div>
        <label>Plan</label>
        <select name="plan">
          <option value="standard">Standard</option>
          <option value="pro">Pro</option>
          <option value="white_label">White Label</option>
        </select>
      </div>
      <div>
        <label>Statut initial</label>
        <select name="statut">
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
    </div>
    <button type="submit">Générer</button>
  </form>
</div>

<div class="card">
  <h2 style="margin-top:0">Toutes les licences ({{ licences|length }})</h2>
  <table>
    <tr>
      <th>Clé de licence</th>
      <th>Type</th>
      <th>Plan</th>
      <th>Source</th>
      <th>État</th>
      <th>Générée le</th>
      <th>Expiration</th>
      <th>Première activation</th>
      <th>Machine (ID)</th>
      <th>Nb. utilisations</th>
    </tr>
    {% for l in licences %}
    {% set expire = l.date_expiration and l.date_expiration < now %}
    {% set en_cours = l.machine_id and not expire and l.statut == 'active' %}
    {% set dispo = not l.machine_id and l.statut == 'active' and not expire %}
    <tr>
      <td style="font-family:monospace;font-size:.88em;white-space:nowrap">{{ l.cle_licence }}</td>
      <td>{{ l.type_licence }}</td>
      <td>
        {% if l.plan == 'pro' %}
          <span class="badge badge-en-cours">Pro</span>
        {% elif l.plan == 'white_label' %}
          <span class="badge badge-active">White Label</span>
        {% else %}
          <span class="badge badge-dispo">Standard</span>
        {% endif %}
      </td>
      <td>
        {% if l.source == 'hishamdigital' %}
          <span class="badge badge-active">hishamdigital</span>
        {% else %}
          <span class="badge badge-dispo">admin</span>
        {% endif %}
      </td>
      <td>
        {% if l.statut != 'active' %}
          <span class="badge badge-inactive">désactivée</span>
        {% elif expire %}
          <span class="badge badge-expire">expirée</span>
        {% elif dispo %}
          <span class="badge badge-dispo">disponible</span>
        {% else %}
          <span class="badge badge-en-cours">en cours d'utilisation</span>
        {% endif %}
      </td>
      <td style="white-space:nowrap;color:#6b7280">{{ l.date_creation[:16].replace('T',' ') if l.date_creation else '—' }}</td>
      <td style="white-space:nowrap">{{ l.date_expiration[:10] if l.date_expiration else '∞' }}</td>
      <td style="white-space:nowrap;color:#6b7280">{{ l.date_activation[:16].replace('T',' ') if l.date_activation else '—' }}</td>
      <td class="machine">{{ l.machine_id or '—' }}</td>
      <td style="text-align:center">{{ l.nb_activations }}</td>
    </tr>
    {% endfor %}
  </table>
</div>
</body>
</html>
"""

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>Admin — Connexion</title>
<style>
  body { font-family: sans-serif; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; background: #f5f5f5; }
  .box { background: #fff; padding: 36px 40px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,.12); width: 320px; }
  h2 { margin-top: 0; color: #333; }
  label { display: block; margin-bottom: 4px; font-weight: bold; font-size: .9em; }
  input { width: 100%; padding: 8px; margin-bottom: 14px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
  button { width: 100%; background: #2563eb; color: #fff; border: none; padding: 10px; border-radius: 4px; cursor: pointer; font-size: 1em; }
  .err { color: #dc2626; font-size: .9em; margin-bottom: 10px; }
</style>
</head>
<body>
<div class="box">
  <h2>🔒 Administration</h2>
  {% if erreur %}<p class="err">{{ erreur }}</p>{% endif %}
  <form method="post">
    <label>Mot de passe</label>
    <input type="password" name="password" autofocus>
    <button type="submit">Connexion</button>
  </form>
</div>
</body>
</html>
"""


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated


def generer_cle_licence(prefix='GB26'):
    """Génère une clé au format PREFIX-XXXX-XXXX-XXXX (alphanumériques majuscules)"""
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    parts = [''.join(secrets.choice(alphabet) for _ in range(4)) for _ in range(3)]
    return prefix + '-' + '-'.join(parts)


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    erreur = None
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin/generer')
        erreur = 'Mot de passe incorrect.'
    return render_template_string(LOGIN_TEMPLATE, erreur=erreur)


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')


@app.route('/admin/generer', methods=['GET', 'POST'])
@admin_required
def admin_generer():
    message = None
    erreur = None
    nouvelle_cle = None

    if request.method == 'POST':
        try:
            type_licence = request.form.get('type_licence', 'annuelle')
            statut = request.form.get('statut', 'active')
            plan = request.form.get('plan', 'standard')
            if plan not in ('standard', 'pro', 'white_label'):
                plan = 'standard'

            if type_licence == 'annuelle':
                date_exp = (datetime.now() + timedelta(days=365)).isoformat()
            elif type_licence == 'trimestrielle':
                date_exp = (datetime.now() + timedelta(days=90)).isoformat()
            elif type_licence == 'mensuelle':
                date_exp = (datetime.now() + timedelta(days=30)).isoformat()
            else:
                date_exp = None  # perpetuelle

            nouvelle_cle = generer_cle_licence()

            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                'INSERT INTO licences (cle_licence, type_licence, date_expiration, statut, source, plan) VALUES (?, ?, ?, ?, ?, ?)',
                (nouvelle_cle, type_licence, date_exp, statut, 'admin', plan)
            )
            conn.commit()
            conn.close()
            message = f'Licence {plan.upper()} créée avec succès.'
        except Exception as e:
            erreur = str(e)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    licences = conn.execute('SELECT * FROM licences ORDER BY date_creation DESC').fetchall()
    conn.close()

    now_iso = datetime.now().isoformat()
    stats = {
        'total': len(licences),
        'disponibles': sum(1 for l in licences if not l['machine_id'] and l['statut'] == 'active' and (not l['date_expiration'] or l['date_expiration'] > now_iso)),
        'en_cours': sum(1 for l in licences if l['machine_id'] and l['statut'] == 'active' and (not l['date_expiration'] or l['date_expiration'] > now_iso)),
        'expirees': sum(1 for l in licences if l['date_expiration'] and l['date_expiration'] < now_iso),
        'inactives': sum(1 for l in licences if l['statut'] != 'active'),
    }

    return render_template_string(
        ADMIN_TEMPLATE,
        licences=licences,
        message=message,
        erreur=erreur,
        nouvelle_cle=nouvelle_cle,
        stats=stats,
        now=now_iso,
    )


if __name__ == '__main__':
    # Mode développement
    app.run(debug=True, host='0.0.0.0', port=5000)
