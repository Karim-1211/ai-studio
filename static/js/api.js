function getCsrfToken() {
  return document.querySelector(
    'meta[name="csrf-token"]'
  )?.content || "";
}


async function apiFetch(url, options = {}) {
  const method = String(options.method || "GET").toUpperCase();
  const headers = new Headers(options.headers || {});

  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    const token = getCsrfToken();
    if (token) {
      headers.set("X-CSRFToken", token);
    }
  }

  const response = await window.fetch(url, {
    ...options,
    credentials: "same-origin",
    headers
  });

  if (response.status === 401) {
    const next = encodeURIComponent(
      `${window.location.pathname}${window.location.search}`
    );
    window.location.assign(`/login?next=${next}`);
  }

  return response;
}


async function readJsonResponse(response) {
  const contentType = response.headers.get("content-type") || "";

  let data;

  if (contentType.includes("application/json")) {
    data = await response.json();
  } else {
    const text = await response.text();
    data = { error: text || "Unexpected server response." };
  }

  if (!response.ok) {
    const message =
      data.error ||
      data.details ||
      `Request failed with status ${response.status}.`;

    const error = new Error(message);
    error.code = data.code || "request_error";
    error.status = response.status;
    error.details = data.details || "";
    throw error;
  }

  return data;
}


export async function fetchModels() {
  const response = await apiFetch("/models");
  return await readJsonResponse(response);
}


export async function sendChatRequest(payload, signal) {
  return await apiFetch("/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload),
    signal
  });
}


export async function createChatInDatabase() {
  const response = await apiFetch("/api/chats", {
    method: "POST"
  });

  return await readJsonResponse(response);
}


export async function fetchChatsFromDatabase() {
  const response = await apiFetch("/api/chats?view=all");
  return await readJsonResponse(response);
}


export async function fetchMessagesFromDatabase(chatId) {
  const response = await apiFetch(
    `/api/chats/${chatId}/messages`
  );

  return await readJsonResponse(response);
}


export async function saveMessageToDatabase(chatId, payload) {
  const response = await apiFetch(
    `/api/chats/${chatId}/messages`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }
  );

  return await readJsonResponse(response);
}


export async function updateChatInDatabase(chatId, payload) {
  const response = await apiFetch(
    `/api/chats/${chatId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }
  );

  return await readJsonResponse(response);
}


export async function deleteChatFromDatabase(chatId) {
  const response = await apiFetch(
    `/api/chats/${chatId}`,
    {
      method: "DELETE"
    }
  );

  return await readJsonResponse(response);
}


export async function fetchChatDocuments(chatId) {
  const response = await apiFetch(
    `/api/chats/${chatId}/documents`
  );

  return await readJsonResponse(response);
}


export async function uploadChatDocument(chatId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiFetch(
    `/api/chats/${chatId}/documents`,
    {
      method: "POST",
      body: formData
    }
  );

  return await readJsonResponse(response);
}


export async function deleteDocumentFromDatabase(documentId) {
  const response = await apiFetch(
    `/api/documents/${documentId}`,
    {
      method: "DELETE"
    }
  );

  return await readJsonResponse(response);
}


export async function fetchGlobalDocuments() {
  const response = await apiFetch(
    "/api/global-documents"
  );

  return await readJsonResponse(response);
}


export async function uploadGlobalDocument(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiFetch(
    "/api/global-documents",
    {
      method: "POST",
      body: formData
    }
  );

  return await readJsonResponse(response);
}


export async function deleteGlobalDocumentFromDatabase(documentId) {
  const response = await apiFetch(
    `/api/global-documents/${documentId}`,
    {
      method: "DELETE"
    }
  );

  return await readJsonResponse(response);
}


export async function fetchSystemHealth() {
  const response = await apiFetch(
    "/api/health",
    {
      cache: "no-store"
    }
  );

  return await readJsonResponse(response);
}


export async function fetchWebsiteSources() {
  const response = await apiFetch(
    "/api/website-sources"
  );

  return await readJsonResponse(response);
}


export async function addWebsiteSource(url) {
  const response = await apiFetch(
    "/api/website-sources",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    }
  );

  return await readJsonResponse(response);
}


export async function refreshWebsiteSource(websiteSourceId) {
  const response = await apiFetch(
    `/api/website-sources/${websiteSourceId}/refresh`,
    {
      method: "POST"
    }
  );

  return await readJsonResponse(response);
}


export async function deleteWebsiteSourceFromDatabase(websiteSourceId) {
  const response = await apiFetch(
    `/api/website-sources/${websiteSourceId}`,
    {
      method: "DELETE"
    }
  );

  return await readJsonResponse(response);
}


export async function discoverWebsitePages(payload) {
  const response = await apiFetch(
    "/api/website-crawler/discover",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(payload)
    }
  );

  return await readJsonResponse(response);
}


export async function indexWebsitePages(urls) {
  const response = await apiFetch(
    "/api/website-crawler/index",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ urls })
    }
  );

  return await readJsonResponse(response);
}


export async function refreshWebsiteDomain(domain) {
  const response = await apiFetch(
    `/api/website-crawler/sites/${encodeURIComponent(domain)}/refresh`,
    { method: "POST" }
  );

  return await readJsonResponse(response);
}


export async function deleteWebsiteDomain(domain) {
  const response = await apiFetch(
    `/api/website-crawler/sites/${encodeURIComponent(domain)}`,
    { method: "DELETE" }
  );

  return await readJsonResponse(response);
}


export async function uploadMessageAttachment(chatId, file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiFetch(
    `/api/chats/${chatId}/attachments`,
    {
      method: "POST",
      body: formData
    }
  );

  return await readJsonResponse(response);
}


export async function deleteMessageAttachment(attachmentId) {
  const response = await apiFetch(
    `/api/attachments/${attachmentId}`,
    { method: "DELETE" }
  );

  return await readJsonResponse(response);
}


export async function fetchSocialSources() {
  const response = await apiFetch("/api/social-sources");
  return await readJsonResponse(response);
}


export async function addSocialSource({ url, title, manualText, importMode }) {
  const response = await apiFetch(
    "/api/social-sources",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        url,
        title,
        manual_text: manualText,
        import_mode: importMode || (manualText ? "manual" : "public")
      })
    }
  );

  return await readJsonResponse(response);
}


export async function refreshSocialSource(sourceId) {
  const response = await apiFetch(
    `/api/social-sources/${sourceId}/refresh`,
    { method: "POST" }
  );

  return await readJsonResponse(response);
}


export async function deleteSocialSourceFromDatabase(sourceId) {
  const response = await apiFetch(
    `/api/social-sources/${sourceId}`,
    { method: "DELETE" }
  );

  return await readJsonResponse(response);
}


export async function fetchChatFolders() {
  const response = await apiFetch("/api/chat-folders");
  return await readJsonResponse(response);
}

export async function createChatFolder(name) {
  const response = await apiFetch("/api/chat-folders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  return await readJsonResponse(response);
}

export async function updateChatFolder(folderId, name) {
  const response = await apiFetch(`/api/chat-folders/${folderId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name })
  });
  return await readJsonResponse(response);
}

