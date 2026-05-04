"""
Fenetre de gestion des sauvegardes - Phase 7
"""
import os
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QCheckBox, QMessageBox, QFileDialog, QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

from ui.theme import Theme


class _BackupThread(QThread):
    """Thread pour les opérations de sauvegarde longues."""
    finished = Signal(bool, str, object)  # succes, message, chemin_ou_None

    def __init__(self, operation, *args):
        super().__init__()
        self._op = operation
        self._args = args

    def run(self):
        try:
            result = self._op(*self._args)
            if len(result) == 3:
                self.finished.emit(result[0], result[1], result[2])
            else:
                self.finished.emit(result[0], result[1], None)
        except Exception as e:
            self.finished.emit(False, str(e), None)


class SauvegardeWindow(QDialog):
    """Fenetre de gestion des sauvegardes et restauration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gestion des sauvegardes")
        self.setMinimumSize(720, 520)
        self.resize(800, 580)
        self._thread = None
        self._setup_ui()
        self._charger_liste()
        self._charger_config()

    # === UI ===

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Titre
        titre = QLabel("Sauvegardes de la base de données")
        titre.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(titre)

        # Groupe liste des sauvegardes
        grp_liste = QGroupBox("Sauvegardes disponibles")
        grp_layout = QVBoxLayout(grp_liste)

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["Date", "Nom du fichier", "Taille"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.setMinimumHeight(200)
        grp_layout.addWidget(self._table)

        # Boutons liste
        btns_liste = QHBoxLayout()
        self._btn_restaurer = QPushButton("Restaurer la sélection")
        self._btn_restaurer.setEnabled(False)
        self._btn_restaurer.clicked.connect(self._restaurer)
        btns_liste.addWidget(self._btn_restaurer)

        self._btn_ouvrir_dossier = QPushButton("Ouvrir le dossier")
        self._btn_ouvrir_dossier.clicked.connect(self._ouvrir_dossier)
        btns_liste.addWidget(self._btn_ouvrir_dossier)

        btns_liste.addStretch()
        grp_layout.addLayout(btns_liste)
        layout.addWidget(grp_liste)

        self._table.selectionModel().selectionChanged.connect(
            lambda: self._btn_restaurer.setEnabled(len(self._table.selectedItems()) > 0)
        )

        # Groupe actions
        grp_actions = QGroupBox("Actions")
        grp_actions_layout = QHBoxLayout(grp_actions)

        self._btn_sauvegarder = QPushButton("  Sauvegarder maintenant")
        self._btn_sauvegarder.setMinimumHeight(40)
        self._btn_sauvegarder.setStyleSheet(
            f"background-color: {Theme.c('primary')}; color: white; "
            "border: none; border-radius: 5px; font-weight: bold; font-size: 13px;"
        )
        self._btn_sauvegarder.clicked.connect(self._sauvegarder)
        grp_actions_layout.addWidget(self._btn_sauvegarder)

        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color: {Theme.c('border')};")
        grp_actions_layout.addWidget(sep)

        self._btn_export_zip = QPushButton("Exporter (ZIP)")
        self._btn_export_zip.setMinimumHeight(40)
        self._btn_export_zip.clicked.connect(self._exporter_zip)
        grp_actions_layout.addWidget(self._btn_export_zip)

        self._btn_import_zip = QPushButton("Importer (ZIP)")
        self._btn_import_zip.setMinimumHeight(40)
        self._btn_import_zip.clicked.connect(self._importer_zip)
        grp_actions_layout.addWidget(self._btn_import_zip)

        layout.addWidget(grp_actions)

        # Groupe config auto
        grp_auto = QGroupBox("Sauvegarde automatique")
        grp_auto_layout = QVBoxLayout(grp_auto)

        self._chk_auto = QCheckBox("Activer la sauvegarde automatique quotidienne (au démarrage)")
        self._chk_auto.stateChanged.connect(self._toggle_auto)
        grp_auto_layout.addWidget(self._chk_auto)

        info = QLabel(
            f"La sauvegarde auto est déclenchée au démarrage si 24h se sont écoulées. "
            f"Les 7 dernières sauvegardes sont conservées."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
        grp_auto_layout.addWidget(info)

        self._lbl_derniere = QLabel("Dernière sauvegarde : —")
        self._lbl_derniere.setStyleSheet(f"color: {Theme.c('text_secondary')}; font-size: 11px;")
        grp_auto_layout.addWidget(self._lbl_derniere)

        layout.addWidget(grp_auto)

        # Barre de progression (cachée par défaut)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # Mode indéterminé
        self._progress.hide()
        layout.addWidget(self._progress)

        # Bouton fermer
        btns_bas = QHBoxLayout()
        btns_bas.addStretch()
        btn_fermer = QPushButton("Fermer")
        btn_fermer.setMinimumWidth(100)
        btn_fermer.clicked.connect(self.accept)
        btns_bas.addWidget(btn_fermer)
        layout.addLayout(btns_bas)

    # === Chargement ===

    def _charger_liste(self):
        from modules.sauvegarde import lister_sauvegardes
        self._sauvegardes = lister_sauvegardes()
        self._table.setRowCount(0)
        for s in self._sauvegardes:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(s['date_affichage']))
            self._table.setItem(row, 1, QTableWidgetItem(s['nom']))
            self._table.setItem(row, 2, QTableWidgetItem(s['taille']))

    def _charger_config(self):
        try:
            from database import db
            actif = db.get_parametre('sauvegarde_auto_actif', '1') == '1'
            self._chk_auto.setChecked(actif)
            derniere = db.get_parametre('sauvegarde_derniere_date', '')
            if derniere:
                self._lbl_derniere.setText(f"Dernière sauvegarde automatique : {derniere}")
        except Exception:
            pass

    # === Actions ===

    def _sauvegarder(self):
        from modules.sauvegarde import sauvegarder_locale
        self._set_busy(True)
        self._thread = _BackupThread(sauvegarder_locale)
        self._thread.finished.connect(self._on_sauvegarde_done)
        self._thread.start()

    def _on_sauvegarde_done(self, succes, message, chemin):
        self._set_busy(False)
        if succes:
            QMessageBox.information(self, "Succès", f"Sauvegarde créée :\n{chemin}")
            self._charger_liste()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def _restaurer(self):
        row = self._table.currentRow()
        if row < 0 or row >= len(self._sauvegardes):
            return
        s = self._sauvegardes[row]
        rep = QMessageBox.question(
            self, "Confirmer la restauration",
            f"Restaurer la sauvegarde du {s['date_affichage']} ?\n\n"
            "La base actuelle sera sauvegardée avant la restauration.",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return
        from modules.sauvegarde import restaurer
        self._set_busy(True)
        self._thread = _BackupThread(restaurer, s['chemin'])
        self._thread.finished.connect(self._on_restaurer_done)
        self._thread.start()

    def _on_restaurer_done(self, succes, message, _):
        self._set_busy(False)
        if succes:
            QMessageBox.information(self, "Succès", message)
            self._charger_liste()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def _exporter_zip(self):
        from modules.sauvegarde import exporter_zip
        self._set_busy(True)
        self._thread = _BackupThread(exporter_zip)
        self._thread.finished.connect(self._on_export_done)
        self._thread.start()

    def _on_export_done(self, succes, message, chemin):
        self._set_busy(False)
        if succes:
            rep = QMessageBox.information(
                self, "Succès",
                f"Export ZIP créé :\n{chemin}\n\nOuvrir le dossier ?",
                QMessageBox.Yes | QMessageBox.No
            )
            if rep == QMessageBox.Yes:
                self._ouvrir_dossier()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def _importer_zip(self):
        chemin, _ = QFileDialog.getOpenFileName(
            self, "Sélectionner un fichier ZIP", "", "Fichiers ZIP (*.zip)"
        )
        if not chemin:
            return
        rep = QMessageBox.question(
            self, "Confirmer l'import",
            "Importer ce fichier ZIP ?\n\n"
            "Les données actuelles seront sauvegardées puis remplacées.",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep != QMessageBox.Yes:
            return
        from modules.sauvegarde import importer_zip
        self._set_busy(True)
        self._thread = _BackupThread(importer_zip, chemin)
        self._thread.finished.connect(self._on_import_done)
        self._thread.start()

    def _on_import_done(self, succes, message, _):
        self._set_busy(False)
        if succes:
            QMessageBox.information(self, "Succès", message)
            self._charger_liste()
        else:
            QMessageBox.critical(self, "Erreur", message)

    def _ouvrir_dossier(self):
        try:
            import config
            from modules.sauvegarde import BACKUP_DIR
            dossier = BACKUP_DIR
            if os.path.exists(dossier):
                import subprocess
                if os.name == 'nt':
                    subprocess.Popen(f'explorer "{dossier}"')
                else:
                    subprocess.Popen(['xdg-open', dossier])
        except Exception:
            pass

    def _toggle_auto(self, state):
        try:
            from database import db
            db.set_parametre('sauvegarde_auto_actif', '1' if state == Qt.Checked else '0')
        except Exception:
            pass

    def _set_busy(self, busy: bool):
        self._btn_sauvegarder.setEnabled(not busy)
        self._btn_restaurer.setEnabled(not busy)
        self._btn_export_zip.setEnabled(not busy)
        self._btn_import_zip.setEnabled(not busy)
        if busy:
            self._progress.show()
        else:
            self._progress.hide()
