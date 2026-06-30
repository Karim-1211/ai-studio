import { fetchModels } from "./api.js";
import { elements } from "./ui.js";


const STORAGE_KEY = "aiStudioSettingsV2";

const DEFAULT_SETTINGS = {
  model: "",
  responseMode: "single",
  theme: "dark",
  temperature: 0.7,
  maxTokens: 1000,
  topP: 0.9,
  topK: 40,
  repeatPenalty: 1.1,
  contextLength: 4096,
  systemPrompt: ""
};

let initialized = false;
let saveNoteTimer = null;


export function initializeSettings() {
  if (initialized) {
    return;
  }

  initialized = true;

  const settings = readStoredSettings();

  applySettingsToControls(settings);
  applyTheme(settings.theme);
  updateSystemPromptCount();

  const persistedControls = [
    elements.responseMode,
    elements.temperature,
    elements.maxTokens,
    elements.topP,
    elements.topK,
    elements.repeatPenalty,
    elements.contextLength
  ];

  persistedControls.forEach(control => {
    const eventName =
      control.tagName === "TEXTAREA"
        ? "input"
        : "change";

    control.addEventListener(
      eventName,
      () => {
        normalizeVisibleSettings();
        saveCurrentSettings();
      }
    );
  });

  elements.systemPrompt.addEventListener(
    "input",
    () => {
      updateSystemPromptCount();
      saveCurrentSettings();
    }
  );

  elements.model.addEventListener(
    "change",
    saveCurrentSettings
  );

  elements.themeToggle.addEventListener(
    "click",
    toggleTheme
  );

  elements.resetSettingsButton.addEventListener(
    "click",
    resetAdvancedSettings
  );

  initializeAdvancedDismissal();
}


function initializeAdvancedDismissal() {
  const advancedBox = document.getElementById(
    "advancedBox"
  );

  if (!advancedBox) {
    return;
  }

  document.addEventListener(
    "pointerdown",
    event => {
      if (
        advancedBox.open
        && !advancedBox.contains(event.target)
      ) {
        advancedBox.open = false;
      }
    }
  );

  document.addEventListener(
    "keydown",
    event => {
      if (event.key === "Escape" && advancedBox.open) {
        advancedBox.open = false;
        advancedBox.querySelector("summary")?.focus();
      }
    }
  );
}


export async function loadModels() {
  const models = await fetchModels();
  const settings = readStoredSettings();

  elements.model.innerHTML = "";

  if (!Array.isArray(models) || models.length === 0) {
    const option = document.createElement("option");

    option.text = "No generation models found";
    option.value = "";

    elements.model.appendChild(option);
    elements.model.disabled = true;

    return;
  }

  elements.model.disabled = false;

  models.forEach(item => {
    const option = document.createElement("option");

    option.text = item;
    option.value = item;

    elements.model.appendChild(option);
  });

  const savedModelExists = models.includes(
    settings.model
  );

  elements.model.value = savedModelExists
    ? settings.model
    : models[0];

  saveCurrentSettings(false);
}


export function getGenerationSettings() {
  const values = normalizeVisibleSettings();

  saveCurrentSettings(false);

  return {
    system_prompt: values.systemPrompt,
    temperature: values.temperature,
    max_tokens: values.maxTokens,
    top_p: values.topP,
    top_k: values.topK,
    repeat_penalty: values.repeatPenalty,
    context_length: values.contextLength
  };
}


function normalizeVisibleSettings() {
  const values = {
    temperature: readFloat(
      elements.temperature,
      0,
      2,
      DEFAULT_SETTINGS.temperature
    ),
    maxTokens: readInteger(
      elements.maxTokens,
      50,
      8192,
      DEFAULT_SETTINGS.maxTokens
    ),
    topP: readFloat(
      elements.topP,
      0.05,
      1,
      DEFAULT_SETTINGS.topP
    ),
    topK: readInteger(
      elements.topK,
      0,
      100,
      DEFAULT_SETTINGS.topK
    ),
    repeatPenalty: readFloat(
      elements.repeatPenalty,
      0.5,
      2,
      DEFAULT_SETTINGS.repeatPenalty
    ),
    contextLength: readInteger(
      elements.contextLength,
      512,
      32768,
      DEFAULT_SETTINGS.contextLength
    ),
    systemPrompt: String(
      elements.systemPrompt.value || ""
    ).slice(0, 4000)
  };

  elements.temperature.value =
    formatNumber(values.temperature);

  elements.maxTokens.value =
    String(values.maxTokens);

  elements.topP.value =
    formatNumber(values.topP);

  elements.topK.value =
    String(values.topK);

  elements.repeatPenalty.value =
    formatNumber(values.repeatPenalty);

  elements.contextLength.value =
    String(values.contextLength);

  elements.systemPrompt.value =
    values.systemPrompt;

  updateSystemPromptCount();

  return values;
}


