"""
Serveur WebSocket pour scanner mobile
Reçoit les codes-barres depuis l'app web mobile
"""
import asyncio
import json
from typing import Set
from PySide6.QtCore import QThread, Signal
from modules.logger import get_logger

logger = get_logger('scanner_mobile')

try:
    import websockets
    from websockets.server import serve
    WEBSOCKETS_DISPONIBLE = True
except ImportError:
    WEBSOCKETS_DISPONIBLE = False
    logger.warning("websockets non installé - Scanner mobile indisponible")


class ScannerMobileServer(QThread):
    """Serveur WebSocket pour recevoir codes-barres depuis mobile"""

    code_recu = Signal(str)  # Signal émis quand un code est scanné
    client_connecte = Signal(str)  # Signal émis quand un client se connecte (IP)
    client_deconnecte = Signal(str)  # Signal émis quand un client se déconnecte
    erreur = Signal(str)  # Signal en cas d'erreur

    def __init__(self, host='0.0.0.0', port=8765):
        super().__init__()
        self.host = host
        self.port = port
        self.clients: Set = set()
        self.running = False
        self.server = None
        self.loop = None

    def run(self):
        """Démarrer le serveur WebSocket dans le thread"""
        if not WEBSOCKETS_DISPONIBLE:
            self.erreur.emit("websockets non installé. Installez-le avec : pip install websockets")
            return

        self.running = True
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            logger.info(f"Démarrage serveur WebSocket sur {self.host}:{self.port}")
            self.loop.run_until_complete(self._start_server())
        except Exception as e:
            logger.error(f"Erreur serveur WebSocket : {e}")
            self.erreur.emit(f"Erreur serveur : {e}")

    async def _start_server(self):
        """Démarrer le serveur async"""
        try:
            async with serve(self._handle_client, self.host, self.port):
                logger.info("Serveur WebSocket démarré")
                # Garder le serveur actif
                while self.running:
                    await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Erreur démarrage serveur : {e}")
            self.erreur.emit(str(e))

    async def _handle_client(self, websocket, path):
        """Gérer une connexion client"""
        client_ip = websocket.remote_address[0] if websocket.remote_address else "inconnu"
        self.clients.add(websocket)
        logger.info(f"Client connecté : {client_ip}")
        self.client_connecte.emit(client_ip)

        try:
            async for message in websocket:
                await self._process_message(message, client_ip)
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client déconnecté : {client_ip}")
        except Exception as e:
            logger.error(f"Erreur client {client_ip} : {e}")
        finally:
            self.clients.discard(websocket)
            self.client_deconnecte.emit(client_ip)

    async def _process_message(self, message: str, client_ip: str):
        """Traiter un message reçu"""
        try:
            data = json.loads(message)
            msg_type = data.get('type')

            if msg_type == 'scan':
                code = data.get('code', '').strip()
                if code:
                    logger.info(f"Code reçu de {client_ip} : {code}")
                    self.code_recu.emit(code)
                else:
                    logger.warning(f"Code vide reçu de {client_ip}")

            elif msg_type == 'ping':
                # Répondre au ping
                await websocket.send(json.dumps({'type': 'pong'}))

            else:
                logger.warning(f"Type de message inconnu : {msg_type}")

        except json.JSONDecodeError:
            logger.error(f"Message JSON invalide de {client_ip} : {message}")
        except Exception as e:
            logger.error(f"Erreur traitement message : {e}")

    def arreter(self):
        """Arrêter le serveur"""
        logger.info("Arrêt du serveur WebSocket")
        self.running = False

        # Fermer toutes les connexions
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self._close_clients(), self.loop)

        # Arrêter la boucle
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)

        self.wait(2000)  # Attendre max 2s pour que le thread se termine

    async def _close_clients(self):
        """Fermer toutes les connexions clients"""
        for client in list(self.clients):
            try:
                await client.close()
            except Exception:
                pass
        self.clients.clear()

    def get_nombre_clients(self) -> int:
        """Retourner le nombre de clients connectés"""
        return len(self.clients)


def est_disponible() -> bool:
    """Vérifier si le scanner mobile est disponible"""
    return WEBSOCKETS_DISPONIBLE
