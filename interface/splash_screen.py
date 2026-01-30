"""
Écran de démarrage - Splash Screen
"""
import tkinter as tk
from PIL import Image, ImageTk
import os
from config import APP_NAME, APP_VERSION, COLORS

class SplashScreen:
    def __init__(self, duree=3000):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # Sans bordure
        
        # Taille
        width = 500
        height = 300
        
        # Centrer
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.configure(bg=COLORS['primary'])
        
        # Container principal
        main = tk.Frame(self.root, bg=COLORS['primary'])
        main.pack(fill='both', expand=True)
        
        # Logo (si existe)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')
        if os.path.exists(logo_path):
            try:
                img = Image.open(logo_path)
                img = img.resize((120, 120), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                logo_label = tk.Label(main, image=photo, bg=COLORS['primary'])
                logo_label.image = photo
                logo_label.pack(pady=(50, 20))
            except Exception as e:
                print(f"Erreur logo: {e}")
        
        # Nom de l'application
        tk.Label(
            main,
            text=APP_NAME.upper(),
            font=("Segoe UI", 28, "bold"),
            bg=COLORS['primary'],
            fg='white'
        ).pack(pady=(20 if not os.path.exists(logo_path) else 0, 5))
        
        # Version
        tk.Label(
            main,
            text=f"Version {APP_VERSION}",
            font=("Segoe UI", 12),
            bg=COLORS['primary'],
            fg='white'
        ).pack(pady=(0, 30))
        
        # Barre de chargement (simulation)
        self.progress_label = tk.Label(
            main,
            text="Chargement...",
            font=("Segoe UI", 10),
            bg=COLORS['primary'],
            fg='white'
        )
        self.progress_label.pack(pady=10)
        
        # Canvas pour barre de progression
        self.canvas = tk.Canvas(main, width=300, height=8, bg=COLORS['primary'], highlightthickness=0)
        self.canvas.pack(pady=10)
        
        # Créer la barre
        self.progress_bar = self.canvas.create_rectangle(
            0, 0, 0, 8,
            fill='white',
            outline=''
        )
        
        # Copyright
        tk.Label(
            main,
            text="© 2026 - Tous droits réservés",
            font=("Segoe UI", 8),
            bg=COLORS['primary'],
            fg='white'
        ).pack(side='bottom', pady=20)
        
        # Animer
        self.animer_chargement()
        
        # Fermer après durée
        self.root.after(duree, self.fermer)
    
    def animer_chargement(self, progress=0):
        """Animer la barre de progression"""
        if progress <= 300:
            self.canvas.coords(self.progress_bar, 0, 0, progress, 8)
            
            # Messages de chargement
            if progress < 100:
                self.progress_label.config(text="Initialisation...")
            elif progress < 200:
                self.progress_label.config(text="Chargement des modules...")
            else:
                self.progress_label.config(text="Presque prêt...")
            
            self.root.after(10, lambda: self.animer_chargement(progress + 3))
    
    def fermer(self):
        """Fermer le splash screen"""
        self.root.destroy()
    
    def afficher(self):
        """Afficher le splash screen"""
        self.root.mainloop()