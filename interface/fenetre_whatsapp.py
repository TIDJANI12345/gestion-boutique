"""
Fenêtre Export WhatsApp - Design moderne
"""
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from modules.whatsapp import WhatsAppExport
from modules.produits import Produit
from config import *

# Pyperclip optionnel
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

class FenetreWhatsApp:
    def __init__(self, parent):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Export WhatsApp")
        self.fenetre.geometry("1200x750")
        self.fenetre.configure(bg=COLORS['bg'])
        
        self.categories_vars = {}
        
        self.creer_interface()
        self.charger_categories()
        self.generer_apercu()
    
    def creer_interface(self):
        """Créer l'interface moderne"""
        
        # En-tête
        header = tk.Frame(self.fenetre, bg=COLORS['warning'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        titre = tk.Label(
            header,
            text="📱 Export WhatsApp",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS['warning'],
            fg="white"
        )
        titre.pack(side='left', padx=30, pady=25)
        
        subtitle = tk.Label(
            header,
            text="Générez un message formaté pour vos revendeurs",
            font=("Segoe UI", 11),
            bg=COLORS['warning'],
            fg="white"
        )
        subtitle.pack(side='left', padx=(0, 30))
        
        # Container principal
        main = tk.Frame(self.fenetre, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Colonne gauche: Configuration
        left_col = tk.Frame(main, bg=COLORS['bg'])
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # === MESSAGE PRINCIPAL ===
        message_panel = tk.Frame(left_col, bg="white", relief='solid', bd=1)
        message_panel.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            message_panel,
            text="✏️ Message principal",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(anchor='w', padx=20, pady=(15, 10))
        
        tk.Frame(message_panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        message_inner = tk.Frame(message_panel, bg="white")
        message_inner.pack(fill='x', padx=20, pady=15)
        
        # Titre
        tk.Label(
            message_inner,
            text="Titre du message",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor='w', pady=(0, 5))
        
        self.entry_titre = tk.Entry(
            message_inner,
            font=("Segoe UI", 11),
            relief='solid',
            bd=1
        )
        self.entry_titre.pack(fill='x', ipady=8, pady=(0, 15))
        self.entry_titre.insert(0, "🛒 PRODUITS DISPONIBLES")
        self.entry_titre.bind('<KeyRelease>', lambda e: self.generer_apercu())
        
        # Message de fin
        tk.Label(
            message_inner,
            text="Message de fin (optionnel)",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor='w', pady=(0, 5))
        
        self.text_message_fin = tk.Text(
            message_inner,
            font=("Segoe UI", 10),
            relief='solid',
            bd=1,
            height=3
        )
        self.text_message_fin.pack(fill='x', pady=(0, 0))
        self.text_message_fin.bind('<KeyRelease>', lambda e: self.generer_apercu())
        
        # === OPTIONS ===
        options_panel = tk.Frame(left_col, bg="white", relief='solid', bd=1)
        options_panel.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            options_panel,
            text="🎨 Options de formatage",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(anchor='w', padx=20, pady=(15, 10))
        
        tk.Frame(options_panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        options_inner = tk.Frame(options_panel, bg="white")
        options_inner.pack(fill='x', padx=20, pady=15)
        
        # Checkboxes
        self.var_grouper = tk.BooleanVar(value=True)
        self.var_afficher_stock = tk.BooleanVar(value=True)
        self.var_stock_only = tk.BooleanVar(value=True)
        self.var_prix_achat = tk.BooleanVar(value=False)
        
        checks = [
            ("📂 Grouper par catégories", self.var_grouper),
            ("📊 Afficher les stocks", self.var_afficher_stock),
            ("✅ Produits en stock uniquement", self.var_stock_only),
            ("💵 Afficher prix d'achat", self.var_prix_achat)
        ]
        
        for text, var in checks:
            cb = tk.Checkbutton(
                options_inner,
                text=text,
                variable=var,
                font=("Segoe UI", 10),
                bg="white",
                command=self.generer_apercu
            )
            cb.pack(anchor='w', pady=5)
        
        # Style emoji
        tk.Label(
            options_inner,
            text="Style d'emojis",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor='w', pady=(15, 5))
        
        self.var_emoji_style = tk.StringVar(value="classic")
        
        styles_frame = tk.Frame(options_inner, bg="white")
        styles_frame.pack(fill='x')
        
        for value, label in [("classic", "🛒 Classique"), ("modern", "🔥 Moderne"), ("professional", "📋 Professionnel")]:
            tk.Radiobutton(
                styles_frame,
                text=label,
                variable=self.var_emoji_style,
                value=value,
                font=("Segoe UI", 9),
                bg="white",
                command=self.generer_apercu
            ).pack(side='left', padx=(0, 15))
        
        # === CATÉGORIES ===
        categories_panel = tk.Frame(left_col, bg="white", relief='solid', bd=1)
        categories_panel.pack(fill='both', expand=True)
        
        tk.Label(
            categories_panel,
            text="📂 Catégories à inclure",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(anchor='w', padx=20, pady=(15, 10))
        
        tk.Frame(categories_panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        # Scrollable frame pour catégories
        canvas = tk.Canvas(categories_panel, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(categories_panel, orient="vertical", command=canvas.yview)
        self.categories_frame = tk.Frame(canvas, bg="white")
        
        self.categories_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.categories_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side='left', fill='both', expand=True, padx=20, pady=15)
        scrollbar.pack(side='right', fill='y', pady=15)
        
        # Colonne droite: Aperçu
        right_col = tk.Frame(main, bg=COLORS['bg'], width=400)
        right_col.pack(side='left', fill='both', padx=(10, 0))
        right_col.pack_propagate(False)
        
        # === APERÇU ===
        apercu_panel = tk.Frame(right_col, bg="white", relief='solid', bd=1)
        apercu_panel.pack(fill='both', expand=True, pady=(0, 15))
        
        tk.Label(
            apercu_panel,
            text="👁️ Aperçu",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(anchor='w', padx=20, pady=(15, 10))
        
        tk.Frame(apercu_panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        # Zone d'aperçu
        self.text_apercu = scrolledtext.ScrolledText(
            apercu_panel,
            font=("Courier New", 9),
            bg=COLORS['light'],
            relief='flat',
            wrap='word',
            padx=10,
            pady=10
        )
        self.text_apercu.pack(fill='both', expand=True, padx=15, pady=15)
        
        # === ACTIONS ===
        actions_panel = tk.Frame(right_col, bg="white", relief='solid', bd=1)
        actions_panel.pack(fill='x')
        
        actions_inner = tk.Frame(actions_panel, bg="white")
        actions_inner.pack(fill='x', padx=20, pady=20)
        
        tk.Button(
            actions_inner,
            text="📋 Copier le message",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['success'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.copier_message
        ).pack(fill='x', ipady=15, pady=(0, 10))
        
        tk.Button(
            actions_inner,
            text="💾 Sauvegarder",
            font=("Segoe UI", 11),
            bg=COLORS['info'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.sauvegarder_export
        ).pack(fill='x', ipady=12)
    
    def charger_categories(self):
        """Charger les catégories avec checkboxes"""
        categories = Produit.obtenir_par_categorie()
        
        # Toutes les catégories
        var_toutes = tk.BooleanVar(value=True)
        self.categories_vars['_TOUTES_'] = var_toutes
        
        cb = tk.Checkbutton(
            self.categories_frame,
            text="✅ Toutes les catégories",
            variable=var_toutes,
            font=("Segoe UI", 10, "bold"),
            bg="white",
            command=self.toggle_toutes_categories
        )
        cb.pack(anchor='w', pady=(5, 10))
        
        # Ligne séparatrice
        tk.Frame(self.categories_frame, bg=COLORS['light'], height=1).pack(fill='x', pady=(0, 10))
        
        # Catégories individuelles
        for categorie, produits in sorted(categories.items()):
            var = tk.BooleanVar(value=True)
            self.categories_vars[categorie] = var
            
            cb = tk.Checkbutton(
                self.categories_frame,
                text=f"{categorie} ({len(produits)})",
                variable=var,
                font=("Segoe UI", 9),
                bg="white",
                command=self.generer_apercu
            )
            cb.pack(anchor='w', pady=3)
    
    def toggle_toutes_categories(self):
        """Activer/désactiver toutes les catégories"""
        etat = self.categories_vars['_TOUTES_'].get()
        for key, var in self.categories_vars.items():
            if key != '_TOUTES_':
                var.set(etat)
        self.generer_apercu()
    
    def generer_apercu(self):
        """Générer l'aperçu du message"""
        # Collecter les catégories sélectionnées
        categories_selectionnees = [
            cat for cat, var in self.categories_vars.items()
            if cat != '_TOUTES_' and var.get()
        ]
        
        # Options
        options = {
            'titre': self.entry_titre.get(),
            'message_fin': self.text_message_fin.get("1.0", "end").strip(),
            'grouper_categories': self.var_grouper.get(),
            'afficher_stock': self.var_afficher_stock.get(),
            'stock_min_only': self.var_stock_only.get(),
            'inclure_prix_achat': self.var_prix_achat.get(),
            'emoji_style': self.var_emoji_style.get(),
            'categories': categories_selectionnees if categories_selectionnees else None
        }
        
        # Générer le message
        message = WhatsAppExport.generer_message(options)
        
        # Afficher l'aperçu
        self.text_apercu.delete('1.0', 'end')
        self.text_apercu.insert('1.0', message)
    
    def copier_message(self):
        """Copier le message dans le presse-papiers"""
        message = self.text_apercu.get("1.0", "end").strip()
        
        if PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(message)
                messagebox.showinfo(
                    "Succès",
                    "✅ Message copié dans le presse-papiers!\n\n"
                    "Vous pouvez maintenant le coller dans WhatsApp."
                )
                return
            except:
                pass
        
        # Utiliser tkinter clipboard
        self.fenetre.clipboard_clear()
        self.fenetre.clipboard_append(message)
        self.fenetre.update()
        messagebox.showinfo(
            "Succès",
            "✅ Message copié!\n\n"
            "Collez-le dans WhatsApp (Ctrl+V)"
        )
    
    def sauvegarder_export(self):
        """Sauvegarder l'export dans un fichier"""
        message = self.text_apercu.get("1.0", "end").strip()
        
        filepath = WhatsAppExport.sauvegarder_export(message)
        
        if filepath:
            messagebox.showinfo(
                "Succès",
                f"✅ Export sauvegardé!\n\n{filepath}"
            )