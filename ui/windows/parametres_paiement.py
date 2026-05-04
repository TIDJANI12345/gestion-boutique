"""
Configuration des modes de paiement actifs.
"""
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QCheckBox, QLineEdit, QScrollArea, QWidget,
    QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import Theme
from ui.components.dialogs import information, erreur, confirmer
from database import db

# Modes natifs (toujours disponibles, jamais supprimables)
MODES_NATIFS = {
    'especes':       'Espèces',
    'mobile_money':  'Mobile Money (Orange, MTN, Moov, Wave…)',
    'virement':      'Virement bancaire',
    'cheque':        'Chèque',
    'mixte':         'Paiement mixte',
}


_MODES_OBSOLETES = {'orange_money', 'mtn_momo', 'moov_money', 'wave'}


def charger_config_paiement() -> dict:
    """Retourne {key: {label, actif}} pour tous les modes (natifs + custom)."""
    raw = db.get_parametre('modes_paiement', None)
    if raw:
        try:
            config = json.loads(raw)
            # Migrer les anciens modes opérateur vers mobile_money
            anciens_presents = _MODES_OBSOLETES & config.keys()
            if anciens_presents:
                for k in anciens_presents:
                    del config[k]
                if 'mobile_money' not in config:
                    config['mobile_money'] = {'label': 'Mobile Money', 'actif': True}
                sauvegarder_config_paiement(config)
            return config
        except Exception:
            pass
    # Valeur par défaut : tous actifs
    return {k: {'label': v, 'actif': True} for k, v in MODES_NATIFS.items()}


def sauvegarder_config_paiement(config: dict):
    db.set_parametre('modes_paiement', json.dumps(config, ensure_ascii=False))


def modes_actifs() -> list[dict]:
    """Retourne [{key, label}] pour les modes actifs uniquement."""
    config = charger_config_paiement()
    return [{'key': k, 'label': v['label']} for k, v in config.items() if v.get('actif')]


class ParametresPaiementWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modes de paiement")
        self.setFixedSize(480, 560)
        self.setModal(True)
        self._config = charger_config_paiement()
        self._checkboxes = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(65)
        header.setStyleSheet(f"background-color: {Theme.c('primary')};")
        h = QHBoxLayout(header)
        h.setContentsMargins(24, 0, 24, 0)
        lbl = QLabel("Modes de paiement")
        lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        lbl.setStyleSheet("color: white; background: transparent;")
        h.addWidget(lbl)
        layout.addWidget(header)

        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 20, 24, 20)
        cl.setSpacing(14)

        # ── Modes existants ──
        lbl_modes = QLabel("Activer / désactiver les modes")
        lbl_modes.setFont(QFont("Segoe UI", 11, QFont.Bold))
        cl.addWidget(lbl_modes)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(220)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E5E7EB; border-radius: 6px; }")

        scroll_w = QWidget()
        scroll_l = QVBoxLayout(scroll_w)
        scroll_l.setContentsMargins(12, 10, 12, 10)
        scroll_l.setSpacing(8)

        for key, val in self._config.items():
            cb = QCheckBox(val['label'])
            cb.setChecked(val.get('actif', True))
            cb.setFont(QFont("Segoe UI", 11))
            # Marquer les modes custom
            if key not in MODES_NATIFS:
                cb.setText(f"{val['label']}  (personnalisé)")
            self._checkboxes[key] = cb

            row = QHBoxLayout()
            row.addWidget(cb, 1)

            if key not in MODES_NATIFS:
                btn_del = QPushButton("Supprimer")
                btn_del.setFixedHeight(28)
                btn_del.setStyleSheet(
                    f"background-color: {Theme.c('danger')}; color: white; "
                    f"border: none; border-radius: 4px; padding: 0 10px; font-size: 11px;"
                )
                btn_del.setToolTip(f"Supprimer le mode personnalisé « {val['label']} »")
                btn_del.setCursor(Qt.PointingHandCursor)
                btn_del.clicked.connect(lambda _, k=key: self._supprimer_mode(k))
                row.addWidget(btn_del)

            scroll_l.addLayout(row)

        scroll_l.addStretch()
        scroll.setWidget(scroll_w)
        cl.addWidget(scroll)

        # ── Ajouter un mode personnalisé ──
        lbl_add = QLabel("Ajouter un mode personnalisé")
        lbl_add.setFont(QFont("Segoe UI", 11, QFont.Bold))
        cl.addWidget(lbl_add)

        add_frame = QFrame()
        add_frame.setStyleSheet(
            f"QFrame {{ background-color: {Theme.c('light')}; border-radius: 6px; "
            f"border: 1px solid {Theme.c('card_border')}; }}"
        )
        add_l = QHBoxLayout(add_frame)
        add_l.setContentsMargins(12, 10, 12, 10)

        self._entry_new = QLineEdit()
        self._entry_new.setPlaceholderText("Ex: Wave, Virement, Chèque…")
        self._entry_new.setFont(QFont("Segoe UI", 11))
        add_l.addWidget(self._entry_new, 1)

        btn_add = QPushButton("Ajouter")
        btn_add.setStyleSheet(
            f"background-color: {Theme.c('success')}; color: white; "
            f"border: none; border-radius: 4px; padding: 6px 14px;"
        )
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self._ajouter_mode)
        add_l.addWidget(btn_add)

        cl.addWidget(add_frame)
        cl.addStretch()

        # ── Boutons ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setMinimumHeight(38)
        btn_annuler.setCursor(Qt.PointingHandCursor)
        btn_annuler.clicked.connect(self.reject)
        btn_row.addWidget(btn_annuler)

        btn_save = QPushButton("Enregistrer")
        btn_save.setMinimumHeight(38)
        btn_save.setStyleSheet(
            f"background-color: {Theme.c('primary')}; color: white; "
            f"border: none; border-radius: 4px; padding: 6px 20px;"
        )
        btn_save.setCursor(Qt.PointingHandCursor)
        btn_save.clicked.connect(self._enregistrer)
        btn_row.addWidget(btn_save)

        cl.addLayout(btn_row)
        layout.addWidget(content, 1)

    def _ajouter_mode(self):
        label = self._entry_new.text().strip()
        if not label:
            return
        key = label.lower().replace(" ", "_").replace("é", "e").replace("è", "e")
        if key in self._config:
            erreur(self, "Erreur", f"Un mode '{label}' existe déjà.")
            return
        self._config[key] = {'label': label, 'actif': True}
        information(self, "Ajouté", f"Mode '{label}' ajouté.\nFerme et réouvre pour voir la modification.")
        self._entry_new.clear()

    def _supprimer_mode(self, key: str):
        label = self._config[key]['label']
        if confirmer(self, "Supprimer", f"Supprimer le mode '{label}' ?"):
            del self._config[key]
            information(self, "Supprimé", f"Mode '{label}' supprimé.\nFerme et réouvre pour voir la modification.")

    def _enregistrer(self):
        actif_count = 0
        for key, cb in self._checkboxes.items():
            if key in self._config:
                self._config[key]['actif'] = cb.isChecked()
                if cb.isChecked():
                    actif_count += 1

        if actif_count == 0:
            erreur(self, "Erreur", "Au moins un mode de paiement doit être actif.")
            return

        sauvegarder_config_paiement(self._config)
        information(self, "Succès", "Modes de paiement enregistrés.")
        self.accept()
