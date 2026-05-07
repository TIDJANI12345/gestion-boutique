"""
Client réseau pour le mode multi-terminaux.
Fournit la même interface que database.py mais passe par l'API locale du PC Serveur.
Utilisé sur les PC clients (caisses) quand MODE_RESEAU = 'client'.
"""
import requests
import sqlite3
from modules.logger import get_logger

logger = get_logger('client_reseau')

_TIMEOUT = 10  # secondes


class _FakeRow(dict):
    """Simule sqlite3.Row : accès par clé et par index."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)

    def keys(self):
        return super().keys()


def _rows(data):
    if isinstance(data, list):
        return [_FakeRow(d) for d in data]
    return data


class ClientReseau:
    """
    Interface identique à database.Database mais sans SQLite local.
    Toutes les opérations passent par l'API locale du serveur.
    """

    def __init__(self, url: str, token: str):
        self._url = url.rstrip('/')
        self._token = token
        self._headers = {'X-Local-Token': token, 'Content-Type': 'application/json'}

    # ── Helpers HTTP ─────────────────────────────────────────────────────────

    def _get(self, path, params=None):
        try:
            r = requests.get(f"{self._url}{path}", headers=self._headers,
                             params=params, timeout=_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error(f"GET {path} échoué : {e}")
            raise ConnectionError(f"Serveur local inaccessible : {e}") from e

    def _post(self, path, data=None):
        try:
            r = requests.post(f"{self._url}{path}", headers=self._headers,
                              json=data, timeout=_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error(f"POST {path} échoué : {e}")
            raise ConnectionError(f"Serveur local inaccessible : {e}") from e

    def _put(self, path, data=None):
        try:
            r = requests.put(f"{self._url}{path}", headers=self._headers,
                             json=data, timeout=_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.error(f"PUT {path} échoué : {e}")
            raise ConnectionError(f"Serveur local inaccessible : {e}") from e

    def ping(self) -> bool:
        try:
            r = requests.get(f"{self._url}/ping", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    # ── Interface database.py ─────────────────────────────────────────────────

    def fetch_all(self, query: str, params=()):
        """
        Pour les requêtes simples de type SELECT * FROM produits / ventes,
        traduit vers l'endpoint REST correspondant.
        Pour les requêtes complexes, lève NotImplementedError.
        """
        q = query.strip().lower()
        if 'from produits' in q and 'where' not in q:
            return _rows(self._get('/produits'))
        if 'from ventes' in q and 'where' not in q:
            return _rows(self._get('/ventes'))
        if 'from utilisateurs' in q:
            return _rows(self._get('/utilisateurs'))
        raise NotImplementedError(
            f"Requête SQL directe non supportée en mode client réseau: {query[:60]}"
        )

    def fetch_one(self, query: str, params=()):
        q = query.strip().lower()
        if 'from produits' in q and 'code_barre' in q and params:
            result = self._get(f'/produits/{params[0]}')
            return _FakeRow(result) if result else None
        rows = self.fetch_all(query, params)
        return rows[0] if rows else None

    def execute_query(self, query: str, params=()):
        """Traduit les INSERT de ventes vers POST /ventes."""
        q = query.strip().lower()
        if q.startswith('insert into ventes'):
            raise NotImplementedError(
                "Utilisez enregistrer_vente() directement pour les ventes en mode réseau."
            )
        raise NotImplementedError(
            f"execute_query non supporté en mode client réseau: {query[:60]}"
        )

    def get_parametre(self, cle: str, defaut: str = "") -> str:
        try:
            result = self._get(f'/parametres/{cle}')
            return result.get('valeur', defaut)
        except Exception:
            return defaut

    def set_parametre(self, cle: str, valeur: str):
        try:
            self._post(f'/parametres/{cle}', {'valeur': valeur})
        except Exception as e:
            logger.warning(f"set_parametre({cle}) échoué en mode réseau: {e}")

    # ── Méthodes métier spécifiques réseau ────────────────────────────────────

    def get_utilisateurs(self):
        return _rows(self._get('/utilisateurs'))

    def login(self, email: str, mot_de_passe: str):
        """Authentifie via le serveur. Retourne le dict utilisateur ou None (mauvais identifiants).
        Lève ConnectionError si le serveur est inaccessible."""
        try:
            r = requests.post(
                f"{self._url}/login",
                headers=self._headers,
                json={'email': email, 'mot_de_passe': mot_de_passe},
                timeout=_TIMEOUT
            )
            if r.status_code == 200:
                data = r.json()
                if data.get('succes'):
                    return data.get('utilisateur')
            return None  # 401 = mauvais identifiants
        except requests.RequestException as e:
            logger.error(f"login réseau échoué : {e}")
            raise ConnectionError(f"Serveur inaccessible : {e}") from e

    def get_produits(self):
        return _rows(self._get('/produits'))

    def get_produit_par_code(self, code_barre: str):
        try:
            result = self._get(f'/produits/{code_barre}')
            return _FakeRow(result)
        except Exception:
            return None

    def enregistrer_vente(self, data: dict) -> int:
        result = self._post('/ventes', data)
        return result.get('vente_id')

    def get_stats_dashboard(self) -> dict:
        return self._get('/stats/dashboard')

    def get_stock_alertes(self):
        return _rows(self._get('/stock/alertes'))
