"""
Fenetre de consultation des logs d'audit
Acces : Super-Admin uniquement
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QDateEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
from modules.permissions import Permissions
from database import db


class LogsAuditWindow(QDialog):
    def __init__(self, utilisateur, parent=None):
        super().__init__(parent)
        self.utilisateur = utilisateur

        # Verifier permission (Super-Admin uniquement)
        if not Permissions.peut(utilisateur, 'sauvegarde_restore'):
            QMessageBox.warning(
                self, "Accès refusé",
                "Seul le Super-Admin peut consulter les logs d'audit."
            )
            self.reject()
            return

        self.setWindowTitle("Logs d'Audit - Système")
        self.setMinimumSize(1200, 700)
        self._setup_ui()
        self._charger_logs()

    def _setup_ui(self):
        """Interface"""
        layout = QVBoxLayout(self)

        # === EN-TETE ===
        titre = QLabel("📊 Logs d'Audit - Traçabilité des Actions")
        titre_font = QFont()
        titre_font.setPointSize(14)
        titre_font.setBold(True)
        titre.setFont(titre_font)
        layout.addWidget(titre)

        # === FILTRES ===
        filtres_layout = QHBoxLayout()

        # Filtre par utilisateur
        filtres_layout.addWidget(QLabel("Utilisateur:"))
        self._combo_user = QComboBox()
        self._combo_user.addItem("Tous", None)
        self._charger_utilisateurs()
        self._combo_user.currentIndexChanged.connect(self._charger_logs)
        filtres_layout.addWidget(self._combo_user)

        # Filtre par action
        filtres_layout.addWidget(QLabel("Action:"))
        self._combo_action = QComboBox()
        self._combo_action.addItem("Toutes", None)
        actions = [
            'connexion', 'deconnexion', 'creation_utilisateur',
            'modification_role', 'annulation_vente', 'suppression_produit',
            'ajustement_stock', 'sauvegarde_db'
        ]
        for action in actions:
            self._combo_action.addItem(action, action)
        self._combo_action.currentIndexChanged.connect(self._charger_logs)
        filtres_layout.addWidget(self._combo_action)

        # Filtre par date
        filtres_layout.addWidget(QLabel("Date début:"))
        self._date_debut = QDateEdit()
        self._date_debut.setDate(QDate.currentDate().addDays(-30))
        self._date_debut.setCalendarPopup(True)
        self._date_debut.dateChanged.connect(self._charger_logs)
        filtres_layout.addWidget(self._date_debut)

        filtres_layout.addWidget(QLabel("Date fin:"))
        self._date_fin = QDateEdit()
        self._date_fin.setDate(QDate.currentDate())
        self._date_fin.setCalendarPopup(True)
        self._date_fin.dateChanged.connect(self._charger_logs)
        filtres_layout.addWidget(self._date_fin)

        filtres_layout.addStretch()

        # Bouton rafraîchir
        btn_refresh = QPushButton("🔄 Rafraîchir")
        btn_refresh.clicked.connect(self._charger_logs)
        filtres_layout.addWidget(btn_refresh)

        layout.addLayout(filtres_layout)

        # === TABLE ===
        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            'ID', 'Date/Heure', 'Utilisateur', 'Action', 'Détails'
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.setColumnWidth(0, 50)
        self._table.setColumnWidth(1, 180)
        self._table.setColumnWidth(2, 200)
        self._table.setColumnWidth(3, 180)
        self._table.setColumnWidth(4, 500)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        # === FOOTER ===
        footer_layout = QHBoxLayout()
        self._label_count = QLabel("0 log(s)")
        footer_layout.addWidget(self._label_count)
        footer_layout.addStretch()

        btn_fermer = QPushButton("Fermer")
        btn_fermer.clicked.connect(self.close)
        footer_layout.addWidget(btn_fermer)

        layout.addLayout(footer_layout)

    def _charger_utilisateurs(self):
        """Charger la liste des utilisateurs pour le filtre"""
        users = db.fetch_all("SELECT id, nom, prenom FROM utilisateurs ORDER BY nom")
        for user in users:
            nom_complet = f"{user['prenom']} {user['nom']}"
            self._combo_user.addItem(nom_complet, user['id'])

    def _charger_logs(self):
        """Charger les logs depuis la DB avec filtres"""
        # Construire la requête avec filtres
        query = """
            SELECT la.id, la.date_action,
                   u.nom || ' ' || u.prenom AS utilisateur,
                   la.action, la.details
            FROM logs_actions la
            JOIN utilisateurs u ON la.utilisateur_id = u.id
            WHERE 1=1
        """
        params = []

        # Filtre utilisateur
        user_id = self._combo_user.currentData()
        if user_id:
            query += " AND la.utilisateur_id = ?"
            params.append(user_id)

        # Filtre action
        action = self._combo_action.currentData()
        if action:
            query += " AND la.action = ?"
            params.append(action)

        # Filtre date
        date_debut = self._date_debut.date().toString("yyyy-MM-dd")
        date_fin = self._date_fin.date().toString("yyyy-MM-dd")
        query += " AND DATE(la.date_action) BETWEEN ? AND ?"
        params.extend([date_debut, date_fin])

        query += " ORDER BY la.date_action DESC LIMIT 1000"

        logs = db.fetch_all(query, tuple(params))

        # Remplir la table
        self._table.setRowCount(0)
        for log in logs:
            row = self._table.rowCount()
            self._table.insertRow(row)

            self._table.setItem(row, 0, QTableWidgetItem(str(log['id'])))
            self._table.setItem(row, 1, QTableWidgetItem(log['date_action']))
            self._table.setItem(row, 2, QTableWidgetItem(log['utilisateur']))
            self._table.setItem(row, 3, QTableWidgetItem(log['action']))
            self._table.setItem(row, 4, QTableWidgetItem(log['details']))

        self._label_count.setText(f"{len(logs)} log(s)")
