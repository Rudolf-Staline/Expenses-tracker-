use serde::{Serialize, Deserialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct Citation {
    pub id: i64,
    pub texte: String,
    pub langue: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Dissertation {
    pub id: i64,
    pub texte_citation: String,
    pub texte_fr: String,
    pub texte_en: String,
    pub date_soumission: String,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Livre {
    pub id: i64,
    pub titre: String,
    pub auteur: Option<String>,
    pub pages_total: Option<i64>,
    pub statut: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct LivreAvecProgres {
    #[serde(flatten)]
    pub livre: Livre,
    pub pages_lues: i64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct EntreeJournal {
    pub contenu: String,
    pub date_entree: String,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DashboardSummary {
    pub citation_du_jour: Option<Citation>,
    pub livres_en_cours: i64,
    pub entree_journal_aujourdhui: bool,
}