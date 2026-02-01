"""
Fenetre de confirmation de vente - PySide6
Dialogue modal affiche apres une vente reussie.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QMessageBox, QScrollArea, QWidget
)
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QFont, QDesktopServices

from ui.theme import Theme

import os


class ConfirmationVenteWindow(QDialog):
    """Dialogue de confirmation apres une vente reussie."""

    nouvelle_vente = Signal()

    def __init__(self, vente_info: dict, chemin_recu: str, parent=None):
        super().__init__(parent)
        self.vente_info = vente_info
        self.chemin_recu = chemin_recu

        self.setWindowTitle("Vente enregistree !")
        self.setFixedSize(600, 700)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === EN-TETE VERT ===
        header = QFrame()
        header.setFixedHeight(180)
        header.setStyleSheet(f"background-color: {Theme.c('success')};")
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignCenter)

        # Cercle avec checkmark
        circle = QLabel("✓")
        circle.setFixedSize(70, 70)
        circle.setAlignment(Qt.AlignCenter)
        circle.setFont(QFont("Segoe UI", 32, QFont.Bold))
        circle.setStyleSheet(
            f"background-color: white; color: {Theme.c('success')}; "
            f"border-radius: 35px;"
        )
        header_layout.addWidget(circle, 0, Qt.AlignCenter)

        lbl_titre = QLabel("Vente enregistree !")
        lbl_titre.setFont(QFont("Segoe UI", 22, QFont.Bold))
        lbl_titre.setStyleSheet("color: white; background: transparent;")
        lbl_titre.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(lbl_titre)

        lbl_numero = QLabel(f"Recu N° {self.vente_info['numero']}")
        lbl_numero.setFont(QFont("Segoe UI", 13))
        lbl_numero.setStyleSheet("color: white; background: transparent;")
        lbl_numero.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(lbl_numero)

        layout.addWidget(header)

        # === CONTENU ===
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(40, 30, 40, 20)
        content_layout.setSpacing(0)

        # Carte info (date + total + client)
        info_frame = QFrame()
        info_frame.setStyleSheet(
            f"background-color: {Theme.c('light')}; border-radius: 8px;"
        )
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setAlignment(Qt.AlignCenter)

        lbl_date = QLabel(self.vente_info['date'])
        lbl_date.setFont(QFont("Segoe UI", 11))
        lbl_date.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(lbl_date)

        lbl_total = QLabel(f"{self.vente_info['total']:,.0f} FCFA")
        lbl_total.setFont(QFont("Segoe UI", 32, QFont.Bold))
        lbl_total.setStyleSheet(f"color: {Theme.c('success')};")
        lbl_total.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(lbl_total)

        if self.vente_info.get('client'):
            lbl_client = QLabel(self.vente_info['client'])
            lbl_client.setFont(QFont("Segoe UI", 10))
            lbl_client.setStyleSheet(f"color: {Theme.c('gray')};")
            lbl_client.setAlignment(Qt.AlignCenter)
            info_layout.addWidget(lbl_client)

        content_layout.addWidget(info_frame)
        content_layout.addSpacing(15)

        # Resume articles
        nb_articles = sum(item['quantite'] for item in self.vente_info['items'])
        nb_lignes = len(self.vente_info['items'])
        lbl_articles = QLabel(
            f"{nb_articles} article{'s' if nb_articles > 1 else ''} "
            f"({nb_lignes} ligne{'s' if nb_lignes > 1 else ''})"
        )
        lbl_articles.setFont(QFont("Segoe UI", 11))
        lbl_articles.setStyleSheet(f"color: {Theme.c('gray')};")
        lbl_articles.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(lbl_articles)
        content_layout.addSpacing(20)

        # === BOUTONS D'ACTION ===
        buttons = [
            ("Ouvrir le recu PDF", 'danger', self._ouvrir_pdf),
            ("Imprimer PDF", 'primary', self._imprimer),
            ("Imprimer ticket", 'warning', self._imprimer_ticket),
            ("Nouvelle vente", 'success', self._nouvelle_vente),
        ]

        for text, color_key, slot in buttons:
            btn = QPushButton(text)
            btn.setFont(QFont("Segoe UI", 13, QFont.Bold))
            btn.setMinimumHeight(50)
            btn.setCursor(Qt.PointingHandCursor)
            couleur = Theme.c(color_key)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {couleur};
                    color: white; border: none; border-radius: 6px;
                }}
                QPushButton:hover {{
                    background-color: {_darken(couleur)};
                }}
            """)
            btn.clicked.connect(slot)
            content_layout.addWidget(btn)
            content_layout.addSpacing(8)

        content_layout.addSpacing(8)

        # Lien retour dashboard
        link = QLabel("← Retour au tableau de bord")
        link.setFont(QFont("Segoe UI", 11))
        link.setStyleSheet(
            f"color: {Theme.c('primary')}; text-decoration: underline;"
        )
        link.setCursor(Qt.PointingHandCursor)
        link.setAlignment(Qt.AlignCenter)
        link.mousePressEvent = lambda e: self.reject()
        content_layout.addWidget(link)

        content_layout.addSpacing(12)

        # Lien voir details
        lbl_details = QLabel("Voir les details")
        lbl_details.setFont(QFont("Segoe UI", 9))
        lbl_details.setStyleSheet(f"color: {Theme.c('gray')};")
        lbl_details.setCursor(Qt.PointingHandCursor)
        lbl_details.setAlignment(Qt.AlignCenter)
        lbl_details.mousePressEvent = lambda e: self._afficher_details()
        content_layout.addWidget(lbl_details)

        content_layout.addStretch()
        layout.addWidget(content, 1)

    def _ouvrir_pdf(self):
        """Ouvrir le PDF avec l'application par defaut du systeme."""
        if self.chemin_recu and os.path.exists(self.chemin_recu):
            url = QUrl.fromLocalFile(self.chemin_recu)
            if not QDesktopServices.openUrl(url):
                QMessageBox.critical(self, "Erreur", "Impossible d'ouvrir le PDF")
        else:
            QMessageBox.critical(self, "Erreur", "Fichier PDF introuvable")

    def _imprimer(self):
        """Ouvrir le PDF pour impression manuelle."""
        self._ouvrir_pdf()
        QMessageBox.information(
            self, "Impression",
            "Le PDF s'est ouvert.\nUtilisez Ctrl+P pour imprimer."
        )

    def _imprimer_ticket(self):
        """Imprimer sur imprimante thermique."""
        vente_id = self.vente_info.get('vente_id')
        if not vente_id:
            QMessageBox.critical(self, "Erreur", "ID de vente non disponible")
            return

        from modules.imprimante import ImprimanteThermique

        if not ImprimanteThermique.est_disponible():
            QMessageBox.warning(
                self, "Imprimante",
                "L'impression thermique n'est pas disponible.\n\n"
                "Verifiez que python-escpos est installe\n"
                "et que l'imprimante est configuree."
            )
            return

        succes, message = ImprimanteThermique.imprimer_recu(vente_id)
        if succes:
            QMessageBox.information(self, "Impression", "Ticket imprime avec succes!")
        else:
            QMessageBox.critical(self, "Erreur", f"Echec de l'impression:\n{message}")

    def _nouvelle_vente(self):
        """Emettre le signal et fermer."""
        self.nouvelle_vente.emit()
        self.accept()

    def _afficher_details(self):
        """Afficher les details de la vente dans un sous-dialogue."""
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Details - {self.vente_info['numero']}")
        dlg.setFixedSize(500, 400)
        dlg.setModal(True)

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(0, 0, 0, 0)

        # Titre
        titre = QLabel(f"Details - {self.vente_info['numero']}")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        titre.setAlignment(Qt.AlignCenter)
        titre.setContentsMargins(0, 20, 0, 15)
        layout.addWidget(titre)

        # Zone scrollable
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(20, 0, 20, 20)
        scroll_layout.setSpacing(8)

        for item in self.vente_info['items']:
            item_frame = QFrame()
            item_frame.setStyleSheet(
                f"background-color: {Theme.c('light')}; border-radius: 6px;"
            )
            item_layout = QVBoxLayout(item_frame)
            item_layout.setContentsMargins(15, 12, 15, 12)

            lbl_nom = QLabel(item['nom'])
            lbl_nom.setFont(QFont("Segoe UI", 11, QFont.Bold))
            item_layout.addWidget(lbl_nom)

            lbl_detail = QLabel(
                f"{item['quantite']} x {item['prix_vente']:,.0f} F = "
                f"{item['sous_total']:,.0f} F"
            )
            lbl_detail.setFont(QFont("Segoe UI", 10))
            lbl_detail.setStyleSheet(f"color: {Theme.c('gray')};")
            item_layout.addWidget(lbl_detail)

            scroll_layout.addWidget(item_frame)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        dlg.exec()


def _darken(hex_color: str) -> str:
    """Assombrir une couleur hex."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f'#{max(0,r-25):02x}{max(0,g-25):02x}{max(0,b-25):02x}'
