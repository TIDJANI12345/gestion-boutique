"""
Gestion des utilisateurs - Interface réservée au Patron
"""
import tkinter as tk
from tkinter import ttk, messagebox
from modules.utilisateurs import Utilisateur
from config import COLORS

class FenetreUtilisateurs:
    def __init__(self, parent, utilisateur_connecte):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Administration - Gestion du Personnel")
        self.fenetre.geometry("1000x650")
        self.fenetre.configure(bg=COLORS['bg'])
        self.fenetre.grab_set()  # Rendre la fenêtre modale
        
        self.user_connecte = utilisateur_connecte
        
        self.creer_interface()
        self.charger_utilisateurs()

    def creer_interface(self):
        # --- EN-TÊTE ---
        header = tk.Frame(self.fenetre, bg=COLORS['primary'], height=100)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(
            header, text="👥 Gestion des Utilisateurs", 
            font=("Segoe UI", 20, "bold"), bg=COLORS['primary'], fg="white"
        ).pack(pady=25)

        # --- FORMULAIRE D'AJOUT (Zone Gauche) ---
        main_container = tk.Frame(self.fenetre, bg=COLORS['bg'])
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        form_frame = tk.LabelFrame(
            main_container, text="Ajouter un nouvel employé", 
            font=("Segoe UI", 12, "bold"), bg="white", padx=20, pady=20
        )
        form_frame.pack(side='left', fill='y', padx=(0, 20))

        fields = [
            ("Nom", "ent_nom"),
            ("Prénom", "ent_prenom"),
            ("Email (Identifiant)", "ent_email"),
            ("Mot de passe", "ent_mdp")
        ]

        for label, var_name in fields:
            tk.Label(form_frame, text=label, bg="white", font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 0))
            entry = tk.Entry(form_frame, font=("Segoe UI", 11), relief='solid', bd=1, width=30)
            if "mdp" in var_name: entry.config(show="●")
            entry.pack(pady=5, ipady=5)
            setattr(self, var_name, entry)

        tk.Label(form_frame, text="Rôle", bg="white", font=("Segoe UI", 10)).pack(anchor='w', pady=(10, 0))
        self.combo_role = ttk.Combobox(form_frame, values=["caissier", "patron"], state="readonly")
        self.combo_role.current(0)
        self.combo_role.pack(fill='x', pady=5, ipady=5)

        tk.Button(
            form_frame, text="✅ Enregistrer l'utilisateur", 
            bg=COLORS['success'], fg="white", font=("Segoe UI", 11, "bold"),
            relief='flat', cursor='hand2', command=self.ajouter_utilisateur
        ).pack(fill='x', pady=20, ipady=10)

        # --- LISTE DES UTILISATEURS (Zone Droite) ---
        list_frame = tk.Frame(main_container, bg="white")
        list_frame.pack(side='right', fill='both', expand=True)

        columns = ("id", "nom", "prenom", "email", "role", "statut")
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Définition des colonnes
        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("prenom", text="Prénom")
        self.tree.heading("email", text="Email")
        self.tree.heading("role", text="Rôle")
        self.tree.heading("statut", text="Statut")

        self.tree.column("id", width=30)
        self.tree.column("role", width=80)
        self.tree.column("statut", width=80)

        self.tree.pack(fill='both', expand=True)

        # Boutons d'action sous la liste
        btn_bar = tk.Frame(list_frame, bg="white")
        btn_bar.pack(fill='x', pady=10)

        tk.Button(btn_bar, text="Activer/Désactiver", command=self.basculer_statut).pack(side='left', padx=5)
        tk.Button(btn_bar, text="Passer en Patron", command=lambda: self.changer_role('patron')).pack(side='left', padx=5)
        tk.Button(btn_bar, text="Passer en Caissier", command=lambda: self.changer_role('caissier')).pack(side='left', padx=5)

    def charger_utilisateurs(self):
        """Rafraîchir la liste"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for u in Utilisateur.obtenir_tous():
            statut = "✅ Actif" if u[6] else "❌ Inactif"
            self.tree.insert('', 'end', values=(u[0], u[1].upper(), u[2], u[3], u[5].upper(), statut))

    def ajouter_utilisateur(self):
        nom = self.ent_nom.get().strip()
        prenom = self.ent_prenom.get().strip()
        email = self.ent_email.get().strip()
        mdp = self.ent_mdp.get().strip()
        role = self.combo_role.get()

        if not all([nom, prenom, email, mdp]):
            messagebox.showwarning("Champs vides", "Veuillez remplir toutes les informations.")
            return

        if Utilisateur.creer_utilisateur(nom, prenom, email, mdp, role):
            messagebox.showinfo("Succès", f"L'utilisateur {nom} a été ajouté.")
            self.charger_utilisateurs()
            # Nettoyage
            for entry in [self.ent_nom, self.ent_prenom, self.ent_email, self.ent_mdp]:
                entry.delete(0, 'end')
        else:
            messagebox.showerror("Erreur", "Cet email est déjà utilisé.")

    def basculer_statut(self):
        selection = self.tree.selection()
        if not selection: return
        
        user_id = self.tree.item(selection[0])['values'][0]
        statut_actuel = self.tree.item(selection[0])['values'][5]

        if int(user_id) == self.user_connecte['id']:
            messagebox.showwarning("Action impossible", "Vous ne pouvez pas vous désactiver vous-même.")
            return

        nouveau_statut = 0 if "Actif" in statut_actuel else 1
        Utilisateur.changer_statut(user_id, nouveau_statut)
        self.charger_utilisateurs()

    def changer_role(self, nouveau_role):
        selection = self.tree.selection()
        if not selection: return
        user_id = self.tree.item(selection[0])['values'][0]
        Utilisateur.modifier_role(user_id, nouveau_role)
        self.charger_utilisateurs()