import sqlite3
from pathlib import Path

# Le chemin de la base de données sera à la racine du projet
DB_PATH = Path(__file__).parent.parent / "depenses.db"

def initialiser_db():
    """
    Initialise la base de données SQLite et crée les tables si elles n'existent pas.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Table pour les items
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            conditionnement TEXT,
            famille TEXT,
            type TEXT,
            volume REAL,
            unite_volume TEXT,
            poids REAL,
            unite_poids TEXT,
            archive INTEGER NOT NULL DEFAULT 0
        );
        """)

        # Table pour l'historique des prix
        # Le prix est stocké ici pour tracer chaque changement
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique_prix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            prix REAL NOT NULL,
            date_changement TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id)
        );
        """)

        # Table pour les dépenses enregistrées
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            quantite REAL NOT NULL,
            prix_unitaire_historique REAL NOT NULL,
            date_depense TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id)
        );
        """)

        # Table pour les surplus et déficits journaliers
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS ajustements_journaliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_ajustement TEXT NOT NULL UNIQUE,
            montant REAL NOT NULL
        );
        """)

        conn.commit()
        print(f"Base de données initialisée avec succès à l'emplacement : {DB_PATH}")

    except sqlite3.Error as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
    finally:
        if conn:
            conn.close()

import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
from . import export_utils

# --- Fonctions de base de données pour les ITEMS ---

def get_connection():
    """Retourne un objet de connexion à la base de données."""
    # S'assure que la DB est initialisée si le fichier n'existe pas
    if not DB_PATH.exists():
        initialiser_db()
    return sqlite3.connect(DB_PATH)

def ajouter_item(nom, prix_initial, conditionnement, famille, type, volume, unite_volume, poids, unite_poids):
    """Ajoute un nouvel item et son prix initial."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Insérer l'item
        cursor.execute("""
            INSERT INTO items (nom, conditionnement, famille, type, volume, unite_volume, poids, unite_poids)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (nom, conditionnement, famille, type, volume, unite_volume, poids, unite_poids))
        item_id = cursor.lastrowid

        # 2. Insérer le prix initial dans l'historique
        date_actuelle = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO historique_prix (item_id, prix, date_changement)
            VALUES (?, ?, ?)
        """, (item_id, prix_initial, date_actuelle))

        conn.commit()
        messagebox.showinfo("Succès", f"L'item '{nom}' a été ajouté avec succès.")
    except sqlite3.IntegrityError:
        messagebox.showerror("Erreur", f"Un item avec le nom '{nom}' existe déjà.")
    except sqlite3.Error as e:
        messagebox.showerror("Erreur de base de données", str(e))
    finally:
        conn.close()

def get_tous_les_items():
    """Récupère tous les items non archivés avec leur prix actuel."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.id, i.nom, i.conditionnement, i.famille, i.type,
               (SELECT hp.prix
                FROM historique_prix hp
                WHERE hp.item_id = i.id
                ORDER BY hp.date_changement DESC
                LIMIT 1) as prix_actuel
        FROM items i
        WHERE i.archive = 0
        ORDER BY i.nom;
    """)
    items = cursor.fetchall()
    conn.close()
    return items

def get_item_details_by_id(item_id):
    """Récupère les détails complets d'un item, y compris son prix actuel."""
    conn = get_connection()
    # Pour récupérer les noms de colonnes dans le résultat
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT i.*,
               (SELECT hp.prix
                FROM historique_prix hp
                WHERE hp.item_id = i.id
                ORDER BY hp.date_changement DESC
                LIMIT 1) as prix_actuel
        FROM items i
        WHERE i.id = ?
    """, (item_id,))
    details = cursor.fetchone()
    conn.close()
    return dict(details) if details else None

def modifier_item(item_id, nom, nouveau_prix, conditionnement, famille, type, volume, unite_volume, poids, unite_poids):
    """Met à jour les informations d'un item et gère le changement de prix."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 1. Mettre à jour les détails de l'item
        cursor.execute("""
            UPDATE items
            SET nom = ?, conditionnement = ?, famille = ?, type = ?, volume = ?, unite_volume = ?, poids = ?, unite_poids = ?
            WHERE id = ?
        """, (nom, conditionnement, famille, type, volume, unite_volume, poids, unite_poids, item_id))

        # 2. Vérifier si le prix a changé
        cursor.execute("""
            SELECT prix FROM historique_prix
            WHERE item_id = ? ORDER BY date_changement DESC LIMIT 1
        """, (item_id,))
        prix_actuel = cursor.fetchone()[0]

        if nouveau_prix != prix_actuel:
            date_changement = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute("""
                INSERT INTO historique_prix (item_id, prix, date_changement)
                VALUES (?, ?, ?)
            """, (item_id, nouveau_prix, date_changement))

        conn.commit()
        messagebox.showinfo("Succès", "L'item a été modifié avec succès.")
    except sqlite3.Error as e:
        messagebox.showerror("Erreur de base de données", str(e))
    finally:
        conn.close()

