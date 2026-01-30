"""
Gestionnaire de theme sombre/clair avec persistance en base
"""
from config import THEME_CLAIR, THEME_SOMBRE, COLORS


class ThemeManager:
    _instance = None
    _current_theme = 'clair'
    _callbacks = []

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        from database import db
        saved = db.get_parametre('theme', 'clair')
        self._current_theme = saved
        self._apply_to_colors()

    def _apply_to_colors(self):
        """Mettre a jour le dict COLORS global en place"""
        source = THEME_SOMBRE if self._current_theme == 'sombre' else THEME_CLAIR
        COLORS.clear()
        COLORS.update(source)

    @property
    def est_sombre(self):
        return self._current_theme == 'sombre'

    @property
    def nom_theme(self):
        return self._current_theme

    def basculer(self):
        """Basculer entre theme clair et sombre"""
        from database import db
        self._current_theme = 'sombre' if self._current_theme == 'clair' else 'clair'
        db.set_parametre('theme', self._current_theme)
        self._apply_to_colors()
        for callback in self._callbacks:
            try:
                callback()
            except Exception:
                pass

    def enregistrer_callback(self, callback):
        """Enregistrer un callback pour notification de changement de theme"""
        self._callbacks.append(callback)

    def retirer_callback(self, callback):
        """Retirer un callback"""
        self._callbacks = [c for c in self._callbacks if c != callback]
