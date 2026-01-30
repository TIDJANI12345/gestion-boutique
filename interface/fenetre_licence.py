import tkinter as tk
from tkinter import messagebox
from config import COLORS, APP_NAME
from modules.licence import GestionLicence

class FenetreLicence:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success 
        self.licence_manager = GestionLicence()
        
        # MODIFICATION ICI : On utilise Toplevel mais on force l'affichage
        self.window = tk.Toplevel(root)
        self.window.title(f"Activation - {APP_NAME}")
        self.window.geometry("500x400")
        self.window.configure(bg=COLORS['bg'])
        self.window.resizable(False, False)
        
        # --- CORRECTION DE L'AFFICHAGE ---
        # On retire cette ligne qui causait le problème :
        # self.window.transient(root) 
        
        # On force la fenêtre à passer devant toutes les autres
        self.window.attributes('-topmost', True)
        self.window.deiconify() # Force l'affichage
        self.window.lift()      # Monte la fenêtre en haut de la pile
        self.window.focus_force() # Force le focus clavier dessus
        
        # Empêcher la fermeture
        self.window.protocol("WM_DELETE_WINDOW", self.quitter_app)
        self.window.grab_set()
        
        self.setup_ui()
        self.centrer_fenetre()

    def centrer_fenetre(self):
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

    def setup_ui(self):
        # Logo ou Icône
        tk.Label(
            self.window, text="🔐", font=("Segoe UI", 40), 
            bg=COLORS['bg']
        ).pack(pady=(20, 10))

        tk.Label(
            self.window, text="Activation Requise", 
            font=("Segoe UI", 18, "bold"), bg=COLORS['bg'], fg=COLORS['dark']
        ).pack()

        tk.Label(
            self.window, 
            text="Veuillez entrer votre clé de produit pour continuer.\nCette licence sera liée à cet ordinateur.",
            font=("Segoe UI", 10), bg=COLORS['bg'], fg=COLORS['gray'], justify="center"
        ).pack(pady=10)

        # Zone de saisie
        frame_input = tk.Frame(self.window, bg=COLORS['bg'])
        frame_input.pack(pady=20, padx=40, fill="x")

        tk.Label(frame_input, text="Clé de licence (Format GB26-...)", bg=COLORS['bg'], anchor="w").pack(fill="x")
        
        self.entry_cle = tk.Entry(
            frame_input, font=("Consolas", 12), justify="center", 
            bd=2, relief="solid"
        )
        self.entry_cle.pack(fill="x", pady=5, ipady=5)

        # Bouton Activer
        self.btn_activer = tk.Button(
            self.window, text="ACTIVER LE LOGICIEL", 
            font=("Segoe UI", 11, "bold"), bg=COLORS['primary'], fg="white",
            relief="flat", cursor="hand2", command=self.action_activer
        )
        self.btn_activer.pack(pady=10, ipady=5, ipadx=20)

        # Bouton Quitter
        tk.Button(
            self.window, text="Quitter", 
            font=("Segoe UI", 9), bg=COLORS['bg'], fg=COLORS['danger'],
            relief="flat", cursor="hand2", command=self.quitter_app
        ).pack(side="bottom", pady=20)

    def action_activer(self):
        cle = self.entry_cle.get().strip()
        if len(cle) < 10:
            messagebox.showwarning("Erreur", "Format de clé invalide")
            return

        self.btn_activer.config(state="disabled", text="Vérification...")
        self.window.update()

        succes, message = self.licence_manager.activer_en_ligne(cle)

        if succes:
            messagebox.showinfo("Félicitations", f"{message}\n\nL'application va maintenant démarrer.")
            self.window.destroy()
            self.on_success() 
        else:
            messagebox.showerror("Echec de l'activation", message)
            self.btn_activer.config(state="normal", text="ACTIVER LE LOGICIEL")

    def quitter_app(self):
        self.root.destroy()