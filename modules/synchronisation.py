"""
Systeme de synchronisation cloud-only
Synchronise les donnees via le serveur PythonAnywhere
Avec file d'attente hors-ligne
"""
import requests
import json
import sqlite3
import threading
import time
from datetime import datetime
from database import db
from config import DB_PATH, SYNC_SERVER_URL, SYNC_INTERVAL
from modules.logger import get_logger

logger = get_logger('sync')


class Synchronisation:
    def __init__(self):
        self.mode = 'offline'
        self._licence_key = None
        self._machine_id = None

    def _get_licence_info(self):
        """Recupere la cle de licence et le machine_id depuis le fichier licence local"""
        if self._licence_key and self._machine_id:
            return self._licence_key, self._machine_id

        try:
            from modules.licence import GestionLicence, FICHIER_LICENCE
            import os

            gl = GestionLicence()
            self._machine_id = gl.get_machine_id()

            if os.path.exists(FICHIER_LICENCE):
                with open(FICHIER_LICENCE, 'rb') as f:
                    data_crypt = f.read()
                data_json = gl.cipher.decrypt(data_crypt).decode()
                data = json.loads(data_json)
                self._licence_key = data.get('cle', '')
            else:
                self._licence_key = ''

            return self._licence_key, self._machine_id
        except Exception as e:
            logger.warning(f"Impossible de lire la licence: {e}")
            return '', ''

    def _get_headers(self):
        """Headers d'authentification pour les requetes sync"""
        licence_key, machine_id = self._get_licence_info()
        return {
            'X-Licence-Key': licence_key,
            'X-Machine-Id': machine_id,
            'Content-Type': 'application/json'
        }

    def _get_dernier_sync(self):
        """Recupere le timestamp de la derniere sync depuis la table parametres"""
        val = db.get_parametre('dernier_sync', '')
        return val if val else None

    def _set_dernier_sync(self, timestamp):
        """Sauvegarde le timestamp de derniere sync dans la table parametres"""
        db.set_parametre('dernier_sync', timestamp)

    def detecter_mode(self):
        """Teste la connectivite au serveur cloud uniquement"""
        try:
            response = requests.get(
                f'{SYNC_SERVER_URL}/api/sync/ping',
                headers=self._get_headers(),
                timeout=5
            )
            if response.status_code == 200:
                self.mode = 'cloud'
                return 'cloud'
        except Exception:
            pass

        self.mode = 'offline'
        return 'offline'

    def synchroniser(self):
        """Synchronise avec le serveur cloud (push puis pull)"""
        mode = self.detecter_mode()

        if mode == 'offline':
            logger.info("Mode offline - synchronisation reportee")
            return False

        try:
            # 1. Vider la file d'attente en premier
            self._flush_queue()

            # 2. Push : envoyer les changements locaux
            succes_push = self._push()

            # 3. Pull : recuperer les changements distants
            succes_pull = self._pull()

            if succes_push or succes_pull:
                self._set_dernier_sync(datetime.now().isoformat())
                logger.info("Synchronisation cloud terminee")
                return True

            return False
        except Exception as e:
            logger.error(f"Erreur synchronisation: {e}")
            return False

    def _push(self):
        """Envoie les changements locaux au serveur"""
        try:
            changements = self.obtenir_changements_locaux()

            if not any(changements.get(k) for k in ('produits', 'ventes', 'details_ventes', 'historique_stock', 'utilisateurs')):
                return True

            response = requests.post(
                f'{SYNC_SERVER_URL}/api/sync/push',
                headers=self._get_headers(),
                json=changements,
                timeout=15
            )

            if response.status_code == 200:
                logger.info("Push reussi")
                return True
            else:
                logger.warning(f"Erreur push: {response.status_code}")
                self._enqueue(changements)
                return False
        except Exception as e:
            logger.error(f"Erreur push: {e}")
            try:
                self._enqueue(changements)
            except Exception:
                pass
            return False

    def _pull(self):
        """Recupere les changements distants depuis le serveur"""
        try:
            dernier_sync = self._get_dernier_sync()
            payload = {
                'depuis': dernier_sync or '2000-01-01T00:00:00'
            }

            response = requests.post(
                f'{SYNC_SERVER_URL}/api/sync/pull',
                headers=self._get_headers(),
                json=payload,
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                self.appliquer_changements_distants(data)
                logger.info("Pull reussi")
                return True
            else:
                logger.warning(f"Erreur pull: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Erreur pull: {e}")
            return False

    # --- File d'attente hors-ligne ---

    def _enqueue(self, changements):
        """Stocker les changements en attente dans sync_queue"""
        try:
            data_json = json.dumps(changements, default=str)
            db.execute_query(
                "INSERT INTO sync_queue (action, table_name, data_json) VALUES (?, ?, ?)",
                ('push', 'all', data_json)
            )
            logger.info("Changements mis en file d'attente")
        except Exception as e:
            logger.error(f"Erreur enqueue: {e}")

    def _flush_queue(self):
        """Envoyer tous les changements en attente"""
        try:
            queue = db.fetch_all("SELECT id, data_json FROM sync_queue ORDER BY created_at ASC")
            if not queue:
                return

            logger.info(f"Vidage de la file d'attente ({len(queue)} elements)")

            for item in queue:
                item_id, data_json = item[0], item[1]
                try:
                    changements = json.loads(data_json)
                    response = requests.post(
                        f'{SYNC_SERVER_URL}/api/sync/push',
                        headers=self._get_headers(),
                        json=changements,
                        timeout=15
                    )
                    if response.status_code == 200:
                        db.execute_query("DELETE FROM sync_queue WHERE id = ?", (item_id,))
                        logger.info(f"Element {item_id} de la queue envoye")
                    else:
                        logger.warning(f"Echec envoi element {item_id}: {response.status_code}")
                        break  # Arreter si un envoi echoue
                except Exception as e:
                    logger.error(f"Erreur flush element {item_id}: {e}")
                    break
        except Exception as e:
            logger.error(f"Erreur flush_queue: {e}")

    # --- Donnees locales ---

    def obtenir_changements_locaux(self):
        """Recupere toutes les donnees modifiees depuis le dernier sync"""
        dernier_sync = self._get_dernier_sync()
        depuis = dernier_sync or '2000-01-01T00:00:00'

        changements = {
            'produits': [],
            'ventes': [],
            'details_ventes': [],
            'historique_stock': [],
            'utilisateurs': [],
            'timestamp': datetime.now().isoformat()
        }

        # Produits modifies
        produits = db.fetch_all(
            "SELECT id, nom, categorie, prix_achat, prix_vente, stock_actuel, "
            "stock_alerte, code_barre, type_code_barre, date_ajout, description, updated_at "
            "FROM produits WHERE updated_at > ?",
            (depuis,)
        )
        for p in produits:
            changements['produits'].append({
                'id': p[0], 'nom': p[1], 'categorie': p[2],
                'prix_achat': p[3], 'prix_vente': p[4],
                'stock_actuel': p[5], 'stock_alerte': p[6],
                'code_barre': p[7], 'type_code_barre': p[8],
                'date_ajout': p[9], 'description': p[10],
                'updated_at': p[11]
            })

        # Ventes
        ventes = db.fetch_all(
            "SELECT id, numero_vente, date_vente, total, client, statut, deleted_at "
            "FROM ventes WHERE date_vente > ?",
            (depuis,)
        )
        for v in ventes:
            changements['ventes'].append({
                'id': v[0], 'numero_vente': v[1], 'date_vente': v[2],
                'total': v[3], 'client': v[4], 'statut': v[5],
                'deleted_at': v[6]
            })

        # Details des ventes liees
        if changements['ventes']:
            vente_ids = [v['id'] for v in changements['ventes']]
            placeholders = ','.join('?' * len(vente_ids))
            details = db.fetch_all(
                f"SELECT id, vente_id, produit_id, quantite, prix_unitaire, sous_total "
                f"FROM details_ventes WHERE vente_id IN ({placeholders})",
                tuple(vente_ids)
            )
            for d in details:
                changements['details_ventes'].append({
                    'id': d[0], 'vente_id': d[1], 'produit_id': d[2],
                    'quantite': d[3], 'prix_unitaire': d[4], 'sous_total': d[5]
                })

        # Historique stock
        historique = db.fetch_all(
            "SELECT id, produit_id, quantite_avant, quantite_apres, operation, date_operation "
            "FROM historique_stock WHERE date_operation > ?",
            (depuis,)
        )
        for h in historique:
            changements['historique_stock'].append({
                'id': h[0], 'produit_id': h[1],
                'quantite_avant': h[2], 'quantite_apres': h[3],
                'operation': h[4], 'date_operation': h[5]
            })

        # Utilisateurs modifies
        utilisateurs = db.fetch_all(
            "SELECT id, nom, prenom, email, mot_de_passe, role, actif, date_creation, dernier_login, updated_at "
            "FROM utilisateurs WHERE updated_at > ?",
            (depuis,)
        )
        for u in utilisateurs:
            changements['utilisateurs'].append({
                'id': u[0], 'nom': u[1], 'prenom': u[2],
                'email': u[3], 'mot_de_passe': u[4], 'role': u[5],
                'actif': u[6], 'date_creation': u[7],
                'dernier_login': u[8], 'updated_at': u[9]
            })

        return changements

    def appliquer_changements_distants(self, data):
        """Applique les changements recus du serveur"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            # Produits : last write wins
            for p in data.get('produits', []):
                existant = cursor.execute(
                    "SELECT updated_at FROM produits WHERE code_barre = ?",
                    (p['code_barre'],)
                ).fetchone()

                if existant and existant[0] and existant[0] > p.get('updated_at', ''):
                    continue

                cursor.execute('''
                    INSERT INTO produits (nom, categorie, prix_achat, prix_vente, stock_actuel,
                        stock_alerte, code_barre, type_code_barre, date_ajout, description, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(code_barre) DO UPDATE SET
                        nom=excluded.nom, categorie=excluded.categorie,
                        prix_achat=excluded.prix_achat, prix_vente=excluded.prix_vente,
                        stock_actuel=excluded.stock_actuel, stock_alerte=excluded.stock_alerte,
                        type_code_barre=excluded.type_code_barre, description=excluded.description,
                        updated_at=excluded.updated_at
                ''', (
                    p['nom'], p['categorie'], p['prix_achat'], p['prix_vente'],
                    p['stock_actuel'], p['stock_alerte'], p['code_barre'],
                    p['type_code_barre'], p['date_ajout'], p['description'],
                    p.get('updated_at', datetime.now().isoformat())
                ))

            # Ventes : INSERT OR IGNORE
            for v in data.get('ventes', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO ventes (numero_vente, date_vente, total, client, statut, deleted_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    v['numero_vente'], v['date_vente'], v['total'],
                    v['client'], v['statut'], v.get('deleted_at')
                ))

            # Details ventes
            for d in data.get('details_ventes', []):
                vente_locale = cursor.execute(
                    "SELECT id FROM ventes WHERE numero_vente = (SELECT numero_vente FROM ventes WHERE id = ? LIMIT 1)",
                    (d['vente_id'],)
                ).fetchone()

                vente_id = vente_locale[0] if vente_locale else d['vente_id']
                cursor.execute('''
                    INSERT OR IGNORE INTO details_ventes (vente_id, produit_id, quantite, prix_unitaire, sous_total)
                    VALUES (?, ?, ?, ?, ?)
                ''', (vente_id, d['produit_id'], d['quantite'], d['prix_unitaire'], d['sous_total']))

            # Historique stock
            for h in data.get('historique_stock', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO historique_stock (produit_id, quantite_avant, quantite_apres, operation, date_operation)
                    VALUES (?, ?, ?, ?, ?)
                ''', (h['produit_id'], h['quantite_avant'], h['quantite_apres'], h['operation'], h['date_operation']))

            # Utilisateurs : last write wins
            for u in data.get('utilisateurs', []):
                existant = cursor.execute(
                    "SELECT updated_at FROM utilisateurs WHERE email = ?",
                    (u['email'],)
                ).fetchone()

                if existant and existant[0] and existant[0] > u.get('updated_at', ''):
                    continue

                cursor.execute('''
                    INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role, actif, date_creation, dernier_login, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(email) DO UPDATE SET
                        nom=excluded.nom, prenom=excluded.prenom,
                        mot_de_passe=excluded.mot_de_passe, role=excluded.role,
                        actif=excluded.actif, dernier_login=excluded.dernier_login,
                        updated_at=excluded.updated_at
                ''', (
                    u['nom'], u['prenom'], u['email'], u['mot_de_passe'],
                    u['role'], u['actif'], u['date_creation'],
                    u['dernier_login'], u.get('updated_at', datetime.now().isoformat())
                ))

            conn.commit()
            conn.close()
            logger.info("Changements distants appliques")
        except Exception as e:
            logger.error(f"Erreur application changements: {e}")

    def sync_automatique_arriere_plan(self):
        """Synchronisation automatique en arriere-plan"""
        def sync_loop():
            while True:
                time.sleep(SYNC_INTERVAL)
                try:
                    self.synchroniser()
                except Exception as e:
                    logger.error(f"Erreur sync auto: {e}")

        thread = threading.Thread(target=sync_loop, daemon=True)
        thread.start()
