import { invoke } from "@tauri-apps/api/tauri";
import "./styles.css";

// --- Data Interfaces ---
interface Citation {
  id: number;
  texte: string;
  langue: string;
}

interface Dissertation {
  id: number;
  texte_citation: string;
  texte_fr: string;
  texte_en: string;
  date_soumission: string;
}

interface Livre {
    id: number;
    titre: string;
    auteur: string | null;
    pages_total: number | null;
    statut: string;
}

interface LivreAvecProgres {
    livre: Livre;
    pages_lues: number;
}

interface EntreeJournal {
    contenu: string;
    date_entree: string;
}

interface DashboardSummary {
    citation_du_jour: Citation | null;
    livres_en_cours: number;
    entree_journal_aujourdhui: boolean;
}


// --- App Navigation ---
const root = document.querySelector<HTMLDivElement>('#root')!;

async function renderMainMenu() {
    root.innerHTML = `
        <div class="container">
            <h1>Tableau de Bord</h1>
            <div id="dashboard-summary">Chargement...</div>
            <div class="main-menu">
                <button id="lang-module-btn">Module de Langues</button>
                <button id="read-module-btn">Module de Lecture</button>
                <button id="journal-module-btn">Journal Intime</button>
            </div>
        </div>
    `;

    try {
        const summary = await invoke<DashboardSummary>("get_dashboard_summary");
        const summaryEl = document.getElementById('dashboard-summary')!;

        const citationHtml = summary.citation_du_jour
            ? `<em>"${summary.citation_du_jour.texte}"</em>`
            : "Pas de citation aujourd'hui.";

        const journalStatus = summary.entree_journal_aujourdhui
            ? '✅ Entrée du journal complétée'
            : "❌ Pensez à votre journal aujourd'hui";

        summaryEl.innerHTML = `
            <div class="summary-item"><strong>Citation :</strong> ${citationHtml}</div>
            <div class="summary-item"><strong>Livres en cours :</strong> ${summary.livres_en_cours}</div>
            <div class="summary-item"><strong>Journal :</strong> ${journalStatus}</div>
        `;
    } catch (e) {
        document.getElementById('dashboard-summary')!.innerHTML = `<div class="error">Erreur de chargement du tableau de bord.</div>`;
    }

    document.getElementById('lang-module-btn')?.addEventListener('click', renderLanguageModule);
    document.getElementById('read-module-btn')?.addEventListener('click', renderReadingModule);
    document.getElementById('journal-module-btn')?.addEventListener('click', renderJournalModule);
}

// --- Language Module ---
async function renderHistoryView() {
    try {
        const history = await invoke<Dissertation[]>("get_historique_dissertations");
        let historyHtml = `
          <div class="container">
            <h1>Historique des Dissertations</h1>
            <button id="back-btn">Retour</button>
            <div class="history-list">
        `;
        if (history.length === 0) {
            historyHtml += '<p>Aucun historique.</p>';
        } else {
            history.forEach(d => {
                historyHtml += `
                  <div class="history-item">
                    <h4>Citation : <em>"${d.texte_citation}"</em></h4>
                    <small>Soumis le : ${new Date(d.date_soumission).toLocaleString()}</small>
                    <details><summary>Voir FR</summary><p>${d.texte_fr || "N/A"}</p></details>
                    <details><summary>Voir EN</summary><p>${d.texte_en || "N/A"}</p></details>
                  </div>
                `;
            });
        }
        historyHtml += '</div></div>';
        root.innerHTML = historyHtml;
        document.getElementById('back-btn')?.addEventListener('click', renderLanguageModule);
    } catch (e) {
        root.innerHTML = `<div class="error">Erreur: ${e}</div>`;
    }
}

async function renderLanguageModule() {
  try {
    const citation = await invoke<Citation>("get_citation_du_jour");
    root.innerHTML = `
      <div class="container">
        <div class="header">
            <button id="home-btn">Accueil</button>
            <h1>Citation du Jour</h1>
            <button id="history-btn">Voir l'historique</button>
        </div>
        <blockquote class="quote">
          <p>"${citation.texte}"</p>
          <footer class="lang">Langue: ${citation.langue.toUpperCase()}</footer>
        </blockquote>
        <div class="dissertation-area">
          <textarea id="dissertation-fr" placeholder="Votre dissertation..."></textarea>
          <textarea id="dissertation-en" placeholder="Your essay..."></textarea>
        </div>
        <button id="submit-btn">Soumettre</button>
      </div>
    `;

    document.getElementById('home-btn')?.addEventListener('click', renderMainMenu);
    document.getElementById('history-btn')?.addEventListener('click', renderHistoryView);
    document.getElementById('submit-btn')?.addEventListener('click', async () => {
        const btn = document.getElementById('submit-btn') as HTMLButtonElement;
        const frEl = document.getElementById('dissertation-fr') as HTMLTextAreaElement;
        const enEl = document.getElementById('dissertation-en') as HTMLTextAreaElement;
        try {
            await invoke('sauvegarder_dissertation', { citationId: citation.id, texteFr: frEl.value, texteEn: enEl.value });
            alert('Sauvegardé !');
            frEl.value = ''; enEl.value = '';
            btn.textContent = 'Soumis !'; btn.disabled = true;
        } catch (e) { alert(`Erreur: ${e}`); }
    });
  } catch (e) { root.innerHTML = `<div class="error">Erreur: ${e}</div>`; }
}