function saveCurrentSettings(showConfirmation = true) {
  const values = normalizeVisibleSettings();

  const settings = {
    model: elements.model.value || "",
    responseMode:
      elements.responseMode.value ||
      DEFAULT_SETTINGS.responseMode,
    theme:
      document.documentElement.dataset.theme === "light"
        ? "light"
        : "dark",
    ...values
  };

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(settings)
  );

  if (showConfirmation) {
    showSavedNote();
  }
}


function readStoredSettings() {
  try {
    const parsed = JSON.parse(
      localStorage.getItem(STORAGE_KEY) || "{}"
    );

    return {
      ...DEFAULT_SETTINGS,
      ...parsed,
      theme:
        parsed.theme === "light"
          ? "light"
          : "dark"
    };

  } catch (error) {
    console.warn(
      "Could not read saved AI Studio settings:",
      error
    );

    return {
      ...DEFAULT_SETTINGS
    };
  }
}


function applySettingsToControls(settings) {
  elements.responseMode.value =
    settings.responseMode;

  elements.temperature.value =
    settings.temperature;

  elements.maxTokens.value =
    settings.maxTokens;

  elements.topP.value =
    settings.topP;

  elements.topK.value =
    settings.topK;

  elements.repeatPenalty.value =
    settings.repeatPenalty;

  elements.contextLength.value =
    settings.contextLength;

  elements.systemPrompt.value =
    settings.systemPrompt || "";

  normalizeVisibleSettings();
}


function toggleTheme() {
  const currentTheme =
    document.documentElement.dataset.theme;

  const nextTheme =
    currentTheme === "light"
      ? "dark"
      : "light";

  applyTheme(nextTheme);
  saveCurrentSettings();
}


function applyTheme(theme) {
  const normalizedTheme =
    theme === "light"
      ? "light"
      : "dark";

  document.documentElement.dataset.theme =
    normalizedTheme;

  const switchingToTheme =
    normalizedTheme === "dark"
      ? "light"
      : "dark";

  elements.themeIcon.innerText =
    normalizedTheme === "dark"
      ? "☀"
      : "☾";

  elements.themeLabel.innerText =
    normalizedTheme === "dark"
      ? "Light"
      : "Dark";

  elements.themeToggle.title =
    `Switch to ${switchingToTheme} theme`;

  elements.themeToggle.setAttribute(
    "aria-label",
    `Switch to ${switchingToTheme} theme`
  );
}


function resetAdvancedSettings() {
  elements.temperature.value =
    DEFAULT_SETTINGS.temperature;

  elements.maxTokens.value =
    DEFAULT_SETTINGS.maxTokens;

  elements.topP.value =
    DEFAULT_SETTINGS.topP;

  elements.topK.value =
    DEFAULT_SETTINGS.topK;

  elements.repeatPenalty.value =
    DEFAULT_SETTINGS.repeatPenalty;

  elements.contextLength.value =
    DEFAULT_SETTINGS.contextLength;

  elements.systemPrompt.value =
    DEFAULT_SETTINGS.systemPrompt;

  normalizeVisibleSettings();
  saveCurrentSettings();

  elements.settingsSaveNote.innerText =
    "Generation settings were reset to defaults.";
}


function updateSystemPromptCount() {
  elements.systemPromptCount.innerText =
    String(elements.systemPrompt.value.length);
}


function showSavedNote() {
  clearTimeout(saveNoteTimer);

  elements.settingsSaveNote.innerText =
    "Saved automatically.";

  elements.settingsSaveNote.classList.add(
    "is-saved"
  );

  saveNoteTimer = setTimeout(() => {
    elements.settingsSaveNote.innerText =
      "Settings save automatically in this browser.";

    elements.settingsSaveNote.classList.remove(
      "is-saved"
    );
  }, 1400);
}


function readFloat(
  input,
  minimum,
  maximum,
  fallback
) {
  const parsed = Number.parseFloat(
    input.value
  );

  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return clamp(
    parsed,
    minimum,
    maximum
  );
}


function readInteger(
  input,
  minimum,
  maximum,
  fallback
) {
  const parsed = Number.parseInt(
    input.value,
    10
  );

  if (!Number.isFinite(parsed)) {
    return fallback;
  }

  return Math.round(
    clamp(
      parsed,
      minimum,
      maximum
    )
  );
}


function clamp(value, minimum, maximum) {
  return Math.min(
    maximum,
    Math.max(minimum, value)
  );
}


function formatNumber(value) {
  return Number(value.toFixed(2)).toString();
}
