"""
API Flask pour Gestion Boutique
- Licences : activation, generation, admin panel
- Synchronisation : push/pull cloud entre postes
"""
import os
import sqlite3
import hashlib
import random
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'licences.db')
SYNC_DB_PATH = os.path.join(BASE_DIR, 'sync_data.db')


# ============================================================
#                    BASE DE DONNEES LICENCES
# ============================================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialisation de la base licences"""
    try:
        conn = get_db()
        conn.execute('''
            CREATE TABLE IF NOT EXISTS licences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cle_licence TEXT UNIQUE NOT NULL,
                type_licence TEXT NOT NULL,
                client_nom TEXT DEFAULT 'Client Web',
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_expiration TIMESTAMP,
                statut TEXT DEFAULT 'disponible',
                machine_id TEXT DEFAULT NULL,
                date_activation TIMESTAMP DEFAULT NULL,
                nb_activations INTEGER DEFAULT 0,
                source TEXT DEFAULT 'manuel'
            )
        ''')
        conn.commit()
        conn.close()
        print("[OK] Base licences initialisee")
    except Exception as e:
        print(f"[ERREUR] Init DB licences: {e}")

init_db()


# ============================================================
#                    BASE DE DONNEES SYNC
# ============================================================

def get_sync_db():
    conn = sqlite3.connect(SYNC_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_sync_db():
    """Creer les tables miroir pour la synchronisation"""
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
    print("[OK] Base sync initialisee")

init_sync_db()


# ============================================================
#                    OUTILS COMMUNS
# ============================================================

def generer_cle_string(type_licence='A'):
    annee = datetime.now().strftime("%y")
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=4))
    raw = f"GB{annee}{type_licence}{part1}{part2}"
    checksum = hashlib.md5(raw.encode()).hexdigest()[:4].upper()
    return f"GB{annee}-{type_licence}{part1}-{part2}-{checksum}"


def valider_licence(licence_key):
    """Verifie qu'une licence est active et non expiree"""
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT * FROM licences WHERE cle_licence = ? AND statut = 'active'",
            (licence_key,)
        ).fetchone()
        conn.close()

        if not row:
            return False

        if row['date_expiration']:
            try:
                exp = datetime.strptime(row['date_expiration'], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    exp = datetime.strptime(row['date_expiration'], '%Y-%m-%d')
                except ValueError:
                    return True
            if datetime.now() > exp:
                return False
        return True
    except Exception:
        return False


def require_sync_auth(f):
    """Decorateur pour valider l'authentification des requetes sync"""
    @wraps(f)
    def decorated(*args, **kwargs):
        licence_key = request.headers.get('X-Licence-Key', '')
        machine_id = request.headers.get('X-Machine-Id', '')

        if not licence_key or not machine_id:
            return jsonify({'error': 'Authentification requise'}), 401

        if not valider_licence(licence_key):
            return jsonify({'error': 'Licence invalide ou expiree'}), 403

        return f(licence_key, machine_id, *args, **kwargs)
    return decorated


# ============================================================
#                    ROUTES LICENCES
# ============================================================

@app.route('/')
def home():
    return """
    <div style="font-family:sans-serif; text-align:center; margin-top:50px;">
        <h1 style="color:#27ae60;">Serveur Gestion Boutique</h1>
        <p>Licences + Synchronisation</p>
        <p><a href="/admin/generer" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Panel Admin</a></p>
    </div>
    """

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'API en ligne'})

@app.route('/api/enregistrer', methods=['POST'])
def enregistrer_licence():
    """Pour EasyWebShop"""
    try:
        data = request.json
        cle = data.get('cle_licence')
        type_l = data.get('type_licence', 'annuelle')
        date_exp = data.get('date_expiration')

        if not cle:
            return jsonify({'error': 'Cle requise'}), 400

        conn = get_db()
        if conn.execute('SELECT 1 FROM licences WHERE cle_licence = ?', (cle,)).fetchone():
            conn.close()
            return jsonify({'error': 'Existe deja'}), 409

        conn.execute('''
            INSERT INTO licences (cle_licence, type_licence, date_expiration, source, statut, client_nom)
            VALUES (?, ?, ?, 'easywebshop', 'disponible', 'Client EasyWebShop')
        ''', (cle, type_l, date_exp))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/activer', methods=['POST'])
