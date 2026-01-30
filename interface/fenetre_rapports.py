"""
Fenêtre des rapports - Design moderne
"""
import tkinter as tk
from tkinter import ttk, messagebox
from modules.rapports import Rapport
from modules.produits import Produit
from config import *
from datetime import datetime
import pandas as pd
from tkinter import filedialog

class FenetreRapports:
    def __init__(self, parent):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Rapports et Statistiques")
        self.fenetre.geometry("1200x700")
        self.fenetre.configure(bg=COLORS['bg'])
        
        self.creer_interface()
        self.actualiser_tout()  # ✅ Charger TOUT au démarrage
    
    def creer_interface(self):
        """Créer l'interface moderne"""
        
        # En-tête
        header = tk.Frame(self.fenetre, bg=COLORS['info'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        titre = tk.Label(
            header,
            text="📊 Rapports et Statistiques",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS['info'],
            fg="white"
        )
        titre.pack(side='left', padx=30, pady=25)
        
        # Bouton actualiser dans l'en-tête
        tk.Button(
            header,
            text="🔄 Actualiser",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=COLORS['info'],
            relief='flat',
            cursor='hand2',
            command=self.actualiser_tout,
            padx=20,
            pady=10
        ).pack(side='right', padx=30)

        # Bouton Excel dans l'en-tête
        tk.Button(
            header,
            text="📊 Exporter Excel",
            font=("Segoe UI", 11, "bold"),
            bg="#107C41", # Vert Excel
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.exporter_excel,
            padx=20,
            pady=10
        ).pack(side='right', padx=5)
        
        # Container principal avec onglets
        main = tk.Frame(self.fenetre, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Notebook moderne
        style = ttk.Style()
        style.configure('Custom.TNotebook', background=COLORS['bg'])
        style.configure('Custom.TNotebook.Tab', font=('Segoe UI', 11, 'bold'))
        
        self.notebook = ttk.Notebook(main, style='Custom.TNotebook')
        self.notebook.pack(fill='both', expand=True)
        
        # Onglet 1: Vue d'ensemble
        tab_overview = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(tab_overview, text="📈 Vue d'ensemble")
        self.creer_onglet_overview(tab_overview)
        
        # Onglet 2: Top produits
        tab_produits = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(tab_produits, text="🏆 Top Produits")
        self.creer_onglet_produits(tab_produits)
        
        # Onglet 3: Stock
        tab_stock = tk.Frame(self.notebook, bg=COLORS['bg'])
        self.notebook.add(tab_stock, text="⚠️ Stock Faible")
        self.creer_onglet_stock(tab_stock)
    
    def creer_onglet_overview(self, parent):
        """Créer l'onglet vue d'ensemble"""
        
        # Grille de statistiques (2x3)
        stats_container = tk.Frame(parent, bg=COLORS['bg'])
        stats_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        for i in range(3):
            stats_container.columnconfigure(i, weight=1, uniform="stat")
        for i in range(2):
            stats_container.rowconfigure(i, weight=1)
        
        # Carte 1: Ventes du jour
        self.carte_ventes_jour = self.creer_carte_stat(
            stats_container,
            "🛒",
            "Ventes aujourd'hui",
            "0",
            COLORS['primary'],
            0, 0
        )
        
        # Carte 2: CA du jour
        self.carte_ca_jour = self.creer_carte_stat(
            stats_container,
            "💰",
            "CA aujourd'hui",
            "0 FCFA",
            COLORS['success'],
            0, 1
        )
        
        # Carte 3: Produits en alerte
        self.carte_alerte = self.creer_carte_stat(
            stats_container,
            "⚠️",
            "Produits en alerte",
            "0",
            COLORS['danger'],
            0, 2
        )
        
        # Carte 4: Total ventes
        self.carte_total_ventes = self.creer_carte_stat(
            stats_container,
            "📦",
            "Total ventes",
            "0",
            COLORS['info'],
            1, 0
        )
        
        # Carte 5: CA total
        self.carte_ca_total = self.creer_carte_stat(
            stats_container,
            "💎",
            "CA Total",
            "0 FCFA",
            COLORS['purple'],
            1, 1
        )
        
        # Carte 6: Valeur stock
        self.carte_valeur_stock = self.creer_carte_stat(
            stats_container,
            "📊",
            "Valeur du stock",
            "0 FCFA",
            COLORS['warning'],
            1, 2
        )
    
    def creer_carte_stat(self, parent, emoji, titre, valeur, couleur, row, col):
        """Créer une carte de statistique"""
        carte = tk.Frame(parent, bg="white", relief='solid', bd=1)
        carte.grid(row=row, column=col, sticky='nsew', padx=10, pady=10)
        
        inner = tk.Frame(carte, bg="white")
        inner.pack(fill='both', expand=True, padx=25, pady=25)
        
        # Top: emoji + valeur
        top_frame = tk.Frame(inner, bg="white")
        top_frame.pack(fill='x')
        
        # Emoji dans cercle coloré
        emoji_bg = tk.Frame(top_frame, bg=self.lighten_color(couleur), width=65, height=65)
        emoji_bg.pack(side='right')
        emoji_bg.pack_propagate(False)
        
        emoji_label = tk.Label(
            emoji_bg,
            text=emoji,
            font=("Segoe UI", 28),
            bg=self.lighten_color(couleur)
        )
        emoji_label.pack(expand=True)
        
        # Valeur et titre
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
            font=("Segoe UI", 22, "bold"),
            bg="white",
            fg=couleur,
            anchor='w'
        )
        valeur_label.pack(anchor='w', pady=(5, 0))
        
        return valeur_label
    
    def creer_onglet_produits(self, parent):
        """Créer l'onglet top produits"""
        
        # Panel
        panel = tk.Frame(parent, bg="white", relief='solid', bd=1)
        panel.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête
        header = tk.Frame(panel, bg="white")
        header.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(
            header,
            text="🏆 Produits les plus vendus",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(side='left')
        
        tk.Label(
            header,
            text="Top 20",
            font=("Segoe UI", 10),
            bg=COLORS['light'],
            fg=COLORS['gray'],
            padx=10,
            pady=5
        ).pack(side='right')
        
        tk.Frame(panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        # Tableau
        table_frame = tk.Frame(panel, bg="white")
        table_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        colonnes = ('Rang', 'Produit', 'Catégorie', 'Qté Vendue', 'CA Généré')
        self.tree_produits = ttk.Treeview(
            table_frame,
            columns=colonnes,
            show='headings',
            yscrollcommand=scrollbar.set,
            height=18
        )
        scrollbar.config(command=self.tree_produits.yview)
        
        self.tree_produits.heading('Rang', text='#')
        self.tree_produits.heading('Produit', text='Produit')
        self.tree_produits.heading('Catégorie', text='Catégorie')
        self.tree_produits.heading('Qté Vendue', text='Quantité')
        self.tree_produits.heading('CA Généré', text='CA Généré')
        
        self.tree_produits.column('Rang', width=50, anchor='center')
        self.tree_produits.column('Produit', width=350)
        self.tree_produits.column('Catégorie', width=150)
        self.tree_produits.column('Qté Vendue', width=120, anchor='center')
        self.tree_produits.column('CA Généré', width=150, anchor='e') 
        
        self.tree_produits.pack(fill='both', expand=True)
        
        self.charger_top_produits()
    
    def creer_onglet_stock(self, parent):
        """Créer l'onglet stock faible"""
        
        # Panel
        panel = tk.Frame(parent, bg="white", relief='solid', bd=1)
        panel.pack(fill='both', expand=True, padx=20, pady=20)
        
        # En-tête
        header = tk.Frame(panel, bg="white")
        header.pack(fill='x', padx=20, pady=(20, 10))
        
        tk.Label(
            header,
            text="⚠️ Produits en alerte de stock",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(side='left')
        
        self.label_nb_alertes = tk.Label(
            header,
            text="0 produits",
            font=("Segoe UI", 10),
            bg=COLORS['danger'],
            fg="white",
            padx=10,
            pady=5
        )
        self.label_nb_alertes.pack(side='right')
        
        tk.Frame(panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        # Info
        info_frame = tk.Frame(panel, bg=COLORS['light'])
        info_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(
            info_frame,
            text="💡 Ces produits ont un stock inférieur ou égal au seuil d'alerte",
            font=("Segoe UI", 9, "italic"),
            bg=COLORS['light'],
            fg=COLORS['gray']
        ).pack(padx=10, pady=8)
        
        # Tableau
        table_frame = tk.Frame(panel, bg="white")
        table_frame.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        colonnes = ('Produit', 'Catégorie', 'Stock', 'Seuil', 'Prix')
        self.tree_stock = ttk.Treeview(
            table_frame,
            columns=colonnes,
            show='headings',
            yscrollcommand=scrollbar.set,
            height=15
        )
        scrollbar.config(command=self.tree_stock.yview)
        
        self.tree_stock.heading('Produit', text='Produit')
        self.tree_stock.heading('Catégorie', text='Catégorie')
        self.tree_stock.heading('Stock', text='Stock Actuel')
        self.tree_stock.heading('Seuil', text='Seuil Alerte')
        self.tree_stock.heading('Prix', text='Prix Vente')
        
        self.tree_stock.column('Produit', width=300)
        self.tree_stock.column('Catégorie', width=150)
        self.tree_stock.column('Stock', width=120, anchor='center')
        self.tree_stock.column('Seuil', width=120, anchor='center')
        self.tree_stock.column('Prix', width=150, anchor='e')
        
        self.tree_stock.pack(fill='both', expand=True)
        
        self.charger_stock_faible()
    
    def afficher_stats_generales(self):
        """Afficher les statistiques générales"""
        try:
            stats = Rapport.statistiques_generales()
            
            # Mettre à jour les cartes
            self.carte_ventes_jour['text'] = str(stats['nb_ventes'])
            self.carte_ca_jour['text'] = f"{stats['ca_jour']:,.0f} F"
            
            # Stock faible
            produits_alerte = Produit.obtenir_stock_faible()
            self.carte_alerte['text'] = str(len(produits_alerte))
            
            # Total ventes
            from modules.ventes import Vente
            toutes_ventes = Vente.obtenir_toutes_ventes()
            self.carte_total_ventes['text'] = str(len(toutes_ventes))
            
            # CA total
            ca_total = sum(v[3] for v in toutes_ventes) if toutes_ventes else 0
            self.carte_ca_total['text'] = f"{ca_total:,.0f} F"
            
            # Valeur stock
            self.carte_valeur_stock['text'] = f"{stats['valeur_stock']:,.0f} F"
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'afficher les stats:\n{e}")
    
    def charger_top_produits(self):
        """Charger les top produits"""
        # Vider
        for item in self.tree_produits.get_children():
            self.tree_produits.delete(item)
        
        # Charger
        produits = Rapport.top_produits(limite=20)
        
        if not produits:
            self.tree_produits.insert('', 'end', values=(
                "—", "Aucune vente enregistrée", "—", "—", "—"
            ))
            return
        
        rang = 1
        for produit in produits:
            self.tree_produits.insert('', 'end', values=(
                f"#{rang}",
                produit[0],  # Nom
                produit[1] or "Sans catégorie",
                int(produit[2]),  # Quantité
                f"{produit[3]:,.0f} F"  # CA
            ))
            rang += 1
    
    def charger_stock_faible(self):
        """Charger les produits en alerte"""
        # Vider
        for item in self.tree_stock.get_children():
            self.tree_stock.delete(item)
        
        # Charger
        produits = Produit.obtenir_stock_faible()
        
        self.label_nb_alertes['text'] = f"{len(produits)} produit{'s' if len(produits) > 1 else ''}"
        
        if not produits:
            self.tree_stock.insert('', 'end', values=(
                "✅ Tous les stocks sont OK", "—", "—", "—", "—"
            ))
            return
        
        for produit in produits:
            # produit = (id, nom, categorie, prix_achat, prix_vente, stock_actuel, stock_alerte, ...)
            self.tree_stock.insert('', 'end', values=(
                produit[1],  # Nom
                produit[2] or "Sans catégorie",  # Catégorie
                produit[5],  # Stock actuel
                produit[6],  # Seuil alerte
                f"{produit[4]:,.0f} F"  # Prix vente
            ))
    
    def actualiser_tout(self):
        """Actualiser tous les onglets"""
        self.afficher_stats_generales()
        self.charger_top_produits()
        self.charger_stock_faible()

    def lighten_color(self, hex_color):
        """Éclaircir une couleur"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = min(255, r + 40)
        g = min(255, g + 40)
        b = min(255, b + 40)
        return f'#{r:02x}{g:02x}{b:02x}'
        
    def exporter_excel(self):
        """Exporter les données vers Excel"""
        try:
            # Demander où enregistrer
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"Rapport_Boutique_{timestamp}.xlsx"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                initialfile=filename,
                filetypes=[("Fichier Excel", "*.xlsx")]
            )
            
            if not filepath:
                return # Annulé par l'utilisateur

            # 1. Récupérer les données du Top Produits
            data_produits = []
            for item in self.tree_produits.get_children():
                vals = self.tree_produits.item(item)['values']
                # Nettoyage des données (enlever les 'F', '#', etc.)
                data_produits.append({
                    'Rang': vals[0],
                    'Produit': vals[1],
                    'Catégorie': vals[2],
                    'Quantité': vals[3],
                    'CA Généré': str(vals[4]).replace(' F', '').replace(',', '').strip()
                })
            
            # 2. Récupérer les données du Stock Faible
            data_stock = []
            for item in self.tree_stock.get_children():
                vals = self.tree_stock.item(item)['values']
                if "Tous les stocks sont OK" in str(vals[0]): continue
                
                data_stock.append({
                    'Produit': vals[0],
                    'Catégorie': vals[1],
                    'Stock Actuel': vals[2],
                    'Seuil Alerte': vals[3],
                    'Prix Vente': str(vals[4]).replace(' F', '').replace(',', '').strip()
                })

            # 3. Création du fichier Excel avec Pandas
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Feuille Top Produits
                if data_produits:
                    df_prod = pd.DataFrame(data_produits)
                    df_prod.to_excel(writer, sheet_name='Top Produits', index=False)
                
                # Feuille Stock Faible
                if data_stock:
                    df_stock = pd.DataFrame(data_stock)
                    df_stock.to_excel(writer, sheet_name='Alerte Stock', index=False)
                else:
                    # Créer une feuille vide ou avec message si tout va bien
                    pd.DataFrame({'Message': ['Tout est OK']}).to_excel(writer, sheet_name='Alerte Stock', index=False)

            messagebox.showinfo("Succès", f"Export Excel réussi !\n\nFichier : {filepath}")

        except ImportError:
            messagebox.showerror(
                "Erreur", 
                "Le module 'pandas' est manquant.\nInstallez-le avec : pip install pandas openpyxl"
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'export :\n{e}")