def supprimer_item(item_id):
    """Supprime un item s'il n'est lié à aucune dépense."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Vérifier si l'item est utilisé dans une dépense
        cursor.execute("SELECT COUNT(*) FROM depenses WHERE item_id = ?", (item_id,))
        count = cursor.fetchone()[0]

        if count > 0:
            messagebox.showwarning("Suppression impossible", "Cet item est utilisé dans des dépenses et ne peut pas être supprimé. Vous pouvez l'archiver.")
            return

        # Supprimer de l'historique des prix et ensuite l'item lui-même
        cursor.execute("DELETE FROM historique_prix WHERE item_id = ?", (item_id,))
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        messagebox.showinfo("Succès", "L'item a été supprimé.")
    except sqlite3.Error as e:
        messagebox.showerror("Erreur", f"Erreur lors de la suppression : {e}")
    finally:
        conn.close()

def archiver_item(item_id):
    """Archive un item pour le cacher des listes principales."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE items SET archive = 1 WHERE id = ?", (item_id,))
        conn.commit()
        messagebox.showinfo("Succès", "L'item a été archivé.")
    except sqlite3.Error as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'archivage : {e}")
    finally:
        conn.close()

def dupliquer_item(item_id):
    """Crée une copie d'un item existant avec un nom modifié."""
    details = get_item_details_by_id(item_id)
    if not details:
        messagebox.showerror("Erreur", "Impossible de trouver l'item à dupliquer.")
        return

    # Créer un nouveau nom pour éviter l'unicité
    nouveau_nom = f"{details['nom']} (copie)"

    # Le prix actuel devient le prix initial du nouvel item
    prix_initial = details['prix_actuel']

    ajouter_item(
        nom=nouveau_nom,
        prix_initial=prix_initial,
        conditionnement=details['conditionnement'],
        famille=details['famille'],
        type=details['type'],
        volume=details['volume'],
        unite_volume=details['unite_volume'],
        poids=details['poids'],
        unite_poids=details['unite_poids']
    )

def get_prix_pour_date(item_id, date_depense):
    """
    Récupère le prix d'un item valide à une date donnée.
    Il s'agit du dernier prix enregistré avant ou à la date de la dépense.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # On convertit la date de la dépense en format TEXT pour la comparaison
    date_depense_str = date_depense.strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute("""
        SELECT prix
        FROM historique_prix
        WHERE item_id = ? AND date_changement <= ?
        ORDER BY date_changement DESC
        LIMIT 1
    """, (item_id, date_depense_str))

    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def enregistrer_depense(item_id, quantite, date_depense):
    """Enregistre une dépense après avoir trouvé le prix historique correct."""
    prix_historique = get_prix_pour_date(item_id, date_depense)

    if prix_historique is None:
        messagebox.showerror("Erreur de prix", f"Aucun prix trouvé pour cet item à la date du {date_depense.strftime('%Y-%m-%d')}.")
        return

    conn = get_connection()
    cursor = conn.cursor()
    try:
        date_depense_str = date_depense.strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT INTO depenses (item_id, quantite, prix_unitaire_historique, date_depense)
            VALUES (?, ?, ?, ?)
        """, (item_id, quantite, prix_historique, date_depense_str))
        conn.commit()
        messagebox.showinfo("Succès", "Dépense enregistrée avec succès.")
    except sqlite3.Error as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement : {e}")
    finally:
        conn.close()

def get_tous_les_ajustements():
    """Récupère tous les ajustements journaliers, triés par date."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ajustements_journaliers ORDER BY date_ajustement DESC")
    ajustements = cursor.fetchall()
    conn.close()
    return ajustements

def enregistrer_ajustement(date_ajustement, montant):
    """Enregistre un ajustement pour une date donnée. Met à jour s'il existe déjà."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        date_str = date_ajustement.strftime('%Y-%m-%d')
        # Utilise INSERT OR REPLACE pour simplifier: insère si la date n'existe pas,
        # ou remplace la ligne existante si la date existe déjà.
        cursor.execute("""
            INSERT OR REPLACE INTO ajustements_journaliers (date_ajustement, montant)
            VALUES (?, ?)
        """, (date_str, montant))
        conn.commit()
        messagebox.showinfo("Succès", "Ajustement enregistré avec succès.")
    except sqlite3.Error as e:
        messagebox.showerror("Erreur", f"Erreur lors de l'enregistrement : {e}")
    finally:
        conn.close()

def get_depenses_par_periode(date_debut, date_fin):
    """Récupère toutes les dépenses dans une plage de dates, avec le nom de l'item."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.date_depense, i.nom, d.quantite, d.prix_unitaire_historique, (d.quantite * d.prix_unitaire_historique) as total
        FROM depenses d
        JOIN items i ON d.item_id = i.id
        WHERE d.date_depense BETWEEN ? AND ?
        ORDER BY d.date_depense
    """, (date_debut, date_fin))
    depenses = cursor.fetchall()
    conn.close()
    return depenses

