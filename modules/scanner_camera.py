"""
Scanner code-barres par webcam avec OpenCV + pyzbar
Degrade gracieusement si les dependances ne sont pas installees
"""
import tkinter as tk
from tkinter import messagebox

SCANNER_DISPONIBLE = False
try:
    import cv2
    from pyzbar.pyzbar import decode as pyzbar_decode
    from PIL import Image, ImageTk
    SCANNER_DISPONIBLE = True
except ImportError:
    pass


class ScannerCamera:
    """Fenetre de scan par webcam"""

    def __init__(self, parent, callback):
        """
        parent: widget tkinter parent
        callback: function(code_barre: str) appelee quand un code est detecte
        """
        if not SCANNER_DISPONIBLE:
            messagebox.showerror("Erreur",
                "Scanner camera non disponible.\n\n"
                "Installez les dependances :\n"
                "pip install opencv-python pyzbar Pillow")
            return

        self.callback = callback
        self.running = True
        self.cap = None

        from config import COLORS

        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Scanner Camera")
        self.fenetre.geometry("660x540")
        self.fenetre.configure(bg=COLORS['bg'])
        self.fenetre.protocol("WM_DELETE_WINDOW", self.fermer)
        self.fenetre.transient(parent)
        self.fenetre.grab_set()

        tk.Label(
            self.fenetre, text="Presentez le code-barres devant la camera",
            font=("Segoe UI", 12, "bold"), bg=COLORS['bg'],
            fg=COLORS.get('text', '#1F2937')
        ).pack(pady=10)

        self.label_video = tk.Label(self.fenetre, bg="black")
        self.label_video.pack(padx=20)

        self.label_statut = tk.Label(
            self.fenetre, text="En attente de detection...",
            font=("Segoe UI", 10), bg=COLORS['bg'], fg=COLORS['gray']
        )
        self.label_statut.pack(pady=5)

        tk.Button(
            self.fenetre, text="Fermer", font=("Segoe UI", 11, "bold"),
            bg=COLORS['danger'], fg="white", relief='flat',
            command=self.fermer, padx=20
        ).pack(pady=10, fill='x', padx=20)

        # Ouvrir la camera
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Erreur", "Impossible d'ouvrir la camera")
            self.fenetre.destroy()
            return

        self.lire_frame()

    def lire_frame(self):
        """Lire et afficher un frame de la webcam"""
        if not self.running:
            return

        ret, frame = self.cap.read()
        if ret:
            # Decoder les codes-barres
            barcodes = pyzbar_decode(frame)
            for barcode in barcodes:
                code = barcode.data.decode('utf-8')
                # Dessiner un rectangle autour du code detecte
                pts = barcode.polygon
                if pts:
                    for i in range(len(pts)):
                        cv2.line(frame,
                                 (pts[i].x, pts[i].y),
                                 (pts[(i+1) % len(pts)].x, pts[(i+1) % len(pts)].y),
                                 (0, 255, 0), 3)

                self.label_statut.config(text=f"Code detecte: {code}", fg="green")
                self.fenetre.after(300, lambda c=code: self._code_detecte(c))
                return

            # Convertir pour affichage tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((620, 400))
            imgtk = ImageTk.PhotoImage(image=img)
            self.label_video.imgtk = imgtk
            self.label_video.configure(image=imgtk)

        self.fenetre.after(33, self.lire_frame)  # ~30 FPS

    def _code_detecte(self, code):
        """Traiter le code detecte"""
        self.fermer()
        self.callback(code)

    def fermer(self):
        """Fermer la camera et la fenetre"""
        self.running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        try:
            self.fenetre.destroy()
        except Exception:
            pass
