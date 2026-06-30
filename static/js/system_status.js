import {
  fetchSystemHealth
} from "./api.js";

import {
  elements
} from "./ui.js";


const COMPONENT_LABELS = {
  database: "Database",
  ollama: "Ollama",
  embedding: "Embeddings",
  ocr: "OCR",
  uploads: "Upload storage"
};

let initialized = false;
let refreshTimer = null;


export function initializeSystemStatus() {
  if (initialized) {
    return;
  }

  initialized = true;

  elements.systemStatusButton.addEventListener(
    "click",
    event => {
      event.stopPropagation();

      const shouldOpen =
        elements.systemStatusPanel.hidden;

      setSystemStatusPanelOpen(
        shouldOpen
      );

      if (shouldOpen) {
        refreshSystemStatus();
      }
    }
  );

  document.addEventListener(
    "click",
    event => {
      if (
        elements.systemStatusPanel.hidden
        || elements.systemStatusPanel.contains(event.target)
        || elements.systemStatusButton.contains(event.target)
      ) {
        return;
      }

      setSystemStatusPanelOpen(false);
    }
  );

  document.addEventListener(
    "keydown",
    event => {
      if (
        event.key === "Escape"
        && !elements.systemStatusPanel.hidden
      ) {
        setSystemStatusPanelOpen(false);
        elements.systemStatusButton.focus();
      }
    }
  );

  elements.systemStatusRefresh.addEventListener(
    "click",
    refreshSystemStatus
  );

  refreshSystemStatus();

  refreshTimer = window.setInterval(
    refreshSystemStatus,
    30_000
  );

  window.addEventListener(
    "beforeunload",
    () => {
      if (refreshTimer) {
        clearInterval(
          refreshTimer
        );
      }
    }
  );
}


function setSystemStatusPanelOpen(isOpen) {
  elements.systemStatusPanel.hidden = !isOpen;

  elements.systemStatusButton.setAttribute(
    "aria-expanded",
    String(isOpen)
  );
}


export async function refreshSystemStatus() {
  setOverallState(
    "checking",
    "Checking"
  );

  elements.systemStatusRefresh.disabled = true;

  try {
    const health =
      await fetchSystemHealth();

    renderHealth(
      health
    );

  } catch (error) {
    console.error(
      "System health check failed:",
      error
    );

    setOverallState(
      "unavailable",
      "Unavailable"
    );

    elements.systemStatusComponents.innerHTML =
      "";

    const item =
      document.createElement("div");

    item.className =
      "system-component system-component-unavailable";

    const title =
      document.createElement("strong");

    title.innerText =
      "Health endpoint";

    const message =
      document.createElement("span");

    message.innerText =
      error.message ||
      "Could not retrieve system status.";

    item.appendChild(
      title
    );

    item.appendChild(
      message
    );

    elements.systemStatusComponents.appendChild(
      item
    );

  } finally {
    elements.systemStatusRefresh.disabled =
      false;

    elements.systemStatusChecked.innerText =
      `Last checked ${new Date().toLocaleTimeString()}`;
  }
}


function renderHealth(
  health
) {
  const overall =
    health?.status || "unavailable";

  setOverallState(
    overall,
    labelForOverall(
      overall
    )
  );

  elements.systemStatusComponents.innerHTML =
    "";

  const components =
    health?.components || {};

  Object.entries(
    COMPONENT_LABELS
  ).forEach(
    ([key, label]) => {
      const component =
        components[key] || {
          ok: false,
          status: "unknown",
          message: "No status returned."
        };

      elements.systemStatusComponents.appendChild(
        createComponent(
          label,
          component
        )
      );
    }
  );
}


function createComponent(
  label,
  component
) {
  const item =
    document.createElement("article");

  item.className =
    `system-component ${
      component.ok
        ? "system-component-ready"
        : "system-component-unavailable"
    }`;

  const header =
    document.createElement("div");

  header.className =
    "system-component-header";

  const title =
    document.createElement("strong");

  title.innerText =
    label;

  const badge =
    document.createElement("span");

  badge.innerText =
    String(
      component.status || "unknown"
    );

  header.appendChild(
    title
  );

  header.appendChild(
    badge
  );

  const message =
    document.createElement("p");

  message.innerText =
    component.message ||
    "No message returned.";

  item.appendChild(
    header
  );

  item.appendChild(
    message
  );

  if (
    Number.isFinite(
      Number(component.latency_ms)
    )
  ) {
    const latency =
      document.createElement("small");

    latency.innerText =
      `${component.latency_ms} ms`;

    item.appendChild(
      latency
    );
  }

  return item;
}


function setOverallState(
  state,
  label
) {
  elements.systemStatusButton.dataset.state =
    state;

  elements.systemStatusDot.className =
    `system-status-dot status-${state}`;

  elements.systemStatusLabel.innerText =
    label;

  elements.systemStatusOverall.className =
    `system-status-overall status-${state}`;

  elements.systemStatusOverall.innerText =
    label;
}


function labelForOverall(
  status
) {
  if (status === "ready") {
    return "Ready";
  }

  if (status === "degraded") {
    return "Degraded";
  }

  return "Unavailable";
}
