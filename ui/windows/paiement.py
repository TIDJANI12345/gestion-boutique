"""
Fenetre de paiement - PySide6
Dialogue modal : especes, mobile money (Orange/MTN/Moov), mixte.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QRadioButton, QButtonGroup, QFrame,
    QMessageBox, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ui.theme import Theme


class PaiementWindow(QDialog):
    """Dialogue de paiement. Retourne la liste des paiements via result()."""

    paiement_confirme = Signal(list)  # liste de dicts paiement

    def __init__(self, total: float, parent=None):
        super().__init__(parent)
        self.total = total
        self._result = None

        self.setWindowTitle("Paiement")
        self.setFixedSize(550, 620)
        self.setModal(True)

        self._setup_ui()

    @property
    def resultat(self) -> list | None:
        return self._result

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # En-tete
        header = QFrame()
        header.setFixedHeight(90)
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(30, 0, 30, 0)

        titre = QLabel("Paiement")
        titre.setFont(QFont("Segoe UI", 20, QFont.Bold))
        titre.setStyleSheet("color: white; background: transparent;")
        h_layout.addWidget(titre)

        h_layout.addStretch()

        montant = QLabel(f"{self.total:,.0f} FCFA")
        montant.setFont(QFont("Segoe UI", 22, QFont.Bold))
        montant.setStyleSheet("color: white; background: transparent;")
        h_layout.addWidget(montant)

        layout.addWidget(header)

        # Contenu
        content = QWidget()
        c_layout = QVBoxLayout(content)
        c_layout.setContentsMargins(30, 20, 30, 20)
        c_layout.setSpacing(8)

        # Mode de paiement
        lbl_mode = QLabel("Mode de paiement")
        lbl_mode.setFont(QFont("Segoe UI", 13, QFont.Bold))
        c_layout.addWidget(lbl_mode)

        self._mode_group = QButtonGroup(self)
        modes = [
            ('especes', 'Especes'),
            ('orange_money', 'Orange Money'),
            ('mtn_momo', 'MTN MoMo'),
            ('moov_money', 'Moov Money'),
            ('mixte', 'Paiement mixte'),
        ]
        for value, label in modes:
            rb = QRadioButton(label)
            rb.setProperty("mode", value)
            rb.setStyleSheet("font-size: 12px; padding: 4px 0;")
            self._mode_group.addButton(rb)
            c_layout.addWidget(rb)
            if value == 'especes':
                rb.setChecked(True)

        self._mode_group.buttonClicked.connect(self._on_mode_change)

        # Separateur
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {Theme.c('separator')};")
        c_layout.addWidget(sep)

        # Zone dynamique
        self._zone_saisie = QVBoxLayout()
        c_layout.addLayout(self._zone_saisie)

        c_layout.addStretch()

        # Boutons
        btn_confirmer = QPushButton("Confirmer le paiement")
        btn_confirmer.setProperty("class", "success")
        btn_confirmer.setFont(QFont("Segoe UI", 13, QFont.Bold))
        btn_confirmer.setMinimumHeight(50)
        btn_confirmer.setCursor(Qt.PointingHandCursor)
        btn_confirmer.clicked.connect(self._confirmer)
        c_layout.addWidget(btn_confirmer)

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setProperty("class", "danger")
        btn_annuler.setMinimumHeight(42)
        btn_annuler.setCursor(Qt.PointingHandCursor)
        btn_annuler.clicked.connect(self.reject)
        c_layout.addWidget(btn_annuler)

        layout.addWidget(content, 1)

        # Afficher les champs du mode par defaut
        self._on_mode_change()

    def _clear_zone(self):
        while self._zone_saisie.count():
            item = self._zone_saisie.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _mode_actuel(self) -> str:
        btn = self._mode_group.checkedButton()
        return btn.property("mode") if btn else "especes"

    def _on_mode_change(self):
        self._clear_zone()
        mode = self._mode_actuel()

        if mode == 'especes':
            self._champs_especes()
        elif mode in ('orange_money', 'mtn_momo', 'moov_money'):
            self._champs_mobile()
        elif mode == 'mixte':
            self._champs_mixte()

    def _champs_especes(self):
        lbl = QLabel("Montant recu du client:")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._zone_saisie.addWidget(lbl)

        self._entry_montant_recu = QLineEdit()
        self._entry_montant_recu.setFont(QFont("Segoe UI", 16))
        self._entry_montant_recu.setAlignment(Qt.AlignCenter)
        self._entry_montant_recu.setText(str(int(self.total)))
        self._entry_montant_recu.selectAll()
        self._entry_montant_recu.textChanged.connect(self._calculer_monnaie)
        self._zone_saisie.addWidget(self._entry_montant_recu)

        self._label_monnaie = QLabel(f"Monnaie a rendre: 0 FCFA")
        self._label_monnaie.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._label_monnaie.setStyleSheet(f"color: {Theme.c('success')};")
        self._label_monnaie.setAlignment(Qt.AlignCenter)
        self._zone_saisie.addWidget(self._label_monnaie)

        self._entry_montant_recu.setFocus()

    def _calculer_monnaie(self):
        try:
            recu = float(self._entry_montant_recu.text().replace(",", "").replace(" ", ""))
            monnaie = recu - self.total
            if monnaie >= 0:
                self._label_monnaie.setText(f"Monnaie a rendre: {monnaie:,.0f} FCFA")
                self._label_monnaie.setStyleSheet(f"color: {Theme.c('success')};")
            else:
                self._label_monnaie.setText(f"Insuffisant: {monnaie:,.0f} FCFA")
                self._label_monnaie.setStyleSheet(f"color: {Theme.c('danger')};")
        except ValueError:
            self._label_monnaie.setText("Montant invalide")
            self._label_monnaie.setStyleSheet(f"color: {Theme.c('danger')};")

    def _champs_mobile(self):
        lbl = QLabel("Reference de la transaction:")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._zone_saisie.addWidget(lbl)

        self._entry_reference = QLineEdit()
        self._entry_reference.setFont(QFont("Segoe UI", 14))
        self._entry_reference.setAlignment(Qt.AlignCenter)
        self._zone_saisie.addWidget(self._entry_reference)

        info = QLabel(f"Montant: {self.total:,.0f} FCFA")
        info.setFont(QFont("Segoe UI", 14, QFont.Bold))
        info.setStyleSheet(f"color: {Theme.c('primary')};")
        info.setAlignment(Qt.AlignCenter)
        self._zone_saisie.addWidget(info)

        self._entry_reference.setFocus()

    def _champs_mixte(self):
        # Especes
        lbl1 = QLabel("Montant en especes:")
        lbl1.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._zone_saisie.addWidget(lbl1)

        self._entry_mixte_especes = QLineEdit("0")
        self._entry_mixte_especes.setFont(QFont("Segoe UI", 14))
        self._entry_mixte_especes.setAlignment(Qt.AlignCenter)
        self._entry_mixte_especes.textChanged.connect(self._maj_mixte)
        self._zone_saisie.addWidget(self._entry_mixte_especes)

        # Mode mobile
        lbl2 = QLabel("Mode Mobile Money:")
        lbl2.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._zone_saisie.addWidget(lbl2)

        self._mixte_mobile_group = QButtonGroup(self)
        mobile_frame = QWidget()
        mobile_layout = QHBoxLayout(mobile_frame)
        mobile_layout.setContentsMargins(0, 0, 0, 0)
        for val, lbl in [('orange_money', 'Orange'), ('mtn_momo', 'MTN'), ('moov_money', 'Moov')]:
            rb = QRadioButton(lbl)
            rb.setProperty("mode", val)
            self._mixte_mobile_group.addButton(rb)
            mobile_layout.addWidget(rb)
            if val == 'orange_money':
                rb.setChecked(True)
        self._zone_saisie.addWidget(mobile_frame)

        # Montant mobile
        lbl3 = QLabel("Montant Mobile Money:")
        lbl3.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._zone_saisie.addWidget(lbl3)

        self._entry_mixte_mobile = QLineEdit(str(int(self.total)))
        self._entry_mixte_mobile.setFont(QFont("Segoe UI", 14))
        self._entry_mixte_mobile.setAlignment(Qt.AlignCenter)
        self._entry_mixte_mobile.textChanged.connect(self._maj_mixte)
        self._zone_saisie.addWidget(self._entry_mixte_mobile)

        # Reference
        lbl4 = QLabel("Reference transaction:")
        lbl4.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self._zone_saisie.addWidget(lbl4)

        self._entry_mixte_ref = QLineEdit()
        self._entry_mixte_ref.setFont(QFont("Segoe UI", 12))
        self._zone_saisie.addWidget(self._entry_mixte_ref)

        # Info
        self._label_mixte_info = QLabel("")
        self._label_mixte_info.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self._label_mixte_info.setAlignment(Qt.AlignCenter)
        self._zone_saisie.addWidget(self._label_mixte_info)

        self._entry_mixte_especes.setFocus()
        self._maj_mixte()

    def _maj_mixte(self):
        try:
            especes = float(self._entry_mixte_especes.text().replace(",", "").replace(" ", "") or "0")
            mobile = float(self._entry_mixte_mobile.text().replace(",", "").replace(" ", "") or "0")
            somme = especes + mobile
            diff = somme - self.total

            if abs(diff) < 0.01:
                self._label_mixte_info.setText(f"Total: {somme:,.0f} FCFA - OK")
                self._label_mixte_info.setStyleSheet(f"color: {Theme.c('success')};")
            elif diff > 0:
                self._label_mixte_info.setText(f"Total: {somme:,.0f} FCFA (excedent: {diff:,.0f})")
                self._label_mixte_info.setStyleSheet(f"color: {Theme.c('warning')};")
            else:
                self._label_mixte_info.setText(f"Total: {somme:,.0f} FCFA (manque: {-diff:,.0f})")
                self._label_mixte_info.setStyleSheet(f"color: {Theme.c('danger')};")
        except ValueError:
            self._label_mixte_info.setText("Montants invalides")
            self._label_mixte_info.setStyleSheet(f"color: {Theme.c('danger')};")

    def _confirmer(self):
        mode = self._mode_actuel()

        try:
            if mode == 'especes':
                montant_recu = float(
                    self._entry_montant_recu.text().replace(",", "").replace(" ", "")
                )
                if montant_recu < self.total:
                    QMessageBox.critical(self, "Erreur", "Le montant recu est insuffisant!")
                    return
                monnaie = montant_recu - self.total
                self._result = [{
                    'mode': 'especes', 'montant': self.total,
                    'reference': None, 'montant_recu': montant_recu,
                    'monnaie_rendue': monnaie,
                }]

            elif mode in ('orange_money', 'mtn_momo', 'moov_money'):
                reference = self._entry_reference.text().strip()
                if not reference:
                    QMessageBox.critical(self, "Erreur",
                                         "Veuillez saisir la reference de la transaction!")
                    return
                self._result = [{
                    'mode': mode, 'montant': self.total,
                    'reference': reference, 'montant_recu': None,
                    'monnaie_rendue': None,
                }]

            elif mode == 'mixte':
                especes = float(
                    self._entry_mixte_especes.text().replace(",", "").replace(" ", "") or "0"
                )
                mobile = float(
                    self._entry_mixte_mobile.text().replace(",", "").replace(" ", "") or "0"
                )
                if especes + mobile < self.total:
                    QMessageBox.critical(self, "Erreur",
                        f"La somme ({especes + mobile:,.0f}) est inferieure au total ({self.total:,.0f})!")
                    return

                mobile_btn = self._mixte_mobile_group.checkedButton()
                mode_mobile = mobile_btn.property("mode") if mobile_btn else "orange_money"
                reference = self._entry_mixte_ref.text().strip()
                if mobile > 0 and not reference:
                    QMessageBox.critical(self, "Erreur",
                                         "Veuillez saisir la reference Mobile Money!")
                    return

                self._result = []
                if especes > 0:
                    self._result.append({
                        'mode': 'especes', 'montant': especes,
                        'reference': None, 'montant_recu': especes,
                        'monnaie_rendue': 0,
                    })
                if mobile > 0:
                    self._result.append({
                        'mode': mode_mobile, 'montant': mobile,
                        'reference': reference, 'montant_recu': None,
                        'monnaie_rendue': None,
                    })

            self.paiement_confirme.emit(self._result)
            self.accept()

        except ValueError:
            QMessageBox.critical(self, "Erreur", "Montant invalide!")
