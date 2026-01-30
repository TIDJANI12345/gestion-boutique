"""
Fenetre de selection du mode de paiement
S'affiche entre la validation du panier et la confirmation de vente
"""
import tkinter as tk
from tkinter import messagebox
from config import COLORS


class FenetrePaiement:
    """Fenetre modale pour le choix du mode de paiement"""

    def __init__(self, parent, total, callback):
        """
        parent: fenetre parente
        total: montant total de la vente
        callback: fonction appelee avec le resultat du paiement
                  callback(result) ou result est une liste de dicts paiement
                  ou None si annule
        """
        self.total = total
        self.callback = callback
        self.result = None

        self.fenetre = tk.Toplevel(parent)
        self.fenetre.title("Paiement")
        self.fenetre.geometry("550x600")
        self.fenetre.configure(bg="white")
        self.fenetre.transient(parent)
        self.fenetre.grab_set()
        self.fenetre.resizable(False, False)

        # Centrer
        self.fenetre.update_idletasks()
        x = (self.fenetre.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.fenetre.winfo_screenheight() // 2) - (600 // 2)
        self.fenetre.geometry(f"550x600+{x}+{y}")

        self.mode_var = tk.StringVar(value='especes')
        self.creer_interface()

        self.fenetre.protocol("WM_DELETE_WINDOW", self.annuler)

    def creer_interface(self):
        """Creer l'interface de paiement"""

        # En-tete
        header = tk.Frame(self.fenetre, bg=COLORS['primary'], height=90)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(
            header, text="Paiement",
            font=("Segoe UI", 20, "bold"), bg=COLORS['primary'], fg="white"
        ).pack(side='left', padx=30, pady=25)

        tk.Label(
            header, text=f"{self.total:,.0f} FCFA",
            font=("Segoe UI", 22, "bold"), bg=COLORS['primary'], fg="white"
        ).pack(side='right', padx=30, pady=25)

        # Contenu
        content = tk.Frame(self.fenetre, bg="white")
        content.pack(fill='both', expand=True, padx=30, pady=20)

        tk.Label(
            content, text="Mode de paiement",
            font=("Segoe UI", 13, "bold"), bg="white", fg=COLORS['dark']
        ).pack(anchor='w', pady=(0, 10))

        # Boutons radio pour les modes
        modes = [
            ('especes', 'Especes'),
            ('orange_money', 'Orange Money'),
            ('mtn_momo', 'MTN MoMo'),
            ('moov_money', 'Moov Money'),
            ('mixte', 'Paiement mixte'),
        ]

        modes_frame = tk.Frame(content, bg="white")
        modes_frame.pack(fill='x', pady=(0, 15))

        for value, label in modes:
            rb = tk.Radiobutton(
                modes_frame, text=label, variable=self.mode_var, value=value,
                font=("Segoe UI", 11), bg="white", activebackground="white",
                command=self.on_mode_change, anchor='w', padx=10, pady=4
            )
            rb.pack(fill='x')

        # Separateur
        tk.Frame(content, bg=COLORS['light'], height=1).pack(fill='x', pady=10)

        # Zone dynamique pour les champs de saisie
        self.zone_saisie = tk.Frame(content, bg="white")
        self.zone_saisie.pack(fill='both', expand=True)

        # Boutons en bas
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill='x', pady=(10, 0))

        tk.Button(
            btn_frame, text="Confirmer le paiement",
            font=("Segoe UI", 13, "bold"), bg=COLORS['success'], fg="white",
            relief='flat', cursor='hand2', command=self.confirmer
        ).pack(fill='x', ipady=14, pady=(0, 8))

        tk.Button(
            btn_frame, text="Annuler",
            font=("Segoe UI", 11), bg=COLORS['danger'], fg="white",
            relief='flat', cursor='hand2', command=self.annuler
        ).pack(fill='x', ipady=10)

        # Afficher les champs du mode par defaut
        self.on_mode_change()

    def on_mode_change(self):
        """Mettre a jour les champs selon le mode selectionne"""
        # Vider la zone de saisie
        for widget in self.zone_saisie.winfo_children():
            widget.destroy()

        mode = self.mode_var.get()

        if mode == 'especes':
            self._champs_especes()
        elif mode in ('orange_money', 'mtn_momo', 'moov_money'):
            self._champs_mobile_money()
        elif mode == 'mixte':
            self._champs_mixte()

    def _champs_especes(self):
        """Champs pour paiement en especes"""
        tk.Label(
            self.zone_saisie, text="Montant recu du client:",
            font=("Segoe UI", 11, "bold"), bg="white"
        ).pack(anchor='w', pady=(5, 5))

        self.entry_montant_recu = tk.Entry(
            self.zone_saisie, font=("Segoe UI", 16), relief='solid', bd=1, justify='center'
        )
        self.entry_montant_recu.pack(fill='x', ipady=10, pady=(0, 10))
        self.entry_montant_recu.insert(0, f"{self.total:,.0f}".replace(",", ""))
        self.entry_montant_recu.select_range(0, 'end')
        self.entry_montant_recu.focus()
        self.entry_montant_recu.bind('<KeyRelease>', self._calculer_monnaie)

        # Monnaie rendue
        self.label_monnaie = tk.Label(
            self.zone_saisie, text="Monnaie a rendre: 0 FCFA",
            font=("Segoe UI", 14, "bold"), bg="white", fg=COLORS['success']
        )
        self.label_monnaie.pack(pady=10)

    def _calculer_monnaie(self, event=None):
        """Calculer la monnaie a rendre"""
        try:
            montant_recu = float(self.entry_montant_recu.get().replace(",", "").replace(" ", ""))
            monnaie = montant_recu - self.total
            if monnaie >= 0:
                self.label_monnaie.config(
                    text=f"Monnaie a rendre: {monnaie:,.0f} FCFA",
                    fg=COLORS['success']
                )
            else:
                self.label_monnaie.config(
                    text=f"Insuffisant: {monnaie:,.0f} FCFA",
                    fg=COLORS['danger']
                )
        except ValueError:
            self.label_monnaie.config(text="Montant invalide", fg=COLORS['danger'])

    def _champs_mobile_money(self):
        """Champs pour paiement mobile money"""
        tk.Label(
            self.zone_saisie, text="Reference de la transaction:",
            font=("Segoe UI", 11, "bold"), bg="white"
        ).pack(anchor='w', pady=(5, 5))

        self.entry_reference = tk.Entry(
            self.zone_saisie, font=("Segoe UI", 14), relief='solid', bd=1, justify='center'
        )
        self.entry_reference.pack(fill='x', ipady=10, pady=(0, 10))
        self.entry_reference.focus()

        tk.Label(
            self.zone_saisie,
            text=f"Montant: {self.total:,.0f} FCFA",
            font=("Segoe UI", 14, "bold"), bg="white", fg=COLORS['primary']
        ).pack(pady=10)

    def _champs_mixte(self):
        """Champs pour paiement mixte (especes + mobile money)"""
        tk.Label(
            self.zone_saisie, text="Montant en especes:",
            font=("Segoe UI", 11, "bold"), bg="white"
        ).pack(anchor='w', pady=(5, 3))

        self.entry_mixte_especes = tk.Entry(
            self.zone_saisie, font=("Segoe UI", 14), relief='solid', bd=1, justify='center'
        )
        self.entry_mixte_especes.pack(fill='x', ipady=8, pady=(0, 10))
        self.entry_mixte_especes.insert(0, "0")
        self.entry_mixte_especes.focus()
        self.entry_mixte_especes.bind('<KeyRelease>', self._maj_mixte_reste)

        # Mode mobile money
        tk.Label(
            self.zone_saisie, text="Mode Mobile Money:",
            font=("Segoe UI", 11, "bold"), bg="white"
        ).pack(anchor='w', pady=(5, 3))

        self.mode_mobile_var = tk.StringVar(value='orange_money')
        modes_mobile = tk.Frame(self.zone_saisie, bg="white")
        modes_mobile.pack(fill='x', pady=(0, 5))
        for val, lbl in [('orange_money', 'Orange Money'), ('mtn_momo', 'MTN MoMo'), ('moov_money', 'Moov Money')]:
            tk.Radiobutton(
                modes_mobile, text=lbl, variable=self.mode_mobile_var, value=val,
                font=("Segoe UI", 10), bg="white", activebackground="white"
            ).pack(side='left', padx=5)

        tk.Label(
            self.zone_saisie, text="Montant Mobile Money:",
            font=("Segoe UI", 11, "bold"), bg="white"
        ).pack(anchor='w', pady=(5, 3))

        self.entry_mixte_mobile = tk.Entry(
            self.zone_saisie, font=("Segoe UI", 14), relief='solid', bd=1, justify='center'
        )
        self.entry_mixte_mobile.pack(fill='x', ipady=8, pady=(0, 5))
        self.entry_mixte_mobile.insert(0, str(int(self.total)))
        self.entry_mixte_mobile.bind('<KeyRelease>', self._maj_mixte_reste)

        tk.Label(
            self.zone_saisie, text="Reference transaction:",
            font=("Segoe UI", 10, "bold"), bg="white"
        ).pack(anchor='w', pady=(5, 3))

        self.entry_mixte_ref = tk.Entry(
            self.zone_saisie, font=("Segoe UI", 12), relief='solid', bd=1
        )
        self.entry_mixte_ref.pack(fill='x', ipady=6, pady=(0, 5))

        self.label_mixte_info = tk.Label(
            self.zone_saisie, text="",
            font=("Segoe UI", 11, "bold"), bg="white", fg=COLORS['primary']
        )
        self.label_mixte_info.pack(pady=5)

        self._maj_mixte_reste()

    def _maj_mixte_reste(self, event=None):
        """Mettre a jour les infos du paiement mixte"""
        try:
            especes = float(self.entry_mixte_especes.get().replace(",", "").replace(" ", "") or "0")
            mobile = float(self.entry_mixte_mobile.get().replace(",", "").replace(" ", "") or "0")
            somme = especes + mobile
            diff = somme - self.total

            if abs(diff) < 0.01:
                self.label_mixte_info.config(
                    text=f"Total: {somme:,.0f} FCFA - OK",
                    fg=COLORS['success']
                )
            elif diff > 0:
                self.label_mixte_info.config(
                    text=f"Total: {somme:,.0f} FCFA (excedent: {diff:,.0f})",
                    fg=COLORS['warning']
                )
            else:
                self.label_mixte_info.config(
                    text=f"Total: {somme:,.0f} FCFA (manque: {-diff:,.0f})",
                    fg=COLORS['danger']
                )
        except ValueError:
            self.label_mixte_info.config(text="Montants invalides", fg=COLORS['danger'])

    def confirmer(self):
        """Confirmer le paiement"""
        mode = self.mode_var.get()

        try:
            if mode == 'especes':
                montant_recu = float(
                    self.entry_montant_recu.get().replace(",", "").replace(" ", "")
                )
                if montant_recu < self.total:
                    messagebox.showerror("Erreur", "Le montant recu est insuffisant!")
                    return

                monnaie = montant_recu - self.total
                self.result = [{
                    'mode': 'especes',
                    'montant': self.total,
                    'reference': None,
                    'montant_recu': montant_recu,
                    'monnaie_rendue': monnaie,
                }]

            elif mode in ('orange_money', 'mtn_momo', 'moov_money'):
                reference = self.entry_reference.get().strip()
                if not reference:
                    messagebox.showerror("Erreur", "Veuillez saisir la reference de la transaction!")
                    return

                self.result = [{
                    'mode': mode,
                    'montant': self.total,
                    'reference': reference,
                    'montant_recu': None,
                    'monnaie_rendue': None,
                }]

            elif mode == 'mixte':
                especes = float(
                    self.entry_mixte_especes.get().replace(",", "").replace(" ", "") or "0"
                )
                mobile = float(
                    self.entry_mixte_mobile.get().replace(",", "").replace(" ", "") or "0"
                )
                somme = especes + mobile

                if somme < self.total:
                    messagebox.showerror("Erreur",
                        f"La somme des paiements ({somme:,.0f}) est inferieure au total ({self.total:,.0f})!")
                    return

                mode_mobile = self.mode_mobile_var.get()
                reference = self.entry_mixte_ref.get().strip()
                if mobile > 0 and not reference:
                    messagebox.showerror("Erreur", "Veuillez saisir la reference Mobile Money!")
                    return

                self.result = []
                if especes > 0:
                    self.result.append({
                        'mode': 'especes',
                        'montant': especes,
                        'reference': None,
                        'montant_recu': especes,
                        'monnaie_rendue': 0,
                    })
                if mobile > 0:
                    self.result.append({
                        'mode': mode_mobile,
                        'montant': mobile,
                        'reference': reference,
                        'montant_recu': None,
                        'monnaie_rendue': None,
                    })

            self.fenetre.destroy()
            self.callback(self.result)

        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide!")

    def annuler(self):
        """Annuler le paiement"""
        self.fenetre.destroy()
        self.callback(None)
