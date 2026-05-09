"""
Serveur de synchronisation pour HishamPOS
Endpoints : /api/sync/ping, /api/sync/push, /api/sync/pull, /api/sync/bootstrap
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

    # Log d'événements de stock — remplace sync_historique_stock.
    # stock_actuel dans sync_produits est toujours recalculé via delta,
    # jamais écrasé par un snapshot client.
    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_uuid TEXT UNIQUE NOT NULL,
            licence_key TEXT NOT NULL,
            terminal_id TEXT NOT NULL,
            code_barre TEXT NOT NULL,
            delta INTEGER NOT NULL,
            event_type TEXT NOT NULL DEFAULT 'vente',
            reference TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute(
        'CREATE INDEX IF NOT EXISTS idx_events_licence ON stock_events(licence_key, id)'
    )

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
    try:
        licence_db = os.path.join(BASE_DIR, 'licences.db')
        if not os.path.exists(licence_db):
            licence_db = LICENCE_DB_PATH
        if not os.path.exists(licence_db):
            return True

        conn = sqlite3.connect(licence_db)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM licences WHERE cle_licence = ? AND statut = 'active'",
            (licence_key,)
        ).fetchone()
        conn.close()

        if row:
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
        return True


def require_auth(f):
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


# --- Routes ---

@app.route('/api/sync/ping', methods=['GET'])
def ping():
    return jsonify({
        'status': 'ok',
        'service': 'sync',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/sync/push', methods=['POST'])
@require_auth
def push(licence_key, machine_id):
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'Aucune donnée'}), 400

        conn = get_sync_db()
        now = datetime.now().isoformat()

        # Produits : infos seulement, jamais stock_actuel (géré via events)
        for p in data.get('produits', []):
            conn.execute('''
                INSERT INTO sync_produits
                    (licence_key, machine_id, code_barre, nom, categorie, prix_achat,
                     prix_vente, stock_alerte, type_code_barre,
                     date_ajout, description, updated_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(licence_key, code_barre) DO UPDATE SET
                    machine_id=excluded.machine_id,
                    nom=excluded.nom,
                    categorie=excluded.categorie,
                    prix_achat=excluded.prix_achat,
                    prix_vente=excluded.prix_vente,
                    stock_alerte=excluded.stock_alerte,
                    type_code_barre=excluded.type_code_barre,
                    description=excluded.description,
                    updated_at=excluded.updated_at,
                    synced_at=excluded.synced_at
            ''', (
                licence_key, machine_id, p['code_barre'], p['nom'],
                p.get('categorie'), p.get('prix_achat', 0), p['prix_vente'],
                p.get('stock_alerte', 5), p.get('type_code_barre', 'code128'),
                p.get('date_ajout'), p.get('description'), p.get('updated_at', now), now
            ))

        # Stock events : idempotent via event_uuid, delta appliqué sur stock_actuel
        for e in data.get('stock_events', []):
            event_uuid = e.get('event_uuid')
            code_barre = e.get('code_barre')
            delta = e.get('delta', 0)
            if not event_uuid or not code_barre or delta == 0:
                continue
            inserted = conn.execute('''
                INSERT OR IGNORE INTO stock_events
                    (event_uuid, licence_key, terminal_id, code_barre, delta, event_type, reference)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_uuid, licence_key, machine_id, code_barre, delta,
                e.get('event_type', 'vente'), e.get('reference')
            )).rowcount
            if inserted:
                conn.execute('''
                    UPDATE sync_produits
                    SET stock_actuel = MAX(0, stock_actuel + ?)
                    WHERE licence_key = ? AND code_barre = ?
                ''', (delta, licence_key, code_barre))

        # Ventes
        for v in data.get('ventes', []):
            conn.execute('''
                INSERT OR IGNORE INTO sync_ventes
                    (licence_key, machine_id, numero_vente, date_vente, total,
                     client, statut, deleted_at, synced_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                licence_key, machine_id, v['numero_vente'], v.get('date_vente'),
                v.get('total'), v.get('client'), v.get('statut', 'terminee'),
                v.get('deleted_at'), now
            ))

        # Détails ventes
        for d in data.get('details_ventes', []):
            numero_vente = d.get('numero_vente', '')
            if not numero_vente:
                continue
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
                licence_key, machine_id, u['nom'], u.get('prenom', ''),
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
@require_auth
def pull(licence_key, machine_id):
    try:
        data = request.json or {}
        depuis_event_id = int(data.get('depuis_event_id', 0))
        depuis_ts = data.get('depuis', '2000-01-01T00:00:00')

        conn = get_sync_db()

        # Événements de stock depuis le dernier ID connu, des autres terminaux
        events = conn.execute('''
            SELECT id, event_uuid, terminal_id, code_barre, delta, event_type, reference, created_at
            FROM stock_events
            WHERE licence_key = ? AND terminal_id != ? AND id > ?
            ORDER BY id
        ''', (licence_key, machine_id, depuis_event_id)).fetchall()

        result_events = []
        last_event_id = depuis_event_id
        for e in events:
            result_events.append({
                'id': e['id'],
                'event_uuid': e['event_uuid'],
                'terminal_id': e['terminal_id'],
                'code_barre': e['code_barre'],
                'delta': e['delta'],
                'event_type': e['event_type'],
                'reference': e['reference'],
                'created_at': e['created_at'],
            })
            if e['id'] > last_event_id:
                last_event_id = e['id']

        # Infos produits (pas stock_actuel) modifiées par d'autres terminaux
        produits = conn.execute('''
            SELECT code_barre, nom, categorie, prix_achat, prix_vente,
                   stock_alerte, type_code_barre, date_ajout, description, updated_at
            FROM sync_produits
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis_ts)).fetchall()

        # Ventes des autres terminaux
        ventes = conn.execute('''
            SELECT numero_vente, date_vente, total, client, statut, deleted_at
            FROM sync_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis_ts)).fetchall()

        # Détails ventes des autres terminaux
        details = conn.execute('''
            SELECT numero_vente, produit_code_barre, quantite, prix_unitaire, sous_total
            FROM sync_details_ventes
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis_ts)).fetchall()

        # Utilisateurs modifiés par d'autres terminaux
        utilisateurs = conn.execute('''
            SELECT nom, prenom, email, mot_de_passe, role, actif,
                   date_creation, dernier_login, updated_at
            FROM sync_utilisateurs
            WHERE licence_key = ? AND machine_id != ? AND synced_at > ?
        ''', (licence_key, machine_id, depuis_ts)).fetchall()

        conn.close()

        return jsonify({
            'stock_events': result_events,
            'last_event_id': last_event_id,
            'produits': [dict(p) for p in produits],
            'ventes': [dict(v) for v in ventes],
            'details_ventes': [dict(d) for d in details],
            'utilisateurs': [dict(u) for u in utilisateurs],
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/sync/bootstrap', methods=['GET'])
@require_auth
def bootstrap(licence_key, machine_id):
    """
    Retourne un snapshot complet du stock + le max event_id courant.
    Un nouveau terminal utilise ce snapshot comme état de départ, puis
    suit le log d'événements à partir de last_event_id.
    """
    try:
        conn = get_sync_db()

        produits = conn.execute('''
            SELECT code_barre, nom, categorie, prix_achat, prix_vente,
                   stock_actuel, stock_alerte, type_code_barre, description
            FROM sync_produits
            WHERE licence_key = ?
        ''', (licence_key,)).fetchall()

        last_event = conn.execute(
            'SELECT MAX(id) as max_id FROM stock_events WHERE licence_key = ?',
            (licence_key,)
        ).fetchone()

        conn.close()

        return jsonify({
            'produits': [dict(p) for p in produits],
            'last_event_id': last_event['max_id'] or 0,
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
