"""
Configuration du mode réseau local multi-terminaux.
Accessible depuis le menu Admin (patron uniquement).
"""
import socket
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QRadioButton, QButtonGroup, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, QThread, Signal

from ui.theme import Theme
from ui.components.dialogs import information, erreur
from database import db
from config import RESEAU_LOCAL_PORT


def _get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


class _PingThread(QThread):
    result = Signal(bool, str)

    def __init__(self, url):
        super().__init__()
        self._url = url

    def run(self):
        try:
            import requests
            r = requests.get(f"{self._url}/ping", timeout=3)
            if r.status_code == 200:
                data = r.json()
                self.result.emit(True, data.get('serveur', 'Serveur'))
            else:
                self.result.emit(False, f"HTTP {r.status_code}")
        except Exception as e:
            self.result.emit(False, str(e))


class _DiscoveryThread(QThread):
    found = Signal(str, int, str)   # ip, port, token
    not_found = Signal()

    def run(self):
        try:
            from serveur_local.discovery import chercher_serveur
            result = chercher_serveur(timeout=6.0)
            if result:
                self.found.emit(result['ip'], result['port'], result['token'])
            else:
                self.not_found.emit()
        except Exception as e:
            self.not_found.emit()


class _TerminauxThread(QThread):
    result = Signal(list, int, int, str)  # terminaux, nb, max, plan

    def __init__(self, url, token):
        super().__init__()
        self._url = url
        self._token = token

    def run(self):
        try:
            import requests
            r = requests.get(
                f"{self._url}/terminaux",
                headers={'X-Local-Token': self._token},
                timeout=3
            )
            if r.status_code == 200:
                data = r.json()
                self.result.emit(
                    data.get('terminaux', []),
                    data.get('nb', 0),
                    data.get('max', 1),
                    data.get('plan', 'standard'),
                )
        except Exception:
            self.result.emit([], 0, 0, '')


