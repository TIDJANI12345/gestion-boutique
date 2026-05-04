"""
Fenêtre d'annulation de vente.
Portée : patron=toutes, gestionnaire=aujourd'hui, caissier=aujourd'hui+ses propres.
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QDateEdit, QGroupBox, QFormLayout, QTextEdit,
    QDialogButtonBox, QFrame, QComboBox
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont

from modules.permissions import Permissions
from modules.ventes import Vente


def _fmt_date(s: str) -> str:
    return s[:16] if s else ""


class MotifDialog(QDialog):
    """Saisie du motif d'annulation + confirmation."""

    def __init__(self, vente: dict, parent=None):
        super().__init__(parent)
        self.vente = vente
        self.setWindowTitle("Confirmer l'annulation")
        self.setMinimumWidth(400)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        avertissement = QLabel(
            f"⚠  Vous allez annuler la vente <b>{self.vente.get('numero_vente', '')}</b><br>"
            f"Montant : <b>{self.vente.get('total', 0):,.0f} FCFA</b> — "
            f"Client : {self.vente.get('client') or '(aucun)'}<br><br>"
            "Le stock sera restauré. Cette action est irréversible."
        )
        avertissement.setTextFormat(Qt.RichText)
        avertissement.setWordWrap(True)
        avertissement.setStyleSheet(
            "background: #FEF3C7; color: #92400E; padding: 10px; border-radius: 6px;"
        )
        layout.addWidget(avertissement)

        form = QFormLayout()
        self._motif = QTextEdit()
        self._motif.setPlaceholderText("Motif obligatoire (erreur de saisie, retour client…)")
        self._motif.setMaximumHeight(80)
        form.addRow("Motif :", self._motif)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Annuler la vente")
        btns.button(QDialogButtonBox.Ok).setStyleSheet(
            "background-color: #EF4444; color: white; font-weight: bold;"
        )
        btns.accepted.connect(self._valider)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _valider(self):
        motif = self._motif.toPlainText().strip()
        if not motif:
            QMessageBox.warning(self, "Motif requis", "Veuillez saisir un motif d'annulation.")
            return
        self._motif_texte = motif
        self.accept()

    def motif(self) -> str:
        return getattr(self, '_motif_texte', '')


