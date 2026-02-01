"""
Scanner code-barres par webcam avec OpenCV + pyzbar (PySide6)
"""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap

SCANNER_DISPONIBLE = False
try:
    import cv2
    from pyzbar.pyzbar import decode as pyzbar_decode
    SCANNER_DISPONIBLE = True
except ImportError:
    pass


class ScannerCameraDialog(QDialog):
    """Dialog de scan par webcam (PySide6)"""

    def __init__(self, callback, parent=None):
        """
        callback: function(code_barre: str) appelée quand un code est détecté
        parent: QWidget parent (optionnel)
        """
        super().__init__(parent)

        if not SCANNER_DISPONIBLE:
            from ui.components.dialogs import erreur
            erreur(parent if parent else self, "Erreur",
                "Scanner caméra non disponible.\n\n"
                "Installez les dépendances :\n"
                "pip install opencv-python pyzbar Pillow")
            self.reject()
            return

        self.callback = callback
        self.running = True
        self.cap = None
        self.code_detecte_flag = False

        self.setWindowTitle("Scanner Caméra")
        self.setFixedSize(660, 540)
        self.setModal(True)

        self._setup_ui()
        self._start_camera()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Instructions
        label_instruction = QLabel("Présentez le code-barres devant la caméra")
        label_instruction.setStyleSheet("font-size: 12pt; font-weight: bold;")
        label_instruction.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_instruction)

        # Video feed
        self.label_video = QLabel()
        self.label_video.setFixedSize(620, 400)
        self.label_video.setStyleSheet("background-color: black;")
        self.label_video.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_video)

        # Status
        self.label_statut = QLabel("En attente de détection...")
        self.label_statut.setStyleSheet("font-size: 10pt; color: gray;")
        self.label_statut.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_statut)

        # Close button
        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #DC2626;
            }
        """)
        close_btn.clicked.connect(self.fermer)
        layout.addWidget(close_btn)

    def _start_camera(self):
        """Ouvrir la caméra et démarrer la lecture"""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            from ui.components.dialogs import erreur
            erreur(self, "Erreur", "Impossible d'ouvrir la caméra")
            self.reject()
            return

        # Timer pour lire les frames
        self.timer = QTimer()
        self.timer.timeout.connect(self._lire_frame)
        self.timer.start(33)  # ~30 FPS

    def _lire_frame(self):
        """Lire et afficher un frame de la webcam"""
        if not self.running or self.code_detecte_flag:
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        # Décoder les codes-barres
        barcodes = pyzbar_decode(frame)
        for barcode in barcodes:
            code = barcode.data.decode('utf-8')

            # ARRÊTER le timer immédiatement pour éviter détections multiples
            self.code_detecte_flag = True
            self.timer.stop()

            # Dessiner un rectangle autour du code détecté
            pts = barcode.polygon
            if pts:
                for i in range(len(pts)):
                    cv2.line(frame,
                             (pts[i].x, pts[i].y),
                             (pts[(i+1) % len(pts)].x, pts[(i+1) % len(pts)].y),
                             (0, 255, 0), 3)

            self.label_statut.setText(f"Code détecté: {code}")
            self.label_statut.setStyleSheet("font-size: 10pt; color: green;")

            # Fermer rapidement et appeler le callback
            QTimer.singleShot(200, lambda c=code: self._code_detecte(c))
            return

        # Convertir pour affichage Qt
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # Redimensionner pour s'adapter au label
        pixmap = QPixmap.fromImage(qt_image)
        pixmap = pixmap.scaled(620, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label_video.setPixmap(pixmap)

    def _code_detecte(self, code):
        """Traiter le code détecté"""
        # IMPORTANT: Appeler le callback AVANT de fermer
        # Sinon le dialog de quantité peut apparaître pendant la fermeture
        callback = self.callback
        self.fermer()
        # Appeler le callback après fermeture complète
        QTimer.singleShot(100, lambda: callback(code))

    def fermer(self):
        """Fermer la caméra et la fenêtre"""
        self.running = False
        if hasattr(self, 'timer'):
            self.timer.stop()
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.reject()

    def closeEvent(self, event):
        """Override pour nettoyer quand la fenêtre est fermée"""
        self.fermer()
        event.accept()
