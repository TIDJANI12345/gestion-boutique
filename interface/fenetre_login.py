"""Fenêtre de connexion"""
import tkinter as tk
from tkinter import messagebox
from modules.utilisateurs import Utilisateur
from config import COLORS

class FenetreLogin:
    def __init__(self, callback_success):
        self.root = tk.Tk()
        self.root.title("Connexion - Gestion Boutique")
        self.root.geometry("450x550")
        self.root.configure(bg="white")
        self.root.resizable(False, False)
        
        self.callback_success = callback_success
        
        # Initialiser la DB (créer tables si 1er lancement)
        Utilisateur.initialiser_tables()
        
        self.centrer_fenetre()
        self.creer_interface()
        
    def centrer_fenetre(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.root.winfo_screenheight() // 2) - (550 // 2)
        self.root.geometry(f"450x550+{x}+{y}")
        
    def creer_interface(self):
        # En-tête
        header = tk.Frame(self.root, bg=COLORS.get('primary', '#2563EB'), height=150)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header, text="🔐", font=("Segoe UI", 50),
            bg=COLORS.get('primary', '#2563EB'), fg="white"
        ).pack(pady=(20, 5))
        
        tk.Label(
            header, text="AUTHENTIFICATION", font=("Segoe UI", 18, "bold"),
            bg=COLORS.get('primary', '#2563EB'), fg="white"
        ).pack()
        
        # Formulaire
        form = tk.Frame(self.root, bg="white")
        form.pack(fill='both', expand=True, padx=50, pady=30)
        
        # Email
        tk.Label(form, text="Email", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_email = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1)
        self.entry_email.pack(fill='x', ipady=8, pady=(5, 20))
        
        # Mot de passe
        tk.Label(form, text="Mot de passe", font=("Segoe UI", 10, "bold"), bg="white").pack(anchor='w')
        self.entry_password = tk.Entry(form, font=("Segoe UI", 12), relief='solid', bd=1, show="●")
        self.entry_password.pack(fill='x', ipady=8, pady=(5, 30))
        self.entry_password.bind('<Return>', lambda e: self.se_connecter())
        
        # Bouton
        tk.Button(
            form, text="SE CONNECTER", font=("Segoe UI", 12, "bold"),
            bg=COLORS.get('primary', '#2563EB'), fg="white", relief='flat', cursor='hand2',
            command=self.se_connecter
        ).pack(fill='x', ipady=12)
        
        # Info par défaut pour le dev
        lbl_info = tk.Label(self.root, text="Admin par défaut: admin@boutique.com / admin123", 
                           font=("Segoe UI", 8), bg="white", fg="gray")
        lbl_info.pack(side='bottom', pady=10)

    def se_connecter(self):
        email = self.entry_email.get().strip()
        password = self.entry_password.get()
        
        if not email or not password:
            messagebox.showwarning("Attention", "Veuillez remplir tous les champs")
            return
            
        user = Utilisateur.authentifier(email, password)
        
        if user:
            # Structure user : (id, nom, prenom, email, mdp, role, ...)
            infos_user = {
                'id': user[0],
                'nom': user[1],
                'prenom': user[2],
                'role': user[5]
            }
            Utilisateur.logger_action(user[0], 'connexion', "Connexion réussie")
            
            self.root.destroy()
            self.callback_success(infos_user)
        else:
            messagebox.showerror("Erreur", "Email ou mot de passe incorrect")
            self.entry_password.delete(0, 'end')

    def afficher(self):
        self.root.mainloop()