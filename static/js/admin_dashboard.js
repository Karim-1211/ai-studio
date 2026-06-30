const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";
const refreshButton = document.getElementById("adminRefreshButton");
const rangeSelect = document.getElementById("adminRange");
const statusElement = document.getElementById("adminStatus");

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let size = bytes / 1024;
  let index = 0;
  while (size >= 1024 && index < units.length - 1) {
    size /= 1024;
    index += 1;
  }
  return `${size.toFixed(size >= 100 ? 0 : 1)} ${units[index]}`;
}

function formatDuration(value) {
  const milliseconds = Number(value || 0);
  if (milliseconds >= 1000) return `${(milliseconds / 1000).toFixed(1)} s`;
  return `${Math.round(milliseconds)} ms`;
}

function text(value) {
  return String(value ?? "—");
}

function renderSummary(summary) {
  const values = {
    adminUsersValue: `${summary.active_users}/${summary.users}`,
    adminChatsValue: summary.chats,
    adminMessagesValue: summary.messages,
    adminStorageValue: formatBytes(summary.upload_disk_bytes),
    adminFailuresValue: summary.failed_requests,
    adminLatencyValue: formatDuration(summary.average_model_duration_ms),
    adminSourcesValue: `${summary.websites} web · ${summary.social_sources} social`,
    adminOrphansValue: summary.orphan_uploads,
  };
  Object.entries(values).forEach(([id, value]) => {
    const element = document.getElementById(id);
    if (element) element.textContent = value;
  });
}

