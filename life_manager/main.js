const { invoke } = window.__TAURI__.tauri;

const addItemForm = document.querySelector("#add-item-form");
const itemNameInput = document.querySelector("#item-name");
const itemPriceInput = document.querySelector("#item-price");
const formMessage = document.querySelector("#form-message");
const itemList = document.querySelector("#item-list");

async function refreshItems() {
  try {
    const items = await invoke("get_all_active_items_with_price");
    itemList.innerHTML = ""; // Clear existing list

    if (items.length === 0) {
      itemList.innerHTML = "<li>No items found. Add one!</li>";
      return;
    }

    items.forEach((item) => {
      const li = document.createElement("li");
      const price = item.price !== null ? `$${item.price.toFixed(2)}` : "No price set";
      li.textContent = `${item.name} - ${price}`;
      itemList.appendChild(li);
    });
  } catch (error) {
    console.error("Failed to refresh items:", error);
    itemList.innerHTML = "<li>Error loading items.</li>";
  }
}

addItemForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const name = itemNameInput.value;
  const price = parseFloat(itemPriceInput.value);

  if (!name || isNaN(price)) {
    formMessage.textContent = "Please enter a valid name and price.";
    formMessage.style.color = "red";
    return;
  }

  try {
    await invoke("create_item", {
      name: name,
      initialPrice: price,
      family: "Other", // Using a default for simplicity
      packaging: null,
      itemType: null,
    });

    formMessage.textContent = `Item "${name}" added successfully!`;
    formMessage.style.color = "green";

    // Clear form and refresh the list
    itemNameInput.value = "";
    itemPriceInput.value = "";
    await refreshItems();

  } catch (error) {
    console.error("Failed to create item:", error);
    formMessage.textContent = `Error: ${error}`;
    formMessage.style.color = "red";
  }
});

// Initial load of items when the page is ready
window.addEventListener("DOMContentLoaded", () => {
  refreshItems();
});