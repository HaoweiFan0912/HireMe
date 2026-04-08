const schemaRoot = document.getElementById("schema-root");
const statusText = document.getElementById("status-text");
const lastFileText = document.getElementById("last-file");
const jsonPreview = document.getElementById("json-preview");
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const submitButton = document.getElementById("submit-button");
const resetButton = document.getElementById("reset-button");
const saveButton = document.getElementById("save-button");
const apiKeyInput = document.getElementById("api-key-input");
const saveApiKeyButton = document.getElementById("save-api-key-button");
const clearApiKeyButton = document.getElementById("clear-api-key-button");
const apiKeyStatus = document.getElementById("api-key-status");

const API_KEY_STORAGE_KEY = "hireme_openai_api_key";

let blueprint = null;
let blankData = null;
let currentData = null;
let draftData = null;
let isDirty = false;

function getApiKeyValue() {
  return apiKeyInput.value.trim();
}

function updateApiKeyStatus(message) {
  apiKeyStatus.textContent = message;
}

function loadApiKey() {
  const savedApiKey = window.localStorage.getItem(API_KEY_STORAGE_KEY);
  if (savedApiKey) {
    apiKeyInput.value = savedApiKey;
    updateApiKeyStatus("A saved browser API key was loaded. Uploads will use it first.");
    return;
  }
  updateApiKeyStatus("No custom key is saved in this browser. Uploads will use the environment or server-side default key if one is configured.");
}

function saveApiKey() {
  const apiKey = getApiKeyValue();
  if (!apiKey) {
    window.localStorage.removeItem(API_KEY_STORAGE_KEY);
    updateApiKeyStatus("The field is empty. Uploads will now use the environment or server-side default key if one is configured.");
    return;
  }

  window.localStorage.setItem(API_KEY_STORAGE_KEY, apiKey);
  updateApiKeyStatus("Your custom API key is now saved in this browser. Uploads will use it first.");
}

function clearApiKey() {
  apiKeyInput.value = "";
  window.localStorage.removeItem(API_KEY_STORAGE_KEY);
  updateApiKeyStatus("The custom API key has been cleared. Uploads will use the environment or server-side default key if one is configured.");
}

function cloneData(value) {
  return structuredClone(value);
}

function formatLabel(value) {
  return value
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function getNamedPath(path) {
  return path.filter((segment) => typeof segment === "string");
}

function isHorizontalChipList(path) {
  const namedPath = getNamedPath(path).join(".");
  return ["skills.languages", "skills.computer", "education.courses"].includes(namedPath);
}

function getValueAtPath(root, path) {
  return path.reduce((accumulator, key) => accumulator?.[key], root);
}

function setValueAtPath(root, path, value) {
  if (path.length === 0) {
    return;
  }

  let cursor = root;
  for (let index = 0; index < path.length - 1; index += 1) {
    cursor = cursor[path[index]];
  }
  cursor[path[path.length - 1]] = value;
}

function updateJsonPreview() {
  jsonPreview.textContent = JSON.stringify(currentData, null, 2);
}

function updateSaveButtonState() {
  saveButton.disabled = !isDirty;
}

function markDirty() {
  isDirty = true;
  updateSaveButtonState();
}

function createSmallButton(label, className = "") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `small-button ${className}`.trim();
  button.textContent = label;
  return button;
}

function addListItem(path, itemTemplate) {
  const target = getValueAtPath(draftData, path);
  if (!Array.isArray(target)) {
    return;
  }
  target.push(cloneData(itemTemplate));
  markDirty();
  renderSchema();
}

function removeListItem(path, index) {
  const target = getValueAtPath(draftData, path);
  if (!Array.isArray(target)) {
    return;
  }
  target.splice(index, 1);
  markDirty();
  renderSchema();
}

function shouldUseTextarea(path) {
  const fieldName = path[path.length - 1];
  return ["content", "method", "result", "description"].includes(fieldName);
}

function createChipInput(path, index, value) {
  const input = document.createElement("input");
  input.type = "text";
  input.className = "chip-input";
  input.value = value ?? "";
  input.placeholder = "New item";
  input.addEventListener("input", (event) => {
    const target = getValueAtPath(draftData, path);
    if (!Array.isArray(target)) {
      return;
    }
    target[index] = event.target.value;
    markDirty();
  });
  return input;
}

