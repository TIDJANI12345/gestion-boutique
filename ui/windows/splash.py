"""
Splash screen - PySide6
"""
import os
from PySide6.QtWidgets import QSplashScreen, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor

from config import APP_NAME, APP_VERSION
from ui.theme import Theme


class SplashScreen(QSplashScreen):
    """Ecran de demarrage avec barre de progression."""

    def __init__(self, duree: int = 2500):
        # Creer le pixmap de fond
        pixmap = QPixmap(500, 300)
        pixmap.fill(QColor(Theme.c('primary')))
        super().__init__(pixmap)

        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self._duree = duree
        self._progress = 0
        self._messages = [
            (0, "Initialisation..."),
            (30, "Chargement des modules..."),
            (60, "Preparation de l'interface..."),
            (90, "Presque pret..."),
        ]

        # Timer pour animation
        self._timer = QTimer(self)
        self._timer.setInterval(25)
        self._timer.timeout.connect(self._tick)

    def show(self):
        super().show()
        self._timer.start()
        # Fermer apres la duree
        QTimer.singleShot(self._duree, self.close)

    def _tick(self):
        self._progress = min(100, self._progress + 1)
        self.repaint()

    def drawContents(self, painter: QPainter):
        """Dessine le contenu du splash screen."""
        w = self.width()
        h = self.height()
        primary = QColor(Theme.c('primary'))

        # Fond
        painter.fillRect(0, 0, w, h, primary)

        # Titre
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(0, 60, w, 50, Qt.AlignCenter, APP_NAME.upper())

        # Version
        painter.setFont(QFont("Segoe UI", 12))
        painter.drawText(0, 110, w, 30, Qt.AlignCenter, f"Version {APP_VERSION}")

        # Message de chargement
        message = "Chargement..."
        for seuil, msg in self._messages:
            if self._progress >= seuil:
                message = msg
        painter.setFont(QFont("Segoe UI", 10))
        painter.drawText(0, 180, w, 30, Qt.AlignCenter, message)

        # Barre de progression
        bar_x = 100
        bar_y = 215
        bar_w = 300
        bar_h = 6

        # Fond de la barre (transparent)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(255, 255, 255, 60))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, bar_h, 3, 3)

        # Progression
        painter.setBrush(QColor("white"))
        progress_w = int(bar_w * self._progress / 100)
        if progress_w > 0:
            painter.drawRoundedRect(bar_x, bar_y, progress_w, bar_h, 3, 3)

        # Copyright
        painter.setPen(QColor(255, 255, 255, 180))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(0, h - 35, w, 20, Qt.AlignCenter,
                         "\u00a9 2026 - Tous droits reserves")
