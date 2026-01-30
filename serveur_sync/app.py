"""
Serveur de synchronisation cloud pour Gestion Boutique
Endpoints : /api/sync/ping, /api/sync/push, /api/sync/pull
Authentification par X-Licence-Key + X-Machine-Id
"""
import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYNC_DB_PATH = os.path.join(BASE_DIR, 'sync_data.db')
LICENCE_DB_PATH = os.path.join(BASE_DIR, '..', 'serveur_licence', 'licences.db')

# --- Base de données sync ---

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


init_sync_db()


# --- Validation licence ---

def valider_licence(licence_key):
    """Verifie que la licence existe et est active dans la base licences"""
    try:
        licence_db = os.path.join(BASE_DIR, 'licences.db')
        if not os.path.exists(licence_db):
            # Chercher dans le dossier serveur_licence au meme niveau
            licence_db = LICENCE_DB_PATH
        if not os.path.exists(licence_db):
            # En production sur PythonAnywhere, la base licences est dans le meme dossier
            return True  # Accepter si pas de base licence disponible

        conn = sqlite3.connect(licence_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM licences WHERE cle_licence = ? AND statut = 'active'",
            (licence_key,)
        ).fetchone()
        conn.close()

        if row:
            # Verifier expiration
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
        return False
    except Exception:
        return True  # En cas d'erreur, on accepte pour ne pas bloquer la sync


def require_auth(f):
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


# --- Routes API ---

@app.route('/api/sync/ping', methods=['GET'])
def ping():
    """Health check"""
    return jsonify({
        'status': 'ok',
        'service': 'sync',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/sync/push', methods=['POST'])
@require_auth
def push(licence_key, machine_id):
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
            # Retrouver le numero_vente pour ce detail
            numero_vente = d.get('numero_vente', '')
            if not numero_vente:
                # Chercher dans les ventes envoyees dans le meme push
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
@require_auth
def pull(licence_key, machine_id):
    """Renvoyer les changements depuis un timestamp, en excluant ceux du meme machine_id"""
    try:
        data = request.json or {}
        depuis = data.get('depuis', '2000-01-01T00:00:00')

        conn = get_sync_db()

        # Produits modifies par d'autres postes de la meme boutique
        produits = conn.execute('''
            SELECT code_barre, nom, categorie, prix_achat, prix_vente,
                   stock_actuel, stock_alerte, type_code_barre, date_ajout,
                   description, updated_at
            FROM sync_produits
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_produits = []
        for p in produits:
            result_produits.append({
                'code_barre': p['code_barre'], 'nom': p['nom'],
                'categorie': p['categorie'], 'prix_achat': p['prix_achat'],
                'prix_vente': p['prix_vente'], 'stock_actuel': p['stock_actuel'],
                'stock_alerte': p['stock_alerte'], 'type_code_barre': p['type_code_barre'],
                'date_ajout': p['date_ajout'], 'description': p['description'],
                'updated_at': p['updated_at']
            })

        # Ventes
        ventes = conn.execute('''
            SELECT numero_vente, date_vente, total, client, statut, deleted_at
            FROM sync_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_ventes = []
        for v in ventes:
            result_ventes.append({
                'numero_vente': v['numero_vente'], 'date_vente': v['date_vente'],
                'total': v['total'], 'client': v['client'],
                'statut': v['statut'], 'deleted_at': v['deleted_at']
            })

        # Details ventes
        details = conn.execute('''
            SELECT numero_vente, produit_code_barre, quantite, prix_unitaire, sous_total
            FROM sync_details_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_details = []
        for d in details:
            result_details.append({
                'numero_vente': d['numero_vente'],
                'produit_code_barre': d['produit_code_barre'],
                'quantite': d['quantite'], 'prix_unitaire': d['prix_unitaire'],
                'sous_total': d['sous_total']
            })

        # Historique stock
        historique = conn.execute('''
            SELECT produit_code_barre, quantite_avant, quantite_apres, operation, date_operation
            FROM sync_historique_stock
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_historique = []
        for h in historique:
            result_historique.append({
                'produit_code_barre': h['produit_code_barre'],
                'quantite_avant': h['quantite_avant'],
                'quantite_apres': h['quantite_apres'],
                'operation': h['operation'], 'date_operation': h['date_operation']
            })

        # Utilisateurs
        utilisateurs = conn.execute('''
            SELECT nom, prenom, email, mot_de_passe, role, actif,
                   date_creation, dernier_login, updated_at
            FROM sync_utilisateurs
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis)).fetchall()

        result_utilisateurs = []
        for u in utilisateurs:
            result_utilisateurs.append({
                'nom': u['nom'], 'prenom': u['prenom'],
                'email': u['email'], 'mot_de_passe': u['mot_de_passe'],
                'role': u['role'], 'actif': u['actif'],
                'date_creation': u['date_creation'],
                'dernier_login': u['dernier_login'],
                'updated_at': u['updated_at']
            })

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


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