def get_ajustements_par_periode(date_debut, date_fin):
    """Calcule la somme des ajustements (surplus/déficit) sur une période."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(montant)
        FROM ajustements_journaliers
        WHERE date_ajustement BETWEEN ? AND ?
    """, (date_debut, date_fin))
    result = cursor.fetchone()[0]
    conn.close()
    return result if result is not None else 0

def get_depenses_par_periode_dataframe(date_debut, date_fin):
    """Récupère les dépenses sur une période et les retourne comme un DataFrame pandas."""
    conn = get_connection()
    query = """
        SELECT
            d.quantite * d.prix_unitaire_historique as total,
            i.famille,
            i.type
        FROM depenses d
        JOIN items i ON d.item_id = i.id
        WHERE d.date_depense BETWEEN ? AND ?
    """
    df = pd.read_sql_query(query, conn, params=(date_debut, date_fin))
    conn.close()
    return df

def get_historique_prix_item(item_id):
    """Récupère l'historique de prix pour un item spécifique."""
    conn = get_connection()
    query = """
        SELECT date_changement, prix
        FROM historique_prix
        WHERE item_id = ?
        ORDER BY date_changement
    """
    df = pd.read_sql_query(query, conn, params=(item_id,))
    conn.close()
    # Convertir la date en objet datetime pour un meilleur affichage
    df['date_changement'] = pd.to_datetime(df['date_changement'])
    return df

# --- Interface Utilisateur ---

