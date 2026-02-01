"""
Module de gestion des sons pour l'application
"""
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl
import os

# Sons disponibles
SOUND_AVAILABLE = False
try:
    # Vérifier si QtMultimedia est disponible
    from PySide6.QtMultimedia import QSoundEffect
    SOUND_AVAILABLE = True
except ImportError:
    pass


class SoundManager:
    """Gestionnaire de sons pour l'application"""

    _beep_effect = None

    @staticmethod
    def play_scan_beep():
        """Jouer un bip de scan (son système)"""
        if not SOUND_AVAILABLE:
            return

        try:
            # Utiliser winsound sur Windows (plus simple pour le beep)
            import platform
            if platform.system() == 'Windows':
                import winsound
                # Fréquence 1000Hz, durée 100ms
                winsound.Beep(1000, 100)
            else:
                # Sur Linux/Mac, utiliser le terminal bell
                print('\a', end='', flush=True)
        except Exception:
            # Fallback silencieux
            pass

    @staticmethod
    def play_scan_sound():
        """
        Jouer le son de scan selon les paramètres
        Vérifie la configuration dans la DB
        """
        from database import db

        # Vérifier si le son est activé
        son_actif = db.get_parametre('son_scan_actif', '1') == '1'
        if not son_actif:
            return

        # Type de son
        son_type = db.get_parametre('son_scan_type', 'beep')

        if son_type == 'beep':
            SoundManager.play_scan_beep()
        elif son_type == 'fichier':
            # Futur : support fichier son personnalisé
            fichier = db.get_parametre('son_scan_fichier', '')
            if fichier and os.path.exists(fichier):
                SoundManager.play_file(fichier)
            else:
                # Fallback sur beep
                SoundManager.play_scan_beep()

    @staticmethod
    def play_file(filepath: str):
        """Jouer un fichier son (WAV, MP3, etc.)"""
        if not SOUND_AVAILABLE or not os.path.exists(filepath):
            return

        try:
            if not SoundManager._beep_effect:
                SoundManager._beep_effect = QSoundEffect()

            SoundManager._beep_effect.setSource(QUrl.fromLocalFile(filepath))
            SoundManager._beep_effect.setVolume(0.5)
            SoundManager._beep_effect.play()
        except Exception:
            pass