class AnnulationVenteWindow(QDialog):
    """Fenêtre de recherche et annulation de ventes."""

    vente_annulee = Signal(int)

    def __init__(self, utilisateur: dict, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur
        self.role = utilisateur.get('role', 'caissier')
        self.est_patron = (
            utilisateur.get('super_admin') == 1 or self.role == 'patron'
        )
        self.setWindowTitle("Annulation de vente")
        self.resize(820, 560)
        self._ventes = []
        self._build()
        self._charger()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Filtres
        grp = QGroupBox("Recherche")
        fl = QHBoxLayout(grp)

        fl.addWidget(QLabel("Du :"))
        self._date_debut = QDateEdit(QDate.currentDate())
        self._date_debut.setCalendarPopup(True)
        self._date_debut.setDisplayFormat("dd/MM/yyyy")
        fl.addWidget(self._date_debut)

        fl.addWidget(QLabel("Au :"))
        self._date_fin = QDateEdit(QDate.currentDate())
        self._date_fin.setCalendarPopup(True)
        self._date_fin.setDisplayFormat("dd/MM/yyyy")
        fl.addWidget(self._date_fin)

        # Gestionnaire/caissier : dates bloquées sur aujourd'hui
        if not self.est_patron:
            self._date_debut.setEnabled(False)
            self._date_fin.setEnabled(False)

        fl.addWidget(QLabel("N° vente / Client :"))
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher…")
        self._search.textChanged.connect(self._filtrer)
        fl.addWidget(self._search)

        btn_search = QPushButton("Actualiser")
        btn_search.clicked.connect(self._charger)
        fl.addWidget(btn_search)

        layout.addWidget(grp)

        # Onglets actives / annulées
        tabs_row = QHBoxLayout()
        self._btn_actives = QPushButton("Ventes actives")
        self._btn_actives.setCheckable(True)
        self._btn_actives.setChecked(True)
        self._btn_actives.clicked.connect(lambda: self._switch_vue('actives'))
        self._btn_annulees = QPushButton("Ventes annulées")
        self._btn_annulees.setCheckable(True)
        self._btn_annulees.clicked.connect(lambda: self._switch_vue('annulees'))
        tabs_row.addWidget(self._btn_actives)
        tabs_row.addWidget(self._btn_annulees)
        tabs_row.addStretch()
        layout.addLayout(tabs_row)
        self._vue = 'actives'

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["N° Vente", "Date", "Client", "Caissier", "Total", "Statut", "Motif annulation"]
        )
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setAlternatingRowColors(True)
        self._table.itemSelectionChanged.connect(self._on_select)
        self._table.doubleClicked.connect(self._annuler)
        layout.addWidget(self._table)

        # Boutons bas
        btn_row = QHBoxLayout()
        self._btn_annuler = QPushButton("Annuler cette vente")
        self._btn_annuler.setEnabled(False)
        self._btn_annuler.setStyleSheet(
            "background-color: #EF4444; color: white; font-weight: bold; padding: 6px 16px;"
        )
        self._btn_annuler.clicked.connect(self._annuler)
        btn_row.addWidget(self._btn_annuler)
        btn_row.addStretch()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.clicked.connect(self.accept)
        btn_row.addWidget(btn_fermer)
        layout.addLayout(btn_row)

    def _switch_vue(self, vue: str):
        self._vue = vue
        self._btn_actives.setChecked(vue == 'actives')
        self._btn_annulees.setChecked(vue == 'annulees')
        self._charger()

    def _charger(self):
        date_debut = self._date_debut.date().toString("yyyy-MM-dd")
        date_fin = self._date_fin.date().toString("yyyy-MM-dd")

        # Scope caissier : uniquement ses propres ventes
        uid = None
        if self.role == 'caissier':
            uid = self.utilisateur.get('id')

        if self._vue == 'annulees':
            self._ventes = Vente.obtenir_ventes_annulees(date_debut, date_fin, uid) or []
        else:
            self._ventes = Vente.obtenir_toutes_ventes(date_debut, date_fin, uid) or []

        self._afficher(self._ventes)

    def _afficher(self, ventes: list):
        self._table.setRowCount(len(ventes))
        for i, v in enumerate(ventes):
            self._table.setItem(i, 0, QTableWidgetItem(v.get('numero_vente', '')))
            self._table.setItem(i, 1, QTableWidgetItem(_fmt_date(str(v.get('date_vente', '')))))
            self._table.setItem(i, 2, QTableWidgetItem(v.get('client') or '—'))
            self._table.setItem(i, 3, QTableWidgetItem(v.get('caissier_nom', '') or ''))
            total_item = QTableWidgetItem(f"{v.get('total', 0):,.0f} FCFA")
            total_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self._table.setItem(i, 4, total_item)

            statut = v.get('statut', 'terminee')
            statut_item = QTableWidgetItem(statut)
            if statut == 'annulee':
                statut_item.setForeground(QColor("#EF4444"))
            else:
                statut_item.setForeground(QColor("#22C55E"))
            self._table.setItem(i, 5, statut_item)

            self._table.setItem(i, 6, QTableWidgetItem(v.get('motif_annulation') or ''))

        self._btn_annuler.setEnabled(False)

    def _filtrer(self, texte: str):
        texte = texte.lower()
        filtres = [
            v for v in self._ventes
            if texte in (v.get('numero_vente') or '').lower()
            or texte in (v.get('client') or '').lower()
            or texte in (v.get('caissier_nom') or '').lower()
        ]
        self._afficher(filtres)
        # Reset so _afficher uses unfiltered list for selection index
        self._displayed = filtres

    def _on_select(self):
        row = self._table.currentRow()
        if row < 0:
            self._btn_annuler.setEnabled(False)
            return
        vente = self._get_vente_row(row)
        peut = (
            vente is not None
            and vente.get('statut') != 'annulee'
            and self._vue == 'actives'
        )
        self._btn_annuler.setEnabled(peut)

    def _get_vente_row(self, row: int):
        """Retrouve la vente correspondant à la ligne affichée."""
        if row < 0:
            return None
        numero = self._table.item(row, 0)
        if not numero:
            return None
        num = numero.text()
        source = getattr(self, '_displayed', self._ventes)
        return next((v for v in source if v.get('numero_vente') == num), None)

    def _annuler(self):
        row = self._table.currentRow()
        vente = self._get_vente_row(row)
        if not vente or vente.get('statut') == 'annulee':
            return

        dlg = MotifDialog(vente, self)
        if dlg.exec() != QDialog.Accepted:
            return

        motif = dlg.motif()
        ok = Vente.annuler_vente(
            vente['id'],
            user_id=self.utilisateur.get('id'),
            motif=motif
        )
        if ok:
            QMessageBox.information(
                self, "Succès",
                f"Vente {vente['numero_vente']} annulée.\nStock restauré."
            )
            self.vente_annulee.emit(vente['id'])
            self._charger()
        else:
            QMessageBox.critical(self, "Erreur", "Impossible d'annuler cette vente.")