function renderHorizontalStringList(path, value) {
  const itemsWrap = document.createElement("div");
  itemsWrap.className = "chip-list";

  if (Array.isArray(value) && value.length > 0) {
    value.forEach((itemValue, index) => {
      const chip = document.createElement("div");
      chip.className = "editable-chip";

      const input = createChipInput(path, index, itemValue);
      const removeButton = createSmallButton("×", "chip-remove");
      removeButton.setAttribute("aria-label", "Delete item");
      removeButton.title = "Delete item";
      removeButton.addEventListener("click", () => {
        removeListItem(path, index);
      });

      chip.append(input, removeButton);
      itemsWrap.append(chip);
    });
    return itemsWrap;
  }

  const emptyCard = document.createElement("div");
  emptyCard.className = "empty-list-card inline-empty-card";

  const emptyText = document.createElement("p");
  emptyText.className = "empty-list-note";
  emptyText.textContent = "This list is empty. Use Add Empty Item to start editing.";

  emptyCard.append(emptyText);
  itemsWrap.append(emptyCard);
  return itemsWrap;
}

function renderChipListRow(name, blueprintNode, value, path) {
  const row = document.createElement("div");
  row.className = "field-row chip-field-row";

  const header = document.createElement("div");
  header.className = "chip-field-header";

  const labelWrap = document.createElement("div");
  labelWrap.className = "chip-field-label-wrap";

  const title = document.createElement("div");
  title.className = "field-name";
  title.textContent = formatLabel(name || blueprintNode.title || "List");

  const type = document.createElement("div");
  type.className = "field-type";
  type.textContent = "list";

  labelWrap.append(title, type);

  const addButton = createSmallButton("Add Empty Item", "ghost-button chip-add-button");
  addButton.addEventListener("click", () => {
    addListItem(path, blueprintNode.item_template);
  });

  header.append(labelWrap, addButton);
  row.append(header, renderHorizontalStringList(path, value));
  return row;
}

function createStringEditor(path, value) {
  const control = shouldUseTextarea(path)
    ? document.createElement("textarea")
    : document.createElement("input");

  control.className = shouldUseTextarea(path) ? "editor-textarea" : "editor-input";
  if (control.tagName === "INPUT") {
    control.type = "text";
  } else {
    control.rows = 4;
  }

  control.value = value ?? "";
  control.placeholder = "Leave blank";
  control.addEventListener("input", (event) => {
    setValueAtPath(draftData, path, event.target.value);
    markDirty();
  });
  return control;
}

function createBooleanEditor(path, value) {
  const select = document.createElement("select");
  select.className = "editor-select";

  const options = [
    ["", "Blank"],
    ["true", "true"],
    ["false", "false"],
  ];

  for (const [optionValue, label] of options) {
    const option = document.createElement("option");
    option.value = optionValue;
    option.textContent = label;
    select.append(option);
  }

  select.value = value === true ? "true" : value === false ? "false" : "";
  select.addEventListener("change", (event) => {
    const nextValue =
      event.target.value === ""
        ? null
        : event.target.value === "true";
    setValueAtPath(draftData, path, nextValue);
    markDirty();
  });

  return select;
}

function renderScalarRow(name, blueprintNode, value, path) {
  const row = document.createElement("div");
  row.className = "field-row";

  const title = document.createElement("div");
  title.className = "field-name";
  title.textContent = formatLabel(name);

  const type = document.createElement("div");
  type.className = "field-type";
  type.textContent = blueprintNode.kind;

  const controlWrap = document.createElement("div");
  controlWrap.className = "field-control";

  if (blueprintNode.kind === "boolean") {
    controlWrap.append(createBooleanEditor(path, value));
  } else {
    controlWrap.append(createStringEditor(path, value));
  }

  row.append(title, type, controlWrap);
  return row;
}

function renderListItemContent(name, itemBlueprint, itemValue, path) {
  if (itemBlueprint.kind === "object") {
    return renderNode(name, itemBlueprint, itemValue, path);
  }

  return renderScalarRow(name, itemBlueprint, itemValue, path);
}

