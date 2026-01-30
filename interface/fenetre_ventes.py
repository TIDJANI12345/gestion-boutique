"""
Fenêtre de ventes - VERSION MÉMOIRE
Aucune donnée en BD tant que la vente n'est pas validée
"""
import tkinter as tk
from tkinter import ttk, messagebox
from modules.produits import Produit
from config import *
from datetime import datetime
import random
import string

class FenetreVentes:
    def __init__(self, parent, callback=None):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Nouvelle Vente")
        self.fenetre.geometry("1200x700")
        self.fenetre.configure(bg=COLORS['bg'])
        
        self.callback = callback
        
        # ==========================================
        # PANIER EN MÉMOIRE (pas de BD)
        # ==========================================
        self.panier = []  # Liste de dict: {'produit_id', 'nom', 'prix', 'quantite', 'sous_total'}
        
        self.creer_interface()
        self.actualiser_panier()
        
        # Focus sur le scanner
        self.entry_scan.focus()
        
        # Gérer la fermeture
        self.fenetre.protocol("WM_DELETE_WINDOW", self.fermer_fenetre)
    
    def creer_interface(self):
        """Créer l'interface moderne"""
        
        # En-tête
        header = tk.Frame(self.fenetre, bg=COLORS['success'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        titre = tk.Label(
            header,
            text="💰 Nouvelle Vente",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS['success'],
            fg="white"
        )
        titre.pack(side='left', padx=30, pady=25)
        
        # Info : pas encore en BD
        self.label_numero = tk.Label(
            header,
            text="🛒 Panier en cours...",
            font=("Segoe UI", 14),
            bg=COLORS['success'],
            fg="white"
        )
        self.label_numero.pack(side='right', padx=30)
        
        # Container principal
        main = tk.Frame(self.fenetre, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Colonne gauche: Scanner + Panier
        left_col = tk.Frame(main, bg=COLORS['bg'])
        left_col.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # === SCANNER ===
        scanner_panel = tk.Frame(left_col, bg="white", relief='solid', bd=1)
        scanner_panel.pack(fill='x', pady=(0, 15))
        
        scanner_inner = tk.Frame(scanner_panel, bg="white")
        scanner_inner.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            scanner_inner,
            text="🔍 Scanner un code-barre",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(anchor='w', pady=(0, 10))
        
        scan_frame = tk.Frame(scanner_inner, bg="white")
        scan_frame.pack(fill='x')
        
        self.entry_scan = tk.Entry(
            scan_frame,
            font=("Segoe UI", 14),
            relief='solid',
            bd=2,
            borderwidth=2
        )
        self.entry_scan.pack(side='left', fill='x', expand=True, ipady=12)
        self.entry_scan.bind('<Return>', self.scanner_produit)
        
        # Indication visuelle
        tk.Label(
            scanner_inner,
            text="💡 Scannez ou tapez le code-barres puis appuyez sur ENTRÉE",
            font=("Segoe UI", 9, "italic"),
            bg="white",
            fg=COLORS['gray']
        ).pack(anchor='w', pady=(8, 0))
        
        # === PANIER ===
        panier_panel = tk.Frame(left_col, bg="white", relief='solid', bd=1)
        panier_panel.pack(fill='both', expand=True)
        
        # En-tête panier
        panier_header = tk.Frame(panier_panel, bg="white")
        panier_header.pack(fill='x', padx=20, pady=15)
        
        tk.Label(
            panier_header,
            text="🛒 Panier",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(side='left')
        
        tk.Button(
            panier_header,
            text="🗑️ Vider",
            font=("Segoe UI", 9, "bold"),
            bg=COLORS['danger'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.vider_panier,
            padx=12,
            pady=5
        ).pack(side='right')
        
        # Séparateur
        tk.Frame(panier_panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        # Tableau panier
        table_frame = tk.Frame(panier_panel, bg="white")
        table_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side='right', fill='y')
        
        colonnes = ('Produit', 'Prix Unit.', 'Qté', 'Sous-total', 'Action')
        self.tree_panier = ttk.Treeview(
            table_frame,
            columns=colonnes,
            show='headings',
            yscrollcommand=scrollbar.set,
            height=10
        )
        scrollbar.config(command=self.tree_panier.yview)
        
        self.tree_panier.heading('Produit', text='Produit')
        self.tree_panier.heading('Prix Unit.', text='Prix Unit.')
        self.tree_panier.heading('Qté', text='Qté')
        self.tree_panier.heading('Sous-total', text='Sous-total')
        self.tree_panier.heading('Action', text='')
        
        self.tree_panier.column('Produit', width=250)
        self.tree_panier.column('Prix Unit.', width=100)
        self.tree_panier.column('Qté', width=70)
        self.tree_panier.column('Sous-total', width=120)
        self.tree_panier.column('Action', width=80)
        
        self.tree_panier.pack(fill='both', expand=True)
        self.tree_panier.bind('<Double-1>', self.retirer_ligne)
        
        # Message vide
        self.label_panier_vide = tk.Label(
            table_frame,
            text="Le panier est vide\n\n🔍 Scannez un produit pour commencer",
            font=("Segoe UI", 11),
            bg="white",
            fg=COLORS['gray']
        )
        
        # Colonne droite: Résumé + Actions
        right_col = tk.Frame(main, bg=COLORS['bg'], width=350)
        right_col.pack(side='left', fill='both', padx=(10, 0))
        right_col.pack_propagate(False)
        
        # === RÉSUMÉ ===
        resume_panel = tk.Frame(right_col, bg="white", relief='solid', bd=1)
        resume_panel.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            resume_panel,
            text="📊 Résumé",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(anchor='w', padx=20, pady=(15, 10))
        
        tk.Frame(resume_panel, bg=COLORS['light'], height=1).pack(fill='x')
        
        # Stats
        stats_frame = tk.Frame(resume_panel, bg="white")
        stats_frame.pack(fill='x', padx=20, pady=20)
        
        # Articles
        articles_frame = tk.Frame(stats_frame, bg="white")
        articles_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            articles_frame,
            text="Articles:",
            font=("Segoe UI", 11),
            bg="white",
            fg=COLORS['gray']
        ).pack(side='left')
        
        self.label_nb_articles = tk.Label(
            articles_frame,
            text="0",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg=COLORS['dark']
        )
        self.label_nb_articles.pack(side='right')
        
        # Total
        tk.Frame(stats_frame, bg=COLORS['light'], height=1).pack(fill='x', pady=(0, 15))
        
        total_frame = tk.Frame(stats_frame, bg="white")
        total_frame.pack(fill='x')
        
        tk.Label(
            total_frame,
            text="TOTAL:",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['dark']
        ).pack(side='left')
        
        self.label_total = tk.Label(
            total_frame,
            text="0 FCFA",
            font=("Segoe UI", 20, "bold"),
            bg="white",
            fg=COLORS['success']
        )
        self.label_total.pack(side='right')
        
        # === ACTIONS ===
        actions_panel = tk.Frame(right_col, bg="white", relief='solid', bd=1)
        actions_panel.pack(fill='both', expand=True)
        
        actions_inner = tk.Frame(actions_panel, bg="white")
        actions_inner.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Bouton valider (gros)
        tk.Button(
            actions_inner,
            text="✅ Valider la vente",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS['success'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.valider_vente
        ).pack(fill='x', ipady=20, pady=(0, 10))
        
        # Client (optionnel)
        tk.Label(
            actions_inner,
            text="Client (optionnel)",
            font=("Segoe UI", 10, "bold"),
            bg="white",
            anchor='w'
        ).pack(fill='x', pady=(10, 5))
        
        self.entry_client = tk.Entry(
            actions_inner,
            font=("Segoe UI", 10),
            relief='solid',
            bd=1
        )
        self.entry_client.pack(fill='x', ipady=8, pady=(0, 15))
        
        # Autres actions
        tk.Button(
            actions_inner,
            text="❌ Annuler la vente",
            font=("Segoe UI", 11),
            bg=COLORS['danger'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.annuler_vente
        ).pack(fill='x', ipady=12)
        
        # Raccourcis clavier
        self.fenetre.bind('<F5>', lambda e: self.entry_scan.focus())
        self.fenetre.bind('<F2>', lambda e: self.valider_vente())
    
    def scanner_produit(self, event=None):
        """Scanner un produit et l'ajouter au panier MÉMOIRE"""
        code_barre = self.entry_scan.get().strip()
        
        if not code_barre:
            return
        
        # Rechercher le produit
        produit = Produit.obtenir_par_code_barre(code_barre)
        
        if not produit:
            messagebox.showerror("Erreur", f"❌ Produit introuvable!\nCode: {code_barre}")
            self.entry_scan.delete(0, 'end')
            return
        
        # Vérifier le stock
        if produit[5] <= 0:
            messagebox.showerror("Stock", "❌ Stock insuffisant!")
            self.entry_scan.delete(0, 'end')
            return
        
        # Demander la quantité
        qte_dialog = tk.Toplevel(self.fenetre)
        qte_dialog.title("Quantité")
        qte_dialog.geometry("350x200")
        qte_dialog.configure(bg="white")
        qte_dialog.transient(self.fenetre)
        qte_dialog.grab_set()
        
        # Centrer
        qte_dialog.update_idletasks()
        x = (qte_dialog.winfo_screenwidth() // 2) - (350 // 2)
        y = (qte_dialog.winfo_screenheight() // 2) - (200 // 2)
        qte_dialog.geometry(f"350x200+{x}+{y}")
        
        tk.Label(
            qte_dialog,
            text=f"📦 {produit[1]}",
            font=("Segoe UI", 13, "bold"),
            bg="white"
        ).pack(pady=(20, 5))
        
        tk.Label(
            qte_dialog,
            text=f"Stock disponible: {produit[5]}",
            font=("Segoe UI", 10),
            bg="white",
            fg=COLORS['gray']
        ).pack(pady=(0, 15))
        
        tk.Label(
            qte_dialog,
            text="Quantité:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack()
        
        entry_qte = tk.Entry(
            qte_dialog,
            font=("Segoe UI", 14),
            justify='center',
            relief='solid',
            bd=1
        )
        entry_qte.pack(ipady=8, padx=40, pady=10)
        entry_qte.insert(0, "1")
        entry_qte.select_range(0, 'end')
        entry_qte.focus()
        
        def ajouter():
            try:
                quantite = int(entry_qte.get())
                if quantite <= 0:
                    messagebox.showerror("Erreur", "Quantité invalide")
                    return
                
                if quantite > produit[5]:
                    messagebox.showerror("Stock", f"Stock insuffisant!\nDisponible: {produit[5]}")
                    return
                
                # ==========================================
                # AJOUTER AU PANIER MÉMOIRE (pas de BD)
                # ==========================================
                self.ajouter_au_panier(produit, quantite)
                
                qte_dialog.destroy()
                self.entry_scan.delete(0, 'end')
                self.entry_scan.focus()
                
                # Feedback visuel
                self.entry_scan.config(bg='#D1FAE5')
                self.fenetre.after(200, lambda: self.entry_scan.config(bg='white'))
            
            except ValueError:
                messagebox.showerror("Erreur", "Quantité invalide")
        
        tk.Button(
            qte_dialog,
            text="✅ Ajouter",
            font=("Segoe UI", 11, "bold"),
            bg=COLORS['success'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=ajouter
        ).pack(ipady=8, padx=40, pady=(10, 0), fill='x')
        
        entry_qte.bind('<Return>', lambda e: ajouter())
        qte_dialog.bind('<Escape>', lambda e: qte_dialog.destroy())
    
    def ajouter_au_panier(self, produit, quantite):
        """Ajouter un produit au panier MÉMOIRE"""
        produit_id = produit[0]
        nom = produit[1]
        prix_vente = produit[4]
        
        # Vérifier si le produit est déjà dans le panier
        for item in self.panier:
            if item['produit_id'] == produit_id:
                # Augmenter la quantité
                item['quantite'] += quantite
                item['sous_total'] = item['prix_vente'] * item['quantite']
                self.actualiser_panier()
                return
        
        # Ajouter nouveau produit
        self.panier.append({
            'produit_id': produit_id,
            'nom': nom,
            'prix_vente': prix_vente,
            'quantite': quantite,
            'sous_total': prix_vente * quantite
        })
        
        self.actualiser_panier()
    
    def actualiser_panier(self):
        """Actualiser l'affichage du panier"""
        # Vider le treeview
        for item in self.tree_panier.get_children():
            self.tree_panier.delete(item)
        
        # Si panier vide
        if not self.panier:
            self.label_panier_vide.place(relx=0.5, rely=0.4, anchor='center')
            self.label_nb_articles.config(text="0")
            self.label_total.config(text="0 FCFA")
            return
        
        self.label_panier_vide.place_forget()
        
        # Afficher les articles
        total_articles = 0
        total_prix = 0
        
        for idx, item in enumerate(self.panier):
            total_articles += item['quantite']
            total_prix += item['sous_total']
            
            self.tree_panier.insert('', 'end', values=(
                item['nom'],
                f"{item['prix_vente']:,.0f} F",
                item['quantite'],
                f"{item['sous_total']:,.0f} F",
                "🗑️"
            ), tags=(idx,))
        
        # Mettre à jour le résumé
        self.label_nb_articles.config(text=str(total_articles))
        self.label_total.config(text=f"{total_prix:,.0f} FCFA")
    
    def retirer_ligne(self, event=None):
        """Retirer une ligne du panier"""
        selection = self.tree_panier.selection()
        if not selection:
            return
        
        item = self.tree_panier.item(selection[0])
        idx = int(self.tree_panier.item(selection[0], 'tags')[0])
        
        reponse = messagebox.askyesno(
            "Confirmation",
            f"Retirer '{item['values'][0]}' du panier?"
        )
        
        if reponse:
            # Retirer du panier MÉMOIRE
            self.panier.pop(idx)
            self.actualiser_panier()
    
    def vider_panier(self):
        """Vider complètement le panier"""
        if not self.panier:
            return
        
        reponse = messagebox.askyesno("Confirmation", "Vider tout le panier?")
        if reponse:
            self.panier = []
            self.actualiser_panier()
    
    def valider_vente(self):
        """Valider la vente - MAINTENANT on écrit dans la BD"""
        if not self.panier:
            messagebox.showwarning("Attention", "Le panier est vide!")
            return
        
        client = self.entry_client.get().strip()
        
        try:
            # ==========================================
            # CRÉER LA VENTE DANS LA BD
            # ==========================================
            from modules.ventes import Vente
            from database import db
            
            # Générer le numéro de vente
            date_str = datetime.now().strftime("%Y%m%d")
            random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            numero_vente = f"V{date_str}-{random_str}"
            
            # Calculer le total
            total = sum(item['sous_total'] for item in self.panier)
            
            # Insérer la vente
            query_vente = """
                INSERT INTO ventes (numero_vente, date_vente, total, client)
                VALUES (?, ?, ?, ?)
            """
            vente_id = db.execute_query(
                query_vente,
                (numero_vente, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), total, client or None)
            )
            
            # Insérer les détails
            query_detail = """
                INSERT INTO details_ventes (vente_id, produit_id, quantite, prix_unitaire, sous_total)
                VALUES (?, ?, ?, ?, ?)
            """
            
            for item in self.panier:
                db.execute_query(
                    query_detail,
                    (vente_id, item['produit_id'], item['quantite'], item['prix_vente'], item['sous_total'])
                )
                
                # Déduire du stock
                db.execute_query(
                    "UPDATE produits SET stock_actuel = stock_actuel - ? WHERE id = ?",
                    (item['quantite'], item['produit_id'])
                )
            
            # ==========================================
            # GÉNÉRER LE REÇU PDF
            # ==========================================
            from modules.recus import generer_recu_pdf
            chemin_recu = generer_recu_pdf(vente_id)
            
            # Préparer les infos pour la confirmation
            vente_info = {
                'numero': numero_vente,
                'date': datetime.now().strftime("%d/%m/%Y à %H:%M"),
                'total': total,
                'client': client,
                'items': self.panier.copy()
            }
            
            # Fermer cette fenêtre
            self.fenetre.destroy()
            
            # Afficher la confirmation
            from interface.fenetre_confirmation_vente import FenetreConfirmationVente
            FenetreConfirmationVente(self.fenetre.master, vente_info, chemin_recu, callback=self.callback)
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de valider la vente:\n{e}")
            import traceback
            traceback.print_exc()
    
    def annuler_vente(self):
        """Annuler la vente - Juste fermer (rien en BD)"""
        if not self.panier:
            self.fenetre.destroy()
            return
        
        reponse = messagebox.askyesno("Confirmation", "Annuler cette vente?")
        if reponse:
            self.fenetre.destroy()
    
    def fermer_fenetre(self):
        """Fermer la fenêtre - Rien à supprimer en BD"""
        if self.panier:
            reponse = messagebox.askyesno(
                "Confirmation",
                "Des articles sont dans le panier.\nVoulez-vous vraiment fermer?"
            )
            if not reponse:
                return
        
        self.fenetre.destroy()