function renderUsers(users, currentUserId) {
  const body = document.getElementById("adminUsersBody");
  body.replaceChildren();
  users.forEach((user) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><strong></strong><small></small></td>
      <td><span class="admin-status-pill"></span></td>
      <td></td><td></td><td></td><td></td><td></td><td></td>
    `;
    row.children[0].querySelector("strong").textContent = user.display_name;
    row.children[0].querySelector("small").textContent = user.email;
    const status = row.children[1].querySelector("span");
    status.textContent = user.active ? "Active" : "Disabled";
    status.classList.toggle("is-off", !user.active);
    row.children[2].textContent = user.chat_count;
    row.children[3].textContent = user.message_count;
    row.children[4].textContent = user.document_count + user.attachment_count;
    row.children[5].textContent = `${user.website_count}/${user.social_count}`;
    row.children[6].textContent = formatBytes(user.storage_bytes);
    const actionCell = row.children[7];
    if (user.id === currentUserId) {
      actionCell.textContent = "Current account";
    } else {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "admin-table-action";
      button.dataset.userId = String(user.id);
      button.dataset.active = String(user.active);
      button.textContent = user.active ? "Disable" : "Enable";
      button.setAttribute(
        "aria-label",
        `${user.active ? "Disable" : "Enable"} ${user.display_name}`
      );
      actionCell.appendChild(button);
    }
    body.appendChild(row);
  });
}

function renderModels(models) {
  const list = document.getElementById("adminModelUsage");
  list.replaceChildren();
  if (!models.length) {
    list.innerHTML = '<p class="admin-empty">Model analytics will appear after new chat requests.</p>';
    return;
  }
  const maximum = Math.max(...models.map((item) => item.requests), 1);
  models.forEach((item) => {
    const row = document.createElement("div");
    row.className = "admin-model-row";
    row.innerHTML = `
      <div class="admin-model-meta"><strong></strong><span></span></div>
      <div class="admin-model-track"><span></span></div>
    `;
    row.querySelector("strong").textContent = item.model;
    row.querySelector(".admin-model-meta span").textContent =
      `${item.requests} requests · ${formatDuration(item.average_duration_ms)} avg · ${item.failures} failed`;
    row.querySelector(".admin-model-track span").style.width =
      `${Math.max(4, (item.requests / maximum) * 100)}%`;
    list.appendChild(row);
  });
}

function renderFailures(items) {
  const list = document.getElementById("adminFailuresList");
  list.replaceChildren();
  if (!items.length) {
    list.innerHTML = '<p class="admin-empty">No failed requests in the selected period.</p>';
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "admin-event-row";
    row.innerHTML = '<strong></strong><span></span><small></small>';
    row.querySelector("strong").textContent = `${item.status_code} · ${item.method}`;
    row.querySelector("span").textContent = item.path;
    row.querySelector("small").textContent =
      `${new Date(item.created_at).toLocaleString()} · ${formatDuration(item.duration_ms)}`;
    list.appendChild(row);
  });
}

function renderHealth(items) {
  const list = document.getElementById("adminHealthList");
  list.replaceChildren();
  if (!items.length) {
    list.innerHTML = '<p class="admin-empty">Health history will appear after health checks run.</p>';
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "admin-event-row";
    row.innerHTML = '<strong></strong><span></span><small></small>';
    row.querySelector("strong").textContent = item.status;
    row.querySelector("strong").className = `health-${item.status}`;
    const componentText = Object.entries(item.components || {})
      .map(([name, component]) => `${name}: ${component.status}`)
      .join(" · ");
    row.querySelector("span").textContent = componentText || "No component details";
    row.querySelector("small").textContent = new Date(item.created_at).toLocaleString();
    list.appendChild(row);
  });
}

function renderAudit(items, users) {
  const names = new Map(users.map((user) => [user.id, user.display_name]));
  const list = document.getElementById("adminAuditList");
  list.replaceChildren();
  if (!items.length) {
    list.innerHTML = '<p class="admin-empty">No audit events recorded yet.</p>';
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "admin-event-row";
    row.innerHTML = '<strong></strong><span></span><small></small>';
    row.querySelector("strong").textContent = item.action;
    row.querySelector("span").textContent =
      `${names.get(item.actor_user_id) || "System"}${item.entity_type ? ` · ${item.entity_type}` : ""}`;
    row.querySelector("small").textContent = new Date(item.created_at).toLocaleString();
    list.appendChild(row);
  });
}

async function loadDashboard() {
  statusElement.textContent = "Refreshing analytics…";
  refreshButton.disabled = true;
  try {
    const response = await fetch(`/api/admin/analytics?days=${encodeURIComponent(rangeSelect.value)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Could not load analytics.");
    renderSummary(data.summary);
    renderUsers(data.users, data.current_user_id);
    renderModels(data.model_usage);
    renderFailures(data.recent_failures);
    renderHealth(data.health_history);
    renderAudit(data.audit_log, data.users);
    statusElement.textContent = `Updated ${new Date().toLocaleTimeString()}`;
  } catch (error) {
    statusElement.textContent = error.message;
  } finally {
    refreshButton.disabled = false;
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-CSRFToken": csrfToken},
    body: JSON.stringify(payload),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Action failed.");
  return data;
}

document.getElementById("adminPreviewCleanup").addEventListener("click", async () => {
  statusElement.textContent = "Checking upload storage…";
  try {
    const response = await fetch("/api/admin/cleanup/preview");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Preview failed.");
    statusElement.textContent = data.count
      ? `${data.count} orphan upload(s) found. Review before deleting.`
      : "No orphan uploads found.";
  } catch (error) {
    statusElement.textContent = error.message;
  }
});

document.getElementById("adminRunCleanup").addEventListener("click", async () => {
  if (!window.confirm("Delete files that are not referenced by the database?")) return;
  try {
    const data = await postJson("/api/admin/cleanup/orphans", {confirm: true});
    statusElement.textContent = `Removed ${data.removed?.length || 0} orphan upload(s).`;
    await loadDashboard();
  } catch (error) {
    statusElement.textContent = error.message;
  }
});

document.getElementById("adminPurgeTelemetry").addEventListener("click", async () => {
  const retention = Number(document.getElementById("adminRetentionDays").value || 90);
  if (!window.confirm(`Delete telemetry older than ${retention} days? Audit logs are kept.`)) return;
  try {
    const data = await postJson("/api/admin/telemetry/purge", {retention_days: retention});
    statusElement.textContent =
      `Purged ${data.request_metrics + data.health_events + data.model_events} old telemetry row(s).`;
    await loadDashboard();
  } catch (error) {
    statusElement.textContent = error.message;
  }
});

document.getElementById("adminUsersBody").addEventListener("click", async (event) => {
  const button = event.target.closest(".admin-table-action");
  if (!button) return;
  const userId = Number(button.dataset.userId);
  const currentlyActive = button.dataset.active === "true";
  const action = currentlyActive ? "disable" : "enable";
  if (!window.confirm(`${action[0].toUpperCase()}${action.slice(1)} this account?`)) return;
  button.disabled = true;
  try {
    await postJson(`/api/admin/users/${userId}/status`, {active: !currentlyActive});
    statusElement.textContent = `Account ${action}d.`;
    await loadDashboard();
  } catch (error) {
    statusElement.textContent = error.message;
    button.disabled = false;
  }
});

refreshButton.addEventListener("click", loadDashboard);
rangeSelect.addEventListener("change", loadDashboard);
loadDashboard();