// --- Reading Module ---
async function renderReadingModule() {
    root.innerHTML = `
        <div class="container">
            <div class="header">
                <button id="home-btn">Accueil</button>
                <h1>Module de Lecture</h1>
            </div>
            <div class="add-book-form">
                <input id="titre-input" placeholder="Titre du livre" />
                <input id="auteur-input" placeholder="Auteur" />
                <input id="pages-input" type="number" placeholder="Pages" />
                <button id="add-book-btn">Ajouter Livre</button>
            </div>
            <div class="library">
                <div class="shelf"><h2>À Lire</h2><div id="a_lire"></div></div>
                <div class="shelf"><h2>En Cours</h2><div id="en_cours"></div></div>
                <div class="shelf"><h2>Terminés</h2><div id="termine"></div></div>
            </div>
        </div>
    `;
    document.getElementById('home-btn')?.addEventListener('click', renderMainMenu);
    document.getElementById('add-book-btn')?.addEventListener('click', async () => {
        const titre = (document.getElementById('titre-input') as HTMLInputElement).value;
        const auteur = (document.getElementById('auteur-input') as HTMLInputElement).value;
        const pages = (document.getElementById('pages-input') as HTMLInputElement).value;
        if (!titre) { alert("Le titre est requis."); return; }
        try {
            await invoke('ajouter_livre', { titre, auteur, pagesTotal: Number(pages) || null });
            loadBooks(); // Recharger la liste
        } catch(e) { alert(`Erreur: ${e}`); }
    });
    loadBooks();
}

async function loadBooks() {
    const shelves: { [key: string]: HTMLElement | null } = {
        'a_lire': document.getElementById('a_lire'),
        'en_cours': document.getElementById('en_cours'),
        'termine': document.getElementById('termine'),
    };
    Object.values(shelves).forEach(s => s ? s.innerHTML = '' : null);

    const livres = await invoke<LivreAvecProgres[]>("get_livres");
    livres.forEach(item => {
        const shelf = shelves[item.livre.statut];
        if (!shelf) return;

        const progress = item.livre.pages_total ? (item.pages_lues / item.livre.pages_total) * 100 : 0;

        const bookEl = document.createElement('div');
        bookEl.className = 'book';

        let actionsHtml = '';
        if (item.livre.statut === 'a_lire') {
            actionsHtml = `<button class="start-reading-btn">Commencer la lecture</button>`;
        } else if (item.livre.statut === 'en_cours') {
            actionsHtml = `
                <div class="session-form">
                    <input type="number" class="pages-read-input" placeholder="Pages lues" />
                    <button class="save-session-btn">Enregistrer</button>
                </div>
                <button class="finish-book-btn">Marquer comme terminé</button>
            `;
        } else {
            actionsHtml = `<p>Félicitations !</p>`;
        }

        bookEl.innerHTML = `
            <h4>${item.livre.titre}</h4>
            <p>${item.livre.auteur || 'Auteur inconnu'}</p>
            <p>${item.pages_lues} / ${item.livre.pages_total || '?'} pages</p>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: ${progress}%"></div>
            </div>
            <div class="book-actions">${actionsHtml}</div>
        `;
        shelf.appendChild(bookEl);

        // Add event listeners
        const startBtn = bookEl.querySelector('.start-reading-btn');
        if (startBtn) {
            startBtn.addEventListener('click', async () => {
                await invoke('changer_statut_livre', { livreId: item.livre.id, statut: 'en_cours' });
                loadBooks();
            });
        }

        const saveBtn = bookEl.querySelector('.save-session-btn');
        if (saveBtn) {
            saveBtn.addEventListener('click', async () => {
                const pagesInput = bookEl.querySelector('.pages-read-input') as HTMLInputElement;
                const pagesLues = Number(pagesInput.value);
                if (pagesLues > 0) {
                    await invoke('enregistrer_session', { livreId: item.livre.id, pagesLues });
                    loadBooks();
                } else {
                    alert("Veuillez entrer un nombre de pages valide.");
                }
            });
        }

        const finishBtn = bookEl.querySelector('.finish-book-btn');
        if (finishBtn) {
            finishBtn.addEventListener('click', async () => {
                await invoke('changer_statut_livre', { livreId: item.livre.id, statut: 'termine' });
                loadBooks();
            });
        }
    });
}

// --- Journal Module ---
async function renderJournalModule() {
    const today = new Date().toISOString().split('T')[0]; // Format YYYY-MM-DD

    root.innerHTML = `
        <div class="container">
            <div class="header">
                <button id="home-btn">Accueil</button>
                <h1>Journal Intime</h1>
            </div>
            <div class="journal-controls">
                <label for="journal-date">Date :</label>
                <input type="date" id="journal-date" value="${today}">
            </div>
            <textarea id="journal-content" placeholder="Écrivez vos pensées ici..."></textarea>
            <button id="save-journal-btn">Sauvegarder l'entrée</button>
        </div>
    `;

    const dateInput = document.getElementById('journal-date') as HTMLInputElement;
    const contentInput = document.getElementById('journal-content') as HTMLTextAreaElement;

    async function loadJournalEntry() {
        try {
            const entry = await invoke<EntreeJournal | null>('get_entree_journal', { date: dateInput.value });
            contentInput.value = entry ? entry.contenu : '';
        } catch (e) {
            console.error("Erreur de chargement de l'entrée:", e);
            contentInput.value = '';
        }
    }

    dateInput.addEventListener('change', loadJournalEntry);

    document.getElementById('home-btn')?.addEventListener('click', renderMainMenu);
    document.getElementById('save-journal-btn')?.addEventListener('click', async () => {
        try {
            await invoke('sauvegarder_entree_journal', {
                date: dateInput.value,
                contenu: contentInput.value
            });
            alert('Entrée sauvegardée !');
        } catch (e) {
            alert(`Erreur lors de la sauvegarde : ${e}`);
        }
    });

    // Load initial entry for today
    loadJournalEntry();
}

// --- Initial Load ---
renderMainMenu();