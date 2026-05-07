"""
API Flask locale pour le mode réseau multi-terminaux.
Tourne sur le PC Serveur (port 5050), accessible sur le réseau local uniquement.
Les PC clients (caisses) envoient leurs requêtes HTTP ici au lieu d'accéder SQLite directement.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from functools import wraps
from datetime import datetime
from database import db
from modules.logger import get_logger

logger = get_logger('api_locale')

app = Flask(__name__)

# Token partagé — généré au premier démarrage et stocké dans les paramètres
def get_token():
    token = db.get_parametre('reseau_local_token')
    if not token:
        import secrets
        token = secrets.token_hex(16)
        db.set_parametre('reseau_local_token', token)
    return token


def require_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('X-Local-Token', '')
        if auth != get_token():
            return jsonify({'error': 'Non autorisé'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Health check ──────────────────────────────────────────────────────────────

@app.route('/ping', methods=['GET'])
def ping():
    boutique = db.get_parametre('nom_boutique') or 'HishamPOS'
    return jsonify({
        'status': 'ok',
        'serveur': boutique,
        'timestamp': datetime.now().isoformat()
    })


# ── Produits ──────────────────────────────────────────────────────────────────

@app.route('/produits', methods=['GET'])
@require_token
def liste_produits():
    try:
        rows = db.fetch_all("SELECT * FROM produits ORDER BY nom")
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/produits/<code_barre>', methods=['GET'])
@require_token
def get_produit(code_barre):
    try:
        row = db.fetch_one("SELECT * FROM produits WHERE code_barre = ?", (code_barre,))
        if not row:
            return jsonify({'error': 'Produit non trouvé'}), 404
        return jsonify(dict(row))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/produits', methods=['POST'])
@require_token
def creer_produit():
    try:
        data = request.json or {}
        required = ['nom', 'prix_vente', 'code_barre']
        if not all(k in data for k in required):
            return jsonify({'error': f'Champs requis: {required}'}), 400

        db.execute_query('''
            INSERT INTO produits (nom, categorie, prix_achat, prix_vente,
                stock_actuel, stock_alerte, code_barre, type_code_barre, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['nom'], data.get('categorie'), data.get('prix_achat', 0),
            data['prix_vente'], data.get('stock_actuel', 0), data.get('stock_alerte', 5),
            data['code_barre'], data.get('type_code_barre', 'code128'), data.get('description')
        ))
        return jsonify({'status': 'ok'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/produits/<code_barre>', methods=['PUT'])
@require_token
def modifier_produit(code_barre):
    try:
        data = request.json or {}
        db.execute_query('''
            UPDATE produits SET nom=?, categorie=?, prix_achat=?, prix_vente=?,
                stock_actuel=?, stock_alerte=?, type_code_barre=?, description=?
            WHERE code_barre=?
        ''', (
            data.get('nom'), data.get('categorie'), data.get('prix_achat', 0),
            data.get('prix_vente'), data.get('stock_actuel', 0), data.get('stock_alerte', 5),
            data.get('type_code_barre', 'code128'), data.get('description'), code_barre
        ))
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Ventes ────────────────────────────────────────────────────────────────────

@app.route('/ventes', methods=['GET'])
@require_token
def liste_ventes():
    try:
        depuis = request.args.get('depuis')
        jusqu = request.args.get('jusqu')

        sql = "SELECT * FROM ventes WHERE 1=1"
        params = []
        if depuis:
            sql += " AND date_vente >= ?"
            params.append(depuis)
        if jusqu:
            sql += " AND date_vente <= ?"
            params.append(jusqu)
        sql += " ORDER BY date_vente DESC LIMIT 500"

        rows = db.fetch_all(sql, params)
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/ventes', methods=['POST'])
@require_token
def enregistrer_vente():
    try:
        data = request.json or {}
        required = ['numero_vente', 'total', 'details']
        if not all(k in data for k in required):
            return jsonify({'error': f'Champs requis: {required}'}), 400

        with db.conn:
            db.execute_query('''
                INSERT INTO ventes (numero_vente, date_vente, total, total_ttc,
                    montant_recu, monnaie, mode_paiement, client_id, utilisateur_id, statut)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['numero_vente'],
                data.get('date_vente', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                data['total'], data.get('total_ttc', data['total']),
                data.get('montant_recu', data['total']), data.get('monnaie', 0),
                data.get('mode_paiement', 'especes'),
                data.get('client_id'), data.get('utilisateur_id'), 'terminee'
            ))
            vente_id = db.fetch_one(
                "SELECT id FROM ventes WHERE numero_vente = ?", (data['numero_vente'],)
            )['id']

            for d in data['details']:
                db.execute_query('''
                    INSERT INTO details_ventes (vente_id, produit_id, quantite,
                        prix_unitaire, sous_total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (vente_id, d['produit_id'], d['quantite'],
                      d['prix_unitaire'], d['sous_total']))
                db.execute_query(
                    "UPDATE produits SET stock_actuel = stock_actuel - ? WHERE id = ?",
                    (d['quantite'], d['produit_id'])
                )

        return jsonify({'status': 'ok', 'vente_id': vente_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Stats dashboard ───────────────────────────────────────────────────────────

@app.route('/stats/dashboard', methods=['GET'])
@require_token
def stats_dashboard():
    try:
        aujourd_hui = datetime.now().strftime('%Y-%m-%d')

        ventes_jour = db.fetch_one(
            "SELECT COUNT(*) as nb, COALESCE(SUM(total), 0) as total FROM ventes "
            "WHERE date_vente >= ? AND statut = 'terminee'", (aujourd_hui + ' 00:00:00',)
        )
        stock_alerte = db.fetch_one(
            "SELECT COUNT(*) as nb FROM produits WHERE stock_actuel <= stock_alerte"
        )
        total_produits = db.fetch_one("SELECT COUNT(*) as nb FROM produits")

        return jsonify({
            'ventes_jour': {'nb': ventes_jour['nb'], 'total': ventes_jour['total']},
            'stock_alerte': stock_alerte['nb'],
            'total_produits': total_produits['nb'],
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Utilisateurs ──────────────────────────────────────────────────────────────

@app.route('/utilisateurs', methods=['GET'])
@require_token
def liste_utilisateurs():
    try:
        rows = db.fetch_all(
            "SELECT id, nom, prenom, email, role, actif FROM utilisateurs ORDER BY nom"
        )
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Stock alertes ─────────────────────────────────────────────────────────────

@app.route('/stock/alertes', methods=['GET'])
@require_token
def stock_alertes():
    try:
        rows = db.fetch_all(
            "SELECT id, nom, code_barre, stock_actuel, stock_alerte "
            "FROM produits WHERE stock_actuel <= stock_alerte ORDER BY stock_actuel"
        )
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Démarrage ─────────────────────────────────────────────────────────────────

def demarrer(host='0.0.0.0', port=5050):
    token = get_token()
    logger.info(f"API locale démarrée sur {host}:{port}")
    logger.info(f"Token réseau : {token}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    demarrer()