class GestionDepensesUI(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent  # Fenêtre principale
        self.title("Gestion des Items")
        self.geometry("1000x600")

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Création des widgets
        self.creer_widgets()
        self.rafraichir_liste_items()

    def on_closing(self):
        """Affiche à nouveau la fenêtre principale lorsqu'on ferme celle-ci."""
        self.destroy()
        self.parent.deiconify()

    def creer_widgets(self):
        # Notebook pour les onglets
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=10, pady=10)

        # --- Onglet 1: Gestion des Items ---
        items_tab = ttk.Frame(self.notebook)
        self.notebook.add(items_tab, text="Gestion des Items")
        self.creer_widgets_items(items_tab)

        # --- Onglet 2: Enregistrer une Dépense ---
        depenses_tab = ttk.Frame(self.notebook)
        self.notebook.add(depenses_tab, text="Enregistrer une Dépense")
        self.creer_widgets_depenses(depenses_tab)

        # --- Onglet 3: Ajustements Journaliers ---
        ajustements_tab = ttk.Frame(self.notebook)
        self.notebook.add(ajustements_tab, text="Ajustements Journaliers")
        self.creer_widgets_ajustements(ajustements_tab)

        # --- Onglet 4: Consultation & Rapports ---
        rapports_tab = ttk.Frame(self.notebook)
        self.notebook.add(rapports_tab, text="Consultation & Rapports")
        self.creer_widgets_rapports(rapports_tab)

    def creer_widgets_rapports(self, parent_frame):
        """Crée les widgets pour l'onglet de consultation et de rapports."""

        # --- Frame pour les contrôles de période ---
        controles_frame = ttk.LabelFrame(parent_frame, text="Sélectionner une Période", padding="10")
        controles_frame.pack(fill="x", pady=5, padx=5)

        ttk.Label(controles_frame, text="Date de début:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.rapport_date_debut_entry = ttk.Entry(controles_frame)
        self.rapport_date_debut_entry.grid(row=0, column=1, padx=5, pady=5)
        self.rapport_date_debut_entry.insert(0, (datetime.date.today() - datetime.timedelta(days=30)).strftime('%Y-%m-%d'))

        ttk.Label(controles_frame, text="Date de fin:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.rapport_date_fin_entry = ttk.Entry(controles_frame)
        self.rapport_date_fin_entry.grid(row=0, column=3, padx=5, pady=5)
        self.rapport_date_fin_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))

        show_button = ttk.Button(controles_frame, text="Afficher le Rapport", command=self.afficher_rapport)
        show_button.grid(row=0, column=4, padx=10, pady=5)

        # --- Frame pour afficher le total ---
        total_frame = ttk.Frame(parent_frame, padding="10")
        total_frame.pack(fill="x", pady=5, padx=5)

        self.total_depenses_label = ttk.Label(total_frame, text="Total des dépenses: N/A", font=("Helvetica", 12, "bold"))
        self.total_depenses_label.pack(side="left")

        # --- Frame pour la liste des dépenses ---
        list_frame = ttk.LabelFrame(parent_frame, text="Dépenses sur la période", padding="10")
        list_frame.pack(expand=True, fill="both", pady=5, padx=5)

        columns = ("date", "item", "quantite", "prix_unitaire", "total")
        self.rapport_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.rapport_tree.heading("date", text="Date")
        self.rapport_tree.heading("item", text="Item")
        self.rapport_tree.heading("quantite", text="Quantité")
        self.rapport_tree.heading("prix_unitaire", text="Prix Unitaire")
        self.rapport_tree.heading("total", text="Total")
        self.rapport_tree.pack(expand=True, fill="both")

        # --- Frame pour les graphiques ---
        graph_frame = ttk.LabelFrame(parent_frame, text="Visualisation Graphique", padding="10")
        graph_frame.pack(fill="x", pady=5, padx=5)

        ttk.Label(graph_frame, text="Type de Graphe:").grid(row=0, column=0, padx=5, pady=5)
        self.graph_type_combo = ttk.Combobox(graph_frame, state="readonly", values=[
            "Dépenses par Famille",
            "Dépenses par Type",
            "Historique de Prix d'un Item"
        ])
        self.graph_type_combo.grid(row=0, column=1, padx=5, pady=5)
        self.graph_type_combo.bind("<<ComboboxSelected>>", self.on_graph_type_select)

        # Ce combobox n'est visible que pour l'historique de prix
        self.graph_item_combo = ttk.Combobox(graph_frame, state="readonly")

        graph_button = ttk.Button(graph_frame, text="Générer le Graphe", command=self.generer_graphe)
        graph_button.grid(row=0, column=3, padx=10)

        # Espace pour le graphique Matplotlib
        self.canvas_frame = ttk.Frame(parent_frame)
        self.canvas_frame.pack(expand=True, fill="both", pady=5, padx=5)
        self.graph_canvas = None

        # --- Frame pour l'export ---
        export_frame = ttk.LabelFrame(parent_frame, text="Exporter le Rapport", padding="10")
        export_frame.pack(fill="x", pady=10, padx=5)

        export_csv_button = ttk.Button(export_frame, text="Exporter en CSV", command=lambda: self.exporter_donnees('csv'))
        export_csv_button.pack(side="left", padx=5)

        export_excel_button = ttk.Button(export_frame, text="Exporter en Excel", command=lambda: self.exporter_donnees('excel'))
        export_excel_button.pack(side="left", padx=5)

        export_pdf_button = ttk.Button(export_frame, text="Exporter en PDF", command=lambda: self.exporter_donnees('pdf'))
        export_pdf_button.pack(side="left", padx=5)

        export_docx_button = ttk.Button(export_frame, text="Exporter en DOCX", command=lambda: self.exporter_donnees('docx'))
        export_docx_button.pack(side="left", padx=5)

    def exporter_donnees(self, format_export):
        """Exporte les données du rapport affiché dans le format choisi."""
        date_debut_str = self.rapport_date_debut_entry.get()
        date_fin_str = self.rapport_date_fin_entry.get()

        # Récupérer les données
        depenses_raw = get_depenses_par_periode(date_debut_str, date_fin_str)
        if not depenses_raw:
            messagebox.showinfo("Rien à Exporter", "Il n'y a aucune dépense à exporter pour la période sélectionnée.")
            return

        # Créer un DataFrame
        df = pd.DataFrame(depenses_raw, columns=["Date", "Item", "Quantité", "Prix Unitaire", "Total"])

        # Récupérer le texte des totaux
        totals_text = self.total_depenses_label.cget("text")

        # Demander le chemin de sauvegarde
        file_types = {
            'csv': [('CSV file', '*.csv')],
            'excel': [('Excel file', '*.xlsx')],
            'pdf': [('PDF file', '*.pdf')],
            'docx': [('Word Document', '*.docx')]
        }
        filepath = filedialog.asksaveasfilename(
            defaultextension=f".{format_export}",
            filetypes=file_types[format_export],
            title=f"Enregistrer le rapport comme {format_export.upper()}"
        )

        if not filepath:
            return # L'utilisateur a annulé

        try:
            if format_export == 'csv':
                export_utils.export_to_csv(filepath, df)
            elif format_export == 'excel':
                export_utils.export_to_excel(filepath, df)
            elif format_export == 'pdf':
                export_utils.export_to_pdf(filepath, df, "Rapport de Dépenses", totals_text)
            elif format_export == 'docx':
                export_utils.export_to_docx(filepath, df, "Rapport de Dépenses", totals_text)

            messagebox.showinfo("Succès", f"Rapport exporté avec succès vers {filepath}")
        except Exception as e:
            messagebox.showerror("Erreur d'Exportation", f"Une erreur est survenue : {e}")


    def on_graph_type_select(self, event=None):
        """Affiche ou cache le combobox de sélection d'item."""
        if self.graph_type_combo.get() == "Historique de Prix d'un Item":
            self.graph_item_combo.grid(row=0, column=2, padx=5, pady=5)
            # Charger les items
            items = get_tous_les_items()
            item_map = {item[1]: item[0] for item in items}
            self.graph_item_combo['values'] = list(item_map.keys())
        else:
            self.graph_item_combo.grid_remove()

    def generer_graphe(self):
        """Génère et affiche le graphique sélectionné."""
        graph_type = self.graph_type_combo.get()
        if not graph_type:
            messagebox.showwarning("Sélection requise", "Veuillez choisir un type de graphe.")
            return

        # Nettoyer le canvas précédent
        if self.graph_canvas:
            self.graph_canvas.get_tk_widget().destroy()

        date_debut = self.rapport_date_debut_entry.get()
        date_fin = self.rapport_date_fin_entry.get()

        if graph_type in ["Dépenses par Famille", "Dépenses par Type"]:
            df = get_depenses_par_periode_dataframe(date_debut, date_fin)
            if df.empty:
                messagebox.showinfo("Aucune donnée", "Aucune dépense trouvée pour cette période.")
                return

            group_by_col = 'famille' if graph_type == "Dépenses par Famille" else 'type'
            self.creer_graphe_camembert(df, group_by_col, f"Répartition des dépenses par {group_by_col}")

        elif graph_type == "Historique de Prix d'un Item":
            nom_item = self.graph_item_combo.get()
            if not nom_item:
                messagebox.showwarning("Sélection requise", "Veuillez choisir un item.")
                return

            # Re-créer le map pour trouver l'ID (ou le stocker dans self)
            items = get_tous_les_items()
            item_map = {item[1]: item[0] for item in items}
            item_id = item_map.get(nom_item)

            df_prix = get_historique_prix_item(item_id)
            if df_prix.empty:
                messagebox.showinfo("Aucune donnée", "Aucun historique de prix pour cet item.")
                return
            self.creer_graphe_historique_prix(df_prix, nom_item)

    def creer_graphe_camembert(self, df, group_by_column, title):
        """Crée et affiche un graphique en camembert."""
        data = df.groupby(group_by_column)['total'].sum()

        fig = Figure(figsize=(6, 4), dpi=100)
        ax = fig.add_subplot(111)
        data.plot(kind='pie', ax=ax, autopct='%1.1f%%', startangle=90)
        ax.set_ylabel('') # Cache le label de l'axe y
        ax.set_title(title)

        self.embed_matplotlib_figure(fig)

    def creer_graphe_historique_prix(self, df, item_name):
        """Crée et affiche un graphique de l'historique des prix."""
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(df['date_changement'], df['prix'], marker='o', linestyle='-')
        ax.set_title(f"Historique du prix pour : {item_name}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Prix (MAD)")
        ax.grid(True)
        fig.autofmt_xdate() # Améliore l'affichage des dates

        self.embed_matplotlib_figure(fig)

    def embed_matplotlib_figure(self, fig):
        """Intègre une figure Matplotlib dans le canvas Tkinter."""
        self.graph_canvas = FigureCanvasTkAgg(fig, master=self.canvas_frame)
        self.graph_canvas.draw()
        self.graph_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def afficher_rapport(self):
        """Affiche le rapport de dépenses pour la période sélectionnée."""
        date_debut_str = self.rapport_date_debut_entry.get()
        date_fin_str = self.rapport_date_fin_entry.get()

        try:
            # Valider les dates
            datetime.datetime.strptime(date_debut_str, '%Y-%m-%d')
            datetime.datetime.strptime(date_fin_str, '%Y-%m-%d')
        except ValueError:
            messagebox.showerror("Format de Date Invalide", "Veuillez utiliser le format AAAA-MM-JJ.")
            return

        # Vider la vue précédente
        for row in self.rapport_tree.get_children():
            self.rapport_tree.delete(row)

        # Récupérer les données
        depenses = get_depenses_par_periode(date_debut_str, date_fin_str)
        total_ajustements = get_ajustements_par_periode(date_debut_str, date_fin_str)

        total_depenses_brut = 0
        for depense in depenses:
            # depense = (date, nom, qte, prix, total)
            date, nom, qte, prix, total = depense
            prix_formate = f"{prix:.2f} MAD"
            total_formate = f"{total:.2f} MAD"
            self.rapport_tree.insert("", tk.END, values=(date, nom, qte, prix_formate, total_formate))
            total_depenses_brut += total

        # Calculer le total final
        total_final = total_depenses_brut + total_ajustements

        # Mettre à jour le label
        signe_ajustement = "+" if total_ajustements >= 0 else ""
        texte_total = (f"Total des dépenses: {total_depenses_brut:.2f} MAD | "
                       f"Ajustements: {signe_ajustement}{total_ajustements:.2f} MAD | "
                       f"Total Final: {total_final:.2f} MAD")
        self.total_depenses_label.config(text=texte_total)


    def creer_widgets_ajustements(self, parent_frame):
        """Crée les widgets pour l'onglet des ajustements journaliers."""
        # --- Frame pour le formulaire ---
        form_frame = ttk.LabelFrame(parent_frame, text="Ajouter un Ajustement", padding="10")
        form_frame.pack(fill="x", pady=5, padx=5)

        ttk.Label(form_frame, text="Date (AAAA-MM-JJ):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ajustement_date_entry = ttk.Entry(form_frame)
        self.ajustement_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.ajustement_date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))

        ttk.Label(form_frame, text="Montant (Surplus > 0, Déficit < 0):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ajustement_montant_entry = ttk.Entry(form_frame)
        self.ajustement_montant_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        save_button = ttk.Button(form_frame, text="Enregistrer l'Ajustement", command=self.enregistrer_nouvel_ajustement)
        save_button.grid(row=2, column=0, columnspan=2, pady=10)

        # --- Frame pour la liste des ajustements ---
        list_frame = ttk.LabelFrame(parent_frame, text="Historique des Ajustements", padding="10")
        list_frame.pack(expand=True, fill="both", pady=5, padx=5)

        columns = ("date", "montant")
        self.ajustements_tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.ajustements_tree.heading("date", text="Date")
        self.ajustements_tree.heading("montant", text="Montant")
        self.ajustements_tree.pack(expand=True, fill="both")

        self.rafraichir_liste_ajustements()

    def rafraichir_liste_ajustements(self):
        """Recharge la liste des ajustements depuis la DB."""
        for row in self.ajustements_tree.get_children():
            self.ajustements_tree.delete(row)

        ajustements = get_tous_les_ajustements()
        for aj in ajustements:
            montant_formate = f"{aj[2]:.2f} MAD"
            self.ajustements_tree.insert("", tk.END, values=(aj[1], montant_formate))

    def enregistrer_nouvel_ajustement(self):
        """Enregistre un nouvel ajustement journalier."""
        date_str = self.ajustement_date_entry.get()
        montant_str = self.ajustement_montant_entry.get()

        if not date_str or not montant_str:
            messagebox.showwarning("Champs requis", "La date et le montant sont obligatoires.")
            return

        try:
            date_ajustement = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            montant = float(montant_str)
        except ValueError:
            messagebox.showerror("Erreur de format", "Veuillez vérifier la date ou le montant.")
            return

        enregistrer_ajustement(date_ajustement, montant)
        self.rafraichir_liste_ajustements()
        self.ajustement_montant_entry.delete(0, tk.END)

    def creer_widgets_depenses(self, parent_frame):
        """Crée les widgets pour l'onglet d'enregistrement des dépenses."""

        # --- Frame pour l'enregistrement ---
        record_frame = ttk.LabelFrame(parent_frame, text="Nouvelle Dépense", padding="10")
        record_frame.pack(fill="x", pady=5, padx=5)

        # Sélection de l'item
        ttk.Label(record_frame, text="Item:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.depense_item_combo = ttk.Combobox(record_frame, state="readonly")
        self.depense_item_combo.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.depense_item_combo.bind("<<ComboboxSelected>>", self.on_depense_item_select)

        # Champ pour le prix (lecture seule)
        ttk.Label(record_frame, text="Prix (auto):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.depense_prix_label = ttk.Label(record_frame, text="N/A")
        self.depense_prix_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        # Quantité
        ttk.Label(record_frame, text="Quantité:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.depense_quantite_entry = ttk.Entry(record_frame)
        self.depense_quantite_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Date de la dépense
        ttk.Label(record_frame, text="Date (AAAA-MM-JJ):").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.depense_date_entry = ttk.Entry(record_frame)
        self.depense_date_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        self.depense_date_entry.insert(0, datetime.date.today().strftime('%Y-%m-%d'))
        self.depense_date_entry.bind("<FocusOut>", self.on_date_change)


        # Bouton d'enregistrement
        record_button = ttk.Button(record_frame, text="Enregistrer la Dépense", command=self.enregistrer_nouvelle_depense)
        record_button.grid(row=4, column=0, columnspan=2, pady=10)

        # Charger les items dans le combobox
        self.charger_items_combobox()

    def charger_items_combobox(self):
        """Charge les noms des items dans le combobox de dépenses."""
        items = get_tous_les_items() # id, nom, ...
        self.item_map = {item[1]: item[0] for item in items} # Map nom -> id
        self.depense_item_combo['values'] = list(self.item_map.keys())

    def on_depense_item_select(self, event=None):
        """Appelé quand un item est sélectionné pour une dépense."""
        self.on_date_change() # Le prix dépend de l'item ET de la date

    def on_date_change(self, event=None):
        """Met à jour le prix affiché quand la date ou l'item change."""
        nom_item = self.depense_item_combo.get()
        date_str = self.depense_date_entry.get()

        if not nom_item or not date_str:
            self.depense_prix_label.config(text="N/A")
            return

        try:
            date_depense = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            item_id = self.item_map[nom_item]
            prix = get_prix_pour_date(item_id, date_depense)
            if prix is not None:
                self.depense_prix_label.config(text=f"{prix:.2f} MAD")
            else:
                self.depense_prix_label.config(text="Prix non trouvé")
        except (ValueError, KeyError):
            self.depense_prix_label.config(text="Date/Item invalide")

    def enregistrer_nouvelle_depense(self):
        """Enregistre la nouvelle dépense dans la base de données."""
        nom_item = self.depense_item_combo.get()
        quantite_str = self.depense_quantite_entry.get()
        date_str = self.depense_date_entry.get()

        if not nom_item or not quantite_str or not date_str:
            messagebox.showwarning("Champs requis", "Tous les champs sont obligatoires.")
            return

        try:
            item_id = self.item_map[nom_item]
            quantite = float(quantite_str)
            date_depense = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, KeyError):
            messagebox.showerror("Erreur de format", "Veuillez vérifier les valeurs saisies.")
            return

        enregistrer_depense(item_id, quantite, date_depense)

        # Vider les champs après enregistrement
        self.depense_quantite_entry.delete(0, tk.END)
        self.depense_item_combo.set('')
        self.depense_prix_label.config(text="N/A")


    def creer_widgets_items(self, parent_frame):
        """Crée les widgets pour l'onglet de gestion des items."""

        # --- Frame pour le formulaire d'ajout ---
        form_frame = ttk.LabelFrame(parent_frame, text="Ajouter/Modifier un Item", padding="10")
        form_frame.pack(fill="x", pady=5, padx=5)

        # Labels et Entrées
        labels = ["Nom:", "Prix Initial:", "Conditionnement:", "Famille:", "Type:", "Volume:", "Unité Vol.:", "Poids:", "Unité Poids:"]
        self.entries = {}
        for i, label_text in enumerate(labels):
            label = ttk.Label(form_frame, text=label_text)
            label.grid(row=i, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(form_frame, width=40)
            entry.grid(row=i, column=1, padx=5, pady=5, sticky="ew")
            self.entries[label_text.replace(":", "").replace(" ", "_").lower()] = entry

        # --- Frame pour les boutons d'action ---
        action_frame = ttk.Frame(form_frame)
        action_frame.grid(row=len(labels), column=0, columnspan=2, pady=10)

        add_button = ttk.Button(action_frame, text="Ajouter l'Item", command=self.ajouter_nouvel_item)
        add_button.pack(side="left", padx=5)

        self.update_button = ttk.Button(action_frame, text="Modifier l'Item", command=self.modifier_item_selectionne, state="disabled")
        self.update_button.pack(side="left", padx=5)

        self.delete_button = ttk.Button(action_frame, text="Supprimer", command=self.supprimer_item_selectionne, state="disabled")
        self.delete_button.pack(side="left", padx=5)

        self.archive_button = ttk.Button(action_frame, text="Archiver", command=self.archiver_item_selectionne, state="disabled")
        self.archive_button.pack(side="left", padx=5)

        self.duplicate_button = ttk.Button(action_frame, text="Dupliquer", command=self.dupliquer_item_selectionne, state="disabled")
        self.duplicate_button.pack(side="left", padx=5)

        clear_button = ttk.Button(action_frame, text="Vider les champs", command=self.vider_formulaire)
        clear_button.pack(side="left", padx=5)


        # --- Frame pour la liste des items ---
        list_frame = ttk.LabelFrame(parent_frame, text="Liste des Items", padding="10")
        list_frame.pack(expand=True, fill="both", pady=5, padx=5)

        # Treeview pour afficher les items
        columns = ("id", "nom", "prix_actuel", "conditionnement", "famille", "type")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")

        # Définir les en-têtes
        self.tree.heading("id", text="ID")
        self.tree.heading("nom", text="Nom")
        self.tree.heading("prix_actuel", text="Prix Actuel")
        self.tree.heading("conditionnement", text="Conditionnement")
        self.tree.heading("famille", text="Famille")
        self.tree.heading("type", text="Type")

        # Ajuster la largeur des colonnes
        self.tree.column("id", width=50, stretch=tk.NO)
        self.tree.column("nom", width=200)
        self.tree.column("prix_actuel", width=100)

        self.tree.pack(expand=True, fill="both", side="left")

        # Scrollbar pour le Treeview
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Lier l'événement de sélection
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)

    def on_item_select(self, event):
        """Gère la sélection d'un item dans la liste."""
        selected_items = self.tree.selection()
        if not selected_items:
            return

        selected_item = selected_items[0]
        item_id = self.tree.item(selected_item)["values"][0]

        # Récupérer les détails complets de l'item
        details = get_item_details_by_id(item_id)
        if not details:
            messagebox.showerror("Erreur", "Impossible de récupérer les détails de l'item.")
            return

        # Vider le formulaire avant de le remplir
        self.vider_formulaire(clear_selection=False)

        # Remplir le formulaire
        self.entries['nom'].insert(0, details.get('nom', ''))
        # Le prix affiché est le prix actuel pour la modification
        self.entries['prix_initial'].insert(0, details.get('prix_actuel', ''))
        self.entries['conditionnement'].insert(0, details.get('conditionnement', ''))
        self.entries['famille'].insert(0, details.get('famille', ''))
        self.entries['type'].insert(0, details.get('type', ''))
        self.entries['volume'].insert(0, details.get('volume', '') or '')
        self.entries['unité_vol.'].insert(0, details.get('unite_volume', ''))
        self.entries['poids'].insert(0, details.get('poids', '') or '')
        self.entries['unité_poids'].insert(0, details.get('unite_poids', ''))

        # Activer les boutons d'action
        self.update_button.config(state="normal")
        self.delete_button.config(state="normal")
        self.archive_button.config(state="normal")
        self.duplicate_button.config(state="normal")


    def rafraichir_liste_items(self):
        """Nettoie et recharge la liste des items depuis la DB."""
        # Vider le treeview
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Récupérer les données et les insérer
        items = get_tous_les_items()
        for item in items:
            prix_formate = f"{item[5]:.2f} MAD" if item[5] is not None else "N/A"
            self.tree.insert("", tk.END, values=(item[0], item[1], prix_formate, item[2], item[3], item[4]))

        # Après le rafraîchissement, vider le formulaire et désactiver les boutons
        self.vider_formulaire()

    def vider_formulaire(self, clear_selection=True):
        """Vide tous les champs du formulaire et réinitialise les boutons."""
        for entry in self.entries.values():
            entry.delete(0, tk.END)

        self.update_button.config(state="disabled")
        self.delete_button.config(state="disabled")
        self.archive_button.config(state="disabled")
        self.duplicate_button.config(state="disabled")

        if clear_selection and self.tree.selection():
            self.tree.selection_remove(self.tree.selection()[0])

    def ajouter_nouvel_item(self):
        """Récupère les données du formulaire et appelle la fonction de la DB."""
        nom = self.entries['nom'].get()
        prix_str = self.entries['prix_initial'].get()

        if not nom or not prix_str:
            messagebox.showwarning("Champs requis", "Le nom et le prix initial sont obligatoires.")
            return

        try:
            prix_initial = float(prix_str)
        except ValueError:
            messagebox.showerror("Erreur de format", "Le prix doit être un nombre.")
            return

        ajouter_item(
            nom=nom,
            prix_initial=prix_initial,
            conditionnement=self.entries['conditionnement'].get(),
            famille=self.entries['famille'].get(),
            type=self.entries['type'].get(),
            volume=self.entries['volume'].get() or None,
            unite_volume=self.entries['unité_vol.'].get(),
            poids=self.entries['poids'].get() or None,
            unite_poids=self.entries['unité_poids'].get()
        )

        self.rafraichir_liste_items()

    def modifier_item_selectionne(self):
        """Modifie l'item actuellement sélectionné."""
        selected_item_id = self.tree.item(self.tree.selection()[0])["values"][0]

        nom = self.entries['nom'].get()
        prix_str = self.entries['prix_initial'].get()

        if not nom or not prix_str:
            messagebox.showwarning("Champs requis", "Le nom et le prix sont obligatoires.")
            return

        try:
            nouveau_prix = float(prix_str)
        except ValueError:
            messagebox.showerror("Erreur de format", "Le prix doit être un nombre.")
            return

        modifier_item(
            item_id=selected_item_id,
            nom=nom,
            nouveau_prix=nouveau_prix,
            conditionnement=self.entries['conditionnement'].get(),
            famille=self.entries['famille'].get(),
            type=self.entries['type'].get(),
            volume=self.entries['volume'].get() or None,
            unite_volume=self.entries['unité_vol.'].get(),
            poids=self.entries['poids'].get() or None,
            unite_poids=self.entries['unité_poids'].get()
        )
        self.rafraichir_liste_items()

    def supprimer_item_selectionne(self):
        item_id = self.tree.item(self.tree.selection()[0])["values"][0]
        nom = self.tree.item(self.tree.selection()[0])["values"][1]
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer l'item '{nom}' ?"):
            supprimer_item(item_id)
            self.rafraichir_liste_items()

    def archiver_item_selectionne(self):
        item_id = self.tree.item(self.tree.selection()[0])["values"][0]
        nom = self.tree.item(self.tree.selection()[0])["values"][1]
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir archiver l'item '{nom}' ?"):
            archiver_item(item_id)
            self.rafraichir_liste_items()

    def dupliquer_item_selectionne(self):
        item_id = self.tree.item(self.tree.selection()[0])["values"][0]
        nom = self.tree.item(self.tree.selection()[0])["values"][1]
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir dupliquer l'item '{nom}' ?"):
            dupliquer_item(item_id)
            self.rafraichir_liste_items()

if __name__ == '__main__':
    # Ce bloc est exécuté seulement si le script est appelé directement
    # Utile pour initialiser la base de données manuellement au début
    initialiser_db()