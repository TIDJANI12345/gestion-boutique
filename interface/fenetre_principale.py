"""
Fenêtre principale - Dashboard moderne inspiré du design PHP
"""
import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from modules.rapports import Rapport
from modules.produits import Produit
import shutil
import os
from datetime import datetime

class FenetrePrincipale:
    def __init__(self, utilisateur=None):
        self.utilisateur = utilisateur  
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.configure(bg=COLORS['bg'])
        
        # Titre dynamique selon l'utilisateur
        self.root.title(f"{APP_NAME} - {self.utilisateur['nom']} ({self.utilisateur['role'].upper()})")      
        
        # 1. Mise en page
        self.centrer_fenetre()
        self.creer_interface()
        self.appliquer_permissions()

        # 2. Premier chargement des donnees
        self.actualiser_stats()

        # 3. Actualisation periodique (toutes les 10s)
        self.actualisation_periodique()

        # 4. Timeout de session (inactivite)
        self._setup_session_timeout()

    def actualisation_periodique(self):
        """Boucle de rafraîchissement automatique"""
        try:
            self.actualiser_stats()
            # On stocke l'ID de l'after pour pouvoir l'annuler si besoin
            self.root.after(10000, self.actualisation_periodique)
        except Exception as e:
            print(f"Erreur actualisation auto: {e}")

    def appliquer_permissions(self):
        """Désactiver/Cacher des éléments pour les caissiers"""
        if self.utilisateur['role'] == 'caissier':
            # On masque les boutons sensibles
            if hasattr(self, 'btn_rapports'):
                self.btn_rapports.grid_remove() 
            
            if hasattr(self, 'btn_produit'):
                # Si vous voulez que le caissier puisse voir mais pas cliquer :
                # self.btn_produit.config(state='disabled', bg='#cccccc')
                # Ou pour masquer complètement :
                self.btn_produit.grid_remove()

    # Modifiez la méthode pour ouvrir les rapports
    def ouvrir_rapports(self):
        if self.utilisateur['role'] != 'patron':
            messagebox.showwarning("Accès refusé", "Réservé à l'administrateur")
            return
        from interface.fenetre_rapports import FenetreRapports
        FenetreRapports(self.root)

    # Ajoutez la méthode pour ouvrir la gestion utilisateurs
    def ouvrir_sync(self):
        """Ouvrir configuration synchronisation"""
        from interface.fenetre_config_sync import FenetreConfigSync
        FenetreConfigSync(self.root)
            
    def centrer_fenetre(self):
        """Centrer la fenêtre sur l'écran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def creer_interface(self):
        """Créer l'interface moderne type Tailwind"""
        
        # Créer la barre de menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        menu_fichier = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="💾 Fichier", menu=menu_fichier)
        
        # Menu Administration (patron uniquement)
        if self.utilisateur and self.utilisateur['role'] == 'patron':
            menu_admin = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="⚙️ Administration", menu=menu_admin)
            menu_admin.add_command(label="👥 Gestion utilisateurs", command=self.ouvrir_utilisateurs)
            menu_admin.add_command(label="🔄 Synchronisation", command=self.ouvrir_sync)
            menu_admin.add_separator()
            menu_admin.add_command(label="📦 Sauvegarde", command=self.sauvegarder)

            menu_fichier.add_command(label="Quitter", command=self.root.quit)
        
        # Menu Aide
        menu_aide = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="❓ Aide", menu=menu_aide)
        menu_aide.add_command(label="À propos", command=self.ouvrir_a_propos)
        menu_aide.add_separator()
        menu_aide.add_command(label="Documentation", command=self.ouvrir_doc)
        menu_aide.add_command(label="Support", command=self.contacter_support)

        # --- EN-TÊTE (Header) ---
        header = tk.Frame(self.root, bg=COLORS['primary'], height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        titre_frame = tk.Frame(header, bg=COLORS['primary'])
        titre_frame.pack(expand=True)
        
        tk.Label(
            titre_frame, text=f"📊 {APP_NAME}", font=("Segoe UI", 28, "bold"),
            bg=COLORS['primary'], fg="white"
        ).pack(side='left', padx=10)

        # --- CONTENEUR PRINCIPAL ---
        main_container = tk.Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Info Utilisateur Connecté
        tk.Label(
            main_container, 
            text=f"Session : {self.utilisateur['nom']} ({self.utilisateur['role'].upper()})",
            font=("Segoe UI", 10, "italic"), bg=COLORS['bg'], fg=COLORS['gray']
        ).pack(anchor='e')

        # Cartes de statistiques
        stats_frame = tk.Frame(main_container, bg=COLORS['bg'])
        stats_frame.pack(fill='x', pady=(0, 25))
        
        self.carte_ventes = self.creer_carte_stat(stats_frame, "🛒", "Ventes jour", "0", COLORS['primary'], 0)
        self.carte_ca = self.creer_carte_stat(stats_frame, "💰", "Chiffre d'affaires", "0 F", COLORS['success'], 1)
        self.carte_alertes = self.creer_carte_stat(stats_frame, "⚠️", "Alertes stock", "0", COLORS['danger'], 2)
        
        # --- ACTIONS RAPIDES ---
        tk.Label(
            main_container, text="⚡ Actions rapides", font=("Segoe UI", 14, "bold"),
            bg=COLORS['bg'], fg=COLORS['dark']
        ).pack(anchor='w', pady=(10, 15))
        
        actions_frame = tk.Frame(main_container, bg=COLORS['bg'])
        actions_frame.pack(fill='x', pady=(0, 20))
        
        # Grid dynamique selon le rôle
        if self.utilisateur and self.utilisateur['role'] == 'patron':
            # PATRON : Grid 3x2 (6 boutons)
            for i in range(3):
                actions_frame.columnconfigure(i, weight=1, uniform="actions")
            
            # Ligne 1
            self.creer_bouton_action(
                actions_frame,
                "💳 Nouvelle vente",
                COLORS['primary'],
                self.ouvrir_ventes,
                0, 0
            )
            
            self.creer_bouton_action(
                actions_frame,
                "➕ Ajouter produit",
                COLORS['success'],
                self.ouvrir_ajout_produit,
                0, 1
            )
            
            self.creer_bouton_action(
                actions_frame,
                "📜 Liste des ventes",
                COLORS['purple'],
                self.ouvrir_liste_ventes,
                0, 2
            )
            
            # Ligne 2
            self.creer_bouton_action(
                actions_frame,
                "📊 Rapports",
                COLORS['info'],
                self.ouvrir_rapports,
                1, 0
            )
            
            self.creer_bouton_action(
                actions_frame,
                "📱 Export WhatsApp",
                COLORS['warning'],
                self.ouvrir_whatsapp,
                1, 1
            )
            
            # NOUVEAU : Bouton Synchronisation (au lieu de Utilisateurs)
            self.creer_bouton_action(
                actions_frame,
                "🔄 Synchronisation",
                COLORS['info'],
                self.ouvrir_sync,
                1, 2
            )
        
        else:
            # CAISSIER : Ne devrait jamais arriver ici
            # (Dashboard caissier séparé)
            pass


        # Bouton 1: Nouvelle vente (Toujours visible)
        self.btn_vente = self.creer_bouton_action(actions_frame, "💳 Nouvelle vente", COLORS['primary'], self.ouvrir_ventes, 0, 0)

        # Bouton 2: Ajouter produit (Variable pour permissions)
        self.btn_produit = self.creer_bouton_action(actions_frame, "➕ Ajouter produit", COLORS['success'], self.ouvrir_ajout_produit, 0, 1)

        # Bouton 3: Liste des ventes
        self.btn_liste = self.creer_bouton_action(actions_frame, "📜 Liste des ventes", COLORS['purple'], self.ouvrir_liste_ventes, 0, 2)

        # Bouton 4: Rapports (Variable pour permissions)
        self.btn_rapports = self.creer_bouton_action(actions_frame, "📊 Rapports", COLORS['info'], self.ouvrir_rapports, 1, 0)

        # Bouton 5: WhatsApp
        self.btn_whatsapp = self.creer_bouton_action(actions_frame, "📱 Export WhatsApp", COLORS['warning'], self.ouvrir_whatsapp, 1, 1)

        # Bouton 6: Utilisateurs (Uniquement Patron)
        if self.utilisateur['role'] == 'patron':
            self.btn_admin = self.creer_bouton_action(actions_frame, "👥 Utilisateurs", COLORS['dark'], self.ouvrir_utilisateurs, 1, 2)

        # --- SECTION INFERIEURE (Listes) ---
        bottom_frame = tk.Frame(main_container, bg=COLORS['bg'])
        bottom_frame.pack(fill='both', expand=True)
        bottom_frame.columnconfigure(0, weight=1); bottom_frame.columnconfigure(1, weight=1)
        
        self.ventes_liste = self.creer_liste_scroll(bottom_frame, "🕐 Dernières ventes", 0)
        self.stock_liste = self.creer_liste_scroll(bottom_frame, "⚠️ Stock faible", 1)

    def creer_liste_scroll(self, parent, titre, col):
        """Helper pour créer les zones de texte du bas"""
        panel = self.creer_panel(parent, titre)
        panel.grid(row=0, column=col, sticky='nsew', padx=10)
        txt = tk.Text(panel, height=8, font=("Segoe UI", 10), bg="white", relief='flat', state='disabled')
        txt.pack(fill='both', expand=True, padx=15, pady=15)
        return txt
    
    def creer_carte_stat(self, parent, emoji, titre, valeur, couleur, col):
        """Créer une carte de statistique moderne"""
        # Frame principale de la carte
        carte = tk.Frame(parent, bg="white", relief='solid', bd=1)
        carte.grid(row=0, column=col, sticky='ew', padx=8, pady=5)
        parent.columnconfigure(col, weight=1, uniform="stat")
        
        # Container interne avec padding
        inner = tk.Frame(carte, bg="white")
        inner.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Top: emoji + valeur
        top_frame = tk.Frame(inner, bg="white")
        top_frame.pack(fill='x')
        
        # Emoji dans un cercle coloré
        emoji_bg = tk.Frame(top_frame, bg=self.lighten_color(couleur), width=60, height=60)
        emoji_bg.pack(side='right')
        emoji_bg.pack_propagate(False)
        
        emoji_label = tk.Label(
            emoji_bg,
            text=emoji,
            font=("Segoe UI", 24),
            bg=self.lighten_color(couleur)
        )
        emoji_label.pack(expand=True)
        
        # Valeur et titre à gauche
        text_frame = tk.Frame(top_frame, bg="white")
        text_frame.pack(side='left', fill='both', expand=True)
        
        titre_label = tk.Label(
            text_frame,
            text=titre,
            font=("Segoe UI", 10),
            bg="white",
            fg=COLORS['gray'],
            anchor='w'
        )
        titre_label.pack(anchor='w')
        
        valeur_label = tk.Label(
            text_frame,
            text=valeur,
            font=("Segoe UI", 24, "bold"),
            bg="white",
            fg=couleur,
            anchor='w'
        )
        valeur_label.pack(anchor='w')
        
        return valeur_label
    
    def creer_bouton_action(self, parent, texte, couleur, commande, row, col):
        """Créer un bouton d'action moderne"""
        btn = tk.Button(
            parent,
            text=texte,
            font=("Segoe UI", 13, "bold"),
            bg=couleur,
            fg="white",
            relief='flat',
            cursor='hand2',
            command=commande,
            activebackground=self.darken_color(couleur),
            activeforeground="white"
        )
        btn.grid(row=row, column=col, sticky='ew', padx=8, pady=8, ipady=20)
        
        # Effet hover
        btn.bind('<Enter>', lambda e: btn.config(bg=self.darken_color(couleur)))
        btn.bind('<Leave>', lambda e: btn.config(bg=couleur))

        return btn
    
    def creer_panel(self, parent, titre):
        """Créer un panel avec titre"""
        panel = tk.Frame(parent, bg="white", relief='solid', bd=1)
        
        # En-tête du panel
        header = tk.Frame(panel, bg="white")
        header.pack(fill='x', padx=15, pady=(15, 10))
        
        titre_label = tk.Label(
            header,
            text=titre,
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg=COLORS['dark']
        )
        titre_label.pack(anchor='w')
        
        # Ligne séparatrice
        separator = tk.Frame(panel, bg=COLORS['light'], height=1)
        separator.pack(fill='x')
        
        return panel
    
    def lighten_color(self, hex_color):
        """Éclaircir une couleur hexadécimale"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, r + 40)
        g = min(255, g + 40)
        b = min(255, b + 40)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def darken_color(self, hex_color):
        """Assombrir une couleur hexadécimale"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, r - 20)
        g = max(0, g - 20)
        b = max(0, b - 20)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def actualiser_stats(self):
        """Actualiser les statistiques"""
        try:
            stats = Rapport.statistiques_generales()
            
            # Mettre à jour les cartes
            self.carte_ventes.config(text=str(stats['nb_ventes']))
            self.carte_ca.config(text=f"{stats['ca_jour']:,.0f} FCFA")
            
            # Stock faible
            produits_alerte = Produit.obtenir_stock_faible()
            self.carte_alertes.config(text=str(len(produits_alerte)))
            
            # Dernières ventes
            from modules.ventes import Vente
            ventes_jour = Vente.obtenir_ventes_du_jour()
            
            self.ventes_liste.config(state='normal')
            self.ventes_liste.delete('1.0', 'end')
            
            if not ventes_jour:
                self.ventes_liste.insert('1.0', "Aucune vente aujourd'hui")
            else:
                for vente in ventes_jour[:5]:
                    numero = vente[1] if len(vente) > 1 else "N/A"
                    total = vente[3] if len(vente) > 3 else 0
                    self.ventes_liste.insert('end', f"• {numero}: {total:,.0f} FCFA\n")
            
            self.ventes_liste.config(state='disabled')
            
            # Stock faible
            self.stock_liste.config(state='normal')
            self.stock_liste.delete('1.0', 'end')
            
            if not produits_alerte:
                self.stock_liste.insert('1.0', "✅ Tous les stocks sont OK")
            else:
                for produit in produits_alerte[:5]:
                    nom = produit[1]
                    stock = produit[5]
                    self.stock_liste.insert('end', f"⚠️ {nom}: Stock {stock}\n")
            
            self.stock_liste.config(state='disabled')
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'actualiser:\n{e}")
    
    def ouvrir_ventes(self):
        """Ouvrir la fenêtre de vente"""
        from interface.fenetre_ventes import FenetreVentes
        FenetreVentes(self.root, callback=self.actualiser_stats)

    def ouvrir_liste_ventes(self):
        """Ouvrir la liste des ventes"""
        from interface.fenetre_liste_ventes import FenetreListeVentes
        FenetreListeVentes(self.root)
        
    def ouvrir_ajout_produit(self):
        """Ouvrir l'ajout de produit"""
        from interface.fenetre_produits import FenetreProduits
        FenetreProduits(self.root)
    
    def ouvrir_rapports(self):
        """Ouvrir les rapports"""
        from interface.fenetre_rapports import FenetreRapports
        FenetreRapports(self.root)
    
    def ouvrir_whatsapp(self):
        """Ouvrir l'export WhatsApp"""
        from interface.fenetre_whatsapp import FenetreWhatsApp
        FenetreWhatsApp(self.root)

    def ouvrir_a_propos(self):
        """Ouvrir la fenêtre À propos"""
        from interface.fenetre_a_propos import FenetreAPropos
        FenetreAPropos(self.root)

    def ouvrir_doc(self):
        """Ouvrir la documentation"""
        messagebox.showinfo("Documentation", "La documentation sera bientôt disponible.")

    def contacter_support(self):
        """Contacter le support"""
        messagebox.showinfo(
            "Support",
            "Pour toute assistance:\n\n"
            "📧 Email: support@votreentreprise.bj\n"
            "📱 Tél: +229 XX XX XX XX"
        )

    def ouvrir_utilisateurs(self):
        """Ouvrir gestion des utilisateurs"""
        from interface.fenetre_utilisateurs import FenetreUtilisateurs
        FenetreUtilisateurs(self.root, self.utilisateur)
    
    def ouvrir_sync(self):
        """Ouvrir configuration synchronisation"""
        from interface.fenetre_config_sync import FenetreConfigSync
        FenetreConfigSync(self.root)
    
    def sauvegarder(self):
        """Sauvegarder la base de données"""
        import shutil
        from datetime import datetime
        from tkinter import messagebox
        
        try:
            # Créer dossier sauvegardes s'il n'existe pas
            backup_dir = os.path.join(BASE_DIR, 'sauvegardes')
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            
            # Nom du fichier de sauvegarde avec date
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"boutique_{timestamp}.db")
            
            # Copier la base de données
            shutil.copy2(DB_PATH, backup_file)
            
            messagebox.showinfo(
                "Succès",
                f"✅ Sauvegarde créée avec succès!\n\n{backup_file}"
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"❌ Erreur de sauvegarde:\n{e}")
    
    
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