"""
Widget caméra intégré pour scan code-barres en continu
"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QImage, QPixmap

SCANNER_DISPONIBLE = False
try:
    import cv2
    from pyzbar.pyzbar import decode as pyzbar_decode
    SCANNER_DISPONIBLE = True
except Exception:
    pass


class CameraWidget(QFrame):
    """Widget caméra intégré avec scan continu"""

    code_scanne = Signal(str)  # Signal émis quand un code est détecté

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cap = None
        self.timer = None
        self.actif = False
        self.code_detecte_flag = False
        self.cooldown_timer = None

        self._setup_ui()
        self._check_auto_start()

    def _check_auto_start(self):
        """Démarrer automatiquement si configuré"""
        try:
            from database import db
            auto_start = db.get_parametre('camera_auto_start', '0') == '1'
            if auto_start and SCANNER_DISPONIBLE:
                QTimer.singleShot(300, self._demarrer_camera)
        except Exception:
            pass

    def _setup_ui(self):
        """Interface du widget"""
        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                background-color: #F9FAFB;
                border: 2px solid #D1D5DB;
                border-radius: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Titre
        titre = QLabel("📷 Scanner Caméra")
        titre.setStyleSheet("font-size: 10pt; font-weight: bold; color: #374151;")
        titre.setAlignment(Qt.AlignCenter)
        layout.addWidget(titre)

        # Zone vidéo
        self.label_video = QLabel()
        self.label_video.setFixedSize(320, 240)
        self.label_video.setStyleSheet("background-color: #1F2937; border-radius: 4px;")
        self.label_video.setAlignment(Qt.AlignCenter)
        self.label_video.setText("Caméra désactivée")
        layout.addWidget(self.label_video)

        # Statut
        self.label_statut = QLabel("En attente...")
        self.label_statut.setStyleSheet("font-size: 9pt; color: #6B7280;")
        self.label_statut.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_statut)

        # Message si scanner non disponible
        if not SCANNER_DISPONIBLE:
            self.label_statut.setText("opencv-python manquant")
            self.label_statut.setStyleSheet("font-size: 9pt; color: #EF4444;")

    def _demarrer_camera(self):
        """Démarrer la caméra et le scan continu"""
        if not SCANNER_DISPONIBLE:
            return

        # Récupérer la source caméra configurée
        source = self._get_camera_source()
        self.cap = cv2.VideoCapture(source)
        if not self.cap.isOpened():
            self.label_statut.setText("Erreur: caméra inaccessible")
            self.label_statut.setStyleSheet("font-size: 9pt; color: #EF4444;")
            return

        self.actif = True
        self.label_statut.setText("Scan en cours...")
        self.label_statut.setStyleSheet("font-size: 9pt; color: #10B981;")

        # Démarrer lecture frames
        self.timer = QTimer()
        self.timer.timeout.connect(self._lire_frame)
        self.timer.start(33)  # ~30 FPS

    def _get_camera_source(self):
        """Récupérer la source caméra depuis la config"""
        try:
            from database import db
            source = db.get_parametre('camera_source', '0')
            # Convertir en int si possible (webcam locale)
            try:
                return int(source)
            except ValueError:
                # C'est une URL (téléphone via DroidCam/IP Webcam)
                return source
        except Exception:
            return 0  # Fallback sur webcam par défaut

    def _arreter_camera(self):
        """Arrêter la caméra"""
        self.actif = False

        if self.timer:
            self.timer.stop()
            self.timer = None

        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None

        self.label_video.clear()
        self.label_video.setText("Caméra désactivée")
        self.label_statut.setText("En attente...")
        self.label_statut.setStyleSheet("font-size: 9pt; color: #6B7280;")

    def _lire_frame(self):
        """Lire et traiter un frame"""
        if not self.actif or self.code_detecte_flag:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # Détection codes-barres
        barcodes = pyzbar_decode(frame)
        for barcode in barcodes:
            code = barcode.data.decode('utf-8')

            # Bloquer détections multiples
            self.code_detecte_flag = True

            # Dessiner rectangle
            pts = barcode.polygon
            if pts:
                for i in range(len(pts)):
                    cv2.line(frame,
                             (pts[i].x, pts[i].y),
                             (pts[(i+1) % len(pts)].x, pts[(i+1) % len(pts)].y),
                             (0, 255, 0), 3)

            self.label_statut.setText(f"✓ {code}")
            self.label_statut.setStyleSheet("font-size: 9pt; color: #10B981; font-weight: bold;")

            # Émettre signal
            self.code_scanne.emit(code)

            # Réactiver après 500ms (cooldown)
            if self.cooldown_timer:
                self.cooldown_timer.stop()
            self.cooldown_timer = QTimer()
            self.cooldown_timer.setSingleShot(True)
            self.cooldown_timer.timeout.connect(self._reactiver_detection)
            self.cooldown_timer.start(500)

            break

        # Afficher frame
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(qt_image)
        pixmap = pixmap.scaled(320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label_video.setPixmap(pixmap)

    def _reactiver_detection(self):
        """Réactiver la détection après cooldown"""
        self.code_detecte_flag = False
        if self.actif:
            self.label_statut.setText("Scan en cours...")
            self.label_statut.setStyleSheet("font-size: 9pt; color: #10B981;")

    def closeEvent(self, event):
        """Nettoyer à la fermeture"""
        self._arreter_camera()
        event.accept()
