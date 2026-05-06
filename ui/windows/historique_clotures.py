"""
Historique des clôtures Z — visualisation + réimpression.
"""
import os
import sys
import subprocess

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from modules.sessions import historique_clotures
from database import db


def _pdf_path_depuis_date(date_cloture: str) -> str:
    import config
    date_str = date_cloture.replace(':', '').replace(' ', '_')
    return os.path.join(config.RECUS_DIR, f"rapport_z_{date_str}.pdf")


def _ouvrir_fichier(chemin: str):
    if sys.platform == 'win32':
        os.startfile(chemin)
    elif sys.platform == 'darwin':
        subprocess.Popen(['open', chemin])
    else:
        subprocess.Popen(['xdg-open', chemin])


class HistoriqueCloturesWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Historique des clôtures Z")
        self.resize(900, 500)
        self._build()
        self._charger()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        titre = QLabel("Historique des clôtures Z")
        titre.setFont(QFont("Segoe UI", 13, QFont.Bold))
        layout.addWidget(titre)

        info = QLabel("Double-cliquez sur une ligne pour ouvrir le rapport PDF.")
        info.setStyleSheet("color: #6B7280; font-size: 10px;")
        layout.addWidget(info)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Date clôture", "Caisse", "Caissier", "Nb ventes", "Total", "Écart", "Hash Z"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self._table.doubleClicked.connect(self._ouvrir_pdf_selection)
        self._table.itemSelectionChanged.connect(self._on_selection)
        layout.addWidget(self._table)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #E5E7EB;")
        layout.addWidget(sep)

        btn_row = QHBoxLayout()

        self._btn_pdf = QPushButton("Ouvrir le rapport PDF")
        self._btn_pdf.setEnabled(False)
        self._btn_pdf.clicked.connect(self._ouvrir_pdf_selection)
        btn_row.addWidget(self._btn_pdf)

        self._btn_imprimer = QPushButton("Imprimer (thermique)")
        self._btn_imprimer.setEnabled(False)
        self._btn_imprimer.clicked.connect(self._imprimer_selection)
        btn_row.addWidget(self._btn_imprimer)

        self._btn_regenerer = QPushButton("Régénérer PDF")
        self._btn_regenerer.setEnabled(False)
        self._btn_regenerer.setToolTip("Recrée le PDF si le fichier est manquant")
        self._btn_regenerer.clicked.connect(self._regenerer_pdf)
        btn_row.addWidget(self._btn_regenerer)

        btn_row.addStretch()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.clicked.connect(self.accept)
        btn_row.addWidget(btn_fermer)

        layout.addLayout(btn_row)

    def _charger(self):
        try:
            from modules.fiscalite import get_devise
            devise = get_devise()
        except Exception:
            devise = 'FCFA'

        self._clotures = historique_clotures(50)
        self._table.setRowCount(len(self._clotures))

        for i, c in enumerate(self._clotures):
            date_str = c.get('date_cloture', '')
            self._table.setItem(i, 0, QTableWidgetItem(date_str[:16]))
            self._table.setItem(i, 1, QTableWidgetItem(c.get('id_caisse', '')))
            self._table.setItem(i, 2, QTableWidgetItem(c.get('caissier_nom', '') or '—'))
            self._table.setItem(i, 3, QTableWidgetItem(str(c.get('nb_ventes', 0))))
            self._table.setItem(i, 4, QTableWidgetItem(f"{c.get('total_general', 0):,} {devise}"))

            ecart = c.get('ecart', 0)
            item_ecart = QTableWidgetItem(f"{ecart:+,} {devise}")
            item_ecart.setForeground(QColor('#10B981' if ecart == 0 else '#EF4444'))
            self._table.setItem(i, 5, item_ecart)

            hash_z = c.get('hash_cloture', '')
            self._table.setItem(i, 6, QTableWidgetItem(hash_z[:12] + '…' if len(hash_z) > 12 else hash_z))

            # Indiquer si le PDF existe
            pdf = _pdf_path_depuis_date(date_str)
            if not os.path.exists(pdf):
                for col in range(7):
                    item = self._table.item(i, col)
                    if item:
                        item.setForeground(QColor('#9CA3AF'))

        if self._clotures:
            self._table.selectRow(0)

    def _on_selection(self):
        row = self._table.currentRow()
        has = row >= 0
        self._btn_pdf.setEnabled(has)
        self._btn_imprimer.setEnabled(has)
        self._btn_regenerer.setEnabled(has)

    def _cloture_selectionnee(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._clotures):
            return None
        return self._clotures[row]

    def _ouvrir_pdf_selection(self):
        c = self._cloture_selectionnee()
        if not c:
            return
        pdf = _pdf_path_depuis_date(c.get('date_cloture', ''))
        if not os.path.exists(pdf):
            rep = QMessageBox.question(
                self, "PDF introuvable",
                "Le fichier PDF n'existe pas. Le régénérer maintenant ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if rep == QMessageBox.Yes:
                self._regenerer_pdf()
            return
        try:
            _ouvrir_fichier(pdf)
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible d'ouvrir le PDF : {e}")

    def _imprimer_selection(self):
        c = self._cloture_selectionnee()
        if not c:
            return
        try:
            from modules.imprimante import ImprimanteThermique
            if not ImprimanteThermique.est_disponible():
                QMessageBox.information(self, "Imprimante",
                    "Aucune imprimante thermique configurée.")
                return
            rapport = dict(c)
            from ui.dialogs.cloture_z import ClotureZDialog
            ClotureZDialog._imprimer_rapport_z_static(rapport)
            QMessageBox.information(self, "Impression", "Rapport Z envoyé à l'imprimante.")
        except Exception as e:
            QMessageBox.warning(self, "Erreur impression", str(e))

    def _regenerer_pdf(self):
        c = self._cloture_selectionnee()
        if not c:
            return
        try:
            from ui.dialogs.cloture_z import ClotureZDialog
            pdf_path = ClotureZDialog._generer_pdf_z_static(dict(c))
            if pdf_path:
                QMessageBox.information(self, "PDF régénéré",
                    f"PDF créé :\n{pdf_path}")
                self._charger()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))
