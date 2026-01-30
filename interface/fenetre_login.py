"""Fenetre de connexion avec protection brute-force"""
import tkinter as tk
from tkinter import messagebox
from modules.utilisateurs import Utilisateur
from config import COLORS


class FenetreLogin:
    MAX_TENTATIVES = 5
    DUREE_BLOCAGE = 30  # secondes

    def __init__(self, callback_success):
        self.root = tk.Tk()
        self.root.title("Connexion - Gestion Boutique")
        self.root.geometry("450x500")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        self.callback_success = callback_success
        self.tentatives_echouees = 0
        self.bloque = False
        self.timer_id = None

        Utilisateur.initialiser_tables()

        self.centrer_fenetre()
        self.creer_interface()

    def centrer_fenetre(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"450x500+{x}+{y}")

    def creer_interface(self):
        # En-tete
        header = tk.Frame(self.root, bg=COLORS.get('primary', '#2563EB'), height=130)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header, text="AUTHENTIFICATION", font=("Segoe UI", 20, "bold"),
            bg=COLORS.get('primary', '#2563EB'), fg="white"
        ).pack(expand=True)

        # Formulaire
        form = tk.Frame(self.root, bg="white")
        form.pack(fill='both', expand=True, padx=50, pady=30)

        # Email
        tk.Label(form, text="Email", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_email = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1)
        self.entry_email.pack(fill='x', ipady=8, pady=(5, 20))

        # Mot de passe
        tk.Label(form, text="Mot de passe", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_password = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1, show="*")
        self.entry_password.pack(fill='x', ipady=8, pady=(5, 30))
        self.entry_password.bind('<Return>', lambda e: self.se_connecter())

        # Bouton connexion
        self.btn_connexion = tk.Button(
            form, text="SE CONNECTER", font=("Segoe UI", 12, "bold"),
            bg=COLORS.get('primary', '#2563EB'), fg="white", relief='flat', cursor='hand2',
            command=self.se_connecter
        )
        self.btn_connexion.pack(fill='x', ipady=12)

        # Label blocage (cache par defaut)
        self.label_blocage = tk.Label(
            form, text="", font=("Segoe UI", 10, "bold"),
            bg="white", fg=COLORS.get('danger', '#EF4444')
        )
        self.label_blocage.pack(pady=(15, 0))

    def se_connecter(self):
        if self.bloque:
            return

        email = self.entry_email.get().strip()
        password = self.entry_password.get()

        if not email or not password:
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
            return

        user = Utilisateur.authentifier(email, password)

        if user:
            self.tentatives_echouees = 0
            infos_user = {
                'id': user[0],
                'nom': user[1],
                'prenom': user[2],
                'role': user[5]
            }
            Utilisateur.logger_action(user[0], 'connexion', "Connexion reussie")

            self.root.destroy()
            self.callback_success(infos_user)
        else:
            self.tentatives_echouees += 1
            restantes = self.MAX_TENTATIVES - self.tentatives_echouees

            if self.tentatives_echouees >= self.MAX_TENTATIVES:
                self.bloquer_formulaire()
            else:
                messagebox.showerror(
                    "Erreur",
                    f"Email ou mot de passe incorrect\n({restantes} tentative(s) restante(s))"
                )
            self.entry_password.delete(0, 'end')

    def bloquer_formulaire(self):
        """Bloquer le formulaire pendant DUREE_BLOCAGE secondes"""
        self.bloque = True
        self.btn_connexion.config(state='disabled', bg='gray')
        self.entry_email.config(state='disabled')
        self.entry_password.config(state='disabled')
        self.compte_a_rebours(self.DUREE_BLOCAGE)

    def compte_a_rebours(self, secondes):
        """Decompte avant deblocage"""
        if secondes > 0:
            self.label_blocage.config(
                text=f"Trop de tentatives. Reessayez dans {secondes}s"
            )
            self.timer_id = self.root.after(1000, self.compte_a_rebours, secondes - 1)
        else:
            self.debloquer_formulaire()

    def debloquer_formulaire(self):
        """Reactiver le formulaire"""
        self.bloque = False
        self.tentatives_echouees = 0
        self.btn_connexion.config(state='normal', bg=COLORS.get('primary', '#2563EB'))
        self.entry_email.config(state='normal')
        self.entry_password.config(state='normal')
        self.label_blocage.config(text="")

    def afficher(self):
        self.root.mainloop()
