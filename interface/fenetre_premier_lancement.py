"""
Fenetre de creation du premier compte (patron)
Affichee au premier lancement quand aucun utilisateur n'existe
"""
import tkinter as tk
from tkinter import messagebox
from modules.utilisateurs import Utilisateur
from config import COLORS


class FenetrePremierLancement:
    def __init__(self, callback_success):
        self.root = tk.Tk()
        self.root.title("Premier lancement - Gestion Boutique")
        self.root.geometry("500x650")
        self.root.configure(bg="white")
        self.root.resizable(False, False)

        self.callback_success = callback_success
        self.centrer_fenetre()
        self.creer_interface()

    def centrer_fenetre(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.root.winfo_screenheight() // 2) - (650 // 2)
        self.root.geometry(f"500x650+{x}+{y}")

    def creer_interface(self):
        # En-tete
        header = tk.Frame(self.root, bg=COLORS.get('success', '#10B981'), height=120)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header, text="Bienvenue !",
            font=("Segoe UI", 22, "bold"),
            bg=COLORS.get('success', '#10B981'), fg="white"
        ).pack(pady=(25, 5))

        tk.Label(
            header, text="Creez votre compte administrateur",
            font=("Segoe UI", 11),
            bg=COLORS.get('success', '#10B981'), fg="white"
        ).pack()

        # Formulaire
        form = tk.Frame(self.root, bg="white")
        form.pack(fill='both', expand=True, padx=50, pady=25)

        # Nom
        tk.Label(form, text="Nom", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_nom = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1)
        self.entry_nom.pack(fill='x', ipady=8, pady=(5, 12))

        # Prenom
        tk.Label(form, text="Prenom", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_prenom = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1)
        self.entry_prenom.pack(fill='x', ipady=8, pady=(5, 12))

        # Email
        tk.Label(form, text="Email", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_email = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1)
        self.entry_email.pack(fill='x', ipady=8, pady=(5, 12))

        # Mot de passe
        tk.Label(form, text="Mot de passe", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_mdp = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1, show="*")
        self.entry_mdp.pack(fill='x', ipady=8, pady=(5, 5))

        tk.Label(
            form, text="Minimum 8 caracteres, au moins 1 chiffre",
            font=("Segoe UI", 8), bg="white", fg="gray"
        ).pack(anchor='w', pady=(0, 12))

        # Confirmation mot de passe
        tk.Label(form, text="Confirmer le mot de passe", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_mdp_confirm = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1, show="*")
        self.entry_mdp_confirm.pack(fill='x', ipady=8, pady=(5, 20))
        self.entry_mdp_confirm.bind('<Return>', lambda e: self.creer_compte())

        # Bouton
        tk.Button(
            form, text="CREER LE COMPTE", font=("Segoe UI", 12, "bold"),
            bg=COLORS.get('success', '#10B981'), fg="white", relief='flat', cursor='hand2',
            command=self.creer_compte
        ).pack(fill='x', ipady=12)

    def creer_compte(self):
        nom = self.entry_nom.get().strip()
        prenom = self.entry_prenom.get().strip()
        email = self.entry_email.get().strip()
        mdp = self.entry_mdp.get()
        mdp_confirm = self.entry_mdp_confirm.get()

        # Validations
        if not all([nom, prenom, email, mdp, mdp_confirm]):
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
            return

        if '@' not in email or '.' not in email:
            messagebox.showwarning("Attention", "Veuillez entrer un email valide")
            return

        if mdp != mdp_confirm:
            messagebox.showerror("Erreur", "Les mots de passe ne correspondent pas")
            self.entry_mdp_confirm.delete(0, 'end')
            return

        # Valider complexite mot de passe
        valide, message = Utilisateur.valider_mot_de_passe(mdp)
        if not valide:
            messagebox.showerror("Mot de passe", message)
            return

        # Creer le compte patron
        succes, message = Utilisateur.creer_utilisateur(nom, prenom, email, mdp, role='patron')

        if succes:
            messagebox.showinfo("Succes", "Compte administrateur cree !\nVous pouvez maintenant vous connecter.")
            self.root.destroy()
            self.callback_success()
        else:
            messagebox.showerror("Erreur", message)

    def afficher(self):
        self.root.mainloop()
