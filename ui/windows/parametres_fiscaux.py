"""
Configuration des parametres fiscaux (TVA et devises)
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QCheckBox, QLineEdit
)
from PySide6.QtCore import Qt

from ui.theme import Theme
from ui.components.table import BoutiqueTableView, BoutiqueTableModel
from ui.components.dialogs import information, erreur
from database import db
from modules.fiscalite import Fiscalite


class ParametresFiscauxWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Parametres fiscaux")
        self.setFixedSize(700, 650)
        self.setStyleSheet(Theme.stylesheet())

        self._setup_ui()
        self._charger_devises()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setObjectName("headerFrame")
        header.setStyleSheet(f"#headerFrame {{ background-color: {Theme.c('info')}; }}")
        header.setFixedHeight(70)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        title = QLabel("Parametres fiscaux")
        title.setStyleSheet("color: white; font-size: 18pt; font-weight: bold;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(header)

        # Content
        content = QFrame()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(15)

        # === TVA Section ===
        tva_label = QLabel("TVA")
        tva_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(tva_label)

        tva_frame = QFrame()
        tva_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 4px;")
        tva_inner = QVBoxLayout(tva_frame)
        tva_inner.setContentsMargins(20, 15, 20, 15)

        self.tva_checkbox = QCheckBox("Activer la TVA sur les recus")
        self.tva_checkbox.setChecked(Fiscalite.tva_active())
        self.tva_checkbox.setStyleSheet("font-size: 11pt;")
        tva_inner.addWidget(self.tva_checkbox)

        taux_row = QHBoxLayout()
        taux_label = QLabel("Taux TVA par defaut (%):")
        taux_label.setStyleSheet("font-size: 11pt;")
        taux_row.addWidget(taux_label)

        self.taux_entry = QLineEdit()
        self.taux_entry.setFixedWidth(80)
        self.taux_entry.setAlignment(Qt.AlignCenter)
        self.taux_entry.setText(str(Fiscalite.taux_tva_defaut()))
        taux_row.addWidget(self.taux_entry)
        taux_row.addStretch()

        tva_inner.addLayout(taux_row)
        content_layout.addWidget(tva_frame)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"background-color: {Theme.c('light')};")
        sep1.setFixedHeight(1)
        content_layout.addWidget(sep1)

        # === Devise Section ===
        devise_label = QLabel("Devise")
        devise_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(devise_label)

        devise_frame = QFrame()
        devise_frame.setStyleSheet(f"background-color: {Theme.c('light')}; border-radius: 4px;")
        devise_inner = QVBoxLayout(devise_frame)
        devise_inner.setContentsMargins(20, 15, 20, 15)

        row1 = QHBoxLayout()
        code_label = QLabel("Code devise:")
        code_label.setStyleSheet("font-size: 11pt;")
        row1.addWidget(code_label)

        self.devise_code_entry = QLineEdit()
        self.devise_code_entry.setFixedWidth(80)
        self.devise_code_entry.setAlignment(Qt.AlignCenter)
        self.devise_code_entry.setText(db.get_parametre('devise_principale', 'XOF'))
        row1.addWidget(self.devise_code_entry)

        row1.addSpacing(20)

        symbole_label = QLabel("Symbole:")
        symbole_label.setStyleSheet("font-size: 11pt;")
        row1.addWidget(symbole_label)

        self.devise_symbole_entry = QLineEdit()
        self.devise_symbole_entry.setFixedWidth(80)
        self.devise_symbole_entry.setAlignment(Qt.AlignCenter)
        self.devise_symbole_entry.setText(db.get_parametre('devise_symbole', 'FCFA'))
        row1.addWidget(self.devise_symbole_entry)

        row1.addStretch()
        devise_inner.addLayout(row1)

        content_layout.addWidget(devise_frame)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet(f"background-color: {Theme.c('light')};")
        sep2.setFixedHeight(1)
        content_layout.addWidget(sep2)

        # === Taux de change ===
        change_label = QLabel("Taux de change")
        change_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {Theme.c('dark')};")
        content_layout.addWidget(change_label)

        colonnes = ["Code", "Symbole", "Taux (par rapport XOF)", "Actif"]
        self.model = BoutiqueTableModel(colonnes)
        self.table = BoutiqueTableView()
        self.table.setModel(self.model)
        self.table.setMinimumHeight(150)
        content_layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        save_btn = QPushButton("Enregistrer")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self._enregistrer)
        btn_layout.addWidget(save_btn)

        content_layout.addLayout(btn_layout)

        layout.addWidget(content)

    def _charger_devises(self):
        devises = Fiscalite.lister_devises()
        data = []
        for d in devises:
            data.append([
                d[1],  # code
                d[2],  # symbole
                f"{d[3]:,.2f}",  # taux
                "Oui" if d[4] else "Non"  # actif
            ])
        self.model.charger_donnees(data)

    def _enregistrer(self):
        # Validate TVA rate
        try:
            taux = float(self.taux_entry.text())
            if taux < 0 or taux > 100:
                erreur(self, "Erreur", "Le taux TVA doit etre entre 0 et 100")
                return
        except ValueError:
            erreur(self, "Erreur", "Taux TVA invalide")
            return

        # Validate devise
        code = self.devise_code_entry.text().strip().upper()
        symbole = self.devise_symbole_entry.text().strip()

        if not code or not symbole:
            erreur(self, "Erreur", "Code et symbole de devise requis")
            return

        # Save parameters
        db.set_parametre('tva_active', '1' if self.tva_checkbox.isChecked() else '0')
        db.set_parametre('tva_taux_defaut', str(taux))
        db.set_parametre('devise_principale', code)
        db.set_parametre('devise_symbole', symbole)

        information(self, "Succes", "Parametres fiscaux enregistres!")
        self.accept()
