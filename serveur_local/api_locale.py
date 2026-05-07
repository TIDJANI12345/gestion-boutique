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

# ── Suivi des terminaux connectés (Étape 7) ───────────────────────────────────
# machine_id → {'ip': ..., 'nom': ..., 'derniere_activite': ...}
_terminaux: dict = {}
_terminaux_lock = __import__('threading').Lock()

def _plan_actuel() -> str:
    try:
        from modules.features import plan_actuel
        return plan_actuel()
    except Exception:
        return 'standard'

def _max_terminaux() -> int:
    try:
        from modules.features import LIMITES
        return LIMITES.get(_plan_actuel(), {}).get('terminaux', 1)
    except Exception:
        return 1

def _enregistrer_terminal(machine_id: str, nom: str, ip: str):
    with _terminaux_lock:
        _terminaux[machine_id] = {
            'ip': ip,
            'nom': nom,
            'derniere_activite': datetime.now().isoformat(),
        }

def _verifier_quota(machine_id: str) -> tuple[bool, str]:
    """Retourne (autorisé, message). Un terminal déjà connu est toujours autorisé."""
    with _terminaux_lock:
        if machine_id in _terminaux:
            return True, 'ok'
        nb = len(_terminaux)
        max_t = _max_terminaux()
        if nb >= max_t:
            plan = _plan_actuel()
            return False, (
                f"Quota atteint : {nb}/{max_t} terminaux autorisés (plan {plan}). "
                f"Passez au plan supérieur pour connecter plus de PC."
            )
        return True, 'ok'

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
        # Mise à jour de l'activité du terminal si machine_id fourni
        machine_id = request.headers.get('X-Machine-Id', '')
        if machine_id and machine_id in _terminaux:
            with _terminaux_lock:
                _terminaux[machine_id]['derniere_activite'] = datetime.now().isoformat()
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


# ── Connexion terminaux (Étape 7) ─────────────────────────────────────────────

@app.route('/connect', methods=['POST'])
@require_token
def connecter_terminal():
    """
    Appelé par un PC client au démarrage pour s'enregistrer.
    Vérifie le quota du plan avant d'autoriser.
    """
    data = request.json or {}
    machine_id = data.get('machine_id', request.headers.get('X-Machine-Id', ''))
    nom = data.get('nom', 'Caisse inconnue')
    ip = request.remote_addr

    if not machine_id:
        return jsonify({'error': 'machine_id requis'}), 400

    autorise, msg = _verifier_quota(machine_id)
    if not autorise:
        return jsonify({'error': msg, 'code': 'QUOTA_DEPASSE'}), 403

    _enregistrer_terminal(machine_id, nom, ip)
    plan = _plan_actuel()
    logger.info(f"Terminal connecté : {nom} ({ip}) — {len(_terminaux)}/{_max_terminaux()} terminaux, plan {plan}")
    try:
        from modules.utilisateurs import Utilisateur
        Utilisateur.logger_action(None, 'terminal_connexion', f"{nom} ({ip}) connecté au réseau")
    except Exception:
        pass
    return jsonify({
        'status': 'ok',
        'plan': plan,
        'terminaux_connectes': len(_terminaux),
        'terminaux_max': _max_terminaux(),
    })


@app.route('/terminaux', methods=['GET'])
@require_token
def liste_terminaux():
    """Liste les terminaux actuellement connectés (vue admin)."""
    with _terminaux_lock:
        data = [
            {'machine_id': mid, **info}
            for mid, info in _terminaux.items()
        ]
    return jsonify({
        'terminaux': data,
        'nb': len(data),
        'max': _max_terminaux(),
        'plan': _plan_actuel(),
    })


@app.route('/deconnecter', methods=['POST'])
@require_token
def deconnecter_terminal():
    machine_id = (request.json or {}).get('machine_id', '')
    if machine_id:
        with _terminaux_lock:
            info = _terminaux.pop(machine_id, None)
        if info:
            nom = info.get('nom', machine_id)
            ip = info.get('ip', '?')
            logger.info(f"Terminal déconnecté : {nom} ({ip})")
            try:
                from modules.utilisateurs import Utilisateur
                Utilisateur.logger_action(None, 'terminal_deconnexion', f"{nom} ({ip}) déconnecté du réseau")
            except Exception:
                pass
    return jsonify({'status': 'ok'})


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
                    montant_recu, monnaie, mode_paiement, client_id, utilisateur_id, nom_caisse, statut)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['numero_vente'],
                data.get('date_vente', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                data['total'], data.get('total_ttc', data['total']),
                data.get('montant_recu', data['total']), data.get('monnaie', 0),
                data.get('mode_paiement', 'especes'),
                data.get('client_id'), data.get('utilisateur_id'),
                data.get('nom_caisse'), 'terminee'
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


@app.route('/login', methods=['POST'])
@require_token
def login_reseau():
    """Authentifie un utilisateur côté serveur, renvoie ses infos sans le hash."""
    try:
        data = request.get_json() or {}
        email = data.get('email', '').strip()
        mot_de_passe = data.get('mot_de_passe', '')
        if not email or not mot_de_passe:
            return jsonify({'succes': False, 'message': 'Identifiants manquants'}), 400
        from modules.utilisateurs import Utilisateur
        user = Utilisateur.authentifier(email, mot_de_passe)
        if user:
            u = dict(user)
            u.pop('mot_de_passe', None)
            return jsonify({'succes': True, 'utilisateur': u})
        return jsonify({'succes': False, 'message': 'Email ou mot de passe incorrect'}), 401
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
    boutique = db.get_parametre('boutique_nom') or 'HishamPOS'
    logger.info(f"API locale démarrée sur {host}:{port}")
    logger.info(f"Token réseau : {token}")
    # Découverte automatique — diffuse la présence sur le réseau local
    try:
        from serveur_local.discovery import demarrer_broadcaster
        demarrer_broadcaster(boutique, port, token)
    except Exception as e:
        logger.warning(f"Broadcaster UDP non démarré : {e}")
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == '__main__':
    demarrer()
