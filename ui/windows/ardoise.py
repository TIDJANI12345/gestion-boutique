"""
Fenêtre de gestion de l'ardoise (crédit client).
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QComboBox, QDialogButtonBox, QGroupBox, QFormLayout,
    QWidget, QSplitter, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from modules.ardoise import (
    liste_debiteurs, liste_ardoise_client, encaissements_ardoise,
    encaisser, stats_ardoise, solde_client
)
from modules.clients import Client as ClientModule


class EncaisserDialog(QDialog):
    """Dialog pour enregistrer un paiement sur une ardoise."""

    def __init__(self, ardoise: dict, parent=None):
        super().__init__(parent)
        self.ardoise = ardoise
        self.setWindowTitle("Encaisser un paiement")
        self.setMinimumWidth(380)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        info = QLabel(
            f"Ardoise #{self.ardoise['id']} — Restant : "
            f"<b>{self.ardoise['montant_restant']:,.0f} FCFA</b>"
        )
        info.setTextFormat(Qt.RichText)
        layout.addWidget(info)

        form = QFormLayout()
        form.setSpacing(8)

        self._montant = QLineEdit()
        self._montant.setPlaceholderText(f"Max {self.ardoise['montant_restant']:,.0f}")
        form.addRow("Montant (FCFA) :", self._montant)

        self._mode = QComboBox()
        self._mode.addItems(["especes", "mobile_money", "virement", "autre"])
        form.addRow("Mode :", self._mode)

        self._reference = QLineEdit()
        self._reference.setPlaceholderText("Optionnel (n° transaction…)")
        form.addRow("Référence :", self._reference)

        self._notes = QLineEdit()
        self._notes.setPlaceholderText("Optionnel")
        form.addRow("Notes :", self._notes)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.button(QDialogButtonBox.Ok).setText("Enregistrer")
        btns.accepted.connect(self._valider)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _valider(self):
        try:
            montant = float(self._montant.text().replace(' ', '').replace(',', '.'))
        except ValueError:
            QMessageBox.warning(self, "Erreur", "Montant invalide.")
            return
        if montant <= 0:
            QMessageBox.warning(self, "Erreur", "Montant doit être positif.")
            return

        ok, msg = encaisser(
            self.ardoise['id'], montant,
            mode=self._mode.currentText(),
            reference=self._reference.text().strip() or None,
            notes=self._notes.text().strip() or None,
        )
        if ok:
            QMessageBox.information(self, "Succès", msg)
            self.accept()
        else:
            QMessageBox.critical(self, "Erreur", msg)


class DetailClientDialog(QDialog):
    """Dialog affichant toutes les ardoises d'un client + encaissements."""

    encaissement_effectue = Signal()

    def __init__(self, client_id: int, client_nom: str, parent=None):
        super().__init__(parent)
        self.client_id = client_id
        self.client_nom = client_nom
        self.setWindowTitle(f"Ardoise — {client_nom}")
        self.resize(700, 480)
        self._build()
        self._charger()

    def _build(self):
        layout = QVBoxLayout(self)

        self._lbl_solde = QLabel()
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        self._lbl_solde.setFont(font)
        layout.addWidget(self._lbl_solde)

        splitter = QSplitter(Qt.Horizontal)

        # Ardoises (gauche)
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.addWidget(QLabel("<b>Ardoises</b>"))
        self._tbl_ardoises = QTableWidget()
        self._tbl_ardoises.setColumnCount(5)
        self._tbl_ardoises.setHorizontalHeaderLabels(
            ["#", "Vente", "Initial", "Restant", "Statut"]
        )
        self._tbl_ardoises.setSelectionBehavior(QTableWidget.SelectRows)
        self._tbl_ardoises.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl_ardoises.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._tbl_ardoises.itemSelectionChanged.connect(self._on_ardoise_selected)
        lv.addWidget(self._tbl_ardoises)

        self._btn_encaisser = QPushButton("Encaisser un paiement")
        self._btn_encaisser.setEnabled(False)
        self._btn_encaisser.clicked.connect(self._encaisser)
        lv.addWidget(self._btn_encaisser)

        splitter.addWidget(left)

        # Encaissements (droite)
        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.addWidget(QLabel("<b>Paiements reçus</b>"))
        self._tbl_enc = QTableWidget()
        self._tbl_enc.setColumnCount(4)
        self._tbl_enc.setHorizontalHeaderLabels(["Date", "Montant", "Mode", "Référence"])
        self._tbl_enc.setEditTriggers(QTableWidget.NoEditTriggers)
        self._tbl_enc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        rv.addWidget(self._tbl_enc)
        splitter.addWidget(right)

        layout.addWidget(splitter)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _charger(self):
        solde = solde_client(self.client_id)
        self._lbl_solde.setText(f"Solde dû : {solde:,.0f} FCFA")
        color = "#EF4444" if solde > 0 else "#22C55E"
        self._lbl_solde.setStyleSheet(f"color: {color};")

        ardoises = liste_ardoise_client(self.client_id)
        self._ardoises = ardoises
        self._tbl_ardoises.setRowCount(len(ardoises))
        for i, a in enumerate(ardoises):
            self._tbl_ardoises.setItem(i, 0, QTableWidgetItem(str(a['id'])))
            self._tbl_ardoises.setItem(i, 1, QTableWidgetItem(a.get('numero_vente') or "—"))
            self._tbl_ardoises.setItem(i, 2, QTableWidgetItem(f"{a['montant_initial']:,.0f}"))
            self._tbl_ardoises.setItem(i, 3, QTableWidgetItem(f"{a['montant_restant']:,.0f}"))
            statut = a['statut']
            item_statut = QTableWidgetItem(statut)
            if statut == 'solde':
                item_statut.setForeground(QColor("#22C55E"))
            elif statut == 'en_cours':
                item_statut.setForeground(QColor("#EF4444"))
            else:
                item_statut.setForeground(QColor("#F59E0B"))
            self._tbl_ardoises.setItem(i, 4, item_statut)

        self._tbl_enc.setRowCount(0)
        self._btn_encaisser.setEnabled(False)

    def _on_ardoise_selected(self):
        rows = self._tbl_ardoises.selectedItems()
        if not rows:
            self._btn_encaisser.setEnabled(False)
            return
        row = self._tbl_ardoises.currentRow()
        ardoise = self._ardoises[row]
        self._btn_encaisser.setEnabled(ardoise['statut'] != 'solde')
        self._charger_encaissements(ardoise['id'])

    def _charger_encaissements(self, ardoise_id: int):
        enc = encaissements_ardoise(ardoise_id)
        self._tbl_enc.setRowCount(len(enc))
        for i, e in enumerate(enc):
            date_str = str(e.get('date_encaissement', ''))[:16]
            self._tbl_enc.setItem(i, 0, QTableWidgetItem(date_str))
            self._tbl_enc.setItem(i, 1, QTableWidgetItem(f"{e['montant']:,.0f}"))
            self._tbl_enc.setItem(i, 2, QTableWidgetItem(e.get('mode_paiement', '')))
            self._tbl_enc.setItem(i, 3, QTableWidgetItem(e.get('reference') or ""))

    def _encaisser(self):
        row = self._tbl_ardoises.currentRow()
        if row < 0:
            return
        ardoise = self._ardoises[row]
        dlg = EncaisserDialog(ardoise, self)
        if dlg.exec() == QDialog.Accepted:
            self.encaissement_effectue.emit()
            self._charger()


