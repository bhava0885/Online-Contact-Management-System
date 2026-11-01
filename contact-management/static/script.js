// script.js - talks to the Flask API and updates the page.

// Opened from Flask (port 5000)? Use the same server.
// Opened with Live Server (port 5500)? Call the Flask server directly.
const API = location.port === "5000" ? "" : "http://127.0.0.1:5000";

const form = document.getElementById("contactForm");
const idField = document.getElementById("contactId");
const nameField = document.getElementById("name");
const phoneField = document.getElementById("phone");
const emailField = document.getElementById("email");
const addressField = document.getElementById("address");
const formTitle = document.getElementById("formTitle");
const saveBtn = document.getElementById("saveBtn");
const cancelBtn = document.getElementById("cancelBtn");
const searchBox = document.getElementById("search");
const listBox = document.getElementById("contactList");
const countBox = document.getElementById("count");
const banner = document.getElementById("offlineBanner");
const toast = document.getElementById("toast");

let toastTimer;
let searchTimer;

// ---- Small helpers ----
function showToast(message, type) {
  toast.textContent = message;
  toast.className = "toast " + type;
  toast.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () { toast.hidden = true; }, 3500);
}

// Sends a request to Flask and returns the JSON answer.
async function request(path, options) {
  options = options || {};
  const settings = { method: options.method || "GET" };
  if (options.body) {
    settings.headers = { "Content-Type": "application/json" };
    settings.body = options.body;
  }

  let response;
  try {
    response = await fetch(API + path, settings);
  } catch (error) {
    banner.hidden = false;
    throw new Error("Cannot reach the server. Start python app.py first.");
  }
  banner.hidden = true;

  let data = {};
  try { data = await response.json(); } catch (error) { /* no JSON body */ }
  if (!response.ok) {
    throw new Error((data.errors || ["Something went wrong."]).join(" "));
  }
  return data;
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) { element.className = className; }
  if (text) { element.textContent = text; }   // textContent keeps user text safe
  return element;
}

function initials(name) {
  const words = name.split(/\s+/).filter(Boolean).slice(0, 2);
  return words.map(function (w) { return w[0].toUpperCase(); }).join("");
}

// ---- Show contacts ----
function renderContacts(contacts) {
  listBox.textContent = "";
  countBox.textContent = contacts.length;

  if (contacts.length === 0) {
    const message = searchBox.value.trim()
      ? "No contacts match your search."
      : "No contacts yet. Add your first one using the form.";
    listBox.appendChild(makeElement("p", "empty", message));
    return;
  }

  contacts.forEach(function (contact) {
    const card = makeElement("article", "contact");
    card.appendChild(makeElement("div", "avatar", initials(contact.name)));

    const info = makeElement("div", "info");
    info.appendChild(makeElement("strong", "", contact.name));
    info.appendChild(makeElement("span", "", "📞 " + contact.phone));
    if (contact.email) { info.appendChild(makeElement("span", "", "✉️ " + contact.email)); }
    if (contact.address) { info.appendChild(makeElement("span", "", "📍 " + contact.address)); }
    card.appendChild(info);

    const actions = makeElement("div", "actions");
    const editBtn = makeElement("button", "btn btn-light btn-sm", "✏️ Edit");
    editBtn.type = "button";
    editBtn.addEventListener("click", function () { startEdit(contact); });
    const deleteBtn = makeElement("button", "btn btn-danger btn-sm", "🗑️ Delete");
    deleteBtn.type = "button";
    deleteBtn.addEventListener("click", function () { deleteContact(contact); });
    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);
    card.appendChild(actions);

    listBox.appendChild(card);
  });
}

async function loadContacts() {
  try {
    const query = encodeURIComponent(searchBox.value.trim());
    const data = await request("/api/contacts?q=" + query);
    renderContacts(data.contacts);
  } catch (error) {
    listBox.textContent = "";
    countBox.textContent = "0";
  }
}

// ---- Add / edit ----
function startEdit(contact) {
  idField.value = contact.id;
  nameField.value = contact.name;
  phoneField.value = contact.phone;
  emailField.value = contact.email;
  addressField.value = contact.address;
  formTitle.textContent = "✏️ Edit contact";
  saveBtn.textContent = "Save changes";
  cancelBtn.hidden = false;
  window.scrollTo({ top: 0, behavior: "smooth" });
  nameField.focus();
}

function resetForm() {
  form.reset();
  idField.value = "";
  formTitle.textContent = "➕ Add contact";
  saveBtn.textContent = "Add contact";
  cancelBtn.hidden = true;
}

form.addEventListener("submit", async function (event) {
  event.preventDefault();
  const id = idField.value;
  const body = JSON.stringify({
    name: nameField.value,
    phone: phoneField.value,
    email: emailField.value,
    address: addressField.value
  });

  try {
    const data = await request(
      id ? "/api/contacts/" + id : "/api/contacts",
      { method: id ? "PUT" : "POST", body: body }
    );
    showToast(data.message, "success");
    resetForm();
    loadContacts();
  } catch (error) {
    showToast(error.message, "error");
  }
});

cancelBtn.addEventListener("click", resetForm);

// ---- Delete ----
async function deleteContact(contact) {
  if (!confirm("Delete " + contact.name + "? This cannot be undone.")) { return; }
  try {
    const data = await request("/api/contacts/" + contact.id, { method: "DELETE" });
    showToast(data.message, "success");
    if (idField.value === String(contact.id)) { resetForm(); }
    loadContacts();
  } catch (error) {
    showToast(error.message, "error");
  }
}

// ---- Search (waits a moment after typing stops) ----
searchBox.addEventListener("input", function () {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadContacts, 250);
});

loadContacts();
