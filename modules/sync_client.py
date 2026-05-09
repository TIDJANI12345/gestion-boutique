"""
Client de synchronisation pour HishamPOS.
Synchronise les données locales avec le serveur sync via push/pull d'événements de stock.

Usage :
    from modules.sync_client import sync_client
    sync_client.configurer(url, licence_key, machine_id)
    sync_client.sync()          # push + pull
    sync_client.bootstrap()     # initialisation d'un nouveau terminal
"""
import requests
from datetime import datetime
from database import db
from modules.logger import get_logger

logger = get_logger('sync_client')


def _operation_to_event_type(operation: str) -> str:
    if not operation:
        return 'vente'
    op = operation.lower()
    if 'vente' in op:
        return 'vente'
    if any(k in op for k in ('reappro', 'approvisionnement', 'entrée', 'reception')):
        return 'reappro'
    if any(k in op for k in ('correction', 'ajustement', 'inventaire')):
        return 'correction'
    if any(k in op for k in ('perte', 'casse', 'vol')):
        return 'perte'
    return 'autre'


class SyncClient:
    def __init__(self):
        self._url = None
        self._licence_key = None
        self._machine_id = None

    def configurer(self, url: str, licence_key: str, machine_id: str):
        self._url = url.rstrip('/')
        self._licence_key = licence_key
        self._machine_id = machine_id

    @property
    def configure(self) -> bool:
        return bool(self._url and self._licence_key and self._machine_id)

    def _headers(self) -> dict:
        return {
            'X-Licence-Key': self._licence_key,
            'X-Machine-Id': self._machine_id,
        }

    def ping(self) -> bool:
        if not self.configure:
            return False
        try:
            r = requests.get(f'{self._url}/api/sync/ping', timeout=5)
            return r.ok
        except Exception:
            return False

    def push(self) -> bool:
        if not self.configure:
            return False
        try:
            payload = self._collecter_payload()
            r = requests.post(
                f'{self._url}/api/sync/push',
                json=payload,
                headers=self._headers(),
                timeout=30,
            )
            if r.ok:
                self._marquer_sync_done(payload['stock_events'])
                db.set_parametre('sync_last_push', datetime.now().isoformat())
                return True
            logger.warning(f"Push échoué : {r.status_code} {r.text[:200]}")
            return False
        except Exception as e:
            logger.error(f"Erreur push sync : {e}")
            return False

    def pull(self) -> bool:
        if not self.configure:
            return False
        try:
            last_event_id = int(db.get_parametre('sync_last_event_id') or 0)
            depuis_ts = db.get_parametre('sync_last_pull') or '2000-01-01T00:00:00'

            r = requests.post(
                f'{self._url}/api/sync/pull',
                json={'depuis_event_id': last_event_id, 'depuis': depuis_ts},
                headers=self._headers(),
                timeout=30,
            )
            if not r.ok:
                logger.warning(f"Pull échoué : {r.status_code} {r.text[:200]}")
                return False

            self._appliquer_pull(r.json())
            db.set_parametre('sync_last_pull', datetime.now().isoformat())
            return True
        except Exception as e:
            logger.error(f"Erreur pull sync : {e}")
            return False

    def sync(self) -> bool:
        return self.push() and self.pull()

    def bootstrap(self) -> bool:
        """
        Initialise un nouveau terminal depuis le snapshot serveur.
        À appeler une seule fois lors du premier démarrage en mode sync.
        """
        if not self.configure:
            return False
        try:
            r = requests.get(
                f'{self._url}/api/sync/bootstrap',
                headers=self._headers(),
                timeout=30,
            )
            if not r.ok:
                logger.error(f"Bootstrap échoué : {r.status_code} {r.text[:200]}")
                return False

            data = r.json()
            for p in data.get('produits', []):
                db.execute_query('''
                    INSERT OR IGNORE INTO produits
                        (code_barre, nom, categorie, prix_achat, prix_vente,
                         stock_actuel, stock_alerte, type_code_barre, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    p['code_barre'], p['nom'], p.get('categorie'),
                    p.get('prix_achat', 0), p['prix_vente'],
                    p.get('stock_actuel', 0), p.get('stock_alerte', 5),
                    p.get('type_code_barre', 'code128'), p.get('description'),
                ))

            last_event_id = data.get('last_event_id', 0)
            db.set_parametre('sync_last_event_id', str(last_event_id))
            db.set_parametre('sync_last_pull', datetime.now().isoformat())
            logger.info(f"Bootstrap terminé : {len(data.get('produits', []))} produits, event_id={last_event_id}")
            return True
        except Exception as e:
            logger.error(f"Erreur bootstrap : {e}")
            return False

    # ── Collecte locale ────────────────────────────────────────────────────────

    def _collecter_payload(self) -> dict:
        machine_id = self._machine_id
        last_push = db.get_parametre('sync_last_push') or '2000-01-01T00:00:00'

        # Événements de stock depuis historique_stock non encore synchronisés
        rows = db.fetch_all('''
            SELECT h.id, h.quantite_avant, h.quantite_apres, h.operation,
                   h.date_operation, p.code_barre
            FROM historique_stock h
            JOIN produits p ON p.id = h.produit_id
            WHERE h.sync_done = 0
        ''')
        stock_events = []
        for row in rows:
            delta = (row['quantite_apres'] or 0) - (row['quantite_avant'] or 0)
            if delta == 0:
                continue
            stock_events.append({
                'event_uuid': f"{machine_id}:{row['id']}",
                'code_barre': row['code_barre'],
                'delta': delta,
                'event_type': _operation_to_event_type(row['operation']),
                'reference': row['operation'],
            })

        # Infos produits modifiées depuis le dernier push (pas stock_actuel)
        produits_rows = db.fetch_all(
            'SELECT * FROM produits WHERE updated_at > ? OR updated_at IS NULL',
            (last_push,)
        )
        produits = []
        for _p in produits_rows:
            p = dict(_p)
            produits.append({
                'code_barre': p['code_barre'],
                'nom': p['nom'],
                'categorie': p.get('categorie'),
                'prix_achat': p.get('prix_achat', 0),
                'prix_vente': p['prix_vente'],
                'stock_alerte': p.get('stock_alerte', 5),
                'type_code_barre': p.get('type_code_barre', 'code128'),
                'description': p.get('description'),
                'date_ajout': p.get('date_ajout'),
                'updated_at': p.get('updated_at'),
            })

        # Ventes depuis le dernier push
        ventes_rows = db.fetch_all(
            "SELECT * FROM ventes WHERE date_vente > ? AND statut = 'terminee'",
            (last_push,)
        )
        ventes = []
        details = []
        for _v in ventes_rows:
            v = dict(_v)
            ventes.append({
                'numero_vente': v['numero_vente'],
                'date_vente': v['date_vente'],
                'total': v['total'],
                'client': v.get('client'),
                'statut': v.get('statut', 'terminee'),
            })
            detail_rows = db.fetch_all('''
                SELECT dv.quantite, dv.prix_unitaire, dv.sous_total, p.code_barre
                FROM details_ventes dv
                JOIN produits p ON p.id = dv.produit_id
                WHERE dv.vente_id = ?
            ''', (v['id'],))
            for d in detail_rows:
                details.append({
                    'numero_vente': v['numero_vente'],
                    'produit_code_barre': d['code_barre'],
                    'quantite': d['quantite'],
                    'prix_unitaire': d['prix_unitaire'],
                    'sous_total': d['sous_total'],
                })

        # Utilisateurs modifiés depuis le dernier push
        users_rows = db.fetch_all(
            'SELECT * FROM utilisateurs WHERE updated_at > ? OR updated_at IS NULL',
            (last_push,)
        )
        utilisateurs = []
        for _u in users_rows:
            u = dict(_u)
            utilisateurs.append({
                'nom': u['nom'],
                'prenom': u.get('prenom', ''),
                'email': u['email'],
                'mot_de_passe': u['mot_de_passe'],
                'role': u['role'],
                'actif': u.get('actif', 1),
                'date_creation': u.get('date_creation'),
                'dernier_login': u.get('dernier_login'),
                'updated_at': u.get('updated_at'),
            })

        return {
            'produits': produits,
            'ventes': ventes,
            'details_ventes': details,
            'stock_events': stock_events,
            'utilisateurs': utilisateurs,
        }

    def _marquer_sync_done(self, events: list):
        prefix = f"{self._machine_id}:"
        for event in events:
            uuid_str = event.get('event_uuid', '')
            if not uuid_str.startswith(prefix):
                continue
            try:
                hist_id = int(uuid_str[len(prefix):])
                db.execute_query(
                    'UPDATE historique_stock SET sync_done = 1 WHERE id = ?',
                    (hist_id,)
                )
            except (ValueError, Exception):
                pass

    # ── Application du pull ────────────────────────────────────────────────────

    def _appliquer_pull(self, data: dict):
        # Déltas de stock des autres terminaux, appliqués dans l'ordre du log serveur
        for event in data.get('stock_events', []):
            delta = event.get('delta', 0)
            code_barre = event.get('code_barre')
            if not code_barre or delta == 0:
                continue
            # MAX(0,...) évite le trigger verifier_stock_positif en cas de conflit
            db.execute_query('''
                UPDATE produits
                SET stock_actuel = MAX(0, stock_actuel + ?)
                WHERE code_barre = ?
            ''', (delta, code_barre))

        last_event_id = data.get('last_event_id', 0)
        if last_event_id:
            db.set_parametre('sync_last_event_id', str(last_event_id))

        # Infos produits (prix, nom, etc.) des autres terminaux — pas stock_actuel
        for p in data.get('produits', []):
            db.execute_query('''
                UPDATE produits SET
                    nom = COALESCE(?, nom),
                    categorie = COALESCE(?, categorie),
                    prix_achat = COALESCE(?, prix_achat),
                    prix_vente = COALESCE(?, prix_vente),
                    stock_alerte = COALESCE(?, stock_alerte)
                WHERE code_barre = ?
            ''', (
                p.get('nom'), p.get('categorie'), p.get('prix_achat'),
                p.get('prix_vente'), p.get('stock_alerte'), p['code_barre'],
            ))

        # Ventes des autres terminaux
        for v in data.get('ventes', []):
            try:
                db.execute_query('''
                    INSERT OR IGNORE INTO ventes
                        (numero_vente, date_vente, total, client, statut)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    v['numero_vente'], v.get('date_vente'),
                    v.get('total', 0), v.get('client'), v.get('statut', 'terminee'),
                ))
            except Exception:
                pass

        # Utilisateurs des autres terminaux
        for u in data.get('utilisateurs', []):
            try:
                db.execute_query('''
                    INSERT OR IGNORE INTO utilisateurs
                        (nom, prenom, email, mot_de_passe, role, actif, date_creation)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    u['nom'], u.get('prenom', ''), u['email'],
                    u['mot_de_passe'], u.get('role', 'caissier'),
                    u.get('actif', 1), u.get('date_creation'),
                ))
            except Exception:
                pass


sync_client = SyncClient()
