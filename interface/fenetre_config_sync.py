"""
Configuration de la synchronisation cloud
"""
import tkinter as tk
from tkinter import messagebox
from modules.synchronisation import Synchronisation
from config import *


class FenetreConfigSync:
    def __init__(self, parent):
        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Synchronisation Cloud")
        self.fenetre.geometry("600x520")
        self.fenetre.configure(bg="white")

        self.sync = Synchronisation()
        self.creer_interface()

    def creer_interface(self):
        """Interface de configuration sync cloud"""

        # En-tete
        header = tk.Frame(self.fenetre, bg=COLORS['info'], height=80)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header,
            text="Synchronisation Cloud",
            font=("Segoe UI", 18, "bold"),
            bg=COLORS['info'],
            fg="white"
        ).pack(expand=True)

        # Contenu
        content = tk.Frame(self.fenetre, bg="white")
        content.pack(fill='both', expand=True, padx=40, pady=30)

        # Statut de connexion
        tk.Label(
            content,
            text="Statut de connexion :",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(anchor='w', pady=(0, 5))

        self.label_mode = tk.Label(
            content,
            text="Detection en cours...",
            font=("Segoe UI", 14, "bold"),
            bg="white",
            fg=COLORS['gray']
        )
        self.label_mode.pack(anchor='w', pady=(0, 10))

        # Derniere synchronisation
        tk.Label(
            content,
            text="Derniere synchronisation :",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(anchor='w', pady=(10, 5))

        dernier_sync = self.sync._get_dernier_sync()
        if dernier_sync:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(dernier_sync)
                texte_sync = dt.strftime("%d/%m/%Y %H:%M:%S")
            except Exception:
                texte_sync = dernier_sync
        else:
            texte_sync = "Jamais"

        self.label_dernier_sync = tk.Label(
            content,
            text=texte_sync,
            font=("Segoe UI", 12),
            bg="white",
            fg=COLORS['dark']
        )
        self.label_dernier_sync.pack(anchor='w', pady=(0, 10))

        # Indicateur serveur
        tk.Label(
            content,
            text=f"Serveur : {SYNC_SERVER_URL}",
            font=("Segoe UI", 9),
            bg="white",
            fg=COLORS['gray']
        ).pack(anchor='w', pady=(0, 20))

        # Boutons
        tk.Button(
            content,
            text="Synchroniser maintenant",
            font=("Segoe UI", 12, "bold"),
            bg=COLORS['primary'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.synchroniser_maintenant
        ).pack(fill='x', ipady=15, pady=(0, 10))

        tk.Button(
            content,
            text="Detecter a nouveau",
            font=("Segoe UI", 11),
            bg=COLORS['info'],
            fg="white",
            relief='flat',
            cursor='hand2',
            command=self.detecter_mode
        ).pack(fill='x', ipady=12)

        # Lancer la detection initiale
        self.fenetre.after(100, self.detecter_mode)

    def _maj_label_mode(self, mode):
        """Met a jour l'affichage du mode"""
        if mode == 'cloud':
            self.label_mode.config(
                text="Connecte (Cloud)",
                fg=COLORS['success']
            )
        else:
            self.label_mode.config(
                text="Hors ligne",
                fg=COLORS['danger']
            )

    def synchroniser_maintenant(self):
        """Lancer la synchronisation"""
        self.label_mode.config(text="Synchronisation en cours...", fg=COLORS['warning'])
        self.fenetre.update()

        try:
            succes = self.sync.synchroniser()
            if succes:
                self._maj_label_mode('cloud')
                # Mettre a jour la date de derniere sync
                dernier_sync = self.sync._get_dernier_sync()
                if dernier_sync:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(dernier_sync)
                        self.label_dernier_sync.config(text=dt.strftime("%d/%m/%Y %H:%M:%S"))
                    except Exception:
                        self.label_dernier_sync.config(text=dernier_sync)
                messagebox.showinfo("Synchronisation", "Synchronisation terminee avec succes !")
            else:
                self._maj_label_mode(self.sync.mode)
                messagebox.showwarning("Synchronisation", "Synchronisation impossible (hors ligne ou erreur)")
        except Exception as e:
            self._maj_label_mode('offline')
            messagebox.showerror("Erreur", f"Erreur: {e}")

    def detecter_mode(self):
        """Redetecter le mode de connexion"""
        self.label_mode.config(text="Detection en cours...", fg=COLORS['warning'])
        self.fenetre.update()

        mode = self.sync.detecter_mode()
        self._maj_label_mode(mode)
