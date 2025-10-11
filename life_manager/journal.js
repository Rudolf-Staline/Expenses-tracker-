const { invoke } = window.__TAURI__.tauri;

const addJournalForm = document.querySelector("#add-journal-form");
const journalTitleInput = document.querySelector("#journal-title");
const journalContentInput = document.querySelector("#journal-content");
const formMessage = document.querySelector("#form-message");
const journalList = document.querySelector("#journal-list");

async function refreshJournalEntries() {
  try {
    const entries = await invoke("get_all_journal_entries");
    journalList.innerHTML = ""; // Clear existing list

    if (entries.length === 0) {
      journalList.innerHTML = "<li>No journal entries yet.</li>";
      return;
    }

    entries.forEach((entry) => {
      const li = document.createElement("li");
      const date = new Date(entry.created_at).toLocaleDateString();
      li.innerHTML = `<strong>${entry.title}</strong> - <em>${date}</em><br/>${entry.content}`;
      journalList.appendChild(li);
    });
  } catch (error) {
    console.error("Failed to refresh journal entries:", error);
    journalList.innerHTML = "<li>Error loading entries.</li>";
  }
}

addJournalForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const title = journalTitleInput.value;
  const content = journalContentInput.value;

  if (!title || !content) {
    formMessage.textContent = "Please fill out all fields.";
    formMessage.style.color = "red";
    return;
  }

  try {
    await invoke("create_journal_entry", { title, content });

    formMessage.textContent = "Entry added successfully!";
    formMessage.style.color = "green";

    journalTitleInput.value = "";
    journalContentInput.value = "";
    await refreshJournalEntries();

  } catch (error) {
    console.error("Failed to create journal entry:", error);
    formMessage.textContent = `Error: ${error}`;
    formMessage.style.color = "red";
  }
});

// Initial load of entries when the page is ready
window.addEventListener("DOMContentLoaded", () => {
  refreshJournalEntries();
});