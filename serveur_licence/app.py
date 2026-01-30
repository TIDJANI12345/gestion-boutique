"""
API Flask pour Gestion Boutique - Version ULTIME
- Moteur : SQLite Natif (Stable)
- Interface : Admin Panel inclu
"""
import os
import sqlite3
import hashlib
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template_string, redirect, url_for

app = Flask(__name__)

# --- CONFIGURATION AUTOMATIQUE ---
# Trouve le dossier automatiquement (plus sûr que le chemin en dur)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'licences.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Permet d'utiliser les noms de colonnes
    return conn

def init_db():
    """Initialisation de la base de données"""
    try:
        conn = get_db()
        # On ajoute 'client_nom' qui manquait dans ta version précédente
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
        print("✅ Base de données initialisée")
    except Exception as e:
        print(f"❌ Erreur Init DB: {e}")

# Lancer l'init au démarrage
init_db()

# --- OUTILS GÉNÉRATION ---
def generer_cle_string(type_licence='A'):
    annee = datetime.now().strftime("%y") 
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    part1 = ''.join(random.choices(chars, k=4))
    part2 = ''.join(random.choices(chars, k=4))
    raw = f"GB{annee}{type_licence}{part1}{part2}"
    checksum = hashlib.md5(raw.encode()).hexdigest()[:4].upper()
    return f"GB{annee}-{type_licence}{part1}-{part2}-{checksum}"

# --- ROUTES API ---

@app.route('/')
def home():
    return f"""
    <div style="font-family:sans-serif; text-align:center; margin-top:50px;">
        <h1 style="color:#27ae60;">Serveur Licences V3 (Stable) 🟢</h1>
        <p><a href="/admin/generer" style="background:#2c3e50; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Accéder au Panel Admin</a></p>
    </div>
    """

@app.route('/api/ping', methods=['GET'])
def ping():
    return jsonify({'status': 'ok', 'message': 'API en ligne 🚀'})

@app.route('/api/enregistrer', methods=['POST'])
def enregistrer_licence():
    """Pour EasyWebShop"""
    try:
        data = request.json
        cle = data.get('cle_licence')
        type_l = data.get('type_licence', 'annuelle')
        date_exp = data.get('date_expiration')
        
        if not cle: return jsonify({'error': 'Clé requise'}), 400
        
        conn = get_db()
        # Vérif doublon
        if conn.execute('SELECT 1 FROM licences WHERE cle_licence = ?', (cle,)).fetchone():
            conn.close()
            return jsonify({'error': 'Existe déjà'}), 409
            
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
            
        # Vérification Date
        if row['date_expiration']:
            exp_str = row['date_expiration']
            # Petit hack pour gérer différents formats de date
            try: exp = datetime.strptime(exp_str, '%Y-%m-%d %H:%M:%S')
            except: 
                try: exp = datetime.strptime(exp_str, '%Y-%m-%d')
                except: exp = datetime.now() + timedelta(days=365) # Fallback
            
            if datetime.now() > exp:
                conn.close()
                return jsonify({'succes': False, 'message': 'Licence expirée'})

        # Logique Activation
        statut = row['statut']
        mach_db = row['machine_id']
        
        if statut == 'disponible' or (statut == 'active' and mach_db == machine):
            if not mach_db: # Première activation
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
                'message': 'Activation validée'
            })
        else:
            conn.close()
            return jsonify({'succes': False, 'message': 'Déjà active sur une autre machine'})

    except Exception as e:
        return jsonify({'succes': False, 'message': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM licences").fetchone()[0]
    actives = conn.execute("SELECT COUNT(*) FROM licences WHERE statut='active'").fetchone()[0]
    conn.close()
    return jsonify({'total': total, 'actives': actives})

# --- ROUTE ADMIN (AJOUTÉE ICI) ---

@app.route('/admin/generer', methods=['GET', 'POST'])
def admin_panel():
    conn = get_db()
    
    # 1. On récupère les infos depuis l'URL (C'est ça qui empêche le bug au refresh)
    message = request.args.get('message', '')
    nouvelle_cle = request.args.get('nouvelle_cle', '')
    
    if request.method == 'POST':
        client = request.form.get('client')
        type_code = request.form.get('type') # A, M, P
        
        cle_str = generer_cle_string(type_code)
        
        # Calcul date
        now = datetime.now()
        if type_code == 'M': exp = now + timedelta(days=31)
        elif type_code == 'A': exp = now + timedelta(days=366)
        else: exp = now + timedelta(days=36500)
        
        type_full = {'M':'mensuel', 'A':'annuel', 'P':'perpetuel'}.get(type_code)
        
        try:
            conn.execute('''
                INSERT INTO licences (cle_licence, client_nom, type_licence, date_expiration, source, statut)
                VALUES (?, ?, ?, ?, 'manuel', 'disponible')
            ''', (cle_str, client, type_full, exp))
            conn.commit()
            
            # --- LA CORRECTION EST ICI ---
            # Au lieu d'afficher la page, on redirige vers l'affichage propre
            conn.close()
            return redirect(url_for('admin_panel', message="✅ Clé générée !", nouvelle_cle=cle_str))
            
        except Exception as e:
            message = f"❌ Erreur: {e}"

    # Récupérer la liste
    licences = conn.execute('SELECT * FROM licences ORDER BY id DESC LIMIT 50').fetchall()
    conn.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Licences</title>
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
        </style>
    </head>
    <body>
        <div class="card">
            <h2>🛠 Générateur Manuel</h2>
            {% if nouvelle_cle %}
                <div class="key-box">{{ nouvelle_cle }}</div>
                <div style="text-align:center; color:green; font-weight:bold;">{{ message }}</div>
                <div style="text-align:center; margin-top:10px;">
                    <a href="/admin/generer" style="color:#7f8c8d; text-decoration:none; font-size:0.9em;">✖ Effacer</a>
                </div>
            {% endif %}
            <form method="POST">
                <input type="text" name="client" placeholder="Nom du Client" required>
                <select name="type">
                    <option value="A">Annuel (1 an)</option>
                    <option value="M">Mensuel (1 mois)</option>
                    <option value="P">Perpétuel (À vie)</option>
                </select>
                <button type="submit">Générer Clé</button>
            </form>
        </div>
        <div class="card">
            <h3>📋 Liste des Licences</h3>
            <table>
                <tr><th>Clé</th><th>Client</th><th>Statut</th><th>Exp</th></tr>
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
    return render_template_string(html, message=message, nouvelle_cle=nouvelle_cle, licences=licences)