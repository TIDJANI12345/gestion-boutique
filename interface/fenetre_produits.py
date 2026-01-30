"""
Fenêtre de gestion des produits - Design moderne avec choix code-barres
"""
import tkinter as tk
from tkinter import ttk, messagebox
from modules.produits import Produit
from modules.codebarres import CodeBarre
from config import *

class FenetreProduits:
    def __init__(self, parent):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Gestion des Produits")
        self.fenetre.geometry("1300x750")
        self.fenetre.configure(bg=COLORS['bg'])
        
        self.mode_code_barre = tk.StringVar(value="auto")
        self.type_code_barre = tk.StringVar(value="code128")
        
        self.creer_interface()
        self.charger_produits()
    
    def creer_interface(self):
        """Créer l'interface moderne"""
        
        # En-tête
        header = tk.Frame(self.fenetre, bg=COLORS['primary'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        titre = tk.Label(
            header,
            text="📦 Gestion des Produits",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS['primary'],
            fg="white"
        )
        titre.pack(pady=25)
        
        # Container principal
        main = tk.Frame(self.fenetre, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Panel formulaire (à gauche)
        form_panel = tk.Frame(main, bg="white", relief='solid', bd=1)
        form_panel.pack(side='left', fill='both', padx=(0, 10), ipadx=20, ipady=20)
        
        # Titre du formulaire
        form_titre = tk.Label(
            form_panel,
            text="✏️ Informations du produit",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        )
        form_titre.pack(anchor='w', pady=(10, 15), padx=15)
        
        # Formulaire avec scroll
        canvas = tk.Canvas(form_panel, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(form_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ===== SECTION CODE-BARRES =====
        section_barcode = tk.LabelFrame(
            scrollable_frame,
            text="🏷️ Code-barres",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=COLORS['dark'],
            padx=15,
            pady=10
        )
        section_barcode.pack(fill='x', padx=15, pady=(0, 15))
        
        # Mode: Manuel ou Auto
        mode_frame = tk.Frame(section_barcode, bg="white")
        mode_frame.pack(fill='x', pady=(5, 10))
        
        tk.Label(
            mode_frame,
            text="Mode:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(side='left', padx=(0, 10))
        
        tk.Radiobutton(
            mode_frame,
            text="🎲 Générer automatiquement",
            variable=self.mode_code_barre,
            value="auto",
            font=("Segoe UI", 10),
            bg="white",
            command=self.toggle_mode_code_barre
        ).pack(side='left', padx=5)
        
        tk.Radiobutton(
            mode_frame,
            text="✏️ Saisir manuellement",
            variable=self.mode_code_barre,
            value="manuel",
            font=("Segoe UI", 10),
            bg="white",
            command=self.toggle_mode_code_barre
        ).pack(side='left', padx=5)
        
        # Type de code-barres
        type_frame = tk.Frame(section_barcode, bg="white")
        type_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            type_frame,
            text="Type:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(side='left', padx=(0, 10))
        
        for code_type, label in BARCODE_TYPES.items():
            tk.Radiobutton(
                type_frame,
                text=label,
                variable=self.type_code_barre,
                value=code_type,
                font=("Segoe UI", 9),
                bg="white"
            ).pack(side='left', padx=5)
        
        # Champ code-barres
        code_frame = tk.Frame(section_barcode, bg="white")
        code_frame.pack(fill='x')
        
        self.entry_code_barre = tk.Entry(
            code_frame,
            font=("Segoe UI", 11),
            relief='solid',
            bd=1,
            state='disabled'
        )
        self.entry_code_barre.pack(side='left', fill='x', expand=True, ipady=8)
        
        self.btn_generer = tk.Button(
            code_frame,
            text="🎲 Générer",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS['gray'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.generer_code_barre,
            padx=15
        )
        self.btn_generer.pack(side='left', padx=(10, 0), ipady=5)
        
        # Info
        self.info_label = tk.Label(
            section_barcode,
            text="💡 Le code sera généré automatiquement",
            font=("Segoe UI", 9, "italic"),
            bg="white",
            fg=COLORS['gray']
        )
        self.info_label.pack(anchor='w', pady=(5, 0))
        
        # ===== INFORMATIONS PRODUIT =====
        section_info = tk.LabelFrame(
            scrollable_frame,
            text="📋 Informations générales",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=COLORS['dark'],
            padx=15,
            pady=10
        )
        section_info.pack(fill='x', padx=15, pady=(0, 15))
        
        # Nom
        self.creer_champ(section_info, "Nom du produit *", "entry_nom")
        
        # Catégorie
        self.creer_champ(section_info, "Catégorie", "entry_categorie")
        
        # Description
        tk.Label(
            section_info,
            text="Description",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            anchor='w'
        ).pack(fill='x', pady=(10, 5))
        
        self.entry_description = tk.Text(
            section_info,
            font=("Segoe UI", 10),
            relief='solid',
            bd=1,
            height=3
        )
        self.entry_description.pack(fill='x', pady=(0, 10))
        
        # ===== PRIX =====
        section_prix = tk.LabelFrame(
            scrollable_frame,
            text="💰 Prix",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=COLORS['dark'],
            padx=15,
            pady=10
        )
        section_prix.pack(fill='x', padx=15, pady=(0, 15))
        
        prix_frame = tk.Frame(section_prix, bg="white")
        prix_frame.pack(fill='x')
        
        # Prix achat
        left_prix = tk.Frame(prix_frame, bg="white")
        left_prix.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.creer_champ(left_prix, "Prix d'achat", "entry_prix_achat")
        
        # Prix vente
        right_prix = tk.Frame(prix_frame, bg="white")
        right_prix.pack(side='left', fill='both', expand=True)
        self.creer_champ(right_prix, "Prix de vente *", "entry_prix_vente")
        
        # ===== STOCK =====
        section_stock = tk.LabelFrame(
            scrollable_frame,
            text="📦 Stock",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=COLORS['dark'],
            padx=15,
            pady=10
        )
        section_stock.pack(fill='x', padx=15, pady=(0, 15))
        
        stock_frame = tk.Frame(section_stock, bg="white")
        stock_frame.pack(fill='x')
        
        # Stock actuel
        left_stock = tk.Frame(stock_frame, bg="white")
        left_stock.pack(side='left', fill='both', expand=True, padx=(0, 10))
        self.creer_champ(left_stock, "Stock initial", "entry_stock")
        
        # Seuil alerte
        right_stock = tk.Frame(stock_frame, bg="white")
        right_stock.pack(side='left', fill='both', expand=True)
        self.creer_champ(right_stock, "Seuil d'alerte", "entry_stock_alerte")
        
        # Valeur par défaut
        self.entry_stock_alerte.insert(0, "5")
        
        # ===== BOUTONS =====
        btn_frame = tk.Frame(scrollable_frame, bg="white")
        btn_frame.pack(fill='x', padx=15, pady=(10, 15))
        
        tk.Button(
            btn_frame,
            text="✅ Enregistrer",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['success'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.ajouter_produit
        ).pack(side='left', fill='x', expand=True, ipady=12, padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="🔄 Réinitialiser",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['gray'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.vider_formulaire
        ).pack(side='left', fill='x', expand=True, ipady=12, padx=(5, 0))
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Panel liste des produits (à droite)
        list_panel = tk.Frame(main, bg="white", relief='solid', bd=1)
        list_panel.pack(side='left', fill='both', expand=True, padx=(10, 0))
        
        # En-tête du panel
        list_header = tk.Frame(list_panel, bg="white")
        list_header.pack(fill='x', padx=15, pady=15)
        
        tk.Label(
            list_header,
            text="📋 Liste des produits",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(side='left')
        
        # Recherche
        search_frame = tk.Frame(list_header, bg="white")
        search_frame.pack(side='right')
        
        tk.Label(
            search_frame,
            text="🔍",
            font=("Segoe UI", 12),
            bg="white"
        ).pack(side='left', padx=(0, 5))
        
        self.entry_recherche = tk.Entry(
            search_frame,
            font=("Segoe UI", 10),
            relief='solid',
            bd=1,
            width=25
        )
        self.entry_recherche.pack(side='left', ipady=5)
        self.entry_recherche.bind('<KeyRelease>', lambda e: self.rechercher_produits())
        
        # Filtres
        filter_frame = tk.Frame(list_panel, bg="white")
        filter_frame.pack(fill='x', padx=15, pady=(8, 5))

        tk.Label(filter_frame, text="Categorie:", font=("Segoe UI", 9), bg="white").pack(side='left', padx=(0, 3))
        self.combo_categorie = ttk.Combobox(filter_frame, width=14, state='readonly', font=("Segoe UI", 9))
        self.combo_categorie.pack(side='left', padx=(0, 8))
        self.combo_categorie.bind('<<ComboboxSelected>>', lambda e: self.appliquer_filtres())

        tk.Label(filter_frame, text="Stock:", font=("Segoe UI", 9), bg="white").pack(side='left', padx=(0, 3))
        self.combo_stock = ttk.Combobox(filter_frame, width=12, state='readonly', font=("Segoe UI", 9),
                                        values=["Tous", "Stock faible", "Rupture"])
        self.combo_stock.set("Tous")
        self.combo_stock.pack(side='left', padx=(0, 8))
        self.combo_stock.bind('<<ComboboxSelected>>', lambda e: self.appliquer_filtres())

        tk.Label(filter_frame, text="Prix:", font=("Segoe UI", 9), bg="white").pack(side='left', padx=(0, 3))
        self.entry_prix_min = tk.Entry(filter_frame, width=7, font=("Segoe UI", 9), relief='solid', bd=1)
        self.entry_prix_min.pack(side='left', padx=(0, 2))
        self.entry_prix_min.insert(0, "Min")
        self.entry_prix_min.bind('<FocusIn>', lambda e: self._clear_placeholder(self.entry_prix_min, "Min"))

        tk.Label(filter_frame, text="-", bg="white").pack(side='left')
        self.entry_prix_max = tk.Entry(filter_frame, width=7, font=("Segoe UI", 9), relief='solid', bd=1)
        self.entry_prix_max.pack(side='left', padx=(2, 5))
        self.entry_prix_max.insert(0, "Max")
        self.entry_prix_max.bind('<FocusIn>', lambda e: self._clear_placeholder(self.entry_prix_max, "Max"))

        tk.Button(filter_frame, text="Filtrer", font=("Segoe UI", 8, "bold"),
                  bg=COLORS['primary'], fg="white", relief='flat',
                  command=self.appliquer_filtres, padx=8).pack(side='left', padx=3)

        tk.Button(filter_frame, text="Reset", font=("Segoe UI", 8, "bold"),
                  bg=COLORS['gray'], fg="white", relief='flat',
                  command=self.reset_filtres, padx=8).pack(side='left')

        # Charger les categories dans le filtre
        self._charger_categories_filtre()

        # Separateur
        tk.Frame(list_panel, bg=COLORS['light'], height=1).pack(fill='x')

        # Boutons actions
        actions_frame = tk.Frame(list_panel, bg="white")
        actions_frame.pack(fill='x', padx=15, pady=10)
        
        btn_style = {
            'font': ("Segoe UI", 9, "bold"),
            'relief': 'flat',
            'cursor': 'hand2',
            'padx': 15,
            'pady': 8
        }
        
        tk.Button(
            actions_frame,
            text="✏️ Modifier",
            bg=COLORS['primary'],
            fg="white",
            command=self.modifier_produit,
            **btn_style
        ).pack(side='left', padx=(0, 5))
        
        tk.Button(
            actions_frame,
            text="🗑️ Supprimer",
            bg=COLORS['danger'],
            fg="white",
            command=self.supprimer_produit,
            **btn_style
        ).pack(side='left', padx=5)
        
        tk.Button(
            actions_frame,
            text="🖨️ Voir code-barres",
            bg=COLORS['info'],
            fg="white",
            command=self.voir_code_barre,
            **btn_style
        ).pack(side='left', padx=5)
        
        tk.Button(
            actions_frame,
            text="🔄 Actualiser",
            bg=COLORS['gray'],
            fg="white",
            command=self.charger_produits,
            **btn_style
        ).pack(side='left', padx=5)
        
        # Tableau
        table_frame = tk.Frame(list_panel, bg="white")
        table_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        scrollbar_y = ttk.Scrollbar(table_frame)
        scrollbar_y.pack(side='right', fill='y')
        
        scrollbar_x = ttk.Scrollbar(table_frame, orient='horizontal')
        scrollbar_x.pack(side='bottom', fill='x')
        
        colonnes = ('ID', 'Nom', 'Catégorie', 'Prix Vente', 'Stock', 'Type', 'Code-barre')
        self.tree = ttk.Treeview(
            table_frame,
            columns=colonnes,
            show='headings',
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # Configuration des colonnes
        self.tree.heading('ID', text='ID')
        self.tree.heading('Nom', text='Nom')
        self.tree.heading('Catégorie', text='Catégorie')
        self.tree.heading('Prix Vente', text='Prix Vente')
        self.tree.heading('Stock', text='Stock')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Code-barre', text='Code-barre')
        
        self.tree.column('ID', width=50)
        self.tree.column('Nom', width=200)
        self.tree.column('Catégorie', width=120)
        self.tree.column('Prix Vente', width=100)
        self.tree.column('Stock', width=80)
        self.tree.column('Type', width=100)
        self.tree.column('Code-barre', width=150)
        
        self.tree.pack(fill='both', expand=True)

        # Pagination
        self.page_actuelle = 0
        self.produits_par_page = PAGINATION['produits_par_page']

        page_frame = tk.Frame(list_panel, bg="white")
        page_frame.pack(fill='x', padx=15, pady=(5, 10))

        self.btn_prev = tk.Button(page_frame, text="< Precedent", font=("Segoe UI", 9),
                                   bg=COLORS['gray'], fg="white", relief='flat',
                                   command=self.page_precedente, padx=10)
        self.btn_prev.pack(side='left')

        self.label_page = tk.Label(page_frame, text="Page 1", font=("Segoe UI", 9, "bold"), bg="white")
        self.label_page.pack(side='left', padx=15)

        self.btn_next = tk.Button(page_frame, text="Suivant >", font=("Segoe UI", 9),
                                   bg=COLORS['gray'], fg="white", relief='flat',
                                   command=self.page_suivante, padx=10)
        self.btn_next.pack(side='left')

        self.label_total_produits = tk.Label(page_frame, text="", font=("Segoe UI", 9),
                                              bg="white", fg=COLORS['gray'])
        self.label_total_produits.pack(side='right')

        # Evenements
        self.tree.bind('<<TreeviewSelect>>', self.selectionner_produit)
        self.tree.bind('<Double-1>', self.voir_code_barre)
    
    def creer_champ(self, parent_widget, label, attr_name):
        """Créer un champ de formulaire"""
        tk.Label(
            parent_widget,
            text=label,
            font=("Segoe UI", 10, "bold"),
            bg="white",
            anchor='w'
        ).pack(fill='x', pady=(10, 5))
        
        entry = tk.Entry(
            parent_widget,
            font=("Segoe UI", 10),
            relief='solid',
            bd=1
        )
        entry.pack(fill='x', ipady=8, pady=(0, 10))
        
        setattr(self, attr_name, entry)
    
    def toggle_mode_code_barre(self):
        """Basculer entre mode manuel et auto"""
        if self.mode_code_barre.get() == "auto":
            self.entry_code_barre.config(state='disabled')
            self.btn_generer.config(state='normal')
            self.info_label.config(text="💡 Le code sera généré automatiquement")
        else:
            self.entry_code_barre.config(state='normal')
            self.btn_generer.config(state='normal')
            self.info_label.config(text="✏️ Saisissez votre code existant ou générez-en un")
            self.entry_code_barre.focus()
    
    def generer_code_barre(self):
        """Générer un code-barres"""
        type_code = self.type_code_barre.get()
        code = Produit.generer_code_barre(type_code)
        
        self.entry_code_barre.config(state='normal')
        self.entry_code_barre.delete(0, 'end')
        self.entry_code_barre.insert(0, code)
        if self.mode_code_barre.get() == "auto":
            self.entry_code_barre.config(state='disabled')
    
    def ajouter_produit(self):
        """Ajouter un nouveau produit"""
        try:
            nom = self.entry_nom.get().strip()
            categorie = self.entry_categorie.get().strip()
            description = self.entry_description.get("1.0", "end").strip()
            prix_achat = float(self.entry_prix_achat.get() or 0)
            prix_vente = float(self.entry_prix_vente.get())
            stock = int(self.entry_stock.get() or 0)
            stock_alerte = int(self.entry_stock_alerte.get() or 5)
            
            if not nom or not prix_vente:
                messagebox.showwarning("Attention", "Le nom et le prix de vente sont obligatoires")
                return
            
            # Code-barres
            code_barre = None
            if self.mode_code_barre.get() == "manuel":
                code_barre = self.entry_code_barre.get().strip()
                if not code_barre:
                    messagebox.showwarning("Attention", "Veuillez saisir ou générer un code-barres")
                    return
            
            type_code = self.type_code_barre.get()
            
            # Ajouter le produit
            code_result = Produit.ajouter(
                nom, categorie, prix_achat, prix_vente, 
                stock, stock_alerte, code_barre, type_code, description
            )
            
            if code_result:
                # Générer l'image du code-barres
                CodeBarre.generer_image(code_result, nom, prix_vente, type_code)
                
                messagebox.showinfo("Succès", f"✅ Produit ajouté!\nCode-barres: {code_result}")
                self.vider_formulaire()
                self.charger_produits()
        
        except ValueError as e:
            messagebox.showerror("Erreur", f"Vérifiez les valeurs saisies:\n{e}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur est survenue:\n{e}")
    
    def _clear_placeholder(self, entry, placeholder):
        """Effacer le placeholder au focus"""
        if entry.get() == placeholder:
            entry.delete(0, 'end')

    def _charger_categories_filtre(self):
        """Charger les categories dans le combobox filtre"""
        try:
            categories = Produit.obtenir_categories()
            self.combo_categorie['values'] = ["Toutes"] + categories
            self.combo_categorie.set("Toutes")
        except Exception:
            self.combo_categorie['values'] = ["Toutes"]
            self.combo_categorie.set("Toutes")

    def _get_filtres(self):
        """Recuperer les valeurs actuelles des filtres"""
        terme = self.entry_recherche.get().strip()
        categorie = self.combo_categorie.get() if hasattr(self, 'combo_categorie') else None
        stock_filter = self.combo_stock.get() if hasattr(self, 'combo_stock') else "Tous"
        if stock_filter == "Tous":
            stock_filter = None

        prix_min_str = self.entry_prix_min.get().strip() if hasattr(self, 'entry_prix_min') else ""
        prix_max_str = self.entry_prix_max.get().strip() if hasattr(self, 'entry_prix_max') else ""

        prix_min = None
        prix_max = None
        try:
            if prix_min_str and prix_min_str != "Min":
                prix_min = float(prix_min_str)
        except ValueError:
            pass
        try:
            if prix_max_str and prix_max_str != "Max":
                prix_max = float(prix_max_str)
        except ValueError:
            pass

        return terme, categorie, stock_filter, prix_min, prix_max

    def charger_produits(self):
        """Charger les produits avec filtres et pagination"""
        self.page_actuelle = 0
        self._charger_page()

    def _charger_page(self):
        """Charger la page actuelle de produits"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        terme, categorie, stock_filter, prix_min, prix_max = self._get_filtres()
        offset = self.page_actuelle * self.produits_par_page

        produits = Produit.rechercher_filtre(
            terme=terme, categorie=categorie, stock_filter=stock_filter,
            prix_min=prix_min, prix_max=prix_max,
            limit=self.produits_par_page, offset=offset
        )

        total = Produit.compter_filtre(
            terme=terme, categorie=categorie, stock_filter=stock_filter,
            prix_min=prix_min, prix_max=prix_max
        )

        for produit in produits:
            self.tree.insert('', 'end', values=(
                produit[0], produit[1], produit[2] or "Sans categorie",
                f"{produit[4]:.0f} FCFA", produit[5],
                produit[8] or "code128", produit[7]
            ))

        # Mise a jour pagination
        nb_pages = max(1, (total + self.produits_par_page - 1) // self.produits_par_page)
        self.label_page.config(text=f"Page {self.page_actuelle + 1} / {nb_pages}")
        self.label_total_produits.config(text=f"{total} produit(s)")

        self.btn_prev.config(state='normal' if self.page_actuelle > 0 else 'disabled')
        self.btn_next.config(state='normal' if self.page_actuelle < nb_pages - 1 else 'disabled')

    def rechercher_produits(self):
        """Rechercher avec mise a jour de la pagination"""
        self.page_actuelle = 0
        self._charger_page()

    def appliquer_filtres(self):
        """Appliquer les filtres et recharger"""
        self.page_actuelle = 0
        self._charger_page()

    def reset_filtres(self):
        """Remettre tous les filtres a zero"""
        self.entry_recherche.delete(0, 'end')
        self.combo_categorie.set("Toutes")
        self.combo_stock.set("Tous")
        self.entry_prix_min.delete(0, 'end')
        self.entry_prix_min.insert(0, "Min")
        self.entry_prix_max.delete(0, 'end')
        self.entry_prix_max.insert(0, "Max")
        self.page_actuelle = 0
        self._charger_page()

    def page_precedente(self):
        """Aller a la page precedente"""
        if self.page_actuelle > 0:
            self.page_actuelle -= 1
            self._charger_page()

    def page_suivante(self):
        """Aller a la page suivante"""
        self.page_actuelle += 1
        self._charger_page()
    
    def selectionner_produit(self, event):
        """Remplir le formulaire avec le produit sélectionné"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            values = item['values']
            
            # Remplir les champs
            self.entry_nom.delete(0, 'end')
            self.entry_nom.insert(0, values[1])
            
            self.entry_categorie.delete(0, 'end')
            self.entry_categorie.insert(0, values[2] if values[2] != "Sans catégorie" else "")
            
            # Récupérer le produit complet pour avoir tous les détails
            produit_id = values[0]
            produit = Produit.obtenir_par_id(produit_id)
            
            if produit:
                self.entry_prix_achat.delete(0, 'end')
                self.entry_prix_achat.insert(0, produit[3] or 0)
                
                self.entry_prix_vente.delete(0, 'end')
                self.entry_prix_vente.insert(0, produit[4])
                
                self.entry_stock.delete(0, 'end')
                self.entry_stock.insert(0, produit[5])
                
                self.entry_stock_alerte.delete(0, 'end')
                self.entry_stock_alerte.insert(0, produit[6])
                
                self.entry_description.delete("1.0", "end")
                if len(produit) > 10 and produit[10]:
                    self.entry_description.insert("1.0", produit[10])
    
    def modifier_produit(self):
        """Modifier le produit sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit")
            return
        
        try:
            item = self.tree.item(selection[0])
            id_produit = item['values'][0]
            
            nom = self.entry_nom.get().strip()
            categorie = self.entry_categorie.get().strip()
            description = self.entry_description.get("1.0", "end").strip()
            prix_achat = float(self.entry_prix_achat.get() or 0)
            prix_vente = float(self.entry_prix_vente.get())
            stock = int(self.entry_stock.get() or 0)
            stock_alerte = int(self.entry_stock_alerte.get() or 5)
            
            if Produit.modifier(id_produit, nom, categorie, prix_achat, prix_vente, stock, stock_alerte, description):
                messagebox.showinfo("Succès", "✅ Produit modifié avec succès")
                self.vider_formulaire()
                self.charger_produits()
        
        except ValueError:
            messagebox.showerror("Erreur", "Vérifiez les valeurs saisies")
    
    def supprimer_produit(self):
        """Supprimer le produit sélectionné"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un produit")
            return
        
        reponse = messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce produit?")
        if reponse:
            item = self.tree.item(selection[0])
            id_produit = item['values'][0]
            
            if Produit.supprimer(id_produit):
                messagebox.showinfo("Succès", "✅ Produit supprimé")
                self.vider_formulaire()
                self.charger_produits()
    
    def voir_code_barre(self, event=None):
        """Afficher le code-barres du produit sélectionné"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            code_barre = item['values'][6]
            CodeBarre.imprimer_code_barre(CodeBarre.obtenir_chemin_image(code_barre))
    
    def vider_formulaire(self):
        """Vider tous les champs du formulaire"""
        self.entry_nom.delete(0, 'end')
        self.entry_categorie.delete(0, 'end')
        self.entry_description.delete("1.0", "end")
        self.entry_prix_achat.delete(0, 'end')
        self.entry_prix_vente.delete(0, 'end')
        self.entry_stock.delete(0, 'end')
        self.entry_stock_alerte.delete(0, 'end')
        self.entry_stock_alerte.insert(0, "5")
        self.entry_code_barre.config(state='normal')
        self.entry_code_barre.delete(0, 'end')
        if self.mode_code_barre.get() == "auto":
            self.entry_code_barre.config(state='disabled')