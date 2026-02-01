"""
Detection de la plateforme et chemins specifiques par OS.
Centralise tout ce qui est specifique a Windows, Linux ou macOS.
"""
import os
import sys
import platform

APP_ID = "GestionBoutique"


def get_system() -> str:
    """Retourne 'Windows', 'Linux' ou 'Darwin' (macOS)."""
    return platform.system()


def is_frozen() -> bool:
    """Retourne True si l'application est executee en mode compile (PyInstaller)."""
    return getattr(sys, 'frozen', False)


def get_base_dir() -> str:
    """Retourne le dossier de donnees de l'application selon l'OS.

    Mode dev  : dossier du projet (racine ou le script main est)
    Mode .exe : dossier standard de l'OS

    Windows : %APPDATA%/GestionBoutique/
    Linux   : ~/.local/share/GestionBoutique/
    macOS   : ~/Library/Application Support/GestionBoutique/
    """
    if not is_frozen():
        # Mode dev : dossier du projet
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    systeme = get_system()
    if systeme == 'Windows':
        base = os.getenv('APPDATA', os.path.expanduser('~'))
    elif systeme == 'Darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library',
                            'Application Support')
    else:
        # Linux et autres Unix
        base = os.environ.get(
            'XDG_DATA_HOME',
            os.path.join(os.path.expanduser('~'), '.local', 'share')
        )
    return os.path.join(base, APP_ID)


def get_config_dir() -> str:
    """Retourne le dossier de configuration selon l'OS.

    Windows : %APPDATA%/GestionBoutique/  (meme que data)
    Linux   : ~/.config/GestionBoutique/
    macOS   : ~/Library/Application Support/GestionBoutique/
    """
    if not is_frozen():
        return get_base_dir()

    systeme = get_system()
    if systeme == 'Windows':
        base = os.getenv('APPDATA', os.path.expanduser('~'))
    elif systeme == 'Darwin':
        base = os.path.join(os.path.expanduser('~'), 'Library',
                            'Application Support')
    else:
        base = os.environ.get(
            'XDG_CONFIG_HOME',
            os.path.join(os.path.expanduser('~'), '.config')
        )
    return os.path.join(base, APP_ID)


def get_log_dir() -> str:
    """Retourne le dossier de logs selon l'OS."""
    if not is_frozen():
        return os.path.join(get_base_dir(), 'data', 'logs')

    systeme = get_system()
    if systeme == 'Windows':
        return os.path.join(get_base_dir(), 'data', 'logs')
    elif systeme == 'Darwin':
        return os.path.join(os.path.expanduser('~'), 'Library', 'Logs',
                            APP_ID)
    else:
        base = os.environ.get(
            'XDG_STATE_HOME',
            os.path.join(os.path.expanduser('~'), '.local', 'state')
        )
        return os.path.join(base, APP_ID, 'logs')


def get_serial_ports() -> list[str]:
    """Retourne les noms de ports serie typiques selon l'OS."""
    systeme = get_system()
    if systeme == 'Windows':
        return [f'COM{i}' for i in range(1, 10)]
    elif systeme == 'Darwin':
        return ['/dev/tty.usbserial', '/dev/tty.usbmodem']
    else:
        return ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']


def fix_encoding():
    """Corrige l'encodage stdout/stderr sur Windows (cp1252 → utf-8)."""
    if get_system() != 'Windows':
        return
    if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


def ensure_directories(base_dir: str):
    """Cree les dossiers necessaires a l'application."""
    dirs = [
        os.path.join(base_dir, 'data'),
        os.path.join(base_dir, 'data', 'logs'),
        os.path.join(base_dir, 'images'),
        os.path.join(base_dir, 'recus'),
        os.path.join(base_dir, 'exports'),
        os.path.join(base_dir, 'sauvegardes'),
    ]
    for d in dirs:
        try:
            os.makedirs(d, exist_ok=True)
        except OSError:
            pass