def activer_licence():
    """Pour le Logiciel Client"""
    try:
        data = request.json
        cle = data.get('cle', '').strip()
        machine = data.get('machine_id')

        conn = get_db()
        row = conn.execute('SELECT * FROM licences WHERE cle_licence = ?', (cle,)).fetchone()

        if not row:
            conn.close()
            return jsonify({'succes': False, 'message': 'Licence introuvable'})

        # Verification Date
        if row['date_expiration']:
            exp_str = row['date_expiration']
            try:
                exp = datetime.strptime(exp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    exp = datetime.strptime(exp_str, '%Y-%m-%d')
                except ValueError:
                    exp = datetime.now() + timedelta(days=365)

            if datetime.now() > exp:
                conn.close()
                return jsonify({'succes': False, 'message': 'Licence expiree'})

        # Logique Activation
        statut = row['statut']
        mach_db = row['machine_id']

        if statut == 'disponible' or (statut == 'active' and mach_db == machine):
            if not mach_db:
                conn.execute('''
                    UPDATE licences SET machine_id=?, statut='active', date_activation=?, nb_activations=1
                    WHERE id=?
                ''', (machine, datetime.now(), row['id']))
                conn.commit()

            conn.close()
            return jsonify({
                'succes': True,
                'expiration': row['date_expiration'],
                'type': row['type_licence'],
                'message': 'Activation validee'
            })
        else:
            conn.close()
            return jsonify({'succes': False, 'message': 'Deja active sur une autre machine'})

    except Exception as e:
        return jsonify({'succes': False, 'message': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM licences").fetchone()[0]
    actives = conn.execute("SELECT COUNT(*) FROM licences WHERE statut='active'").fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'actives': actives})


# ============================================================
#                    ROUTES SYNCHRONISATION
# ============================================================

@app.route('/api/sync/ping', methods=['GET'])
def sync_ping():
    """Health check sync"""
    return jsonify({
        'status': 'ok',
        'service': 'sync',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/sync/push', methods=['POST'])
@require_sync_auth
def sync_push(licence_key, machine_id):
    """Recevoir les changements d'un client"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Aucune donnee'}), 400

        conn = get_sync_db()
        now = datetime.now().isoformat()

        # Produits
        for p in data.get('produits', []):
            conn.execute('''
                INSERT INTO sync_produits
                    (licence_key, machine_id, code_barre, nom, categorie, prix_achat,
                     prix_vente, stock_actuel, stock_alerte, type_code_barre,
                     date_ajout, description, updated_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(licence_key, code_barre) DO UPDATE SET
                    machine_id=excluded.machine_id,
                    nom=excluded.nom, categorie=excluded.categorie,
                    prix_achat=excluded.prix_achat, prix_vente=excluded.prix_vente,
                    stock_actuel=excluded.stock_actuel, stock_alerte=excluded.stock_alerte,
                    type_code_barre=excluded.type_code_barre,
                    description=excluded.description,
                    updated_at=excluded.updated_at, synced_at=excluded.synced_at
            ''', (
                licence_key, machine_id, p['code_barre'], p['nom'],
                p.get('categorie'), p.get('prix_achat', 0), p['prix_vente'],
                p.get('stock_actuel', 0), p.get('stock_alerte', 5),
                p.get('type_code_barre', 'code128'), p.get('date_ajout'),
                p.get('description'), p.get('updated_at', now), now
            ))

        # Ventes
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

        # Details ventes
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
                d.get('produit_code_barre', ''),
                d['quantite'], d['prix_unitaire'], d['sous_total'], now
            ))

        # Historique stock
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

        # Utilisateurs
        for u in data.get('utilisateurs', []):
            conn.execute('''
                INSERT INTO sync_utilisateurs
                    (licence_key, machine_id, nom, prenom, email, mot_de_passe,
                     role, actif, date_creation, dernier_login, updated_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(licence_key, email) DO UPDATE SET
                    machine_id=excluded.machine_id,
                    nom=excluded.nom, prenom=excluded.prenom,
                    mot_de_passe=excluded.mot_de_passe, role=excluded.role,
                    actif=excluded.actif, dernier_login=excluded.dernier_login,
                    updated_at=excluded.updated_at, synced_at=excluded.synced_at
            ''', (
                licence_key, machine_id, u['nom'], u['prenom'],
                u['email'], u['mot_de_passe'], u.get('role', 'caissier'),
                u.get('actif', 1), u.get('date_creation'),
                u.get('dernier_login'), u.get('updated_at', now), now
            ))

        conn.commit()
        conn.close()

        return jsonify({'status': 'ok', 'message': 'Push recu'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sync/pull', methods=['POST'])
@require_sync_auth
def sync_pull(licence_key, machine_id):
    """Renvoyer les changements depuis un timestamp, excluant le meme machine_id"""
    try:
        data = request.json or {}
        depuis = data.get('depuis', '2000-01-01T00:00:00')

        conn = get_sync_db()

        # Produits
        produits = conn.execute('''
            SELECT code_barre, nom, categorie, prix_achat, prix_vente,
                   stock_actuel, stock_alerte, type_code_barre, date_ajout,
                   description, updated_at
            FROM sync_produits
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_produits = [dict(p) for p in produits]

        # Ventes
        ventes = conn.execute('''
            SELECT numero_vente, date_vente, total, client, statut, deleted_at
            FROM sync_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_ventes = [dict(v) for v in ventes]

        # Details ventes
        details = conn.execute('''
            SELECT numero_vente, produit_code_barre, quantite, prix_unitaire, sous_total
            FROM sync_details_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_details = [dict(d) for d in details]

        # Historique stock
        historique = conn.execute('''
            SELECT produit_code_barre, quantite_avant, quantite_apres, operation, date_operation
            FROM sync_historique_stock
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_historique = [dict(h) for h in historique]

        # Utilisateurs
        utilisateurs = conn.execute('''
            SELECT nom, prenom, email, mot_de_passe, role, actif,
                   date_creation, dernier_login, updated_at
            FROM sync_utilisateurs
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_utilisateurs = [dict(u) for u in utilisateurs]

        conn.close()

        return jsonify({
            'produits': result_produits,
            'ventes': result_ventes,
            'details_ventes': result_details,
            'historique_stock': result_historique,
            'utilisateurs': result_utilisateurs,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
#                    ADMIN PANEL
# ============================================================

@app.route('/admin/generer', methods=['GET', 'POST'])
def admin_panel():
    conn = get_db()

    message = request.args.get('message', '')
    nouvelle_cle = request.args.get('nouvelle_cle', '')

    if request.method == 'POST':
        client = request.form.get('client')
        type_code = request.form.get('type')

        cle_str = generer_cle_string(type_code)

        now = datetime.now()
        if type_code == 'M':
            exp = now + timedelta(days=31)
        elif type_code == 'A':
            exp = now + timedelta(days=366)
        else:
            exp = now + timedelta(days=36500)

        type_full = {'M': 'mensuel', 'A': 'annuel', 'P': 'perpetuel'}.get(type_code)

        try:
            conn.execute('''
                INSERT INTO licences (cle_licence, client_nom, type_licence, date_expiration, source, statut)
                VALUES (?, ?, ?, ?, 'manuel', 'disponible')
            ''', (cle_str, client, type_full, exp))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_panel', message="Cle generee !", nouvelle_cle=cle_str))

        except Exception as e:
            message = f"Erreur: {e}"

    licences = conn.execute('SELECT * FROM licences ORDER BY id DESC LIMIT 50').fetchall()

    # Stats sync
    try:
        sconn = get_sync_db()
        sync_produits = sconn.execute("SELECT COUNT(*) FROM sync_produits").fetchone()[0]
        sync_ventes = sconn.execute("SELECT COUNT(*) FROM sync_ventes").fetchone()[0]
        sconn.close()
    except Exception:
        sync_produits = 0
        sync_ventes = 0

    conn.close()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin - Gestion Boutique</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, sans-serif; background: #f4f6f8; padding: 20px; max-width: 800px; margin: auto; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); margin-bottom: 20px; }
            input, select, button { padding: 10px; width: 100%; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px; box-sizing:border-box;}
            button { background: #3498db; color: white; border: none; cursor: pointer; font-weight: bold;}
            .key-box { background: #e8f8f5; color: #27ae60; padding: 15px; text-align: center; font-family: monospace; font-size: 1.2em; border: 2px dashed #27ae60; border-radius: 5px; margin-bottom: 10px;}
            table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
            th, td { text-align: left; padding: 10px; border-bottom: 1px solid #eee; }
            .badge { padding: 3px 8px; border-radius: 10px; font-size: 0.8em; }
            .active { background: #d4edda; color: #155724; }
            .dispo { background: #cce5ff; color: #004085; }
            .stats { display: flex; gap: 15px; margin-bottom: 15px; }
            .stat-box { flex:1; background: #f0f4ff; padding: 12px; border-radius: 8px; text-align: center; }
            .stat-box strong { display: block; font-size: 1.3em; color: #2c3e50; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Generateur Manuel</h2>
            {% if nouvelle_cle %}
                <div class="key-box">{{ nouvelle_cle }}</div>
                <div style="text-align:center; color:green; font-weight:bold;">{{ message }}</div>
                <div style="text-align:center; margin-top:10px;">
                    <a href="/admin/generer" style="color:#7f8c8d; text-decoration:none; font-size:0.9em;">Effacer</a>
                </div>
            {% endif %}
            <form method="POST">
                <input type="text" name="client" placeholder="Nom du Client" required>
                <select name="type">
                    <option value="A">Annuel (1 an)</option>
                    <option value="M">Mensuel (1 mois)</option>
                    <option value="P">Perpetuel (A vie)</option>
                </select>
                <button type="submit">Generer Cle</button>
            </form>
        </div>
        <div class="card">
            <h3>Synchronisation Cloud</h3>
            <div class="stats">
                <div class="stat-box"><strong>{{ sync_produits }}</strong>Produits synces</div>
                <div class="stat-box"><strong>{{ sync_ventes }}</strong>Ventes syncees</div>
            </div>
        </div>
        <div class="card">
            <h3>Liste des Licences</h3>
            <table>
                <tr><th>Cle</th><th>Client</th><th>Statut</th><th>Exp</th></tr>
                {% for lic in licences %}
                <tr>
                    <td style="font-family:monospace">{{ lic.cle_licence }}</td>
                    <td>{{ lic.client_nom }}<br><small style="color:gray">{{ lic.source }}</small></td>
                    <td><span class="badge {% if lic.statut=='active' %}active{% else %}dispo{% endif %}">{{ lic.statut }}</span></td>
                    <td>{{ lic.date_expiration }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, message=message, nouvelle_cle=nouvelle_cle,
                                 licences=licences, sync_produits=sync_produits, sync_ventes=sync_ventes)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
