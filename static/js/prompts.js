import {
  createPromptTemplate,
  deletePromptTemplate,
  fetchPromptTemplates,
  recordPromptTemplateUse,
  updatePromptTemplate
} from "./api.js";

import { elements } from "./ui.js";


let promptTemplates = [];
let favoritesOnly = false;
let searchTimer = null;
const knownCategories = new Set();


const ui = {};


function setStatus(message = "", isError = false) {
  ui.status.textContent = message;
  ui.status.classList.toggle("is-error", isError);
}


function openDrawer() {
  ui.drawer.classList.add("is-open");
  ui.drawer.setAttribute("aria-hidden", "false");
  ui.backdrop.hidden = false;
  ui.openButton.setAttribute("aria-expanded", "true");
  document.body.classList.add("prompt-library-open");
  window.setTimeout(() => ui.search.focus(), 50);
}


function closeDrawer() {
  ui.drawer.classList.remove("is-open");
  ui.drawer.setAttribute("aria-hidden", "true");
  ui.backdrop.hidden = true;
  ui.openButton.setAttribute("aria-expanded", "false");
  document.body.classList.remove("prompt-library-open");
}


function resetForm() {
  ui.form.reset();
  ui.templateId.value = "";
  ui.category.value = "General";
  ui.form.hidden = true;
  ui.save.textContent = "Save prompt";
}


function openForm(template = null, useCurrentText = false) {
  ui.form.hidden = false;
  ui.templateId.value = template?.id ?? "";
  ui.title.value = template?.title ?? "";
  ui.category.value = template?.category || "General";
  ui.content.value = template?.content ?? (
    useCurrentText ? elements.promptInput.value.trim() : ""
  );
  ui.favorite.checked = Boolean(template?.is_favorite);
  ui.save.textContent = template ? "Update prompt" : "Save prompt";
  setStatus();
  window.setTimeout(() => {
    (template ? ui.title : (ui.content.value ? ui.title : ui.content)).focus();
  }, 30);
}


function categoriesFromTemplates() {
  promptTemplates.forEach(item => {
    const category = String(item.category || "General").trim();
    if (category) knownCategories.add(category);
  });

  return [...knownCategories].sort((a, b) => a.localeCompare(b));
}


function renderCategoryFilter() {
  const current = ui.categoryFilter.value;
  ui.categoryFilter.innerHTML = '<option value="">All categories</option>';

  categoriesFromTemplates().forEach(category => {
    const option = document.createElement("option");
    option.value = category;
    option.textContent = category;
    ui.categoryFilter.appendChild(option);
  });

  ui.categoryFilter.value = categoriesFromTemplates().includes(current)
    ? current
    : "";
}


function insertPromptText(template) {
  const textarea = elements.promptInput;
  const start = textarea.selectionStart ?? textarea.value.length;
  const end = textarea.selectionEnd ?? textarea.value.length;
  const before = textarea.value.slice(0, start);
  const after = textarea.value.slice(end);
  const separator = before && !before.endsWith("\n") ? "\n\n" : "";
  const text = `${separator}${template.content}`;

  textarea.value = `${before}${text}${after}`;
  const caret = before.length + text.length;
  textarea.setSelectionRange(caret, caret);
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
  textarea.focus();

  recordPromptTemplateUse(template.id).catch(error => {
    console.warn("Could not update prompt usage:", error);
  });

  closeDrawer();
}


function createIconButton(label, title, text) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "prompt-card-icon-button";
  button.setAttribute("aria-label", label);
  button.title = title;
  button.textContent = text;
  return button;
}


function renderPromptList() {
  ui.list.innerHTML = "";

  if (promptTemplates.length === 0) {
    const empty = document.createElement("div");
    empty.className = "prompt-library-empty";
    empty.innerHTML = `
      <strong>No saved prompts yet</strong>
      <p>Create a reusable prompt or save the text currently in the composer.</p>
    `;
    ui.list.appendChild(empty);
    return;
  }

  promptTemplates.forEach(template => {
    const card = document.createElement("article");
    card.className = "prompt-template-card";

    const heading = document.createElement("div");
    heading.className = "prompt-template-card-heading";

    const titleWrap = document.createElement("div");
    titleWrap.className = "prompt-template-card-title";

    const title = document.createElement("strong");
    title.textContent = template.title;

    const meta = document.createElement("span");
    meta.textContent = `${template.category || "General"} · used ${template.usage_count || 0}`;

    titleWrap.append(title, meta);

    const controls = document.createElement("div");
    controls.className = "prompt-template-card-controls";

    const favorite = createIconButton(
      template.is_favorite ? "Remove favorite" : "Add favorite",
      template.is_favorite ? "Remove favorite" : "Add favorite",
      template.is_favorite ? "★" : "☆"
    );
    favorite.classList.toggle("is-favorite", template.is_favorite);
    favorite.addEventListener("click", async () => {
      try {
        await updatePromptTemplate(template.id, {
          is_favorite: !template.is_favorite
        });
        await loadTemplates();
      } catch (error) {
        setStatus(error.message, true);
      }
    });

    const edit = createIconButton("Edit prompt", "Edit prompt", "✎");
    edit.addEventListener("click", () => openForm(template));

    const remove = createIconButton("Delete prompt", "Delete prompt", "×");
    remove.classList.add("is-danger");
    remove.addEventListener("click", async () => {
      if (!window.confirm(`Delete “${template.title}”?`)) return;
      try {
        await deletePromptTemplate(template.id);
        await loadTemplates();
        setStatus("Prompt deleted.");
      } catch (error) {
        setStatus(error.message, true);
      }
    });

    controls.append(favorite, edit, remove);
    heading.append(titleWrap, controls);

    const preview = document.createElement("p");
    preview.className = "prompt-template-preview";
    preview.textContent = template.content;

    const actions = document.createElement("div");
    actions.className = "prompt-template-card-actions";

    const insert = document.createElement("button");
    insert.type = "button";
    insert.className = "prompt-template-insert";
    insert.textContent = "Insert into message";
    insert.addEventListener("click", () => insertPromptText(template));

    const copy = document.createElement("button");
    copy.type = "button";
    copy.textContent = "Copy";
    copy.addEventListener("click", async () => {
      await navigator.clipboard.writeText(template.content);
      copy.textContent = "Copied";
      window.setTimeout(() => { copy.textContent = "Copy"; }, 1200);
    });

    actions.append(insert, copy);
    card.append(heading, preview, actions);
    ui.list.appendChild(card);
  });
}


