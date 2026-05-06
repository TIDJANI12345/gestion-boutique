"""
Confirmation de vente — écran rapide pour le caissier.
"""
import os

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QUrl
from PySide6.QtGui import QFont, QDesktopServices

from ui.theme import Theme


def _supprimer_fichier(chemin: str):
    try:
        if os.path.exists(chemin):
            os.remove(chemin)
    except Exception:
        pass


class ConfirmationVenteWindow(QDialog):
    """Dialogue de confirmation rapide après vente."""

    nouvelle_vente = Signal()

    def __init__(self, vente_info: dict, chemin_recu: str = "", parent=None):
        super().__init__(parent)
        self.vente_info = vente_info
        self.chemin_recu = chemin_recu
        self.setWindowTitle("Vente enregistrée !")
        self.setFixedSize(420, 320)
        self.setModal(True)
        self._setup_ui()
        self._auto_imprimer_ticket()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tête vert
        header = QFrame()
        header.setFixedHeight(140)
        header.setStyleSheet(f"background-color: {Theme.c('success')};")
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignCenter)

        check = QLabel("✓")
        check.setFixedSize(60, 60)
        check.setAlignment(Qt.AlignCenter)
        check.setFont(QFont("Segoe UI", 28, QFont.Bold))
        check.setStyleSheet(
            f"background-color: white; color: {Theme.c('success')}; border-radius: 30px;"
        )
        h_layout.addWidget(check, 0, Qt.AlignCenter)

        lbl_ok = QLabel("Vente enregistrée !")
        lbl_ok.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl_ok.setStyleSheet("color: white; background: transparent;")
        lbl_ok.setAlignment(Qt.AlignCenter)
        h_layout.addWidget(lbl_ok)

        layout.addWidget(header)

        # Corps
        body = QFrame()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(30, 20, 30, 20)
        body_layout.setSpacing(12)

        from modules.fiscalite import get_devise
        devise = get_devise()

        lbl_total = QLabel(f"{self.vente_info['total']:,.0f} {devise}")
        lbl_total.setFont(QFont("Segoe UI", 30, QFont.Bold))
        lbl_total.setStyleSheet(f"color: {Theme.c('success')};")
        lbl_total.setAlignment(Qt.AlignCenter)
        body_layout.addWidget(lbl_total)

        lbl_num = QLabel(f"N° {self.vente_info['numero']}")
        lbl_num.setFont(QFont("Segoe UI", 10))
        lbl_num.setStyleSheet(f"color: {Theme.c('text_secondary')};")
        lbl_num.setAlignment(Qt.AlignCenter)
        body_layout.addWidget(lbl_num)

        body_layout.addStretch()

        # Boutons
        btn_row = QHBoxLayout()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setMinimumHeight(44)
        btn_fermer.setFont(QFont("Segoe UI", 11))
        btn_fermer.clicked.connect(self.reject)
        btn_row.addWidget(btn_fermer)

        btn_nouvelle = QPushButton("Nouvelle vente →")
        btn_nouvelle.setMinimumHeight(44)
        btn_nouvelle.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_nouvelle.setStyleSheet(
            f"background: {Theme.c('success')}; color: white; border: none; border-radius: 6px;"
        )
        btn_nouvelle.setCursor(Qt.PointingHandCursor)
        btn_nouvelle.clicked.connect(self._nouvelle_vente)
        btn_row.addWidget(btn_nouvelle)

        body_layout.addLayout(btn_row)
        layout.addWidget(body, 1)

        # Focus sur "Nouvelle vente" pour appui Entrée
        btn_nouvelle.setDefault(True)
        btn_nouvelle.setFocus()

    def _auto_imprimer_ticket(self):
        """Imprimer le ticket thermique automatiquement si la préférence est activée."""
        from database import db
        if db.get_parametre('ticket_auto_impression', '1') != '1':
            return
        vente_id = self.vente_info.get('vente_id')
        if not vente_id:
            return
        try:
            from modules.imprimante import ImprimanteThermique
            if ImprimanteThermique.est_disponible():
                ImprimanteThermique.imprimer_recu(vente_id)
        except Exception:
            pass

    def _nouvelle_vente(self):
        self.nouvelle_vente.emit()
        self.accept()