class ArdoiseWindow(QDialog):
    """Fenêtre principale de gestion des ardoises (liste débiteurs)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ardoise — Crédit Client")
        self.resize(680, 500)
        self._build()
        self._charger()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Stats
        self._lbl_stats = QLabel()
        self._lbl_stats.setStyleSheet(
            "background: #FEF3C7; color: #92400E; padding: 8px 12px; border-radius: 6px;"
        )
        layout.addWidget(self._lbl_stats)

        # Barre de recherche
        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("Rechercher un client…")
        self._search.textChanged.connect(self._filtrer)
        search_row.addWidget(self._search)

        btn_refresh = QPushButton("Rafraîchir")
        btn_refresh.clicked.connect(self._charger)
        search_row.addWidget(btn_refresh)
        layout.addLayout(search_row)

        # Table débiteurs
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels(["Client", "Téléphone", "Nb ardoises", "Total dû"])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.doubleClicked.connect(self._ouvrir_client)
        layout.addWidget(self._table)

        btn_row = QHBoxLayout()
        self._btn_detail = QPushButton("Voir ardoises / Encaisser")
        self._btn_detail.setEnabled(False)
        self._btn_detail.clicked.connect(self._ouvrir_client)
        btn_row.addWidget(self._btn_detail)
        btn_row.addStretch()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.clicked.connect(self.accept)
        btn_row.addWidget(btn_fermer)
        layout.addLayout(btn_row)

        self._table.itemSelectionChanged.connect(
            lambda: self._btn_detail.setEnabled(bool(self._table.selectedItems()))
        )

    def _charger(self):
        stats = stats_ardoise()
        self._lbl_stats.setText(
            f"Total dû : <b>{stats['total_du']:,.0f} FCFA</b> — "
            f"{stats['nb_debiteurs']} client(s) débiteur(s)"
        )
        self._lbl_stats.setTextFormat(Qt.RichText)

        self._debiteurs = liste_debiteurs()
        self._afficher(self._debiteurs)

    def _afficher(self, debiteurs: list):
        self._table.setRowCount(len(debiteurs))
        for i, d in enumerate(debiteurs):
            self._table.setItem(i, 0, QTableWidgetItem(d.get('client_nom', '')))
            self._table.setItem(i, 1, QTableWidgetItem(d.get('client_telephone') or ""))
            self._table.setItem(i, 2, QTableWidgetItem(str(d.get('nb_ardoises', 0))))
            montant_item = QTableWidgetItem(f"{d.get('solde_total', 0):,.0f} FCFA")
            montant_item.setForeground(QColor("#EF4444"))
            self._table.setItem(i, 3, montant_item)

    def _filtrer(self, texte: str):
        texte = texte.lower()
        filtres = [
            d for d in self._debiteurs
            if texte in d.get('client_nom', '').lower()
            or texte in (d.get('client_telephone') or '').lower()
        ]
        self._afficher(filtres)

    def _ouvrir_client(self):
        row = self._table.currentRow()
        if row < 0:
            return
        # Retrouver le débiteur dans la liste filtrée
        nom = self._table.item(row, 0).text()
        d = next((x for x in self._debiteurs if x['client_nom'] == nom), None)
        if not d:
            return
        dlg = DetailClientDialog(d['client_id'], d['client_nom'], self)
        dlg.encaissement_effectue.connect(self._charger)
        dlg.exec()
