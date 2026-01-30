"""
Dashboard ultra-simple pour les caissiers
Interface épurée et efficace
"""
import os
import tkinter as tk
from tkinter import messagebox
from modules.rapports import Rapport
from modules.ventes import Vente
from modules.logger import get_logger
from config import *

logger = get_logger('fenetre_caissier')

class FenetrePrincipaleCaissier:
    def __init__(self, utilisateur):
        self.utilisateur = utilisateur
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - Caissier")
        self.root.geometry("900x700")
        self.root.configure(bg=COLORS['bg'])
        
        self.centrer_fenetre()
        self.creer_interface()
        self.actualiser_stats()
        
        # Timeout session
        self._setup_session_timeout()

        # Actualisation automatique
        self.root.after(30000, self.actualisation_periodique)
    
    def centrer_fenetre(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.root.winfo_screenheight() // 2) - (700 // 2)
        self.root.geometry(f"900x700+{x}+{y}")
    
    def creer_interface(self):
        """Interface ultra-simple pour caissier"""
        
        # En-tête avec info utilisateur
        header = tk.Frame(self.root, bg=COLORS['primary'], height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_inner = tk.Frame(header, bg=COLORS['primary'])
        header_inner.pack(expand=True, fill='both', padx=30)
        
        # Info caissier à gauche
        left_info = tk.Frame(header_inner, bg=COLORS['primary'])
        left_info.pack(side='left', fill='y')
        
        tk.Label(
            left_info,
            text=f"🔐 Caissier",
            font=("Segoe UI", 11),
            bg=COLORS['primary'],
            fg="white"
        ).pack(anchor='w')
        
        tk.Label(
            left_info,
            text=f"{self.utilisateur['prenom']} {self.utilisateur['nom']}",
            font=("Segoe UI", 20, "bold"),
            bg=COLORS['primary'],
            fg="white"
        ).pack(anchor='w')
        
        # Bouton déconnexion à droite
        tk.Button(
            header_inner,
            text="🚪 Déconnexion",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=COLORS['primary'],
            relief='flat',
            cursor='hand2',
            command=self.deconnexion,
            padx=20,
            pady=10
        ).pack(side='right')
        
        # Container principal
        main = tk.Frame(self.root, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=40, pady=40)
        
        # GRAND BOUTON NOUVELLE VENTE
        grand_btn = tk.Button(
            main,
            text="💳 NOUVELLE VENTE",
            font=("Segoe UI", 24, "bold"),
            bg=COLORS['success'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.ouvrir_ventes,
            activebackground=self.darken_color(COLORS['success'])
        )
        grand_btn.pack(fill='x', ipady=50, pady=(0, 30))
        
        # Effet hover
        grand_btn.bind('<Enter>', lambda e: grand_btn.config(bg=self.darken_color(COLORS['success'])))
        grand_btn.bind('<Leave>', lambda e: grand_btn.config(bg=COLORS['success']))
        
        # Statistiques du jour
        stats_frame = tk.Frame(main, bg="white", relief='solid', bd=1)
        stats_frame.pack(fill='x', pady=(0, 20))
        
        stats_inner = tk.Frame(stats_frame, bg="white")
        stats_inner.pack(padx=30, pady=30)
        
        tk.Label(
            stats_inner,
            text="📊 Vos statistiques du jour",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(anchor='w', pady=(0, 20))
        
        # Grille 2x2 pour stats
        grid = tk.Frame(stats_inner, bg="white")
        grid.pack(fill='x')
        
        # Ventes
        ventes_card = tk.Frame(grid, bg=COLORS['light'])
        ventes_card.grid(row=0, column=0, sticky='ew', padx=(0, 10), pady=(0, 10))
        grid.columnconfigure(0, weight=1)
        
        tk.Frame(ventes_card, bg="white").pack(padx=20, pady=15)
        card_inner = tk.Frame(ventes_card, bg=COLORS['light'])
        card_inner.pack(padx=20, pady=15)
        
        tk.Label(
            card_inner,
            text="Ventes aujourd'hui",
            font=("Segoe UI", 10),
            bg=COLORS['light'],
            fg=COLORS['gray']
        ).pack()
        
        self.label_ventes = tk.Label(
            card_inner,
            text="0",
            font=("Segoe UI", 32, "bold"),
            bg=COLORS['light'],
            fg=COLORS['primary']
        )
        self.label_ventes.pack()
        
        # CA
        ca_card = tk.Frame(grid, bg=COLORS['light'])
        ca_card.grid(row=0, column=1, sticky='ew', padx=(10, 0), pady=(0, 10))
        grid.columnconfigure(1, weight=1)
        
        card_inner2 = tk.Frame(ca_card, bg=COLORS['light'])
        card_inner2.pack(padx=20, pady=15)
        
        tk.Label(
            card_inner2,
            text="Chiffre d'affaires",
            font=("Segoe UI", 10),
            bg=COLORS['light'],
            fg=COLORS['gray']
        ).pack()
        
        self.label_ca = tk.Label(
            card_inner2,
            text="0 FCFA",
            font=("Segoe UI", 32, "bold"),
            bg=COLORS['light'],
            fg=COLORS['success']
        )
        self.label_ca.pack()
        
        # Boutons secondaires
        btns_frame = tk.Frame(main, bg=COLORS['bg'])
        btns_frame.pack(fill='x')
        
        tk.Button(
            btns_frame,
            text="📜 Voir mes ventes",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS['info'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.voir_mes_ventes
        ).pack(fill='x', ipady=15)
        
        # Footer
        footer = tk.Frame(self.root, bg=COLORS['light'], height=40)
        footer.pack(fill='x', side='bottom')
        
        tk.Label(
            footer,
            text=f"© 2026 {APP_NAME} v{APP_VERSION} - Mode Caissier",
            font=("Segoe UI", 9),
            bg=COLORS['light'],
            fg=COLORS['gray']
        ).pack(pady=10)
    
    def actualiser_stats(self):
        """Actualiser les statistiques du caissier"""
        try:
            stats = Rapport.statistiques_generales()
            self.label_ventes.config(text=str(stats['nb_ventes']))
            self.label_ca.config(text=f"{stats['ca_jour']:,.0f} FCFA")
        except Exception as e:
            logger.error(f"Erreur actualisation: {e}")
    
    def actualisation_periodique(self):
        """Actualiser périodiquement"""
        self.actualiser_stats()
        self.root.after(30000, self.actualisation_periodique)
    
    def ouvrir_ventes(self):
        """Ouvrir nouvelle vente"""
        from interface.fenetre_ventes import FenetreVentes
        FenetreVentes(self.root, callback=self.actualiser_stats)
    
    def voir_mes_ventes(self):
        """Voir les ventes du caissier"""
        from interface.fenetre_liste_ventes import FenetreListeVentes
        FenetreListeVentes(self.root)
    
    def deconnexion(self):
        """Se déconnecter"""
        from modules.utilisateurs import Utilisateur
        Utilisateur.logger_action(
            self.utilisateur['id'],
            'deconnexion',
            f"Déconnexion de {self.utilisateur['email']}"
        )
        
        self.root.destroy()
        
        # Relancer l'écran de login
        import sys
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def darken_color(self, hex_color):
        """Assombrir une couleur"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, r - 20)
        g = max(0, g - 20)
        b = max(0, b - 20)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _setup_session_timeout(self):
        """Configurer le timeout de session par inactivite"""
        from database import db
        timeout_str = db.get_parametre('session_timeout', '900')
        try:
            self._session_timeout = int(timeout_str) * 1000  # en ms
        except ValueError:
            self._session_timeout = 900000  # 15 min par defaut

        self._timeout_id = None
        self._reset_timeout()

        # Detecter toute activite
        self.root.bind_all('<Any-KeyPress>', self._on_activity)
        self.root.bind_all('<Any-ButtonPress>', self._on_activity)

    def _on_activity(self, event=None):
        """Reset le timer a chaque activite"""
        self._reset_timeout()

    def _reset_timeout(self):
        """Rearmer le timer de session"""
        if self._timeout_id:
            self.root.after_cancel(self._timeout_id)
        self._timeout_id = self.root.after(self._session_timeout, self._session_expired)

    def _session_expired(self):
        """Session expiree : deconnecter l'utilisateur"""
        messagebox.showinfo("Session expiree", "Vous avez ete deconnecte pour inactivite.")
        self.root.destroy()
        # Relancer le login
        from main import demander_login
        demander_login()

    def lancer(self):
        """Lancer l'application"""
        self.root.mainloop()