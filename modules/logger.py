"""
Systeme de logging centralise pour Gestion Boutique
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from config import DATA_DIR

# Dossier des logs
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOGS_DIR, 'app.log')

# Format commun
_formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Handler fichier avec rotation (5 x 1 Mo)
_file_handler = RotatingFileHandler(
    LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding='utf-8'
)
_file_handler.setFormatter(_formatter)
_file_handler.setLevel(logging.DEBUG)

# Handler console (pour le dev)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_formatter)
_console_handler.setLevel(logging.INFO)


def get_logger(nom):
    """Obtenir un logger nomme avec les handlers configures"""
    logger = logging.getLogger(nom)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
    return logger