export async function deleteChatFolder(folderId) {
  const response = await apiFetch(`/api/chat-folders/${folderId}`, {
    method: "DELETE"
  });
  return await readJsonResponse(response);
}

export async function fetchChatTags() {
  const response = await apiFetch("/api/chat-tags");
  return await readJsonResponse(response);
}

export async function createChatTag(name, color = "violet") {
  const response = await apiFetch("/api/chat-tags", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, color })
  });
  return await readJsonResponse(response);
}

export async function updateChatTag(tagId, payload) {
  const response = await apiFetch(`/api/chat-tags/${tagId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return await readJsonResponse(response);
}

export async function deleteChatTag(tagId) {
  const response = await apiFetch(`/api/chat-tags/${tagId}`, {
    method: "DELETE"
  });
  return await readJsonResponse(response);
}

export async function bulkUpdateChats(payload) {
  const response = await apiFetch("/api/chats/bulk", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return await readJsonResponse(response);
}

export async function downloadWorkspaceBackup() {
  const response = await apiFetch("/api/workspace/backup", {
    cache: "no-store"
  });
  if (!response.ok) {
    return await readJsonResponse(response);
  }
  return await response.blob();
}

export async function restoreWorkspaceBackup(file) {
  const formData = new FormData();
  formData.append("backup", file);
  const response = await apiFetch("/api/workspace/restore", {
    method: "POST",
    body: formData
  });
  return await readJsonResponse(response);
}

export async function fetchPromptTemplates(params = {}) {
  const query = new URLSearchParams();
  if (params.search) query.set("search", params.search);
  if (params.category) query.set("category", params.category);
  if (params.favorites) query.set("favorites", "true");
  const suffix = query.toString() ? `?${query.toString()}` : "";
  const response = await apiFetch(`/api/prompt-templates${suffix}`);
  return await readJsonResponse(response);
}

export async function createPromptTemplate(payload) {
  const response = await apiFetch("/api/prompt-templates", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return await readJsonResponse(response);
}

export async function updatePromptTemplate(templateId, payload) {
  const response = await apiFetch(`/api/prompt-templates/${templateId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return await readJsonResponse(response);
}

export async function deletePromptTemplate(templateId) {
  const response = await apiFetch(`/api/prompt-templates/${templateId}`, {
    method: "DELETE"
  });
  return await readJsonResponse(response);
}

export async function recordPromptTemplateUse(templateId) {
  const response = await apiFetch(`/api/prompt-templates/${templateId}/use`, {
    method: "POST"
  });
  return await readJsonResponse(response);
}

export async function branchChatFromMessage(chatId, payload) {
  const response = await apiFetch(`/api/chats/${chatId}/branch`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  return await readJsonResponse(response);
}
