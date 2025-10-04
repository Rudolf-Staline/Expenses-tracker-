import tkinter as tk
from tkinter import ttk
from ttkthemes import ThemedTk
from modules import gestion_depenses

class App(ThemedTk):
    def __init__(self):
        super().__init__()

        # Thème initial
        self.set_theme("radiance")

        self.title("Application Modulaire")
        self.geometry("400x300")

        # Créer le menu
        self.creer_menu()

        # Frame principale
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        # --- Tableau de Bord ---
        dashboard_frame = ttk.LabelFrame(main_frame, text="Tableau de Bord (Mois en cours)", padding="15")
        dashboard_frame.pack(pady=10, fill="x")

        self.revenus_label = ttk.Label(dashboard_frame, text="Revenus: ...", font=("Helvetica", 12))
        self.revenus_label.pack(anchor="w", pady=2)

        self.depenses_label = ttk.Label(dashboard_frame, text="Dépenses: ...", font=("Helvetica", 12))
        self.depenses_label.pack(anchor="w", pady=2)

        self.solde_label = ttk.Label(dashboard_frame, text="Solde: ...", font=("Helvetica", 14, "bold"))
        self.solde_label.pack(anchor="w", pady=10)

        # Bouton pour lancer le module de gestion
        launch_button = ttk.Button(
            main_frame,
            text="Ouvrir le Gestionnaire de Dépenses",
            command=self.lancer_gestion_depenses
        )
        launch_button.pack(pady=10, ipadx=10, ipady=5, expand=True)

        refresh_button = ttk.Button(main_frame, text="Actualiser le Tableau de Bord", command=self.actualiser_dashboard)
        refresh_button.pack(pady=5)

        # Charger les données initiales
        self.actualiser_dashboard()

    def actualiser_dashboard(self):
        """Récupère et affiche les données financières du mois en cours."""
        revenus = gestion_depenses.get_revenus_pour_mois_en_cours()
        depenses = gestion_depenses.get_depenses_pour_mois_en_cours()
        solde = revenus - depenses

        self.revenus_label.config(text=f"Revenus du mois: {revenus:.2f} MAD")
        self.depenses_label.config(text=f"Dépenses du mois: {depenses:.2f} MAD")

        solde_color = "green" if solde >= 0 else "red"
        self.solde_label.config(text=f"Solde actuel: {solde:.2f} MAD", foreground=solde_color)

    def lancer_gestion_depenses(self):
        # On cache la fenêtre principale et on ouvre celle du module
        self.withdraw()
        # Crée une instance de la fenêtre du module de dépenses
        # On passe 'self' pour que la fenêtre du module puisse ré-afficher la fenêtre principale à sa fermeture
        gestion_depenses.GestionDepensesUI(self)

    def creer_menu(self):
        """Crée la barre de menu principale avec le sélecteur de thèmes."""
        menu_bar = tk.Menu(self)
        self.config(menu=menu_bar)

        # Menu Thèmes
        theme_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Thèmes", menu=theme_menu)

        # Liste de thèmes à proposer
        themes = sorted([
            "arc", "radiance", "scidblue", "equilux",
            "itft1", "plastik", "scidgreen", "scidmint",
            "scidpink", "scidsand", "scidpurple", "black", "blue"
        ])

        for theme_name in themes:
            theme_menu.add_command(
                label=theme_name,
                command=lambda t=theme_name: self.set_theme(t)
            )


if __name__ == "__main__":
    app = App()
    app.mainloop()