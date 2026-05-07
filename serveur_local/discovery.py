"""
Découverte automatique du serveur local via UDP broadcast.
Le serveur diffuse sa présence toutes les 5 secondes sur le réseau local.
Les clients écoutent et trouvent le serveur sans saisir l'IP manuellement.
"""
import socket
import json
import threading
import time
from modules.logger import get_logger

logger = get_logger('discovery')

DISCOVERY_PORT = 5051
BROADCAST_INTERVAL = 5  # secondes
DISCOVERY_MAGIC = 'HISHIPOS_DISCOVERY_V1'


def demarrer_broadcaster(serveur_nom: str, api_port: int, token: str):
    """Diffuse la présence du serveur sur le réseau local (UDP broadcast)."""
    payload = json.dumps({
        'magic': DISCOVERY_MAGIC,
        'nom': serveur_nom,
        'port': api_port,
        'token': token,
    }).encode('utf-8')

    def _broadcast():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        logger.info(f"Broadcaster UDP démarré sur port {DISCOVERY_PORT}")
        while True:
            try:
                sock.sendto(payload, ('<broadcast>', DISCOVERY_PORT))
            except Exception as e:
                logger.warning(f"Broadcast échoué : {e}")
            time.sleep(BROADCAST_INTERVAL)

    t = threading.Thread(target=_broadcast, daemon=True)
    t.start()


def chercher_serveur(timeout: float = 6.0) -> dict | None:
    """
    Écoute le réseau local et retourne les infos du premier serveur trouvé.
    Retourne None si aucun serveur détecté dans le délai.
    Format retourné : {'ip': '192.168.x.x', 'port': 5050, 'nom': '...', 'token': '...'}
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(timeout)
    try:
        sock.bind(('', DISCOVERY_PORT))
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                info = json.loads(data.decode('utf-8'))
                if info.get('magic') == DISCOVERY_MAGIC:
                    return {
                        'ip': addr[0],
                        'port': info.get('port', 5050),
                        'nom': info.get('nom', 'Serveur'),
                        'token': info.get('token', ''),
                    }
            except socket.timeout:
                return None
            except Exception:
                continue
    except OSError as e:
        logger.warning(f"Impossible d'écouter le port {DISCOVERY_PORT} : {e}")
        return None
    finally:
        sock.close()
