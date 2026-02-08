"""
Configuration du logiciel de gestion de boutique - Version 2.0
Multiplateforme : Windows, Linux, macOS
"""
import os
import sys
import platform

# ===== VERSION DE L'APPLICATION =====
# Format: MAJEUR.MINEUR.PATCH (Semantic Versioning)
# À incrémenter à chaque release
APP_VERSION = "2.0.0"
APP_NAME = "Gestion Boutique"

# Forcer UTF-8 sur stdout/stderr (necessaire uniquement sur Windows cp1252)
if platform.system() == 'Windows' and sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def _get_base_dir() -> str:
    """Retourne le dossier de donnees selon l'OS et le mode d'execution."""
    if not getattr(sys, 'frozen', False):
        # Mode dev - dossier projet
        return os.path.dirname(os.path.abspath(__file__))

    # Mode compile (PyInstaller)
    systeme = platform.system()
    if systeme == 'Windows':
        base = os.getenv('APPDATA', os.path.expanduser('~'))
    elif systeme == 'Darwin':  # macOS
        base = os.path.join(os.path.expanduser('~'), 'Library',
                            'Application Support')
    else:  # Linux et autres
        base = os.environ.get(
            'XDG_DATA_HOME',
            os.path.join(os.path.expanduser('~'), '.local', 'share')
        )
    return os.path.join(base, 'GestionBoutique')


BASE_DIR = _get_base_dir()

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
        # Logger pas encore disponible (depend de DATA_DIR), utiliser logging directement
        import logging
        logging.warning(f"Impossible de creer {directory}: {e}")

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

# Themes
THEME_CLAIR = {
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
    'card_bg': '#FFFFFF',
    'card_border': '#E5E7EB',
    'input_bg': '#FFFFFF',
    'input_fg': '#1F2937',
    'separator': '#E5E7EB',
}

THEME_SOMBRE = {
    'primary': '#3B82F6',
    'success': '#10B981',
    'danger': '#EF4444',
    'warning': '#F59E0B',
    'info': '#06B6D4',
    'purple': '#8B5CF6',
    'gray': '#9CA3AF',
    'dark': '#F9FAFB',
    'light': '#374151',
    'white': '#1F2937',
    'bg': '#111827',
    'text': '#F9FAFB',
    'card_bg': '#1F2937',
    'card_border': '#374151',
    'input_bg': '#374151',
    'input_fg': '#F9FAFB',
    'separator': '#374151',
}

# Palette active (mise a jour par ThemeManager au demarrage)
COLORS = dict(THEME_CLAIR)

# Raccourcis clavier
RACCOURCIS_CLAVIER = {
    'nouvelle_vente': '<F1>',
    'rechercher_produit': '<F2>',
    'liste_ventes': '<F3>',
    'rapports': '<F4>',
    'actualiser': '<F5>',
    'export_whatsapp': '<F6>',
    'clients': '<F7>',
}

# Pagination
PAGINATION = {
    'produits_par_page': 50,
    'ventes_par_page': 50,
    'clients_par_page': 50,
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

# Configuration des sauvegardes
BACKUP_DIR = os.path.join(BASE_DIR, 'sauvegardes')
BACKUP_MAX_COUNT = 10  # Nombre max de sauvegardes locales

# Configuration imprimante thermique
IMPRIMANTE_LARGEURS = {
    '58mm': 32,
    '80mm': 48,
}

# Configuration fiscale par defaut
TVA_TAUX_DEFAUT = 18  # % - Standard Benin
DEVISE_DEFAUT_CODE = 'XOF'
DEVISE_DEFAUT_SYMBOLE = 'FCFA'