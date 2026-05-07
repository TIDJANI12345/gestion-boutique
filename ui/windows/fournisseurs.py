"""
Fenêtre gestion fournisseurs et commandes d'approvisionnement.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QWidget,
    QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox,
    QComboBox, QFrame, QHeaderView, QMessageBox, QDateEdit,
    QFormLayout, QScrollArea
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

from ui.theme import Theme
from ui.components.dialogs import information, erreur
from modules.fournisseurs import Fournisseur, CommandeFournisseur


def _style_btn(couleur='primary'):
    c = Theme.c(couleur)
    return (
        f"QPushButton {{ background:{c}; color:#fff; border:none; "
        f"border-radius:6px; padding:7px 16px; font-weight:bold; }}"
        f"QPushButton:hover {{ opacity:0.9; }}"
    )


class FournisseursWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fournisseurs & Commandes")
        self.setMinimumSize(1000, 650)
        self._build_ui()
        self._charger_fournisseurs()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        titre = QLabel("Fournisseurs & Approvisionnement")
        titre.setFont(QFont("Segoe UI", 16, QFont.Bold))
        titre.setStyleSheet(f"color: {Theme.c('text')};")
        layout.addWidget(titre)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"color: {Theme.c('text')};")
        layout.addWidget(self._tabs)

        self._tabs.addTab(self._build_tab_fournisseurs(), "Fournisseurs")
        self._tabs.addTab(self._build_tab_commandes(), "Commandes")

    # ── Onglet Fournisseurs ───────────────────────────────────────────────────

    def _build_tab_fournisseurs(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_nouveau = QPushButton("+ Nouveau fournisseur")
        btn_nouveau.setStyleSheet(_style_btn('primary'))
        btn_nouveau.clicked.connect(self._nouveau_fournisseur)
        btn_layout.addWidget(btn_nouveau)
        layout.addLayout(btn_layout)

        self._table_fournisseurs = QTableWidget()
        self._table_fournisseurs.setColumnCount(5)
        self._table_fournisseurs.setHorizontalHeaderLabels(
            ["Nom", "Téléphone", "Email", "Contact", "Actions"]
        )
        self._table_fournisseurs.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table_fournisseurs.setSelectionBehavior(QTableWidget.SelectRows)
        self._table_fournisseurs.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_fournisseurs.verticalHeader().setVisible(False)
        self._table_fournisseurs.setStyleSheet(
            f"color: {Theme.c('text')}; background: {Theme.c('card_bg')};"
        )
        layout.addWidget(self._table_fournisseurs)
        return w

    def _charger_fournisseurs(self):
        rows = Fournisseur.lister()
        self._table_fournisseurs.setRowCount(len(rows))
        for i, f in enumerate(rows):
            self._table_fournisseurs.setItem(i, 0, QTableWidgetItem(f['nom']))
            self._table_fournisseurs.setItem(i, 1, QTableWidgetItem(f['telephone'] or ''))
            self._table_fournisseurs.setItem(i, 2, QTableWidgetItem(f['email'] or ''))
            self._table_fournisseurs.setItem(i, 3, QTableWidgetItem(f['contact_nom'] or ''))

            btn_frame = QWidget()
            btn_h = QHBoxLayout(btn_frame)
            btn_h.setContentsMargins(4, 2, 4, 2)
            btn_h.setSpacing(6)

            btn_cmd = QPushButton("Commande")
            btn_cmd.setStyleSheet(_style_btn('primary'))
            btn_cmd.clicked.connect(lambda _, fid=f['id'], fn=f['nom']: self._nouvelle_commande(fid, fn))

            btn_edit = QPushButton("Modifier")
            btn_edit.setStyleSheet(
                f"QPushButton {{ background:{Theme.c('card_bg')}; color:{Theme.c('text')}; "
                f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:5px 12px; }}"
            )
            btn_edit.clicked.connect(lambda _, fid=f['id']: self._modifier_fournisseur(fid))

            btn_h.addWidget(btn_cmd)
            btn_h.addWidget(btn_edit)
            self._table_fournisseurs.setCellWidget(i, 4, btn_frame)
            self._table_fournisseurs.setRowHeight(i, 44)

    def _nouveau_fournisseur(self):
        dlg = _DialogueFournisseur(parent=self)
        if dlg.exec():
            Fournisseur.creer(**dlg.valeurs())
            self._charger_fournisseurs()

    def _modifier_fournisseur(self, fournisseur_id):
        f = Fournisseur.obtenir(fournisseur_id)
        if not f:
            return
        dlg = _DialogueFournisseur(parent=self, fournisseur=f)
        if dlg.exec():
            vals = dlg.valeurs()
            Fournisseur.modifier(fournisseur_id, **vals)
            self._charger_fournisseurs()

    # ── Onglet Commandes ──────────────────────────────────────────────────────

    def _build_tab_commandes(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(8)

        self._table_commandes = QTableWidget()
        self._table_commandes.setColumnCount(6)
        self._table_commandes.setHorizontalHeaderLabels(
            ["#", "Fournisseur", "Date", "Livraison prévue", "Total", "Statut", ]
        )
        self._table_commandes.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._table_commandes.setSelectionBehavior(QTableWidget.SelectRows)
        self._table_commandes.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table_commandes.verticalHeader().setVisible(False)
        self._table_commandes.setStyleSheet(
            f"color: {Theme.c('text')}; background: {Theme.c('card_bg')};"
        )
        self._table_commandes.doubleClicked.connect(self._ouvrir_commande)
        layout.addWidget(self._table_commandes)

        lbl = QLabel("Double-cliquez sur une commande pour voir les détails et enregistrer une réception.")
        lbl.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 9pt;")
        layout.addWidget(lbl)

        return w

    def _charger_commandes(self):
        rows = CommandeFournisseur.lister()
        self._table_commandes.setRowCount(len(rows))
        couleurs_statut = {
            'en_attente': '#f59e0b',
            'envoyee':    '#3b82f6',
            'partielle':  '#8b5cf6',
            'recue':      '#10b981',
            'annulee':    '#6b7280',
        }
        for i, c in enumerate(rows):
            self._table_commandes.setItem(i, 0, QTableWidgetItem(str(c['id'])))
            self._table_commandes.setItem(i, 1, QTableWidgetItem(c['fournisseur_nom']))
            self._table_commandes.setItem(i, 2, QTableWidgetItem((c['date_commande'] or '')[:10]))
            self._table_commandes.setItem(i, 3, QTableWidgetItem(c['date_livraison_prevue'] or '—'))
            self._table_commandes.setItem(i, 4, QTableWidgetItem(f"{c['total']:,.0f} FCFA"))
            statut_txt = CommandeFournisseur.STATUTS.get(c['statut'], c['statut'])
            item_statut = QTableWidgetItem(statut_txt)
            item_statut.setForeground(
                __import__('PySide6.QtGui', fromlist=['QColor']).QColor(
                    couleurs_statut.get(c['statut'], '#6b7280')
                )
            )
            self._table_commandes.setItem(i, 5, item_statut)
            self._table_commandes.setRowHeight(i, 36)

    def showEvent(self, event):
        super().showEvent(event)
        self._charger_commandes()

    def _tabs_changed(self, idx):
        if idx == 1:
            self._charger_commandes()

    def _nouvelle_commande(self, fournisseur_id, fournisseur_nom):
        dlg = _DialogueCommande(fournisseur_id, fournisseur_nom, parent=self)
        if dlg.exec():
            lignes, date_liv, notes = dlg.valeurs()
            if not lignes:
                erreur(self, "Commande vide", "Ajoutez au moins un produit.")
                return
            CommandeFournisseur.creer(fournisseur_id, lignes, date_liv, notes)
            self._tabs.setCurrentIndex(1)
            self._charger_commandes()
            information(self, "Commande créée", "La commande a été enregistrée.")

    def _ouvrir_commande(self, index):
        row = index.row()
        commande_id = int(self._table_commandes.item(row, 0).text())
        dlg = _DialogueReception(commande_id, parent=self)
        if dlg.exec():
            self._charger_commandes()


# ── Dialogues internes ────────────────────────────────────────────────────────

class _DialogueFournisseur(QDialog):

    def __init__(self, parent=None, fournisseur=None):
        super().__init__(parent)
        self._f = fournisseur
        self.setWindowTitle("Nouveau fournisseur" if not fournisseur else "Modifier fournisseur")
        self.setMinimumWidth(420)
        self._build()

    def _build(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        style_input = (
            f"background:{Theme.c('input_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:6px;"
        )

        self._nom = QLineEdit()
        self._tel = QLineEdit()
        self._email = QLineEdit()
        self._adresse = QLineEdit()
        self._contact = QLineEdit()

        for w in [self._nom, self._tel, self._email, self._adresse, self._contact]:
            w.setStyleSheet(style_input)

        layout.addRow("Nom *", self._nom)
        layout.addRow("Téléphone", self._tel)
        layout.addRow("Email", self._email)
        layout.addRow("Adresse", self._adresse)
        layout.addRow("Nom du contact", self._contact)

        if self._f:
            self._nom.setText(self._f['nom'])
            self._tel.setText(self._f['telephone'] or '')
            self._email.setText(self._f['email'] or '')
            self._adresse.setText(self._f['adresse'] or '')
            self._contact.setText(self._f['contact_nom'] or '')

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Enregistrer")
        btn_ok.setStyleSheet(_style_btn('primary'))
        btn_ok.clicked.connect(self._valider)
        btn_layout.addWidget(btn_ok)
        layout.addRow(btn_layout)

    def _valider(self):
        if not self._nom.text().strip():
            erreur(self, "Champ requis", "Le nom du fournisseur est obligatoire.")
            return
        self.accept()

    def valeurs(self):
        return {
            'nom': self._nom.text().strip(),
            'telephone': self._tel.text().strip(),
            'email': self._email.text().strip(),
            'adresse': self._adresse.text().strip(),
            'contact_nom': self._contact.text().strip(),
        }


class _DialogueCommande(QDialog):

    def __init__(self, fournisseur_id, fournisseur_nom, parent=None):
        super().__init__(parent)
        self._fournisseur_id = fournisseur_id
        self.setWindowTitle(f"Nouvelle commande — {fournisseur_nom}")
        self.setMinimumSize(700, 500)
        self._lignes = []
        self._build()
        self._charger_produits()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        style_input = (
            f"background:{Theme.c('input_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:6px;"
        )

        # Date livraison prévue
        top = QHBoxLayout()
        top.addWidget(QLabel("Livraison prévue :"))
        self._date_liv = QDateEdit(QDate.currentDate().addDays(7))
        self._date_liv.setCalendarPopup(True)
        self._date_liv.setStyleSheet(style_input)
        top.addWidget(self._date_liv)
        top.addStretch()
        layout.addLayout(top)

        # Sélecteur produit
        add_layout = QHBoxLayout()
        self._combo_produit = QComboBox()
        self._combo_produit.setStyleSheet(style_input)
        self._combo_produit.setMinimumWidth(250)
        self._spin_qte = QSpinBox()
        self._spin_qte.setRange(1, 9999)
        self._spin_qte.setValue(1)
        self._spin_qte.setStyleSheet(style_input)
        self._spin_prix = QDoubleSpinBox()
        self._spin_prix.setRange(0, 9999999)
        self._spin_prix.setDecimals(0)
        self._spin_prix.setStyleSheet(style_input)
        btn_add = QPushButton("Ajouter")
        btn_add.setStyleSheet(_style_btn('success'))
        btn_add.clicked.connect(self._ajouter_ligne)

        add_layout.addWidget(QLabel("Produit :"))
        add_layout.addWidget(self._combo_produit, 1)
        add_layout.addWidget(QLabel("Qté :"))
        add_layout.addWidget(self._spin_qte)
        add_layout.addWidget(QLabel("P.U. :"))
        add_layout.addWidget(self._spin_prix)
        add_layout.addWidget(btn_add)
        layout.addLayout(add_layout)

        # Table lignes
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(["Produit", "Qté", "Prix unitaire", "Sous-total", ""])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setStyleSheet(f"color: {Theme.c('text')};")
        layout.addWidget(self._table, 1)

        # Notes + total
        self._notes = QLineEdit()
        self._notes.setPlaceholderText("Notes (optionnel)")
        self._notes.setStyleSheet(style_input)
        layout.addWidget(self._notes)

        self._lbl_total = QLabel("Total : 0 FCFA")
        self._lbl_total.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._lbl_total.setStyleSheet(f"color: {Theme.c('text')};")
        layout.addWidget(self._lbl_total)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_ok = QPushButton("Créer la commande")
        btn_ok.setStyleSheet(_style_btn('primary'))
        btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(btn_ok)
        layout.addLayout(btn_layout)

    def _charger_produits(self):
        from modules.produits import Produit
        self._produits = Produit.obtenir_tous()
        self._combo_produit.clear()
        for p in self._produits:
            self._combo_produit.addItem(
                f"{p['nom']} (stock: {p['stock_actuel']})", p['id']
            )
            prix = p.get('prix_achat', 0) or 0
            if self._combo_produit.currentData() == p['id']:
                self._spin_prix.setValue(prix)
        self._combo_produit.currentIndexChanged.connect(self._on_produit_change)
        self._on_produit_change()

    def _on_produit_change(self):
        idx = self._combo_produit.currentIndex()
        if idx >= 0 and idx < len(self._produits):
            prix = self._produits[idx].get('prix_achat', 0) or 0
            self._spin_prix.setValue(prix)

    def _ajouter_ligne(self):
        produit_id = self._combo_produit.currentData()
        nom = self._combo_produit.currentText().split(' (')[0]
        qte = self._spin_qte.value()
        prix = self._spin_prix.value()
        self._lignes.append({'produit_id': produit_id, 'nom': nom,
                              'quantite': qte, 'prix_unitaire': prix})
        self._rafraichir_table()

    def _rafraichir_table(self):
        self._table.setRowCount(len(self._lignes))
        total = 0
        for i, l in enumerate(self._lignes):
            st = l['quantite'] * l['prix_unitaire']
            total += st
            self._table.setItem(i, 0, QTableWidgetItem(l['nom']))
            self._table.setItem(i, 1, QTableWidgetItem(str(l['quantite'])))
            self._table.setItem(i, 2, QTableWidgetItem(f"{l['prix_unitaire']:,.0f}"))
            self._table.setItem(i, 3, QTableWidgetItem(f"{st:,.0f}"))
            btn_del = QPushButton("✕")
            btn_del.setStyleSheet("color: #ef4444; background: transparent; border: none;")
            btn_del.clicked.connect(lambda _, idx=i: self._supprimer_ligne(idx))
            self._table.setCellWidget(i, 4, btn_del)
        self._lbl_total.setText(f"Total : {total:,.0f} FCFA")

    def _supprimer_ligne(self, idx):
        del self._lignes[idx]
        self._rafraichir_table()

    def valeurs(self):
        date_liv = self._date_liv.date().toString("yyyy-MM-dd")
        return self._lignes, date_liv, self._notes.text().strip()


class _DialogueReception(QDialog):

    def __init__(self, commande_id, parent=None):
        super().__init__(parent)
        self._commande_id = commande_id
        self._commande = CommandeFournisseur.obtenir(commande_id)
        self._details = CommandeFournisseur.obtenir_details(commande_id)
        self.setWindowTitle(f"Commande #{commande_id} — {self._commande['fournisseur_nom'] if self._commande else ''}")
        self.setMinimumSize(620, 400)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        if self._commande:
            statut = CommandeFournisseur.STATUTS.get(self._commande['statut'], '')
            info = QLabel(f"Statut : {statut}  |  Date : {(self._commande['date_commande'] or '')[:10]}")
            info.setStyleSheet(f"color: {Theme.c('text')}; font-size: 10pt;")
            layout.addWidget(info)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Produit", "Commandé", "Déjà reçu", "Recevoir maintenant", "Stock actuel"]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setStyleSheet(f"color: {Theme.c('text')};")
        self._spins = []

        self._table.setRowCount(len(self._details))
        for i, d in enumerate(self._details):
            self._table.setItem(i, 0, QTableWidgetItem(d['produit_nom']))
            self._table.setItem(i, 1, QTableWidgetItem(str(d['quantite_commandee'])))
            self._table.setItem(i, 2, QTableWidgetItem(str(d['quantite_recue'])))
            restant = d['quantite_commandee'] - d['quantite_recue']
            spin = QSpinBox()
            spin.setRange(0, max(restant, 0))
            spin.setValue(max(restant, 0))
            spin.setStyleSheet(
                f"background:{Theme.c('input_bg')}; color:{Theme.c('text')}; "
                f"border:1px solid {Theme.c('input_border')}; border-radius:4px;"
            )
            self._table.setCellWidget(i, 3, spin)
            self._spins.append(spin)
            self._table.setItem(i, 4, QTableWidgetItem(str(d['stock_actuel'])))
            self._table.setRowHeight(i, 40)

        layout.addWidget(self._table, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        if self._commande and self._commande['statut'] not in ('recue', 'annulee'):
            btn_rec = QPushButton("Enregistrer la réception")
            btn_rec.setStyleSheet(_style_btn('success'))
            btn_rec.clicked.connect(self._enregistrer)
            btn_layout.addWidget(btn_rec)

        btn_fermer = QPushButton("Fermer")
        btn_fermer.setStyleSheet(
            f"QPushButton {{ background:{Theme.c('card_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:7px 16px; }}"
        )
        btn_fermer.clicked.connect(self.reject)
        btn_layout.addWidget(btn_fermer)
        layout.addLayout(btn_layout)

    def _enregistrer(self):
        receptions = []
        for i, (d, spin) in enumerate(zip(self._details, self._spins)):
            if spin.value() > 0:
                receptions.append({'detail_id': d['id'], 'quantite_recue': spin.value()})
        if not receptions:
            erreur(self, "Rien à recevoir", "Saisissez les quantités reçues.")
            return
        CommandeFournisseur.recevoir(self._commande_id, receptions)
        information(self, "Réception enregistrée", "Le stock a été mis à jour.")
        self.accept()
