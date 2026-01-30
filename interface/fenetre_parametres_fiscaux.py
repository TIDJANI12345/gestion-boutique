"""
Fenetre de configuration des parametres fiscaux (TVA et devises)
"""
import tkinter as tk
from tkinter import ttk, messagebox
from config import COLORS
from database import db
from modules.fiscalite import Fiscalite


class FenetreParametresFiscaux:
    def __init__(self, parent):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Parametres fiscaux")
        self.fenetre.geometry("700x650")
        self.fenetre.configure(bg="white")
        self.fenetre.transient(parent)
        self.fenetre.resizable(False, False)

        # Centrer
        self.fenetre.update_idletasks()
        x = (self.fenetre.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.fenetre.winfo_screenheight() // 2) - (650 // 2)
        self.fenetre.geometry(f"700x650+{x}+{y}")

        self.creer_interface()

    def creer_interface(self):
        # En-tete
        header = tk.Frame(self.fenetre, bg=COLORS['info'], height=70)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header, text="Parametres fiscaux",
            font=("Segoe UI", 18, "bold"), bg=COLORS['info'], fg="white"
        ).pack(side='left', padx=30, pady=20)

        content = tk.Frame(self.fenetre, bg="white")
        content.pack(fill='both', expand=True, padx=30, pady=20)

        # === SECTION TVA ===
        tk.Label(
            content, text="TVA", font=("Segoe UI", 14, "bold"),
            bg="white", fg=COLORS['dark']
        ).pack(anchor='w', pady=(0, 10))

        tva_frame = tk.Frame(content, bg=COLORS['light'], relief='flat')
        tva_frame.pack(fill='x', pady=(0, 15))

        inner = tk.Frame(tva_frame, bg=COLORS['light'])
        inner.pack(fill='x', padx=20, pady=15)

        # TVA active
        self.tva_active_var = tk.BooleanVar(value=Fiscalite.tva_active())
        tk.Checkbutton(
            inner, text="Activer la TVA sur les recus",
            variable=self.tva_active_var,
            font=("Segoe UI", 11), bg=COLORS['light'], activebackground=COLORS['light']
        ).pack(anchor='w', pady=(0, 10))

        # Taux par defaut
        taux_frame = tk.Frame(inner, bg=COLORS['light'])
        taux_frame.pack(fill='x')

        tk.Label(
            taux_frame, text="Taux TVA par defaut (%):",
            font=("Segoe UI", 11), bg=COLORS['light']
        ).pack(side='left')

        self.entry_taux = tk.Entry(
            taux_frame, font=("Segoe UI", 12), width=8, relief='solid', bd=1, justify='center'
        )
        self.entry_taux.pack(side='left', padx=10, ipady=4)
        self.entry_taux.insert(0, str(Fiscalite.taux_tva_defaut()))

        tk.Frame(content, bg=COLORS['light'], height=1).pack(fill='x', pady=10)

        # === SECTION DEVISE ===
        tk.Label(
            content, text="Devise", font=("Segoe UI", 14, "bold"),
            bg="white", fg=COLORS['dark']
        ).pack(anchor='w', pady=(0, 10))

        devise_frame = tk.Frame(content, bg=COLORS['light'], relief='flat')
        devise_frame.pack(fill='x', pady=(0, 15))

        devise_inner = tk.Frame(devise_frame, bg=COLORS['light'])
        devise_inner.pack(fill='x', padx=20, pady=15)

        # Devise principale
        row1 = tk.Frame(devise_inner, bg=COLORS['light'])
        row1.pack(fill='x', pady=(0, 8))

        tk.Label(
            row1, text="Code devise:", font=("Segoe UI", 11), bg=COLORS['light']
        ).pack(side='left')

        self.entry_devise_code = tk.Entry(
            row1, font=("Segoe UI", 12), width=8, relief='solid', bd=1, justify='center'
        )
        self.entry_devise_code.pack(side='left', padx=10, ipady=4)
        self.entry_devise_code.insert(0, db.get_parametre('devise_principale', 'XOF'))

        tk.Label(
            row1, text="Symbole:", font=("Segoe UI", 11), bg=COLORS['light']
        ).pack(side='left', padx=(20, 0))

        self.entry_devise_symbole = tk.Entry(
            row1, font=("Segoe UI", 12), width=8, relief='solid', bd=1, justify='center'
        )
        self.entry_devise_symbole.pack(side='left', padx=10, ipady=4)
        self.entry_devise_symbole.insert(0, db.get_parametre('devise_symbole', 'FCFA'))

        # Tableau des devises
        tk.Frame(content, bg=COLORS['light'], height=1).pack(fill='x', pady=10)

        tk.Label(
            content, text="Taux de change", font=("Segoe UI", 14, "bold"),
            bg="white", fg=COLORS['dark']
        ).pack(anchor='w', pady=(0, 10))

        tree_frame = tk.Frame(content, bg="white")
        tree_frame.pack(fill='both', expand=True)

        colonnes = ('Code', 'Symbole', 'Taux (par rapport XOF)', 'Actif')
        self.tree_devises = ttk.Treeview(
            tree_frame, columns=colonnes, show='headings', height=5
        )
        for col in colonnes:
            self.tree_devises.heading(col, text=col)
            self.tree_devises.column(col, width=120)
        self.tree_devises.pack(fill='both', expand=True)

        self._charger_devises()

        # Boutons
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill='x', pady=(15, 0))

        tk.Button(
            btn_frame, text="Enregistrer",
            font=("Segoe UI", 12, "bold"), bg=COLORS['success'], fg="white",
            relief='flat', cursor='hand2', command=self.enregistrer
        ).pack(side='right', ipady=10, ipadx=20)

        tk.Button(
            btn_frame, text="Fermer",
            font=("Segoe UI", 12), bg=COLORS['gray'], fg="white",
            relief='flat', cursor='hand2', command=self.fenetre.destroy
        ).pack(side='right', ipady=10, ipadx=20, padx=(0, 10))

    def _charger_devises(self):
        for item in self.tree_devises.get_children():
            self.tree_devises.delete(item)

        devises = Fiscalite.lister_devises()
        for d in devises:
            self.tree_devises.insert('', 'end', values=(
                d[1], d[2], f"{d[3]:,.2f}", "Oui" if d[4] else "Non"
            ))

    def enregistrer(self):
        try:
            taux = float(self.entry_taux.get())
            if taux < 0 or taux > 100:
                messagebox.showerror("Erreur", "Le taux TVA doit etre entre 0 et 100")
                return
        except ValueError:
            messagebox.showerror("Erreur", "Taux TVA invalide")
            return

        code = self.entry_devise_code.get().strip().upper()
        symbole = self.entry_devise_symbole.get().strip()

        if not code or not symbole:
            messagebox.showerror("Erreur", "Code et symbole de devise requis")
            return

        db.set_parametre('tva_active', '1' if self.tva_active_var.get() else '0')
        db.set_parametre('tva_taux_defaut', str(taux))
        db.set_parametre('devise_principale', code)
        db.set_parametre('devise_symbole', symbole)

        messagebox.showinfo("Succes", "Parametres fiscaux enregistres!")
        self.fenetre.destroy()
