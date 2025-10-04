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

        # Titre de la page d'accueil
        title_label = ttk.Label(
            main_frame,
            text="Bienvenue",
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=10)

        description_label = ttk.Label(
            main_frame,
            text="Veuillez sélectionner un module à lancer.",
            font=("Helvetica", 10)
        )
        description_label.pack(pady=5)

        # Bouton pour lancer le module de gestion de dépenses
        launch_button = ttk.Button(
            main_frame,
            text="Gestion de Dépenses",
            command=self.lancer_gestion_depenses
        )
        launch_button.pack(pady=20, ipadx=10, ipady=5)

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