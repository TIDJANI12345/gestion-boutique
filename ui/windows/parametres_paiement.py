"""
Configuration des modes de paiement actifs.
"""
import json
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QCheckBox, QLineEdit, QScrollArea, QWidget,
    QMessageBox, QButtonGroup, QRadioButton, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ui.theme import Theme
from ui.components.dialogs import information, erreur, confirmer
from database import db

# Modes natifs (jamais supprimables)
MODES_NATIFS = {
    'especes':      {'label': 'Espèces',                          'type': 'especes'},
    'mobile_money': {'label': 'Mobile Money (Orange, MTN, Moov, Wave…)', 'type': 'mobile_money'},
    'virement':     {'label': 'Virement bancaire',                 'type': 'virement'},
    'cheque':       {'label': 'Chèque',                            'type': 'cheque'},
    'mixte':        {'label': 'Paiement mixte',                    'type': 'mixte'},
}

TYPES_LABELS = {
    'mobile_money': 'Mobile Money',
    'virement':     'Virement bancaire',
    'cheque':       'Chèque',
    'carte':        'Carte bancaire',
    'autre':        'Autre',
}

_MODES_OBSOLETES = {'orange_money', 'mtn_momo', 'moov_money', 'wave'}


def charger_config_paiement() -> dict:
    """Retourne {key: {label, actif, type}} pour tous les modes."""
    raw = db.get_parametre('modes_paiement', None)
    config = {}
    if raw:
        try:
            config = json.loads(raw)
        except Exception:
            config = {}

    # Migration : anciens modes opérateur → mobile_money
    anciens = _MODES_OBSOLETES & config.keys()
    if anciens:
        for k in anciens:
            del config[k]
        if 'mobile_money' not in config:
            config['mobile_money'] = {'label': 'Mobile Money', 'actif': True, 'type': 'mobile_money'}
        sauvegarder_config_paiement(config)

    # Migration : ajouter type aux modes sans type
    modifie = False
    for key, val in config.items():
        if 'type' not in val:
            if key in MODES_NATIFS:
                val['type'] = MODES_NATIFS[key]['type']
            else:
                val['type'] = 'autre'
            modifie = True
    if modifie:
        sauvegarder_config_paiement(config)

    # Si config vide, retourner les natifs par défaut
    if not config:
        return {k: {'label': v['label'], 'actif': True, 'type': v['type']}
                for k, v in MODES_NATIFS.items()}

    return config


def sauvegarder_config_paiement(config: dict):
    db.set_parametre('modes_paiement', json.dumps(config, ensure_ascii=False))


def modes_actifs() -> list[dict]:
    """Retourne [{key, label, type}] pour les modes actifs uniquement."""
    config = charger_config_paiement()
    return [
        {'key': k, 'label': v['label'], 'type': v.get('type', 'autre')}
        for k, v in config.items()
        if v.get('actif')
    ]


def get_type_mode(key: str) -> str:
    """Retourne le type d'un mode de paiement depuis la config."""
    config = charger_config_paiement()
    return config.get(key, {}).get('type', 'autre')


class ParametresPaiementWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modes de paiement")
        self.setMinimumSize(500, 600)
        self.resize(500, 640)
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
        scroll.setFixedHeight(230)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #E5E7EB; border-radius: 6px; }")

        scroll_w = QWidget()
        scroll_l = QVBoxLayout(scroll_w)
        scroll_l.setContentsMargins(12, 10, 12, 10)
        scroll_l.setSpacing(8)

        for key, val in self._config.items():
            is_custom = key not in MODES_NATIFS
            type_label = TYPES_LABELS.get(val.get('type', 'autre'), '')
            label_text = val['label']
            if is_custom and type_label:
                label_text = f"{val['label']}  [{type_label}]"

            cb = QCheckBox(label_text)
            cb.setChecked(val.get('actif', True))
            cb.setFont(QFont("Segoe UI", 11))
            self._checkboxes[key] = cb

            row = QHBoxLayout()
            row.addWidget(cb, 1)

            if is_custom:
                btn_del = QPushButton("✕")
                btn_del.setFixedSize(28, 28)
                btn_del.setStyleSheet(
                    f"background-color: {Theme.c('danger')}; color: white; "
                    f"border: none; border-radius: 4px; font-size: 12px;"
                )
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
            f"QFrame {{ background-color: {Theme.c('light')}; border-radius: 8px; "
            f"border: 1px solid {Theme.c('card_border')}; }}"
        )
        add_l = QVBoxLayout(add_frame)
        add_l.setContentsMargins(14, 12, 14, 12)
        add_l.setSpacing(10)

        # Nom
        nom_row = QHBoxLayout()
        nom_row.addWidget(QLabel("Nom :"))
        self._entry_new = QLineEdit()
        self._entry_new.setPlaceholderText("Ex : PayPal, Payoneer, Orange Money…")
        self._entry_new.setFont(QFont("Segoe UI", 11))
        nom_row.addWidget(self._entry_new, 1)
        add_l.addLayout(nom_row)

        # Question Mobile Money
        mm_lbl = QLabel("Ce mode est-il un Mobile Money ?")
        mm_lbl.setFont(QFont("Segoe UI", 10))
        add_l.addWidget(mm_lbl)

        mm_row = QHBoxLayout()
        self._rb_mm_group = QButtonGroup(self)
        self._rb_mm_oui = QRadioButton("Oui  (compté dans Mobile Money du rapport Z)")
        self._rb_mm_non = QRadioButton("Non")
        self._rb_mm_non.setChecked(True)
        self._rb_mm_group.addButton(self._rb_mm_oui)
        self._rb_mm_group.addButton(self._rb_mm_non)
        mm_row.addWidget(self._rb_mm_oui)
        mm_row.addWidget(self._rb_mm_non)
        mm_row.addStretch()
        add_l.addLayout(mm_row)

        # Sélecteur de type (visible seulement si "Non")
        self._type_row = QHBoxLayout()
        self._type_row.addWidget(QLabel("Type :"))
        self._combo_type = QComboBox()
        for k, v in TYPES_LABELS.items():
            if k != 'mobile_money':
                self._combo_type.addItem(v, k)
        self._combo_type.setFont(QFont("Segoe UI", 10))
        self._type_row.addWidget(self._combo_type, 1)
        add_l.addLayout(self._type_row)

        self._rb_mm_oui.toggled.connect(self._on_mm_toggle)

        btn_add = QPushButton("+ Ajouter ce mode")
        btn_add.setStyleSheet(
            f"background-color: {Theme.c('success')}; color: white; "
            f"border: none; border-radius: 4px; padding: 7px 14px; font-size: 11px;"
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

    def _on_mm_toggle(self, checked: bool):
        for i in range(self._type_row.count()):
            item = self._type_row.itemAt(i)
            if item and item.widget():
                item.widget().setVisible(not checked)

    def _ajouter_mode(self):
        label = self._entry_new.text().strip()
        if not label:
            erreur(self, "Erreur", "Veuillez saisir un nom.")
            return
        key = label.lower().replace(" ", "_")
        for c in 'éèêë':
            key = key.replace(c, 'e')
        for c in 'àâä':
            key = key.replace(c, 'a')
        for c in 'ùûü':
            key = key.replace(c, 'u')
        if key in self._config:
            erreur(self, "Erreur", f"Un mode « {label} » existe déjà.")
            return

        if self._rb_mm_oui.isChecked():
            type_mode = 'mobile_money'
        else:
            type_mode = self._combo_type.currentData()

        self._config[key] = {'label': label, 'actif': True, 'type': type_mode}
        sauvegarder_config_paiement(self._config)
        information(self, "Ajouté",
            f"Mode « {label} » ajouté (type : {TYPES_LABELS.get(type_mode, type_mode)}).\n"
            "Réouvre la fenêtre pour voir la mise à jour.")
        self._entry_new.clear()
        self._rb_mm_non.setChecked(True)

    def _supprimer_mode(self, key: str):
        label = self._config[key]['label']
        if confirmer(self, "Supprimer", f"Supprimer le mode « {label} » ?"):
            del self._config[key]
            sauvegarder_config_paiement(self._config)
            information(self, "Supprimé",
                f"Mode « {label} » supprimé.\nRéouvre la fenêtre pour voir la mise à jour.")

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
