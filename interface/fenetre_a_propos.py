"""
Fenêtre À propos
"""
import tkinter as tk
from config import *
import os

class FenetreAPropos:
    def __init__(self, parent):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("À propos")
        self.fenetre.geometry("500x650")
        self.fenetre.configure(bg="white")
        self.fenetre.resizable(False, False)
        self.fenetre.transient(parent)
        
        self.creer_interface()
        
        # Centrer
        self.fenetre.update_idletasks()
        x = (self.fenetre.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.fenetre.winfo_screenheight() // 2) - (650 // 2)
        self.fenetre.geometry(f"500x650+{x}+{y}")
    
    def creer_interface(self):
        """Créer l'interface"""
        
        # En-tête coloré
        header = tk.Frame(self.fenetre, bg=COLORS['primary'], height=180)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Logo (si existe)
        logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logo.png')
        if os.path.exists(logo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(logo_path)
                img = img.resize((100, 100), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                logo_label = tk.Label(header, image=photo, bg=COLORS['primary'])
                logo_label.image = photo
                logo_label.pack(pady=(30, 15))
            except:
                pass
        
        tk.Label(
            header,
            text=APP_NAME.upper(),
            font=("Segoe UI", 20, "bold"),
            bg=COLORS['primary'],
            fg="white"
        ).pack(pady=(0 if os.path.exists(logo_path) else 50, 10))
        
        # Contenu
        content = tk.Frame(self.fenetre, bg="white")
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Version
        tk.Label(
            content,
            text=f"Version {APP_VERSION}",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(pady=(0, 10))
        
        # Description
        tk.Label(
            content,
            text="Logiciel de gestion pour boutiques\nau Bénin et en Afrique",
            font=("Segoe UI", 11),
            bg="white",
            fg=COLORS['gray'],
            justify='center'
        ).pack(pady=(0, 25))
        
        # Séparateur
        tk.Frame(content, bg=COLORS['light'], height=1).pack(fill='x', pady=15)
        
        # Informations contact
        info_frame = tk.Frame(content, bg="white")
        info_frame.pack(fill='x', pady=10)
        
        infos = [
            ("📧 Email", "contact@votreentreprise.bj"),
            ("📱 Téléphone", "+229 XX XX XX XX"),
            ("🌐 Site web", "www.gestionboutique.bj"),
            ("💼 Support", "support@votreentreprise.bj"),
        ]
        
        for label, valeur in infos:
            row = tk.Frame(info_frame, bg="white")
            row.pack(fill='x', pady=6)
            
            tk.Label(
                row,
                text=label,
                font=("Segoe UI", 10, "bold"),
                bg="white",
                fg=COLORS['dark']
            ).pack(side='left')
            
            tk.Label(
                row,
                text=valeur,
                font=("Segoe UI", 10),
                bg="white",
                fg=COLORS['primary']
            ).pack(side='right')
        
        # Séparateur
        tk.Frame(content, bg=COLORS['light'], height=1).pack(fill='x', pady=15)
        
        # Info licence
        from modules.licence import GestionLicence
        manager = GestionLicence()
        licence_info = manager.obtenir_info_locale()
        
        if licence_info:
            licence_frame = tk.Frame(content, bg=COLORS['light'])
            licence_frame.pack(fill='x', pady=10)
            
            inner = tk.Frame(licence_frame, bg=COLORS['light'])
            inner.pack(padx=15, pady=15)
            
            tk.Label(
                inner,
                text="🔑 Informations de licence",
                font=("Segoe UI", 11, "bold"),
                bg=COLORS['light'],
                fg=COLORS['dark']
            ).pack(anchor='w', pady=(0, 10))
            
            tk.Label(
                inner,
                text=f"Clé: {licence_info.get('cle_licence', 'N/A')}",
                font=("Segoe UI", 9),
                bg=COLORS['light'],
                fg=COLORS['gray']
            ).pack(anchor='w')
            
            tk.Label(
                inner,
                text=f"Type: {licence_info.get('type_licence', 'N/A')}",
                font=("Segoe UI", 9),
                bg=COLORS['light'],
                fg=COLORS['gray']
            ).pack(anchor='w')
            
            tk.Label(
                inner,
                text=f"Expire le: {licence_info.get('date_expiration', 'N/A')}",
                font=("Segoe UI", 9),
                bg=COLORS['light'],
                fg=COLORS['gray']
            ).pack(anchor='w')
        
        # Copyright
        tk.Label(
            content,
            text="© 2026 - Tous droits réservés",
            font=("Segoe UI", 9),
            bg="white",
            fg=COLORS['gray']
        ).pack(side='bottom', pady=(20, 10))
        
        # Bouton Fermer
        tk.Button(
            content,
            text="Fermer",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['primary'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.fenetre.destroy
        ).pack(side='bottom', fill='x', ipady=12)