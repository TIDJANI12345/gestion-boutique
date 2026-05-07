"""
Singleton du client réseau. Initialisé dans main.py si mode='client'.
Les modules métier consultent actif() avant d'appeler get_client().
"""
from modules.logger import get_logger

logger = get_logger('reseau')

_client = None  # ClientReseau | None


def actif() -> bool:
    return _client is not None


def get_client():
    """Retourne le ClientReseau actif. Lève RuntimeError si non initialisé."""
    if _client is None:
        raise RuntimeError("Client réseau non initialisé")
    return _client


def initialiser(url: str, token: str, machine_id: str, nom_caisse: str) -> bool:
    """
    Crée et enregistre le client réseau. Appelle /connect sur le serveur.
    Retourne True si connecté et autorisé, False sinon.
    """
    global _client
    try:
        from modules.client_reseau import ClientReseau
        client = ClientReseau(url, token)

        if not client.ping():
            logger.error(f"Serveur local inaccessible : {url}")
            return False

        # S'enregistrer auprès du serveur (vérification quota)
        import requests
        r = requests.post(
            f"{url}/connect",
            json={'machine_id': machine_id, 'nom': nom_caisse},
            headers={'X-Local-Token': token, 'X-Machine-Id': machine_id},
            timeout=5
        )
        if r.status_code == 403:
            data = r.json()
            logger.error(f"Connexion refusée : {data.get('error', '')}")
            return False
        if r.status_code != 200:
            logger.error(f"Erreur /connect : HTTP {r.status_code}")
            return False

        info = r.json()
        plan = info.get('plan', 'standard')
        logger.info(
            f"Connecté au serveur {url} "
            f"({info.get('terminaux_connectes', '?')}/{info.get('terminaux_max', '?')} terminaux, "
            f"plan {plan})"
        )
        # Stocker le plan du serveur localement pour que features.plan_actuel() soit correct
        try:
            from database import db as _db
            _db.set_parametre('licence_plan_enc', f'__reseau_{plan}__')
        except Exception:
            pass
        _client = client
        return True

    except Exception as e:
        logger.error(f"Impossible d'initialiser le client réseau : {e}")
        return False


def deconnecter(machine_id: str):
    """Notifie le serveur de la déconnexion."""
    global _client
    if _client is None:
        return
    try:
        _client._post('/deconnecter', {'machine_id': machine_id})
    except Exception:
        pass
    _client = None
