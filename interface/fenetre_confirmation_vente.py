"""
Fenêtre de confirmation de vente - Version moderne et épurée
"""
import tkinter as tk
from tkinter import messagebox
from config import *
import os

class FenetreConfirmationVente:
    def __init__(self, parent, vente_info, chemin_recu, callback=None):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Vente enregistrée !")
        self.fenetre.geometry("600x700")
        self.fenetre.configure(bg="white")
        self.fenetre.transient(parent)
        self.fenetre.resizable(False, False)
        
        self.vente_info = vente_info
        self.chemin_recu = chemin_recu
        self.callback = callback
        
        self.creer_interface()
        
        # Centrer
        self.fenetre.update_idletasks()
        x = (self.fenetre.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.fenetre.winfo_screenheight() // 2) - (700 // 2)
        self.fenetre.geometry(f"600x700+{x}+{y}")
        
        # Ouvrir automatiquement le PDF
        # self.fenetre.after(500, self.ouvrir_pdf)
    
    def creer_interface(self):
        """Créer l'interface moderne et épurée"""
        
        # ==========================================
        # EN-TÊTE VERT AVEC CHECKMARK
        # ==========================================
        
        header = tk.Frame(self.fenetre, bg=COLORS['success'], height=180)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        # Cercle blanc avec checkmark
        circle = tk.Frame(header, bg="white", width=80, height=80)
        circle.pack(pady=(35, 15))
        circle.pack_propagate(False)
        
        # Créer un canvas pour dessiner un cercle
        canvas = tk.Canvas(circle, width=80, height=80, bg="white", highlightthickness=0)
        canvas.pack()
        canvas.create_oval(5, 5, 75, 75, fill=COLORS['success'], outline="")
        canvas.create_text(40, 40, text="✓", font=("Segoe UI", 35, "bold"), fill="white")
        
        tk.Label(
            header,
            text="Vente enregistrée !",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS['success'],
            fg="white"
        ).pack(pady=(0, 5))
        
        tk.Label(
            header,
            text=f"Reçu N° {self.vente_info['numero']}",
            font=("Segoe UI", 13),
            bg=COLORS['success'],
            fg="white"
        ).pack()
        
        # ==========================================
        # CONTENU
        # ==========================================
        
        content = tk.Frame(self.fenetre, bg="white")
        content.pack(fill='both', expand=True, padx=40, pady=30)
        
        # Date et Total dans un cadre
        info_frame = tk.Frame(content, bg=COLORS['light'], relief='flat')
        info_frame.pack(fill='x', pady=(0, 25))
        
        info_inner = tk.Frame(info_frame, bg=COLORS['light'])
        info_inner.pack(padx=20, pady=20)
        
        # Date
        tk.Label(
            info_inner,
            text="📅 " + self.vente_info['date'],
            font=("Segoe UI", 11),
            bg=COLORS['light'],
            fg=COLORS['dark']
        ).pack(pady=(0, 10))
        
        # Total (gros et visible)
        tk.Label(
            info_inner,
            text=f"{self.vente_info['total']:,.0f} FCFA",
            font=("Segoe UI", 32, "bold"),
            bg=COLORS['light'],
            fg=COLORS['success']
        ).pack()
        
        # Client si présent
        if self.vente_info.get('client'):
            tk.Label(
                info_inner,
                text=f"👤 {self.vente_info['client']}",
                font=("Segoe UI", 10),
                bg=COLORS['light'],
                fg=COLORS['gray']
            ).pack(pady=(10, 0))
        
        # Articles vendus (résumé simple)
        nb_articles = sum(item['quantite'] for item in self.vente_info['items'])
        nb_lignes = len(self.vente_info['items'])
        
        tk.Label(
            content,
            text=f"📦 {nb_articles} article{'s' if nb_articles > 1 else ''} ({nb_lignes} ligne{'s' if nb_lignes > 1 else ''})",
            font=("Segoe UI", 11),
            bg="white",
            fg=COLORS['gray']
        ).pack(pady=(0, 30))
        
        # ==========================================
        # BOUTONS D'ACTION (GROS ET CLAIRS)
        # ==========================================
        
        # Bouton OUVRIR PDF (principal)
        btn_pdf = tk.Button(
            content,
            text="📄  Ouvrir le reçu PDF",
            font=("Segoe UI", 14, "bold"),
            bg=COLORS['danger'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.ouvrir_pdf,
            activebackground=self.darken_color(COLORS['danger'])
        )
        btn_pdf.pack(fill='x', ipady=18, pady=(0, 12))
        
        # Effet hover
        btn_pdf.bind('<Enter>', lambda e: btn_pdf.config(bg=self.darken_color(COLORS['danger'])))
        btn_pdf.bind('<Leave>', lambda e: btn_pdf.config(bg=COLORS['danger']))
        
        # Bouton IMPRIMER PDF
        btn_print = tk.Button(
            content,
            text="🖨️  Imprimer PDF",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS['primary'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.imprimer,
            activebackground=self.darken_color(COLORS['primary'])
        )
        btn_print.pack(fill='x', ipady=16, pady=(0, 12))

        btn_print.bind('<Enter>', lambda e: btn_print.config(bg=self.darken_color(COLORS['primary'])))
        btn_print.bind('<Leave>', lambda e: btn_print.config(bg=COLORS['primary']))

        # Bouton IMPRIMER TICKET THERMIQUE
        btn_ticket = tk.Button(
            content,
            text="🧾  Imprimer ticket",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS['warning'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.imprimer_ticket,
            activebackground=self.darken_color(COLORS['warning'])
        )
        btn_ticket.pack(fill='x', ipady=16, pady=(0, 12))

        btn_ticket.bind('<Enter>', lambda e: btn_ticket.config(bg=self.darken_color(COLORS['warning'])))
        btn_ticket.bind('<Leave>', lambda e: btn_ticket.config(bg=COLORS['warning']))
        
        # Bouton NOUVELLE VENTE
        btn_new = tk.Button(
            content,
            text="➕  Nouvelle vente",
            font=("Segoe UI", 13, "bold"),
            bg=COLORS['success'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.nouvelle_vente,
            activebackground=self.darken_color(COLORS['success'])
        )
        btn_new.pack(fill='x', ipady=16, pady=(0, 20))
        
        btn_new.bind('<Enter>', lambda e: btn_new.config(bg=self.darken_color(COLORS['success'])))
        btn_new.bind('<Leave>', lambda e: btn_new.config(bg=COLORS['success']))
        
        # Lien retour dashboard
        link = tk.Label(
            content,
            text="← Retour au tableau de bord",
            font=("Segoe UI", 11, "underline"),
            bg="white",
            fg=COLORS['primary'],
            cursor='hand2'
        )
        link.pack()
        link.bind('<Button-1>', lambda e: self.fermer())
        
        # Afficher les détails en petit en bas
        self.toggle_details = tk.Label(
            content,
            text="▼ Voir les détails",
            font=("Segoe UI", 9),
            bg="white",
            fg=COLORS['gray'],
            cursor='hand2'
        )
        self.toggle_details.pack(pady=(15, 0))
        self.toggle_details.bind('<Button-1>', lambda e: self.afficher_details())
    
    def afficher_details(self):
        """Afficher une fenêtre popup avec les détails"""
        details_win = tk.Toplevel(self.fenetre)
        details_win.title("Détails de la vente")
        details_win.geometry("500x400")
        details_win.configure(bg="white")
        details_win.transient(self.fenetre)
        
        # En-tête
        tk.Label(
            details_win,
            text=f"Détails - {self.vente_info['numero']}",
            font=("Segoe UI", 14, "bold"),
            bg="white"
        ).pack(pady=20)
        
        # Scrollable frame
        canvas = tk.Canvas(details_win, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(details_win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Articles
        for item in self.vente_info['items']:
            item_frame = tk.Frame(scrollable_frame, bg=COLORS['light'], relief='flat')
            item_frame.pack(fill='x', padx=20, pady=5)
            
            inner = tk.Frame(item_frame, bg=COLORS['light'])
            inner.pack(fill='x', padx=15, pady=12)
            
            # Nom
            tk.Label(
                inner,
                text=item['nom'],
                font=("Segoe UI", 11, "bold"),
                bg=COLORS['light'],
                anchor='w'
            ).pack(fill='x')
            
            # Quantité et prix
            tk.Label(
                inner,
                text=f"{item['quantite']} × {item['prix_vente']:,.0f} F = {item['sous_total']:,.0f} F",
                font=("Segoe UI", 10),
                bg=COLORS['light'],
                fg=COLORS['gray'],
                anchor='w'
            ).pack(fill='x')
        
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Centrer
        details_win.update_idletasks()
        x = (details_win.winfo_screenwidth() // 2) - (500 // 2)
        y = (details_win.winfo_screenheight() // 2) - (400 // 2)
        details_win.geometry(f"500x400+{x}+{y}")
    
    def ouvrir_pdf(self):
        """Ouvrir le PDF"""
        if self.chemin_recu and os.path.exists(self.chemin_recu):
            try:
                os.startfile(self.chemin_recu)
            except:
                messagebox.showerror("Erreur", "Impossible d'ouvrir le PDF")
        else:
            messagebox.showerror("Erreur", "Fichier PDF introuvable")
    
    def imprimer(self):
        """Imprimer le reçu PDF"""
        self.ouvrir_pdf()
        messagebox.showinfo("Impression", "Le PDF s'est ouvert.\nUtilisez Ctrl+P pour imprimer.")

    def imprimer_ticket(self):
        """Imprimer sur imprimante thermique"""
        vente_id = self.vente_info.get('vente_id')
        if not vente_id:
            messagebox.showerror("Erreur", "ID de vente non disponible")
            return

        from modules.imprimante import ImprimanteThermique

        if not ImprimanteThermique.est_disponible():
            messagebox.showwarning(
                "Imprimante",
                "L'impression thermique n'est pas disponible.\n\n"
                "Verifiez que python-escpos est installe\n"
                "et que l'imprimante est configuree."
            )
            return

        succes, message = ImprimanteThermique.imprimer_recu(vente_id)
        if succes:
            messagebox.showinfo("Impression", "Ticket imprime avec succes!")
        else:
            messagebox.showerror("Erreur", f"Echec de l'impression:\n{message}")
    
    def nouvelle_vente(self):
        """Ouvrir une nouvelle vente"""
        self.fenetre.destroy()
        if self.callback:
            self.callback()
    
    def fermer(self):
        """Fermer la fenêtre"""
        self.fenetre.destroy()
    
    def darken_color(self, hex_color):
        """Assombrir une couleur pour effet hover"""
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        r = max(0, r - 20)
        g = max(0, g - 20)
        b = max(0, b - 20)
        return f'#{r:02x}{g:02x}{b:02x}'