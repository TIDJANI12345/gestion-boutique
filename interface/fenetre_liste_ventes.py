"""
Fenêtre Liste des Ventes - Voir l'historique complet
"""
import tkinter as tk
from tkinter import ttk, messagebox
from modules.ventes import Vente
from config import *
from datetime import datetime

class FenetreListeVentes:
    def __init__(self, parent):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Liste des Ventes")
        self.fenetre.geometry("1200x700")
        self.fenetre.configure(bg=COLORS['bg'])
        
        self.creer_interface()
        self.charger_ventes()
    
    def creer_interface(self):
        """Créer l'interface"""
        
        # En-tête
        header = tk.Frame(self.fenetre, bg=COLORS['success'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        titre = tk.Label(
            header,
            text="📜 Liste des Ventes",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS['success'],
            fg="white"
        )
        titre.pack(side='left', padx=30, pady=25)
        
        # Container principal
        main = tk.Frame(self.fenetre, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Barre de recherche et filtres
        top_frame = tk.Frame(main, bg="white", relief='solid', bd=1)
        top_frame.pack(fill='x', pady=(0, 15))
        
        top_inner = tk.Frame(top_frame, bg="white")
        top_inner.pack(fill='x', padx=20, pady=15)
        
        # Recherche
        tk.Label(
            top_inner,
            text="🔍 Rechercher:",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(side='left', padx=(0, 10))
        
        self.entry_recherche = tk.Entry(
            top_inner,
            font=("Segoe UI", 11),
            relief='solid',
            bd=1,
            width=30
        )
        self.entry_recherche.pack(side='left', ipady=8, padx=(0, 15))
        self.entry_recherche.bind('<KeyRelease>', lambda e: self.rechercher_ventes())
        
        # Boutons
        tk.Button(
            top_inner,
            text="🔄 Actualiser",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS['primary'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.charger_ventes,
            padx=15,
            pady=8
        ).pack(side='left', padx=5)
        
        tk.Button(
            top_inner,
            text="📊 Statistiques",
            font=("Segoe UI", 10, "bold"),
            bg=COLORS['info'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.afficher_stats,
            padx=15,
            pady=8
        ).pack(side='left', padx=5)
        
        # Statistiques rapides
        stats_frame = tk.Frame(top_frame, bg="white")
        stats_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        tk.Frame(top_frame, bg=COLORS['light'], height=1).pack(fill='x')
        
        stats_inner = tk.Frame(stats_frame, bg="white")
        stats_inner.pack(fill='x', pady=10)
        
        self.label_total_ventes = tk.Label(
            stats_inner,
            text="Total ventes: 0",
            font=("Segoe UI", 10),
            bg="white",
            fg=COLORS['gray']
        )
        self.label_total_ventes.pack(side='left', padx=(0, 30))
        
        self.label_ca_total = tk.Label(
            stats_inner,
            text="CA Total: 0 FCFA",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            fg=COLORS['success']
        )
        self.label_ca_total.pack(side='left')
        
        # Tableau des ventes
        table_frame = tk.Frame(main, bg="white", relief='solid', bd=1)
        table_frame.pack(fill='both', expand=True)
        
        # En-tête du tableau
        table_header = tk.Frame(table_frame, bg="white")
        table_header.pack(fill='x', padx=15, pady=(15, 10))
        
        tk.Label(
            table_header,
            text="📋 Historique des ventes",
            font=("Segoe UI", 13, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(side='left')
        
        tk.Frame(table_frame, bg=COLORS['light'], height=1).pack(fill='x')
        
        # TreeView
        tree_container = tk.Frame(table_frame, bg="white")
        tree_container.pack(fill='both', expand=True, padx=15, pady=15)
        
        # Scrollbars
        scrollbar_y = ttk.Scrollbar(tree_container)
        scrollbar_y.pack(side='right', fill='y')
        
        scrollbar_x = ttk.Scrollbar(tree_container, orient='horizontal')
        scrollbar_x.pack(side='bottom', fill='x')
        
        # Colonnes
        colonnes = ('ID', 'Numéro', 'Date', 'Heure', 'Client', 'Total', 'Articles')
        self.tree = ttk.Treeview(
            tree_container,
            columns=colonnes,
            show='headings',
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            height=20
        )
        
        scrollbar_y.config(command=self.tree.yview)
        scrollbar_x.config(command=self.tree.xview)
        
        # En-têtes
        self.tree.heading('ID', text='ID')
        self.tree.heading('Numéro', text='Numéro Vente')
        self.tree.heading('Date', text='Date')
        self.tree.heading('Heure', text='Heure')
        self.tree.heading('Client', text='Client')
        self.tree.heading('Total', text='Total (FCFA)')
        self.tree.heading('Articles', text='Nb Articles')
        
        # Largeurs
        self.tree.column('ID', width=50)
        self.tree.column('Numéro', width=200)
        self.tree.column('Date', width=120)
        self.tree.column('Heure', width=100)
        self.tree.column('Client', width=200)
        self.tree.column('Total', width=150)
        self.tree.column('Articles', width=100)
        
        self.tree.pack(fill='both', expand=True)
        
        # Double-clic pour voir détails
        self.tree.bind('<Double-1>', self.voir_details)
        
        # Menu contextuel
        self.menu_contextuel = tk.Menu(self.tree, tearoff=0)
        self.menu_contextuel.add_command(label="👁️ Voir détails", command=self.voir_details)
        self.menu_contextuel.add_command(label="🖨️ Réimprimer reçu", command=self.reimprimer_recu)
        self.menu_contextuel.add_separator()
        self.menu_contextuel.add_command(label="🗑️ Supprimer", command=self.supprimer_vente)
        
        self.tree.bind('<Button-3>', self.afficher_menu_contextuel)
    
    def charger_ventes(self):
        """Charger les ventes depuis la base de données avec tri et statistiques"""
        # 1. Nettoyer le tableau actuel
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 2. Récupérer les données (Triées par ID décroissant pour avoir les plus récentes)
        from database import db
        ventes = db.fetch_all("SELECT id, numero_vente, date_vente, total, client FROM ventes ORDER BY id DESC")
        
        # 3. Gérer le cas où il n'y a pas de ventes
        if not ventes:
            self.label_total_ventes.config(text="Total ventes: 0")
            self.label_ca_total.config(text="CA Total: 0 FCFA")
            return
        
        # 4. Initialiser les statistiques
        total_ca = 0
        
        # 5. Parcourir et afficher (Les données sont déjà dans le bon ordre grâce au SQL)
        for vente in ventes:
            vente_id = vente[0]
            numero = vente[1]
            date_vente = vente[2]
            total = vente[3]
            client = vente[4] if len(vente) > 4 and vente[4] else "—"
            
            total_ca += total
            
            # Formatage de la date et de l'heure
            try:
                dt = datetime.strptime(date_vente, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d/%m/%Y")
                heure_str = dt.strftime("%H:%M:%S")
            except:
                date_str = date_vente
                heure_str = ""
            
            # Récupérer le nombre d'articles pour cette vente
            details = Vente.obtenir_details_vente(vente_id)
            nb_articles = sum(d[2] for d in details) if details else 0
            
            # 6. Insertion unique dans le tableau visuel
            self.tree.insert('', 'end', values=(
                vente_id,
                numero,
                date_str,
                heure_str,
                client,
                f"{total:,.0f}",
                nb_articles
            ))
        
        # 7. Mettre à jour les labels de statistiques
        self.label_total_ventes.config(text=f"Total ventes: {len(ventes)}")
        self.label_ca_total.config(text=f"CA Total: {total_ca:,.0f} FCFA")
    
    def rechercher_ventes(self):
        """Rechercher des ventes"""
        terme = self.entry_recherche.get().strip().lower()
        
        # Vider le tableau
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Récupérer toutes les ventes
        ventes = Vente.obtenir_toutes_ventes()
        
        # Filtrer
        for vente in reversed(ventes):
            vente_id = vente[0]
            numero = vente[1].lower()
            date_vente = vente[2]
            total = vente[3]
            client = (vente[4] if len(vente) > 4 and vente[4] else "").lower()
            
            # Vérifier si correspond à la recherche
            if terme in numero or terme in client or terme in date_vente:
                try:
                    dt = datetime.strptime(date_vente, "%Y-%m-%d %H:%M:%S")
                    date_str = dt.strftime("%d/%m/%Y")
                    heure_str = dt.strftime("%H:%M:%S")
                except:
                    date_str = date_vente
                    heure_str = ""
                
                details = Vente.obtenir_details_vente(vente_id)
                nb_articles = sum(d[2] for d in details) if details else 0
                
                self.tree.insert('', 'end', values=(
                    vente_id,
                    vente[1],
                    date_str,
                    heure_str,
                    vente[4] if len(vente) > 4 and vente[4] else "—",
                    f"{total:,.0f}",
                    nb_articles
                ))
    
    def voir_details(self, event=None):
        """Voir les détails d'une vente"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        vente_id = item['values'][0]
        numero = item['values'][1]
        
        # Créer une fenêtre de détails
        details_win = tk.Toplevel(self.fenetre)
        details_win.title(f"Détails - {numero}")
        details_win.geometry("600x500")
        details_win.configure(bg="white")
        
        # En-tête
        tk.Label(
            details_win,
            text=f"📋 {numero}",
            font=("Segoe UI", 16, "bold"),
            bg="white"
        ).pack(pady=20)
        
        # Infos vente
        info_frame = tk.Frame(details_win, bg="white")
        info_frame.pack(fill='x', padx=30, pady=(0, 20))
        
        tk.Label(info_frame, text=f"Date: {item['values'][2]}", font=("Segoe UI", 10), bg="white").pack(anchor='w')
        tk.Label(info_frame, text=f"Heure: {item['values'][3]}", font=("Segoe UI", 10), bg="white").pack(anchor='w')
        tk.Label(info_frame, text=f"Client: {item['values'][4]}", font=("Segoe UI", 10), bg="white").pack(anchor='w')
        
        tk.Frame(details_win, bg=COLORS['light'], height=1).pack(fill='x', padx=30, pady=15)
        
        # Détails produits
        tk.Label(
            details_win,
            text="Produits vendus:",
            font=("Segoe UI", 12, "bold"),
            bg="white"
        ).pack(anchor='w', padx=30, pady=(0, 10))
        
        # Tableau détails
        tree_frame = tk.Frame(details_win, bg="white")
        tree_frame.pack(fill='both', expand=True, padx=30, pady=(0, 20))
        
        cols = ('Produit', 'Qté', 'P.U.', 'Total')
        tree_details = ttk.Treeview(tree_frame, columns=cols, show='headings', height=10)
        
        for col in cols:
            tree_details.heading(col, text=col)
        
        tree_details.column('Produit', width=250)
        tree_details.column('Qté', width=80)
        tree_details.column('P.U.', width=100)
        tree_details.column('Total', width=120)
        
        # Charger les détails
        details = Vente.obtenir_details_vente(vente_id)
        for detail in details:
            tree_details.insert('', 'end', values=(
                detail[1],
                detail[2],
                f"{detail[3]:,.0f} F",
                f"{detail[4]:,.0f} F"
            ))
        
        tree_details.pack(fill='both', expand=True)
        
        # Total
        tk.Label(
            details_win,
            text=f"TOTAL: {item['values'][5]} FCFA",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['success']
        ).pack(pady=20)
    
    def afficher_menu_contextuel(self, event):
        """Afficher le menu contextuel"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu_contextuel.post(event.x_root, event.y_root)
    
    def reimprimer_recu(self):
        """Réimprimer le reçu d'une vente"""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        vente_id = item['values'][0]
        
        from modules.recus import generer_recu_pdf
        chemin = generer_recu_pdf(vente_id)
        
        if chemin:
            messagebox.showinfo("Succès", f"✅ Reçu régénéré!\n\n{chemin}")
            import os
            os.startfile(chemin)
    
    def supprimer_vente(self):
        """Supprimer une vente"""
        selection = self.tree.selection()
        if not selection:
            return
        
    # def supprimer_vente(self):
    #     if self.parent.utilisateur['role'] != 'patron':
    #         messagebox.showerror("Interdit", "Seul le patron peut supprimer une vente.")
    #         return
        
        item = self.tree.item(selection[0])
        numero = item['values'][1]
        
        reponse = messagebox.askyesno(
            "Confirmation",
            f"⚠️ Supprimer la vente {numero}?\n\nCette action est irréversible!"
        )
        
        if reponse:
            vente_id = item['values'][0]
            if Vente.annuler_vente(vente_id):
                messagebox.showinfo("Succès", "✅ Vente supprimée")
                self.charger_ventes()
            else:
                messagebox.showerror("Erreur", "❌ Impossible de supprimer")
    
    def afficher_stats(self):
        """Afficher des statistiques détaillées"""
        messagebox.showinfo("Statistiques", "Fonctionnalité en cours de développement...")