class ConfigReseauWindow(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration réseau")
        self.setMinimumWidth(520)
        self._ping_thread = None
        self._discovery_thread = None
        self._terminaux_thread = None
        self._build_ui()
        self._charger()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Réseau local multi-terminaux")
        title.setStyleSheet(f"font-size: 16pt; font-weight: bold; color: {Theme.c('text')};")
        layout.addWidget(title)

        # ── Mode ─────────────────────────────────────────────────────────────
        grp_mode = QGroupBox("Mode de fonctionnement")
        grp_mode.setStyleSheet(f"color: {Theme.c('text')}; font-weight: bold;")
        mode_layout = QVBoxLayout(grp_mode)
        mode_layout.setSpacing(8)

        self._btn_standalone = QRadioButton("Standalone — PC seul, pas de réseau (défaut)")
        self._btn_serveur = QRadioButton("Serveur — ce PC héberge la base de données")
        self._btn_client = QRadioButton("Client — ce PC se connecte au serveur")

        for btn in [self._btn_standalone, self._btn_serveur, self._btn_client]:
            btn.setStyleSheet(f"color: {Theme.c('text')}; font-weight: normal; font-size: 11pt;")
            mode_layout.addWidget(btn)

        self._mode_group = QButtonGroup(self)
        self._mode_group.addButton(self._btn_standalone, 0)
        self._mode_group.addButton(self._btn_serveur, 1)
        self._mode_group.addButton(self._btn_client, 2)
        self._mode_group.buttonClicked.connect(self._on_mode_change)

        layout.addWidget(grp_mode)

        # ── Infos serveur (affiché si mode=serveur) ───────────────────────────
        self._frame_serveur = QFrame()
        self._frame_serveur.setStyleSheet(
            f"background:{Theme.c('card_bg')}; border-radius:8px; padding:8px;"
        )
        srv_layout = QVBoxLayout(self._frame_serveur)
        srv_layout.setSpacing(6)

        ip_label = QLabel(f"IP de ce PC : <b>{_get_local_ip()}</b>")
        ip_label.setStyleSheet(f"color: {Theme.c('text')};")
        port_label = QLabel(f"Port : <b>{RESEAU_LOCAL_PORT}</b>")
        port_label.setStyleSheet(f"color: {Theme.c('text')};")

        self._lbl_token = QLabel()
        self._lbl_token.setStyleSheet(
            f"color: {Theme.c('text')}; font-family: monospace; font-size: 10pt;"
        )
        self._lbl_token.setTextInteractionFlags(Qt.TextSelectableByMouse)

        btn_terminaux = QPushButton("Voir les terminaux connectés")
        btn_terminaux.setStyleSheet(
            f"background:{Theme.c('card_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:6px 14px;"
        )
        btn_terminaux.clicked.connect(self._voir_terminaux)

        self._lbl_terminaux = QLabel()
        self._lbl_terminaux.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        self._lbl_terminaux.setWordWrap(True)

        srv_layout.addWidget(ip_label)
        srv_layout.addWidget(port_label)
        srv_layout.addWidget(self._lbl_token)
        srv_layout.addWidget(btn_terminaux)
        srv_layout.addWidget(self._lbl_terminaux)
        layout.addWidget(self._frame_serveur)

        # ── Config client (affiché si mode=client) ────────────────────────────
        self._frame_client = QFrame()
        self._frame_client.setStyleSheet(
            f"background:{Theme.c('card_bg')}; border-radius:8px; padding:8px;"
        )
        cli_layout = QVBoxLayout(self._frame_client)
        cli_layout.setSpacing(8)

        # Bouton découverte automatique
        btn_decouvrir = QPushButton("Rechercher le serveur automatiquement")
        btn_decouvrir.setStyleSheet(
            f"background:{Theme.c('primary')}; color:#fff; "
            f"border:none; border-radius:6px; padding:7px 14px; font-weight:bold;"
        )
        btn_decouvrir.clicked.connect(self._decouvrir_serveur)
        self._lbl_decouverte = QLabel()
        self._lbl_decouverte.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")

        lbl_ip = QLabel("IP du serveur :")
        lbl_ip.setStyleSheet(f"color: {Theme.c('text')};")
        self._input_ip = QLineEdit()
        self._input_ip.setPlaceholderText("ex: 192.168.1.10")
        self._input_ip.setStyleSheet(
            f"background:{Theme.c('input_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:6px;"
        )

        lbl_token = QLabel("Token partagé :")
        lbl_token.setStyleSheet(f"color: {Theme.c('text')};")
        self._input_token = QLineEdit()
        self._input_token.setPlaceholderText("Token fourni par le PC serveur")
        self._input_token.setStyleSheet(
            f"background:{Theme.c('input_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:6px;"
        )

        btn_ping = QPushButton("Tester la connexion")
        btn_ping.setStyleSheet(
            f"background:{Theme.c('card_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:6px 14px;"
        )
        btn_ping.clicked.connect(self._tester_connexion)

        self._lbl_ping = QLabel()
        self._lbl_ping.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")

        cli_layout.addWidget(btn_decouvrir)
        cli_layout.addWidget(self._lbl_decouverte)
        cli_layout.addWidget(lbl_ip)
        cli_layout.addWidget(self._input_ip)
        cli_layout.addWidget(lbl_token)
        cli_layout.addWidget(self._input_token)
        cli_layout.addWidget(btn_ping)
        cli_layout.addWidget(self._lbl_ping)
        layout.addWidget(self._frame_client)

        # ── Boutons ───────────────────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        btn_annuler = QPushButton("Annuler")
        btn_annuler.setStyleSheet(
            f"background:{Theme.c('card_bg')}; color:{Theme.c('text')}; "
            f"border:1px solid {Theme.c('input_border')}; border-radius:6px; padding:7px 18px;"
        )
        btn_annuler.clicked.connect(self.reject)

        btn_sauver = QPushButton("Enregistrer")
        btn_sauver.setStyleSheet(
            f"background:{Theme.c('primary')}; color:#fff; "
            f"border:none; border-radius:6px; padding:7px 18px; font-weight:bold;"
        )
        btn_sauver.clicked.connect(self._sauvegarder)

        btn_layout.addWidget(btn_annuler)
        btn_layout.addWidget(btn_sauver)
        layout.addLayout(btn_layout)

    def _charger(self):
        mode = db.get_parametre('reseau_mode', 'standalone')
        if mode == 'serveur':
            self._btn_serveur.setChecked(True)
        elif mode == 'client':
            self._btn_client.setChecked(True)
        else:
            self._btn_standalone.setChecked(True)

        ip = db.get_parametre('reseau_serveur_ip', '')
        self._input_ip.setText(ip)

        token_client = db.get_parametre('reseau_client_token', '')
        self._input_token.setText(token_client)

        self._update_token_label()
        self._on_mode_change()

    def _update_token_label(self):
        token = db.get_parametre('reseau_local_token', '')
        if token:
            self._lbl_token.setText(f"Token réseau : <b>{token}</b>")
        else:
            self._lbl_token.setText("Token : (sera généré au premier démarrage du serveur)")

    def _on_mode_change(self, *_):
        mode = self._mode_actuel()
        self._frame_serveur.setVisible(mode == 'serveur')
        self._frame_client.setVisible(mode == 'client')

    def _mode_actuel(self) -> str:
        if self._btn_serveur.isChecked():
            return 'serveur'
        if self._btn_client.isChecked():
            return 'client'
        return 'standalone'

    def _decouvrir_serveur(self):
        self._lbl_decouverte.setStyleSheet(f"color: {Theme.c('gray')}; font-size: 10pt;")
        self._lbl_decouverte.setText("Recherche en cours (6 secondes max)...")
        self._discovery_thread = _DiscoveryThread()
        self._discovery_thread.found.connect(self._on_serveur_trouve)
        self._discovery_thread.not_found.connect(self._on_serveur_non_trouve)
        self._discovery_thread.start()

    def _on_serveur_trouve(self, ip: str, port: int, token: str):
        self._lbl_decouverte.setStyleSheet("color: #16a34a; font-size: 10pt;")
        self._lbl_decouverte.setText(f"Serveur trouvé : {ip}")
        self._input_ip.setText(ip)
        self._input_token.setText(token)

    def _on_serveur_non_trouve(self):
        self._lbl_decouverte.setStyleSheet("color: #dc2626; font-size: 10pt;")
        self._lbl_decouverte.setText("Aucun serveur trouvé. Saisissez l'IP manuellement.")

    def _voir_terminaux(self):
        ip = _get_local_ip()
        token = db.get_parametre('reseau_local_token', '')
        if not token:
            self._lbl_terminaux.setText("Serveur pas encore démarré.")
            return
        url = f"http://127.0.0.1:{RESEAU_LOCAL_PORT}"
        self._lbl_terminaux.setText("Chargement...")
        self._terminaux_thread = _TerminauxThread(url, token)
        self._terminaux_thread.result.connect(self._on_terminaux_result)
        self._terminaux_thread.start()

    def _on_terminaux_result(self, terminaux: list, nb: int, max_t: int, plan: str):
        if not terminaux:
            self._lbl_terminaux.setText(f"0/{max_t} terminaux connectés (plan {plan})")
            return
        lignes = [f"{nb}/{max_t} terminaux (plan {plan}) :"]
        for t in terminaux:
            lignes.append(f"  • {t.get('nom','?')} — {t.get('ip','?')}")
        self._lbl_terminaux.setText("\n".join(lignes))

    def _tester_connexion(self):
        ip = self._input_ip.text().strip()
        token = self._input_token.text().strip()
        if not ip:
            self._lbl_ping.setText("Saisissez l'IP du serveur.")
            return

        url = f"http://{ip}:{RESEAU_LOCAL_PORT}"
        self._lbl_ping.setText("Connexion en cours...")

        self._ping_thread = _PingThread(url)
        self._ping_thread.result.connect(self._on_ping_result)
        self._ping_thread.start()

    def _on_ping_result(self, ok: bool, msg: str):
        if ok:
            self._lbl_ping.setStyleSheet("color: #16a34a; font-size: 10pt;")
            self._lbl_ping.setText(f"Connecté — Boutique : {msg}")
        else:
            self._lbl_ping.setStyleSheet("color: #dc2626; font-size: 10pt;")
            self._lbl_ping.setText(f"Échec : {msg}")

    def _sauvegarder(self):
        mode = self._mode_actuel()
        db.set_parametre('reseau_mode', mode)

        if mode == 'client':
            ip = self._input_ip.text().strip()
            token = self._input_token.text().strip()
            if not ip or not token:
                erreur(self, "Champs requis", "Saisissez l'IP du serveur et le token.")
                return
            db.set_parametre('reseau_serveur_ip', ip)
            db.set_parametre('reseau_client_token', token)

        information(
            self, "Enregistré",
            f"Mode réseau : {mode.capitalize()}\n"
            "Redémarrez l'application pour appliquer le changement."
        )
        self.accept()
