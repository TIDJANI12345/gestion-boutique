"""
Serveur HTTP pour servir la page web mobile du scanner
"""
import os
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler
from PySide6.QtCore import QThread, Signal
from modules.logger import get_logger

logger = get_logger('scanner_mobile_http')


class ScannerHTTPHandler(SimpleHTTPRequestHandler):
    """Handler HTTP personnalisé pour servir la page mobile"""

    def __init__(self, *args, resources_dir=None, **kwargs):
        self.resources_dir = resources_dir
        super().__init__(*args, directory=resources_dir, **kwargs)

    def do_GET(self):
        """Gérer les requêtes GET"""
        # Ignorer favicon.ico
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, format, *args):
        """Rediriger les logs vers le logger"""
        # Ignorer les logs de requêtes binaires (tentatives HTTPS)
        try:
            msg = format % args
            if msg.isprintable() or 'GET' in msg or 'POST' in msg:
                logger.info(f"{self.address_string()} - {msg}")
        except Exception:
            pass

    def end_headers(self):
        """Ajouter headers CORS et cache"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()


class ScannerMobileHTTP(QThread):
    """Serveur HTTP pour servir la page web mobile"""

    erreur = Signal(str)
    demarrage_ok = Signal(str)  # Signal avec l'URL du serveur

    def __init__(self, port=8080):
        super().__init__()
        self.port = port
        self.running = False
        self.server = None
        self.resources_dir = self._get_resources_dir()

    def _get_resources_dir(self):
        """Obtenir le dossier des ressources (compatible PyInstaller)"""
        import sys

        # 1. Mode compilé PyInstaller : sys._MEIPASS contient les fichiers bundlés
        if hasattr(sys, '_MEIPASS'):
            resources = os.path.join(sys._MEIPASS, 'ui', 'resources')
            if os.path.exists(resources):
                return resources

        # 2. Mode développement : chemin relatif au projet
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        resources = os.path.join(current_dir, 'ui', 'resources')
        if os.path.exists(resources):
            return resources

        # 3. Fallback : créer le dossier
        os.makedirs(resources, exist_ok=True)
        return resources

    def run(self):
        """Démarrer le serveur HTTP"""
        self.running = True

        try:
            # Créer le handler avec le dossier resources
            def handler(*args, **kwargs):
                return ScannerHTTPHandler(*args, resources_dir=self.resources_dir, **kwargs)

            self.server = HTTPServer(('0.0.0.0', self.port), handler)

            # Obtenir l'IP locale
            ip = self._get_local_ip()
            url = f"http://{ip}:{self.port}/scanner_mobile.html"

            logger.info(f"Serveur HTTP démarré sur {url}")
            self.demarrage_ok.emit(url)

            # Servir les requêtes
            while self.running:
                self.server.handle_request()

        except OSError as e:
            if e.errno == 48 or e.errno == 98:  # Port déjà utilisé (macOS/Linux)
                msg = f"Port {self.port} déjà utilisé"
            else:
                msg = f"Erreur serveur HTTP : {e}"
            logger.error(msg)
            self.erreur.emit(msg)
        except Exception as e:
            logger.error(f"Erreur serveur HTTP : {e}")
            self.erreur.emit(str(e))

    def _get_local_ip(self):
        """Obtenir l'IP locale du PC"""
        try:
            # Créer une socket UDP pour détecter l'IP locale
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def arreter(self):
        """Arrêter le serveur"""
        logger.info("Arrêt du serveur HTTP")
        self.running = False

        if self.server:
            self.server.shutdown()
            self.server = None

        self.wait(2000)  # Attendre max 2s

    def get_url(self):
        """Obtenir l'URL du serveur"""
        ip = self._get_local_ip()
        return f"http://{ip}:{self.port}/scanner_mobile.html"