function renderNode(name, blueprintNode, value, path = []) {
  if (blueprintNode.kind === "object") {
    const card = document.createElement("section");
    card.className = "schema-card";

    const header = document.createElement("div");
    header.className = "object-header";

    const title = document.createElement("h3");
    title.textContent = formatLabel(name || blueprintNode.title || "Object");

    const hint = document.createElement("span");
    hint.className = "field-type";
    hint.textContent = "object";

    header.append(title, hint);

    const grid = document.createElement("div");
    grid.className = "field-grid";

    for (const field of blueprintNode.fields) {
      const nextValue =
        value && typeof value === "object" && !Array.isArray(value) ? value[field.name] : undefined;
      grid.append(renderNode(field.name, field.blueprint, nextValue, [...path, field.name]));
    }

    card.append(header, grid);
    return card;
  }

  if (blueprintNode.kind === "list") {
    if (blueprintNode.item_blueprint.kind === "string" && isHorizontalChipList(path)) {
      return renderChipListRow(name, blueprintNode, value, path);
    }

    const card = document.createElement("section");
    card.className = "schema-card";

    const header = document.createElement("div");
    header.className = "list-header";

    const title = document.createElement("h3");
    title.textContent = formatLabel(name || blueprintNode.title || "List");

    const toolbar = document.createElement("div");
    toolbar.className = "list-toolbar";

    const hint = document.createElement("span");
    hint.className = "field-type";
    hint.textContent = "list";

    const addButton = createSmallButton("Add Item", "ghost-button");
    addButton.addEventListener("click", () => {
      addListItem(path, blueprintNode.item_template);
    });

    toolbar.append(hint, addButton);
    header.append(title, toolbar);

    const itemsWrap = document.createElement("div");
    itemsWrap.className = "list-items";

    if (Array.isArray(value) && value.length > 0) {
      value.forEach((itemValue, index) => {
        const itemCard = document.createElement("div");
        itemCard.className = "list-item-card";

        const itemToolbar = document.createElement("div");
        itemToolbar.className = "item-toolbar";

        const itemLabel = document.createElement("p");
        itemLabel.className = "list-item-label";
        itemLabel.textContent = `Item ${index + 1}`;

        const removeButton = createSmallButton("Delete", "danger-button");
        removeButton.addEventListener("click", () => {
          removeListItem(path, index);
        });

        itemToolbar.append(itemLabel, removeButton);
        itemCard.append(itemToolbar);
        itemCard.append(
          renderListItemContent(
            name,
            blueprintNode.item_blueprint,
            itemValue,
            [...path, index],
          ),
        );
        itemsWrap.append(itemCard);
      });
    } else {
      const emptyCard = document.createElement("div");
      emptyCard.className = "empty-list-card";

      const emptyText = document.createElement("p");
      emptyText.className = "empty-list-note";
      emptyText.textContent = "This list is empty. Use Add Item to start editing.";

      emptyCard.append(emptyText);
      itemsWrap.append(emptyCard);
    }

    card.append(header, itemsWrap);
    return card;
  }

  return renderScalarRow(name, blueprintNode, value ?? (blueprintNode.kind === "boolean" ? null : ""), path);
}

function renderSchema() {
  schemaRoot.innerHTML = "";
  if (!blueprint || !draftData) {
    return;
  }

  schemaRoot.append(renderNode("resume_schema", blueprint, draftData, []));
  updateSaveButtonState();
}

async function loadSchema() {
  statusText.textContent = "Loading schema...";
  const response = await fetch("/api/schema");
  if (!response.ok) {
    throw new Error("Failed to load the schema.");
  }

  const payload = await response.json();
  blueprint = payload.blueprint;
  blankData = payload.blank_data;
  currentData = cloneData(payload.data);
  draftData = cloneData(payload.data);
  isDirty = false;
  renderSchema();
  updateJsonPreview();
  statusText.textContent = payload.has_saved_record ? "Saved record loaded." : "Blank schema loaded.";
}

async function saveDraft() {
  saveButton.disabled = true;
  statusText.textContent = "Saving edits...";

  try {
    const response = await fetch("/api/record", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(draftData),
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Failed to save edits.");
    }

    currentData = cloneData(payload.data);
    draftData = cloneData(payload.data);
    isDirty = false;
    renderSchema();
    updateJsonPreview();
    statusText.textContent = "Edits saved. The JSON preview and backend record are now updated.";
  } catch (error) {
    statusText.textContent = error.message;
    updateSaveButtonState();
  }
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = fileInput.files?.[0];
  if (!file) {
    statusText.textContent = "Please choose a file first.";
    return;
  }

  submitButton.disabled = true;
  statusText.textContent = "Extracting with OpenAI...";

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("current_data", JSON.stringify(draftData));
    if (getApiKeyValue()) {
      formData.append("openai_api_key", getApiKeyValue());
    }

    const response = await fetch("/api/extract", {
      method: "POST",
      body: formData,
    });

    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || "Extraction failed.");
    }

    draftData = cloneData(payload.data);
    isDirty = true;
    renderSchema();
    statusText.textContent = "Extraction finished. The result is now in the editable draft. Save when you want to sync the JSON preview and backend record.";
    lastFileText.textContent = `Last processed file: ${payload.filename || file.name}`;
  } catch (error) {
    statusText.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});

saveButton.addEventListener("click", () => {
  saveDraft();
});

saveApiKeyButton.addEventListener("click", () => {
  saveApiKey();
});

clearApiKeyButton.addEventListener("click", () => {
  clearApiKey();
});

resetButton.addEventListener("click", () => {
  draftData = cloneData(blankData);
  isDirty = true;
  renderSchema();
  statusText.textContent = "The draft has been reset to the blank schema. Save when you want to sync the JSON preview and backend.";
  fileInput.value = "";
});

loadApiKey();
loadSchema().catch((error) => {
  statusText.textContent = error.message;
});
