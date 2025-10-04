// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod database;
mod models;

use models::{Citation, Dissertation, Livre, LivreAvecProgres, EntreeJournal, DashboardSummary};
use rusqlite::{params, Connection, Result, OptionalExtension};
use rand::Rng;
use chrono::Utc;

#[tauri::command]
fn get_citation_du_jour() -> Result<Citation, String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM citations", [], |row| row.get(0)).map_err(|e| e.to_string())?;
    if count == 0 { return Err("Aucune citation trouvée.".into()); }
    let random_index = rand::thread_rng().gen_range(0..count);
    let citation = conn.query_row(
        "SELECT id, texte, langue FROM citations LIMIT 1 OFFSET ?",
        params![random_index],
        |row| Ok(Citation { id: row.get(0)?, texte: row.get(1)?, langue: row.get(2)? })
    ).map_err(|e| e.to_string())?;
    Ok(citation)
}

#[tauri::command]
fn sauvegarder_dissertation(citation_id: i64, texte_fr: String, texte_en: String) -> Result<(), String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    let date_soumission = Utc::now().to_rfc3339();
    conn.execute(
        "INSERT INTO dissertations (citation_id, texte_fr, texte_en, date_soumission) VALUES (?1, ?2, ?3, ?4)",
        params![citation_id, texte_fr, texte_en, date_soumission],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_historique_dissertations() -> Result<Vec<Dissertation>, String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    let mut stmt = conn.prepare(
        "SELECT d.id, c.texte, d.texte_fr, d.texte_en, d.date_soumission
         FROM dissertations d
         JOIN citations c ON d.citation_id = c.id
         ORDER BY d.date_soumission DESC"
    ).map_err(|e| e.to_string())?;

    let dissertations_iter = stmt.query_map([], |row| {
        Ok(Dissertation {
            id: row.get(0)?,
            texte_citation: row.get(1)?,
            texte_fr: row.get(2)?,
            texte_en: row.get(3)?,
            date_soumission: row.get(4)?,
        })
    }).map_err(|e| e.to_string())?;

    let mut dissertations = Vec::new();
    for dissertation in dissertations_iter {
        dissertations.push(dissertation.map_err(|e| e.to_string())?);
    }

    Ok(dissertations)
}

#[tauri::command]
fn ajouter_livre(titre: String, auteur: Option<String>, pages_total: Option<i64>) -> Result<(), String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO livres (titre, auteur, pages_total) VALUES (?1, ?2, ?3)",
        params![titre, auteur, pages_total],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_livres() -> Result<Vec<LivreAvecProgres>, String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    let mut stmt = conn.prepare(
        "SELECT id, titre, auteur, pages_total, statut FROM livres"
    ).map_err(|e| e.to_string())?;

    let livres_iter = stmt.query_map([], |row| {
        Ok(Livre {
            id: row.get(0)?,
            titre: row.get(1)?,
            auteur: row.get(2)?,
            pages_total: row.get(3)?,
            statut: row.get(4)?,
        })
    }).map_err(|e| e.to_string())?;

    let mut livres_avec_progres = Vec::new();
    for livre_result in livres_iter {
        let livre = livre_result.map_err(|e| e.to_string())?;
        let pages_lues: i64 = conn.query_row(
            "SELECT COALESCE(SUM(pages_lues), 0) FROM sessions_lecture WHERE livre_id = ?1",
            params![livre.id],
            |row| row.get(0)
        ).unwrap_or(0);

        livres_avec_progres.push(LivreAvecProgres {
            livre,
            pages_lues,
        });
    }

    Ok(livres_avec_progres)
}

#[tauri::command]
fn enregistrer_session(livre_id: i64, pages_lues: i64) -> Result<(), String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    let date_session = Utc::now().to_rfc3339();
    conn.execute(
        "INSERT INTO sessions_lecture (livre_id, pages_lues, date_session) VALUES (?1, ?2, ?3)",
        params![livre_id, pages_lues, date_session],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn changer_statut_livre(livre_id: i64, statut: String) -> Result<(), String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    conn.execute(
        "UPDATE livres SET statut = ?1 WHERE id = ?2",
        params![statut, livre_id],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_entree_journal(date: String) -> Result<Option<EntreeJournal>, String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    let entree = conn.query_row(
        "SELECT contenu, date_entree FROM journal WHERE date_entree = ?1",
        params![date],
        |row| Ok(EntreeJournal {
            contenu: row.get(0)?,
            date_entree: row.get(1)?,
        })
    ).optional().map_err(|e| e.to_string())?;
    Ok(entree)
}

#[tauri::command]
fn sauvegarder_entree_journal(date: String, contenu: String) -> Result<(), String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;
    conn.execute(
        "INSERT INTO journal (date_entree, contenu) VALUES (?1, ?2)
         ON CONFLICT(date_entree) DO UPDATE SET contenu=excluded.contenu",
        params![date, contenu],
    ).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
fn get_dashboard_summary() -> Result<DashboardSummary, String> {
    let conn = Connection::open("./life_manager.db").map_err(|e| e.to_string())?;

    // 1. Get citation
    let count: i64 = conn.query_row("SELECT COUNT(*) FROM citations", [], |row| row.get(0)).unwrap_or(0);
    let citation_du_jour = if count > 0 {
        let random_index = rand::thread_rng().gen_range(0..count);
        conn.query_row(
            "SELECT id, texte, langue FROM citations LIMIT 1 OFFSET ?",
            params![random_index],
            |row| Ok(Citation { id: row.get(0)?, texte: row.get(1)?, langue: row.get(2)? })
        ).optional().map_err(|e| e.to_string())?
    } else {
        None
    };

    // 2. Get books in progress
    let livres_en_cours: i64 = conn.query_row(
        "SELECT COUNT(*) FROM livres WHERE statut = 'en_cours'",
        [],
        |row| row.get(0)
    ).unwrap_or(0);

    // 3. Check for today's journal entry
    let today_str = Utc::now().format("%Y-%m-%d").to_string();
    let entree_journal_aujourdhui: i64 = conn.query_row(
        "SELECT COUNT(*) FROM journal WHERE date_entree = ?1",
        params![today_str],
        |row| row.get(0)
    ).unwrap_or(0);

    Ok(DashboardSummary {
        citation_du_jour,
        livres_en_cours,
        entree_journal_aujourdhui: entree_journal_aujourdhui > 0,
    })
}

fn main() {
    if let Err(e) = database::initialize_database() {
        eprintln!("Erreur lors de l'initialisation de la base de données : {}", e);
    }

    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_citation_du_jour,
            sauvegarder_dissertation,
            get_historique_dissertations,
            ajouter_livre,
            get_livres,
            enregistrer_session,
            changer_statut_livre,
            get_entree_journal,
            sauvegarder_entree_journal,
            get_dashboard_summary
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}