"""
Préférences caisse — paramètres par poste (accessible à tous les rôles).
Scanner, son, caméra, écran client, remise, imprimante, apparence.
"""
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFrame, QLabel,
    QPushButton, QRadioButton, QButtonGroup, QCheckBox, QScrollArea, QLineEdit,
    QComboBox, QFileDialog, QColorDialog, QSpinBox
)
from PySide6.QtCore import Qt

from ui.theme import Theme
from ui.components.dialogs import information, erreur
from database import db


class PreferencesCaisseWindow(QDialog):

    def _chk(self, texte, bold=True):
        cb = QCheckBox(texte)
        weight = "bold" if bold else "normal"
        cb.setStyleSheet(f"""
            QCheckBox {{ color:{Theme.c('text')}; font-size:11pt; font-weight:{weight}; spacing:8px; }}
            QCheckBox::indicator {{ width:18px; height:18px; border-radius:4px;
                border:2px solid {Theme.c('input_border')}; background:{Theme.c('input_bg')}; }}
            QCheckBox::indicator:hover {{ border-color:{Theme.c('primary')}; }}
            QCheckBox::indicator:checked {{ background:{Theme.c('primary')}; border-color:{Theme.c('primary')}; }}
            QCheckBox:disabled {{ color:{Theme.c('gray')}; }}
        """)
        cb.stateChanged.connect(self._marquer_modifie)
        return cb

    def _radio(self, texte, bold=True):
        rb = QRadioButton(texte)
        weight = "bold" if bold else "normal"
        rb.setStyleSheet(f"""
            QRadioButton {{ color:{Theme.c('text')}; font-size:11pt; font-weight:{weight}; spacing:8px; }}
            QRadioButton::indicator {{ width:18px; height:18px; border-radius:9px;
                border:2px solid {Theme.c('input_border')}; background:{Theme.c('input_bg')}; }}
            QRadioButton::indicator:hover {{ border-color:{Theme.c('primary')}; }}
            QRadioButton::indicator:checked {{ background:{Theme.c('primary')}; border-color:{Theme.c('primary')}; }}
        """)
        rb.toggled.connect(self._marquer_modifie)
        return rb

    def _section(self, titre):
        lbl = QLabel(titre)
        lbl.setStyleSheet(f"font-size:13pt; font-weight:bold; color:{Theme.c('text')};")
        return lbl

    def _frame(self):
        f = QFrame()
        f.setStyleSheet(f"background:{Theme.c('light')}; border-radius:8px; padding:16px;")
        return f

    def _marquer_modifie(self, *_):
        self._modifie = True
        if hasattr(self, '_btn_enregistrer'):
            self._btn_enregistrer.setStyleSheet(self._style_save_actif())

    def _style_save_actif(self):
        return (f"QPushButton {{ background:{Theme.c('success')}; color:white; "
                f"padding:12px 30px; font-size:11pt; font-weight:bold; border-radius:6px; border:none; }}"
                f"QPushButton:hover {{ background:{Theme.c('success_hover')}; }}")

    def _style_save_neutre(self):
        return (f"QPushButton {{ background:{Theme.c('card_border')}; color:{Theme.c('text_secondary')}; "
                f"padding:12px 30px; font-size:11pt; font-weight:bold; border-radius:6px; border:none; }}")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Préférences caisse")
        self.setMinimumSize(680, 580)
        self._modifie = False
        self._setup_ui()
        self._charger_parametres()
        self._modifie = False  # reset après chargement — évite le "dirty" à l'ouverture

        for w in self.findChildren(QLineEdit):
            w.textChanged.connect(self._marquer_modifie)
        for w in self.findChildren(QComboBox):
            w.currentIndexChanged.connect(self._marquer_modifie)

        if self.parent():
            self.adjustSize()
            parent_rect = self.parent().frameGeometry()
            dlg_rect = self.frameGeometry()
            dlg_rect.moveCenter(parent_rect.center())
            self.move(dlg_rect.topLeft())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(f"background:{Theme.c('primary')};")
        header.setFixedHeight(65)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(30, 0, 30, 0)
        title = QLabel("Préférences caisse")
        title.setStyleSheet("color:white; font-size:17pt; font-weight:bold;")
        hl.addWidget(title)
        sub = QLabel("Paramètres propres à ce poste")
        sub.setStyleSheet("color:rgba(255,255,255,0.75); font-size:10pt;")
        hl.addStretch()
        hl.addWidget(sub)
        layout.addWidget(header)

        content = QFrame()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(30, 24, 30, 24)
        cl.setSpacing(20)

        # === COMPORTEMENT AU SCAN ===
        cl.addWidget(self._section("Comportement au scan"))
        desc = QLabel("Comportement après la détection d'un code-barres.")
        desc.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:10pt;")
        cl.addWidget(desc)

        mode_frame = self._frame()
        mfl = QVBoxLayout(mode_frame)
        mfl.setSpacing(12)
        self.radio_group = QButtonGroup(self)
        self.radio_auto = self._radio("Automatique — ajouter directement avec quantité 1")
        self.radio_group.addButton(self.radio_auto, 1)
        mfl.addWidget(self.radio_auto)
        auto_desc = QLabel("Re-scan du même article → quantité s'incrémente.")
        auto_desc.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:9pt; margin-left:26px;")
        mfl.addWidget(auto_desc)
        self.radio_manuel = self._radio("Manuel — demander la quantité à chaque scan")
        self.radio_group.addButton(self.radio_manuel, 0)
        mfl.addWidget(self.radio_manuel)
        manuel_desc = QLabel("Une popup s'ouvre à chaque scan.")
        manuel_desc.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:9pt; margin-left:26px;")
        mfl.addWidget(manuel_desc)
        cl.addWidget(mode_frame)
        f9 = QLabel("Astuce : F9 dans la fenêtre Ventes pour basculer rapidement")
        f9.setStyleSheet(f"color:{Theme.c('info')}; font-size:9pt; font-style:italic;")
        cl.addWidget(f9)

        # === ÉCRAN CLIENT ===
        cl.addWidget(self._section("Écran client"))
        ec_frame = self._frame()
        ecl = QVBoxLayout(ec_frame)
        self.checkbox_ecran_client = self._chk("Afficher l'écran client lors des ventes")
        ecl.addWidget(self.checkbox_ecran_client)
        ec_info = QLabel("Ouvre une fenêtre face au client avec les articles et le total en temps réel.\n"
                         "Sur 2 écrans : s'affiche automatiquement sur le 2ème écran.")
        ec_info.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:9pt; margin-left:26px;")
        ec_info.setWordWrap(True)
        ecl.addWidget(ec_info)
        cl.addWidget(ec_frame)

        # === SON ===
        cl.addWidget(self._section("Son de confirmation"))
        son_frame = self._frame()
        sfl = QVBoxLayout(son_frame)
        self.checkbox_son = self._chk("Activer le son de scan")
        sfl.addWidget(self.checkbox_son)
        sfl.addWidget(QLabel("Un bip court est joué à chaque ajout au panier."))
        cl.addWidget(son_frame)

        # === CAMÉRA ===
        cl.addWidget(self._section("Scanner caméra"))
        cam_desc = QLabel("Activez uniquement si vous n'avez pas de lecteur de codes-barres USB.")
        cam_desc.setStyleSheet(f"color:{Theme.c('text_secondary')}; font-size:10pt;")
        cam_desc.setWordWrap(True)
        cl.addWidget(cam_desc)

        cam_frame = self._frame()
        caml = QVBoxLayout(cam_frame)
        caml.setSpacing(10)
        self.checkbox_camera_actif = self._chk("Activer le scanner caméra")
        caml.addWidget(self.checkbox_camera_actif)

        self._camera_suboptions = QFrame()
        subl = QVBoxLayout(self._camera_suboptions)
        subl.setContentsMargins(20, 0, 0, 0)
        subl.setSpacing(8)
        self.checkbox_camera_auto = self._chk("Ouvrir la caméra automatiquement à l'ouverture des Ventes", bold=False)
        subl.addWidget(self.checkbox_camera_auto)
        src_lbl = QLabel("Source caméra :")
        src_lbl.setStyleSheet("font-size:10pt; font-weight:bold;")
        subl.addWidget(src_lbl)
        src_row = QHBoxLayout()
        self.input_camera_source = QLineEdit()
        self.input_camera_source.setPlaceholderText("0 (webcam PC) ou http://IP:PORT/video (téléphone)")
        self.input_camera_source.setStyleSheet(f"padding:8px; border:1px solid {Theme.c('gray')}; border-radius:4px;")
        src_row.addWidget(self.input_camera_source)
        btn_test_cam = QPushButton("Tester")
        btn_test_cam.setStyleSheet(f"background:{Theme.c('info')}; color:white; padding:8px 14px; border-radius:4px; font-weight:bold;")
        btn_test_cam.clicked.connect(self._tester_camera)
        src_row.addWidget(btn_test_cam)
        subl.addLayout(src_row)
        subl.addWidget(QLabel("0 = webcam intégrée · 1 = 2ème webcam USB"))
        caml.addWidget(self._camera_suboptions)
        self.checkbox_camera_actif.toggled.connect(self._camera_suboptions.setEnabled)
        cl.addWidget(cam_frame)

        # === REMISE PAR DÉFAUT ===
        cl.addWidget(self._section("Remise par défaut"))
        rem_frame = self._frame()
        rfl = QVBoxLayout(rem_frame)
        rfl.setSpacing(8)
        self.radio_remise_group = QButtonGroup(self)
        self.radio_remise_pct     = self._radio("% Pourcentage  (ex: 10 %)")
        self.radio_remise_montant = self._radio("FCFA Montant fixe  (ex: 500 FCFA)")
        self.radio_remise_group.addButton(self.radio_remise_pct, 0)
        self.radio_remise_group.addButton(self.radio_remise_montant, 1)
        rfl.addWidget(self.radio_remise_pct)
        rfl.addWidget(self.radio_remise_montant)
        cl.addWidget(rem_frame)

        # === IMPRESSION THERMIQUE ===
        cl.addWidget(self._section("Impression thermique"))
        imp_frame = self._frame()
        ifl = QVBoxLayout(imp_frame)
        ifl.setSpacing(8)
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode :"))
        self.combo_imp_mode = QComboBox()
        self.combo_imp_mode.addItems(["USB", "Réseau (IP)", "Série (COM)"])
        mode_row.addWidget(self.combo_imp_mode, 1)
        ifl.addLayout(mode_row)
        self.chk_ticket_auto = self._chk("Imprimer le ticket automatiquement après chaque vente")
        ifl.addWidget(self.chk_ticket_auto)
        btn_test_imp = QPushButton("Imprimer ticket de test")
        btn_test_imp.setProperty("class", "secondary")
        btn_test_imp.setCursor(Qt.PointingHandCursor)
        btn_test_imp.clicked.connect(self._tester_impression)
        ifl.addWidget(btn_test_imp)
        cl.addWidget(imp_frame)

        # === APPARENCE ===
        cl.addWidget(self._section("Apparence"))
        app_frame = self._frame()
        afl = QHBoxLayout(app_frame)
        afl.setSpacing(12)
        afl.addWidget(QLabel("Couleur principale :"))
        self._btn_couleur = QPushButton()
        self._btn_couleur.setFixedSize(40, 40)
        self._btn_couleur.setCursor(Qt.PointingHandCursor)
        self._btn_couleur.clicked.connect(self._choisir_couleur)
        afl.addWidget(self._btn_couleur)
        self._lbl_couleur_hex = QLabel()
        self._lbl_couleur_hex.setStyleSheet(f"color:{Theme.c('gray')}; font-size:10pt; font-family:Consolas;")
        afl.addWidget(self._lbl_couleur_hex)
        afl.addStretch()
        btn_reset = QPushButton("Réinitialiser")
        btn_reset.setProperty("class", "secondary")
        btn_reset.setCursor(Qt.PointingHandCursor)
        btn_reset.clicked.connect(self._reinitialiser_couleur)
        afl.addWidget(btn_reset)
        cl.addWidget(app_frame)

        cl.addStretch()

        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet(f"background:{Theme.c('light')}; color:{Theme.c('text')}; "
                                f"padding:12px 24px; font-size:11pt; border-radius:6px; "
                                f"border:1px solid {Theme.c('card_border')};")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)
        self._btn_enregistrer = QPushButton("Enregistrer")
        self._btn_enregistrer.setCursor(Qt.PointingHandCursor)
        self._btn_enregistrer.setStyleSheet(self._style_save_neutre())
        self._btn_enregistrer.clicked.connect(self._enregistrer)
        btn_layout.addWidget(self._btn_enregistrer)
        cl.addLayout(btn_layout)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border:none; }")
        scroll.setWidget(content)
        layout.addWidget(scroll)

    def _charger_parametres(self):
        mode_auto = db.get_parametre('mode_scan_auto', '1') == '1'
        self.radio_auto.setChecked(mode_auto)
        self.radio_manuel.setChecked(not mode_auto)

        self.checkbox_ecran_client.setChecked(db.get_parametre('ecran_client_actif', '0') == '1')
        self.checkbox_son.setChecked(db.get_parametre('son_scan_actif', '1') == '1')

        camera_actif = db.get_parametre('scanner_camera_actif', '0') == '1'
        self.checkbox_camera_actif.setChecked(camera_actif)
        self._camera_suboptions.setEnabled(camera_actif)
        self.checkbox_camera_auto.setChecked(db.get_parametre('camera_auto_start', '0') == '1')
        self.input_camera_source.setText(db.get_parametre('camera_source', '0'))

        remise_pct = db.get_parametre('remise_type_defaut', 'pct') == 'pct'
        self.radio_remise_pct.setChecked(remise_pct)
        self.radio_remise_montant.setChecked(not remise_pct)

        mode_imp = db.get_parametre('imprimante_mode', 'usb')
        self.combo_imp_mode.setCurrentIndex({'usb': 0, 'reseau': 1, 'serie': 2}.get(mode_imp, 0))
        self.chk_ticket_auto.setChecked(db.get_parametre('ticket_auto_impression', '1') == '1')

        couleur = db.get_parametre('theme_couleur_primaire', Theme.c('primary'))
        self._actualiser_btn_couleur(couleur)

    def _enregistrer(self):
        db.set_parametre('mode_scan_auto', '1' if self.radio_auto.isChecked() else '0')
        db.set_parametre('ecran_client_actif', '1' if self.checkbox_ecran_client.isChecked() else '0')
        db.set_parametre('son_scan_actif', '1' if self.checkbox_son.isChecked() else '0')
        db.set_parametre('son_scan_type', 'beep')
        db.set_parametre('scanner_camera_actif', '1' if self.checkbox_camera_actif.isChecked() else '0')
        db.set_parametre('camera_auto_start', '1' if self.checkbox_camera_auto.isChecked() else '0')
        db.set_parametre('camera_source', self.input_camera_source.text().strip() or '0')
        mode_imp_map = ['usb', 'reseau', 'serie']
        db.set_parametre('imprimante_mode', mode_imp_map[self.combo_imp_mode.currentIndex()])
        db.set_parametre('ticket_auto_impression', '1' if self.chk_ticket_auto.isChecked() else '0')
        db.set_parametre('remise_type_defaut', 'pct' if self.radio_remise_pct.isChecked() else 'montant')

        self._modifie = False
        self._btn_enregistrer.setStyleSheet(self._style_save_neutre())
        information(self, "Préférences sauvegardées", "Paramètres enregistrés avec succès.")
        self.accept()

    def reject(self):
        if self._modifie:
            from PySide6.QtWidgets import QMessageBox
            rep = QMessageBox.question(
                self, "Modifications non sauvegardées",
                "Voulez-vous enregistrer avant de fermer ?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if rep == QMessageBox.Save:
                self._enregistrer()
                return
            elif rep == QMessageBox.Cancel:
                return
        super().reject()

    def closeEvent(self, event):
        if self._modifie:
            from PySide6.QtWidgets import QMessageBox
            rep = QMessageBox.question(
                self, "Modifications non sauvegardées",
                "Voulez-vous enregistrer avant de fermer ?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            if rep == QMessageBox.Save:
                self._enregistrer()
                event.accept()
            elif rep == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _actualiser_btn_couleur(self, hex_color):
        from PySide6.QtGui import QColor
        if not QColor(hex_color).isValid():
            hex_color = Theme.c('primary')
        self._btn_couleur.setStyleSheet(
            f"QPushButton {{ background:{hex_color}; border-radius:6px; border:2px solid rgba(0,0,0,0.2); }}"
            f"QPushButton:hover {{ border:2px solid rgba(0,0,0,0.4); }}")
        self._lbl_couleur_hex.setText(hex_color.upper())

    def _choisir_couleur(self):
        from PySide6.QtGui import QColor
        couleur_actuelle = db.get_parametre('theme_couleur_primaire', Theme.c('primary'))
        couleur = QColorDialog.getColor(QColor(couleur_actuelle), self, "Choisir la couleur principale")
        if couleur.isValid():
            hex_color = couleur.name()
            Theme.appliquer_couleur_primaire(hex_color, sauvegarder=True)
            self._actualiser_btn_couleur(hex_color)

    def _reinitialiser_couleur(self):
        hex_default = '#3B82F6'
        Theme.appliquer_couleur_primaire(hex_default, sauvegarder=True)
        self._actualiser_btn_couleur(hex_default)

    def _tester_impression(self):
        from modules.imprimante import ImprimanteThermique
        if not ImprimanteThermique.est_disponible():
            erreur(self, "Module manquant", "python-escpos n'est pas installé.")
            return
        mode_imp_map = ['usb', 'reseau', 'serie']
        db.set_parametre('imprimante_mode', mode_imp_map[self.combo_imp_mode.currentIndex()])
        ok, msg = ImprimanteThermique.imprimer_test()
        if ok:
            information(self, "Test réussi", msg)
        else:
            erreur(self, "Échec du test", msg)

    def _tester_camera(self):
        try:
            import cv2
        except ImportError:
            erreur(self, "Erreur", "opencv-python n'est pas installé.")
            return
        source = self.input_camera_source.text().strip() or '0'
        try:
            source = int(source)
        except ValueError:
            pass
        cap = cv2.VideoCapture(source)
        if cap.isOpened():
            ret, _ = cap.read()
            cap.release()
            if ret:
                information(self, "Test réussi", f"Caméra connectée avec succès ! Source : {source}")
            else:
                erreur(self, "Erreur", "Caméra trouvée mais impossible de lire les images.")
        else:
            erreur(self, "Erreur", f"Impossible de se connecter à la caméra.\nSource testée : {source}")