async function loadTemplates() {
  try {
    promptTemplates = await fetchPromptTemplates({
      search: ui.search.value.trim(),
      category: ui.categoryFilter.value,
      favorites: favoritesOnly
    });
    renderCategoryFilter();
    renderPromptList();
  } catch (error) {
    setStatus(error.message || "Could not load prompts.", true);
  }
}


async function submitPrompt(event) {
  event.preventDefault();

  const payload = {
    title: ui.title.value.trim(),
    category: ui.category.value.trim() || "General",
    content: ui.content.value.trim(),
    is_favorite: ui.favorite.checked
  };

  if (!payload.title || !payload.content) {
    setStatus("Title and prompt text are required.", true);
    return;
  }

  ui.save.disabled = true;
  setStatus("Saving prompt...");

  try {
    if (ui.templateId.value) {
      await updatePromptTemplate(Number(ui.templateId.value), payload);
      setStatus("Prompt updated.");
    } else {
      await createPromptTemplate(payload);
      setStatus("Prompt saved.");
    }
    resetForm();
    await loadTemplates();
  } catch (error) {
    setStatus(error.message || "Could not save the prompt.", true);
  } finally {
    ui.save.disabled = false;
  }
}


export function initializePromptLibrary() {
  Object.assign(ui, {
    openButton: document.getElementById("promptLibraryButton"),
    drawer: document.getElementById("promptLibraryDrawer"),
    backdrop: document.getElementById("promptLibraryBackdrop"),
    close: document.getElementById("promptLibraryClose"),
    search: document.getElementById("promptLibrarySearch"),
    categoryFilter: document.getElementById("promptLibraryCategoryFilter"),
    favorites: document.getElementById("promptLibraryFavorites"),
    newButton: document.getElementById("promptLibraryNew"),
    saveCurrent: document.getElementById("promptLibrarySaveCurrent"),
    form: document.getElementById("promptTemplateForm"),
    templateId: document.getElementById("promptTemplateId"),
    title: document.getElementById("promptTemplateTitle"),
    category: document.getElementById("promptTemplateCategory"),
    content: document.getElementById("promptTemplateContent"),
    favorite: document.getElementById("promptTemplateFavorite"),
    save: document.getElementById("promptTemplateSave"),
    cancel: document.getElementById("promptTemplateCancel"),
    status: document.getElementById("promptLibraryStatus"),
    list: document.getElementById("promptLibraryList")
  });

  if (!ui.openButton || !ui.drawer) return;

  ui.openButton.addEventListener("click", () => {
    if (ui.drawer.classList.contains("is-open")) closeDrawer();
    else openDrawer();
  });
  ui.close.addEventListener("click", closeDrawer);
  ui.backdrop.addEventListener("click", closeDrawer);
  ui.newButton.addEventListener("click", () => openForm());
  ui.saveCurrent.addEventListener("click", () => openForm(null, true));
  ui.cancel.addEventListener("click", resetForm);
  ui.form.addEventListener("submit", submitPrompt);

  ui.search.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(loadTemplates, 180);
  });
  ui.categoryFilter.addEventListener("change", loadTemplates);
  ui.favorites.addEventListener("click", () => {
    favoritesOnly = !favoritesOnly;
    ui.favorites.classList.toggle("is-active", favoritesOnly);
    ui.favorites.setAttribute("aria-pressed", String(favoritesOnly));
    ui.favorites.querySelector("span").textContent = favoritesOnly ? "★" : "☆";
    loadTemplates();
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && ui.drawer.classList.contains("is-open")) {
      closeDrawer();
    }
  });

  loadTemplates();
}
