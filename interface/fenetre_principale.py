"""
Fenetre principale - Dashboard moderne avec graphiques
"""
import tkinter as tk
from tkinter import ttk, messagebox
from config import *
from modules.rapports import Rapport
from modules.produits import Produit
from modules.theme import ThemeManager
import shutil
import os
from datetime import datetime

# Import matplotlib avec backend TkAgg
try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_DISPONIBLE = True
except ImportError:
    MATPLOTLIB_DISPONIBLE = False


class FenetrePrincipale:
    def __init__(self, utilisateur=None):
        self.utilisateur = utilisateur
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} - {self.utilisateur['nom']} ({self.utilisateur['role'].upper()})")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(1024, 600)
        self.root.configure(bg=COLORS['bg'])

        self.centrer_fenetre()
        self.creer_interface()
        self.appliquer_permissions()

        # Premier chargement des donnees
        self.actualiser_stats()

        # Actualisation periodique (toutes les 10s)
        self.actualisation_periodique()

        # Timeout de session
        self._setup_session_timeout()

        # Sauvegarde automatique au demarrage
        try:
            from modules.sauvegarde import planifier_sauvegarde_auto
            planifier_sauvegarde_auto()
        except Exception as e:
            print(f"Erreur sauvegarde auto: {e}")

    def actualisation_periodique(self):
        """Boucle de rafraichissement automatique"""
        try:
            self.actualiser_stats()
            self.root.after(10000, self.actualisation_periodique)
        except Exception as e:
            print(f"Erreur actualisation auto: {e}")

    def appliquer_permissions(self):
        """Desactiver/Cacher des elements pour les caissiers"""
        if self.utilisateur['role'] == 'caissier':
            if hasattr(self, 'btn_rapports'):
                self.btn_rapports.grid_remove()
            if hasattr(self, 'btn_produit'):
                self.btn_produit.grid_remove()

    def centrer_fenetre(self):
        """Centrer la fenetre sur l'ecran"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def creer_interface(self):
        """Creer l'interface moderne avec graphiques"""

        # --- MENU ---
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        menu_fichier = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=menu_fichier)
        menu_fichier.add_command(label="Quitter", command=self.root.quit)

        if self.utilisateur and self.utilisateur['role'] == 'patron':
            menu_admin = tk.Menu(menubar, tearoff=0)
            menubar.add_cascade(label="Administration", menu=menu_admin)
            menu_admin.add_command(label="Gestion utilisateurs", command=self.ouvrir_utilisateurs)
            menu_admin.add_command(label="Synchronisation", command=self.ouvrir_sync)
            menu_admin.add_command(label="Parametres fiscaux", command=self.ouvrir_parametres_fiscaux)
            menu_admin.add_separator()
            menu_admin.add_command(label="Sauvegarde", command=self.sauvegarder)
            menu_admin.add_command(label="Restaurer", command=self.restaurer)
            menu_admin.add_separator()
            menu_admin.add_command(label="Exporter (ZIP)", command=self.exporter_zip)
            menu_admin.add_command(label="Importer (ZIP)", command=self.importer_zip)

        menu_aide = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=menu_aide)
        menu_aide.add_command(label="A propos", command=self.ouvrir_a_propos)
        menu_aide.add_separator()
        menu_aide.add_command(label="Documentation", command=self.ouvrir_doc)
        menu_aide.add_command(label="Support", command=self.contacter_support)

        # --- EN-TETE ---
        header = tk.Frame(self.root, bg=COLORS['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        titre_frame = tk.Frame(header, bg=COLORS['primary'])
        titre_frame.pack(fill='x', padx=20)

        tk.Label(
            titre_frame, text=f"  {APP_NAME}", font=("Segoe UI", 24, "bold"),
            bg=COLORS['primary'], fg="white"
        ).pack(side='left', pady=20)

        # Bouton theme sombre/clair
        theme_icon = "Sombre" if not ThemeManager.instance().est_sombre else "Clair"
        self.btn_theme = tk.Button(
            titre_frame, text=theme_icon,
            font=("Segoe UI", 10, "bold"),
            bg=COLORS['primary'], fg="white",
            relief='flat', cursor='hand2', bd=0,
            command=self.basculer_theme
        )
        self.btn_theme.pack(side='right', padx=10, pady=20)

        # --- CONTENEUR PRINCIPAL (scrollable) ---
        main_container = tk.Frame(self.root, bg=COLORS['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=15)

        # Info session
        tk.Label(
            main_container,
            text=f"Session : {self.utilisateur['nom']} ({self.utilisateur['role'].upper()})",
            font=("Segoe UI", 10, "italic"), bg=COLORS['bg'], fg=COLORS['gray']
        ).pack(anchor='e')

        # --- CARTES STATISTIQUES ---
        stats_frame = tk.Frame(main_container, bg=COLORS['bg'])
        stats_frame.pack(fill='x', pady=(0, 10))
        for i in range(3):
            stats_frame.columnconfigure(i, weight=1, uniform="stat")

        self.carte_ventes = self.creer_carte_stat(stats_frame, "Ventes jour", "0", COLORS['primary'], 0)
        self.carte_ca = self.creer_carte_stat(stats_frame, "Chiffre d'affaires", "0 F", COLORS['success'], 1)
        self.carte_alertes = self.creer_carte_stat(stats_frame, "Alertes stock", "0", COLORS['danger'], 2)

        # Ligne de comparaison
        comp_frame = tk.Frame(main_container, bg=COLORS['bg'])
        comp_frame.pack(fill='x', pady=(0, 15))

        self.label_comparaison = tk.Label(
            comp_frame, text="",
            font=("Segoe UI", 10, "bold"), bg=COLORS['bg'], fg=COLORS['gray']
        )
        self.label_comparaison.pack(anchor='w')

        # --- ACTIONS RAPIDES ---
        tk.Label(
            main_container, text="Actions rapides", font=("Segoe UI", 13, "bold"),
            bg=COLORS['bg'], fg=COLORS['dark']
        ).pack(anchor='w', pady=(5, 10))

        actions_frame = tk.Frame(main_container, bg=COLORS['bg'])
        actions_frame.pack(fill='x', pady=(0, 15))

        for i in range(3):
            actions_frame.columnconfigure(i, weight=1, uniform="actions")

        # Ligne 1
        self.btn_vente = self.creer_bouton_action(actions_frame, "F1  Nouvelle vente", COLORS['primary'], self.ouvrir_ventes, 0, 0)
        self.btn_produit = self.creer_bouton_action(actions_frame, "F2  Produits", COLORS['success'], self.ouvrir_ajout_produit, 0, 1)
        self.btn_liste = self.creer_bouton_action(actions_frame, "F3  Liste des ventes", COLORS['purple'], self.ouvrir_liste_ventes, 0, 2)

        # Ligne 2
        self.btn_rapports = self.creer_bouton_action(actions_frame, "F4  Rapports", COLORS['info'], self.ouvrir_rapports, 1, 0)
        self.btn_whatsapp = self.creer_bouton_action(actions_frame, "F6  Export WhatsApp", COLORS['warning'], self.ouvrir_whatsapp, 1, 1)

        if self.utilisateur['role'] == 'patron':
            self.creer_bouton_action(actions_frame, "Synchronisation", COLORS['info'], self.ouvrir_sync, 1, 2)

        # --- SECTION INFERIEURE : Graphique + Listes ---
        bottom_frame = tk.Frame(main_container, bg=COLORS['bg'])
        bottom_frame.pack(fill='both', expand=True)
        bottom_frame.columnconfigure(0, weight=3)
        bottom_frame.columnconfigure(1, weight=2)
        bottom_frame.rowconfigure(0, weight=1)

        # Gauche : Graphique ventes
        chart_panel = self.creer_panel(bottom_frame, "Ventes de la semaine")
        chart_panel.grid(row=0, column=0, sticky='nsew', padx=(0, 8))

        # Selecteur de periode
        periode_frame = tk.Frame(chart_panel, bg=COLORS['card_bg'])
        periode_frame.pack(fill='x', padx=15, pady=(5, 0))

        self.periode_var = tk.StringVar(value='semaine')
        for txt, val in [("Jour", "jour"), ("Semaine", "semaine"), ("Mois", "mois")]:
            tk.Radiobutton(
                periode_frame, text=txt, variable=self.periode_var, value=val,
                font=("Segoe UI", 9), bg=COLORS['card_bg'],
                fg=COLORS.get('text', '#1F2937'),
                selectcolor=COLORS['card_bg'],
                command=lambda: self.dessiner_graphique_ventes()
            ).pack(side='left', padx=5)

        self.chart_frame = tk.Frame(chart_panel, bg=COLORS['card_bg'])
        self.chart_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Droite : Dernieres ventes + Stock faible
        right_panel = tk.Frame(bottom_frame, bg=COLORS['bg'])
        right_panel.grid(row=0, column=1, sticky='nsew', padx=(8, 0))
        right_panel.rowconfigure(0, weight=1)
        right_panel.rowconfigure(1, weight=1)

        self.ventes_liste = self.creer_liste_scroll(right_panel, "Dernieres ventes", 0)
        self.stock_liste = self.creer_liste_scroll(right_panel, "Stock faible", 1)

        # --- BARRE DE RACCOURCIS EN BAS ---
        footer = tk.Frame(self.root, bg=COLORS['light'], height=28)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)

        tk.Label(
            footer,
            text="F1=Nouvelle vente | F2=Produits | F3=Ventes | F4=Rapports | F5=Actualiser | F6=WhatsApp",
            font=("Segoe UI", 8),
            bg=COLORS['light'], fg=COLORS['gray']
        ).pack(expand=True)

        # --- RACCOURCIS CLAVIER ---
        self.root.bind('<F1>', lambda e: self.ouvrir_ventes())
        self.root.bind('<F2>', lambda e: self.ouvrir_ajout_produit())
        self.root.bind('<F3>', lambda e: self.ouvrir_liste_ventes())
        self.root.bind('<F4>', lambda e: self.ouvrir_rapports())
        self.root.bind('<F5>', lambda e: self.actualiser_stats())
        self.root.bind('<F6>', lambda e: self.ouvrir_whatsapp())

    def creer_liste_scroll(self, parent, titre, row):
        """Helper pour creer les zones de texte du bas"""
        panel = self.creer_panel(parent, titre)
        panel.grid(row=row, column=0, sticky='nsew', pady=(0, 5) if row == 0 else (5, 0))
        txt = tk.Text(panel, height=5, font=("Segoe UI", 10),
                      bg=COLORS['card_bg'], fg=COLORS.get('text', '#1F2937'),
                      relief='flat', state='disabled')
        txt.pack(fill='both', expand=True, padx=15, pady=(5, 15))
        return txt

    def creer_carte_stat(self, parent, titre, valeur, couleur, col):
        """Creer une carte de statistique"""
        carte = tk.Frame(parent, bg=COLORS['card_bg'], relief='solid', bd=1,
                         highlightbackground=COLORS.get('card_border', '#E5E7EB'),
                         highlightthickness=1)
        carte.grid(row=0, column=col, sticky='ew', padx=5, pady=5)

        inner = tk.Frame(carte, bg=COLORS['card_bg'])
        inner.pack(fill='both', expand=True, padx=20, pady=15)

        titre_label = tk.Label(
            inner, text=titre,
            font=("Segoe UI", 10), bg=COLORS['card_bg'], fg=COLORS['gray'], anchor='w'
        )
        titre_label.pack(anchor='w')

        valeur_label = tk.Label(
            inner, text=valeur,
            font=("Segoe UI", 22, "bold"), bg=COLORS['card_bg'], fg=couleur, anchor='w'
        )
        valeur_label.pack(anchor='w')

        return valeur_label

    def creer_bouton_action(self, parent, texte, couleur, commande, row, col):
        """Creer un bouton d'action"""
        btn = tk.Button(
            parent, text=texte,
            font=("Segoe UI", 12, "bold"),
            bg=couleur, fg="white",
            relief='flat', cursor='hand2',
            command=commande,
            activebackground=self.darken_color(couleur),
            activeforeground="white"
        )
        btn.grid(row=row, column=col, sticky='ew', padx=5, pady=5, ipady=15)

        btn.bind('<Enter>', lambda e: btn.config(bg=self.darken_color(couleur)))
        btn.bind('<Leave>', lambda e: btn.config(bg=couleur))

        return btn

    def creer_panel(self, parent, titre):
        """Creer un panel avec titre"""
        panel = tk.Frame(parent, bg=COLORS['card_bg'], relief='solid', bd=1,
                         highlightbackground=COLORS.get('card_border', '#E5E7EB'),
                         highlightthickness=1)

        header = tk.Frame(panel, bg=COLORS['card_bg'])
        header.pack(fill='x', padx=15, pady=(12, 8))

        tk.Label(
            header, text=titre,
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['card_bg'], fg=COLORS['dark']
        ).pack(anchor='w')

        tk.Frame(panel, bg=COLORS.get('separator', '#E5E7EB'), height=1).pack(fill='x')

        return panel

    def lighten_color(self, hex_color):
        """Eclaircir une couleur hexadecimale"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, r + 40)
        g = min(255, g + 40)
        b = min(255, b + 40)
        return f'#{r:02x}{g:02x}{b:02x}'

    def darken_color(self, hex_color):
        """Assombrir une couleur hexadecimale"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, r - 20)
        g = max(0, g - 20)
        b = max(0, b - 20)
        return f'#{r:02x}{g:02x}{b:02x}'

    def dessiner_graphique_ventes(self):
        """Dessiner le graphique des ventes avec matplotlib"""
        # Nettoyer le frame
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        if not MATPLOTLIB_DISPONIBLE:
            tk.Label(
                self.chart_frame, text="matplotlib non installe\npip install matplotlib",
                font=("Segoe UI", 10), bg=COLORS['card_bg'], fg=COLORS['gray']
            ).pack(expand=True)
            return

        periode = self.periode_var.get()
        data = Rapport.donnees_graphique_ventes(periode)

        if not data:
            tk.Label(
                self.chart_frame, text="Pas de donnees pour cette periode",
                font=("Segoe UI", 11), bg=COLORS['card_bg'], fg=COLORS['gray']
            ).pack(expand=True)
            return

        labels = [d[0] for d in data]
        values = [d[1] for d in data]

        bg_color = COLORS['card_bg']
        text_color = COLORS.get('text', '#1F2937')
        bar_color = COLORS['primary']
        sep_color = COLORS.get('separator', '#E5E7EB')

        fig = Figure(figsize=(5, 2.5), dpi=100)
        fig.patch.set_facecolor(bg_color)

        ax = fig.add_subplot(111)
        ax.set_facecolor(bg_color)
        ax.bar(labels, values, color=bar_color, width=0.6)
        ax.set_ylabel('CA (FCFA)', color=text_color, fontsize=9)
        ax.tick_params(colors=text_color, labelsize=8)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(sep_color)
        ax.spines['left'].set_color(sep_color)

        # Formater les valeurs sur l'axe Y
        ax.yaxis.set_major_formatter(
            matplotlib.ticker.FuncFormatter(lambda x, _: f'{x:,.0f}')
        )

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True)

    def actualiser_stats(self):
        """Actualiser les statistiques"""
        try:
            stats = Rapport.statistiques_generales()

            # Cartes
            self.carte_ventes.config(text=str(stats['nb_ventes']))
            self.carte_ca.config(text=f"{stats['ca_jour']:,.0f} FCFA")

            # Stock faible
            produits_alerte = Produit.obtenir_stock_faible()
            self.carte_alertes.config(text=str(len(produits_alerte)))

            # Comparaison vs hier
            try:
                comp = Rapport.comparaison_jour_precedent()
                variation = comp['variation_ca_pct']
                signe = "+" if variation >= 0 else ""
                couleur = COLORS['success'] if variation >= 0 else COLORS['danger']
                fleche = "^" if variation >= 0 else "v"
                self.label_comparaison.config(
                    text=f"{fleche} {signe}{variation:.0f}% vs hier  |  CA mois: {stats['ca_mois']:,.0f} FCFA",
                    fg=couleur
                )
            except Exception:
                pass

            # Dernieres ventes
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
                    self.ventes_liste.insert('end', f"  {numero}: {total:,.0f} FCFA\n")

            self.ventes_liste.config(state='disabled')

            # Stock faible
            self.stock_liste.config(state='normal')
            self.stock_liste.delete('1.0', 'end')

            if not produits_alerte:
                self.stock_liste.insert('1.0', "Tous les stocks sont OK")
            else:
                for produit in produits_alerte[:5]:
                    nom = produit[1]
                    stock = produit[5]
                    self.stock_liste.insert('end', f"  {nom}: Stock {stock}\n")

            self.stock_liste.config(state='disabled')

            # Graphique
            self.dessiner_graphique_ventes()

        except Exception as e:
            print(f"Erreur actualisation: {e}")

    # --- Ouverture des fenetres ---

    def ouvrir_ventes(self):
        from interface.fenetre_ventes import FenetreVentes
        FenetreVentes(self.root, callback=self.actualiser_stats)

    def ouvrir_liste_ventes(self):
        from interface.fenetre_liste_ventes import FenetreListeVentes
        FenetreListeVentes(self.root)

    def ouvrir_ajout_produit(self):
        from interface.fenetre_produits import FenetreProduits
        FenetreProduits(self.root)

    def ouvrir_rapports(self):
        if self.utilisateur['role'] != 'patron':
            messagebox.showwarning("Acces refuse", "Reserve a l'administrateur")
            return
        from interface.fenetre_rapports import FenetreRapports
        FenetreRapports(self.root)

    def ouvrir_whatsapp(self):
        from interface.fenetre_whatsapp import FenetreWhatsApp
        FenetreWhatsApp(self.root)

    def ouvrir_a_propos(self):
        from interface.fenetre_a_propos import FenetreAPropos
        FenetreAPropos(self.root)

    def ouvrir_doc(self):
        messagebox.showinfo("Documentation", "La documentation sera bientot disponible.")

    def contacter_support(self):
        messagebox.showinfo(
            "Support",
            "Pour toute assistance:\n\n"
            "Email: support@votreentreprise.bj\n"
            "Tel: +229 XX XX XX XX"
        )

    def ouvrir_utilisateurs(self):
        from interface.fenetre_utilisateurs import FenetreUtilisateurs
        FenetreUtilisateurs(self.root, self.utilisateur)

    def ouvrir_sync(self):
        from interface.fenetre_config_sync import FenetreConfigSync
        FenetreConfigSync(self.root)

    def basculer_theme(self):
        """Basculer entre theme sombre et clair"""
        ThemeManager.instance().basculer()
        nouveau = "Clair" if ThemeManager.instance().est_sombre else "Sombre"
        self.btn_theme.config(text=nouveau)
        messagebox.showinfo("Theme",
            f"Theme {ThemeManager.instance().nom_theme} active.\n\n"
            "Fermez et rouvrez l'application pour appliquer completement.")

    # --- Sauvegarde / Restauration ---

    def sauvegarder(self):
        from modules.sauvegarde import sauvegarder_locale
        succes, message, chemin = sauvegarder_locale()
        if succes:
            messagebox.showinfo("Succes", f"Sauvegarde creee!\n\n{chemin}")
        else:
            messagebox.showerror("Erreur", f"Erreur de sauvegarde:\n{message}")

    def restaurer(self):
        from modules.sauvegarde import lister_sauvegardes, restaurer

        sauvegardes = lister_sauvegardes()
        if not sauvegardes:
            messagebox.showinfo("Info", "Aucune sauvegarde disponible.")
            return

        win = tk.Toplevel(self.root)
        win.title("Restaurer une sauvegarde")
        win.geometry("500x400")
        win.configure(bg=COLORS['card_bg'])
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win, text="Choisir une sauvegarde",
            font=("Segoe UI", 14, "bold"), bg=COLORS['card_bg'],
            fg=COLORS.get('text', '#1F2937')
        ).pack(pady=15)

        listbox = tk.Listbox(win, font=("Segoe UI", 11), height=10,
                             bg=COLORS.get('input_bg', 'white'),
                             fg=COLORS.get('input_fg', '#1F2937'))
        listbox.pack(fill='both', expand=True, padx=20, pady=(0, 10))

        for s in sauvegardes:
            listbox.insert('end', f"{s['date_affichage']} - {s['taille']}")

        def confirmer():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Attention", "Selectionnez une sauvegarde")
                return
            idx = sel[0]
            chemin = sauvegardes[idx]['chemin']
            reponse = messagebox.askyesno(
                "Confirmation",
                f"Restaurer la sauvegarde du {sauvegardes[idx]['date_affichage']}?\n\n"
                "La base actuelle sera sauvegardee avant la restauration."
            )
            if reponse:
                win.destroy()
                succes, message = restaurer(chemin)
                if succes:
                    messagebox.showinfo("Succes", message)
                    self.actualiser_stats()
                else:
                    messagebox.showerror("Erreur", message)

        tk.Button(
            win, text="Restaurer", font=("Segoe UI", 12, "bold"),
            bg=COLORS['primary'], fg="white", relief='flat',
            command=confirmer
        ).pack(fill='x', padx=20, ipady=10, pady=(0, 10))

        tk.Button(
            win, text="Annuler", font=("Segoe UI", 11),
            bg=COLORS['gray'], fg="white", relief='flat',
            command=win.destroy
        ).pack(fill='x', padx=20, ipady=8, pady=(0, 10))

    def exporter_zip(self):
        from modules.sauvegarde import exporter_zip
        succes, message, chemin = exporter_zip()
        if succes:
            messagebox.showinfo("Succes", f"Export ZIP cree!\n\n{chemin}")
        else:
            messagebox.showerror("Erreur", message)

    def importer_zip(self):
        from tkinter import filedialog
        from modules.sauvegarde import importer_zip

        chemin = filedialog.askopenfilename(
            title="Selectionner un fichier ZIP",
            filetypes=[("Fichiers ZIP", "*.zip")],
            parent=self.root
        )
        if not chemin:
            return

        reponse = messagebox.askyesno(
            "Confirmation",
            "Importer ce fichier?\n\n"
            "Les donnees actuelles seront sauvegardees puis remplacees."
        )
        if reponse:
            succes, message = importer_zip(chemin)
            if succes:
                messagebox.showinfo("Succes", message)
                self.actualiser_stats()
            else:
                messagebox.showerror("Erreur", message)

    def ouvrir_parametres_fiscaux(self):
        from interface.fenetre_parametres_fiscaux import FenetreParametresFiscaux
        FenetreParametresFiscaux(self.root)

    # --- Session timeout ---

    def _setup_session_timeout(self):
        from database import db
        timeout_str = db.get_parametre('session_timeout', '900')
        try:
            self._session_timeout = int(timeout_str) * 1000
        except ValueError:
            self._session_timeout = 900000

        self._timeout_id = None
        self._reset_timeout()

        self.root.bind_all('<Any-KeyPress>', self._on_activity)
        self.root.bind_all('<Any-ButtonPress>', self._on_activity)

    def _on_activity(self, event=None):
        self._reset_timeout()

    def _reset_timeout(self):
        if self._timeout_id:
            self.root.after_cancel(self._timeout_id)
        self._timeout_id = self.root.after(self._session_timeout, self._session_expired)

    def _session_expired(self):
        messagebox.showinfo("Session expiree", "Vous avez ete deconnecte pour inactivite.")
        self.root.destroy()
        from main import demander_login
        demander_login()

    def lancer(self):
        """Lancer l'application"""
        self.root.mainloop()
