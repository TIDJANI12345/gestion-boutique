"""
Configuration du logiciel de gestion de boutique - Version 2.0
Design inspiré de l'interface PHP moderne
"""
import os
import sys

# ✅ CORRECTION : Utiliser AppData pour données utilisateur
if getattr(sys, 'frozen', False):
    # Mode .exe - Données dans AppData
    APPDATA = os.getenv('APPDATA') or os.path.expanduser('~')
    BASE_DIR = os.path.join(APPDATA, 'GestionBoutique')
else:
    # Mode dev - Dossier projet
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Chemins des dossiers de données
DATA_DIR = os.path.join(BASE_DIR, 'data')
IMAGES_DIR = os.path.join(BASE_DIR, 'images')
RECUS_DIR = os.path.join(BASE_DIR, 'recus')
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
DB_PATH = os.path.join(DATA_DIR, 'boutique.db')

# ✅ Créer les dossiers avec gestion d'erreur
for directory in [DATA_DIR, IMAGES_DIR, RECUS_DIR, EXPORTS_DIR]:
    try:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    except Exception as e:
        print(f"⚠️ Impossible de créer {directory}: {e}")

# Configuration de l'application
APP_NAME = "Gestion Boutique"
APP_VERSION = "2.0.0"

# Configuration de l'interface
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800

# Couleurs (compatibilité avec l'ancienne version)
BG_COLOR = "#F9FAFB"
PRIMARY_COLOR = "#3B82F6"
SUCCESS_COLOR = "#10B981"
DANGER_COLOR = "#EF4444"
WARNING_COLOR = "#F59E0B"

# Palette de couleurs complète
COLORS = {
    'primary': '#3B82F6',
    'success': '#10B981',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'info': '#06B6D4',
    'purple': '#8B5CF6',
    'gray': '#6B7280',
    'dark': '#1F2937',
    'light': '#F3F4F6',
    'white': '#FFFFFF',
    'bg': '#F9FAFB',
    'text': '#1F2937',
}

# Configuration des codes-barres
BARCODE_TYPES = {
    'code128': 'Code 128 (recommandé)',
}
BARCODE_DEFAULT = 'code128'
BARCODE_FORMAT = 'code128'
BARCODE_DPI = 300

# Configuration de la boutique
BOUTIQUE_NOM = "Ma Boutique"
BOUTIQUE_ADRESSE = "Cotonou, Bénin"
BOUTIQUE_TELEPHONE = "+229 XX XX XX XX"
BOUTIQUE_EMAIL = "contact@maboutique.bj"

# Configuration du stock
STOCK_ALERTE_SEUIL = 5

# Configuration WhatsApp
WHATSAPP_EMOJI_STYLES = {
    'classic': {
        'product': '▫️',
        'price': '💰',
        'stock': '✅',
        'category': '📂',
    },
    'modern': {
        'product': '🔥',
        'price': '💵',
        'stock': '📦',
        'category': '🎯',
    },
    'professional': {
        'product': '•',
        'price': '💲',
        'stock': '✓',
        'category': '📋',
    }
}

# Préfixe pour génération de codes-barres
BARCODE_PREFIX = "PRD"

# Configuration de la synchronisation cloud
SYNC_SERVER_URL = "https://gbserver.pythonanywhere.com"
SYNC_INTERVAL = 300  # 5 minutes