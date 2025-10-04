use rusqlite::{Connection, Result};

pub fn initialize_database() -> Result<()> {
    let path = "./life_manager.db";
    let conn = Connection::open(path)?;

    // Table pour stocker les citations
    conn.execute(
        "CREATE TABLE IF NOT EXISTS citations (
            id INTEGER PRIMARY KEY,
            texte TEXT NOT NULL UNIQUE,
            langue TEXT NOT NULL
        )",
        [],
    )?;

    // Table pour stocker les dissertations de l'utilisateur
    conn.execute(
        "CREATE TABLE IF NOT EXISTS dissertations (
            id INTEGER PRIMARY KEY,
            citation_id INTEGER NOT NULL,
            texte_fr TEXT,
            texte_en TEXT,
            date_soumission TEXT NOT NULL,
            FOREIGN KEY (citation_id) REFERENCES citations (id)
        )",
        [],
    )?;

    // Tables pour le module de lecture
    conn.execute(
        "CREATE TABLE IF NOT EXISTS livres (
            id INTEGER PRIMARY KEY,
            titre TEXT NOT NULL,
            auteur TEXT,
            pages_total INTEGER,
            statut TEXT NOT NULL DEFAULT 'a_lire' -- a_lire, en_cours, termine
        )",
        [],
    )?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions_lecture (
            id INTEGER PRIMARY KEY,
            livre_id INTEGER NOT NULL,
            pages_lues INTEGER NOT NULL,
            date_session TEXT NOT NULL,
            FOREIGN KEY (livre_id) REFERENCES livres (id)
        )",
        [],
    )?;

    // Table pour le journal intime
    conn.execute(
        "CREATE TABLE IF NOT EXISTS journal (
            id INTEGER PRIMARY KEY,
            contenu TEXT NOT NULL,
            date_entree TEXT NOT NULL UNIQUE
        )",
        [],
    )?;

    // Peupler la base de données avec des citations initiales si elle est vide
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM citations", [], |row| row.get(0))?;
    if count == 0 {
        let initial_citations = vec![
            ("Le seul moyen de faire du bon travail est d'aimer ce que vous faites.", "fr"),
            ("The only way to do great work is to love what you do.", "en"),
            ("La vie, c'est ce qui arrive quand on est occupé à faire d'autres projets.", "fr"),
            ("Life is what happens when you're busy making other plans.", "en"),
            ("Le succès, c'est d'aller d'échec en échec sans perdre son enthousiasme.", "fr"),
            ("Success is stumbling from failure to failure with no loss of enthusiasm.", "en"),
        ];

        for (texte, langue) in initial_citations {
            conn.execute(
                "INSERT INTO citations (texte, langue) VALUES (?1, ?2)",
                &[texte, langue],
            )?;
        }
    }

    Ok(())
}