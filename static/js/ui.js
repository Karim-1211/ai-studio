const MESSAGE_METADATA_PATTERN =
  /\n\n<!--AI_STUDIO_META:([A-Za-z0-9+/=]+)-->$/;


export const elements = {
  model: document.getElementById("model"),
  responseMode: document.getElementById("responseMode"),

  temperature: document.getElementById("temperature"),
  maxTokens: document.getElementById("maxTokens"),
  topP: document.getElementById("topP"),
  topK: document.getElementById("topK"),
  repeatPenalty: document.getElementById("repeatPenalty"),
  contextLength: document.getElementById("contextLength"),
  systemPrompt: document.getElementById("systemPrompt"),
  systemPromptCount: document.getElementById("systemPromptCount"),
  resetSettingsButton: document.getElementById("resetSettingsButton"),
  settingsSaveNote: document.getElementById("settingsSaveNote"),

  themeToggle: document.getElementById("themeToggle"),
  themeIcon: document.getElementById("themeIcon"),
  themeLabel: document.getElementById("themeLabel"),

  systemStatusButton: document.getElementById(
    "systemStatusButton"
  ),
  systemStatusDot: document.getElementById(
    "systemStatusDot"
  ),
  systemStatusLabel: document.getElementById(
    "systemStatusLabel"
  ),
  systemStatusPanel: document.getElementById(
    "systemStatusPanel"
  ),
  systemStatusOverall: document.getElementById(
    "systemStatusOverall"
  ),
  systemStatusComponents: document.getElementById(
    "systemStatusComponents"
  ),
  systemStatusRefresh: document.getElementById(
    "systemStatusRefresh"
  ),
  systemStatusChecked: document.getElementById(
    "systemStatusChecked"
  ),

  chat: document.getElementById("chat"),
  chatList: document.getElementById("chatList"),
  chatSearch: document.getElementById("chatSearch"),

  inputArea: document.getElementById("inputArea"),
  promptInput: document.getElementById("prompt"),
  sendButton: document.getElementById("sendButton"),
  attachmentInput: document.getElementById("attachmentInput"),
  attachmentButton: document.getElementById("attachmentButton"),
  attachmentPreviewList: document.getElementById("attachmentPreviewList"),
  attachmentStatus: document.getElementById("attachmentStatus"),
  voiceInputButton: document.getElementById("voiceInputButton"),
  voiceOutputButton: document.getElementById("voiceOutputButton"),
  voiceStatus: document.getElementById("voiceStatus"),

  newChatButton: document.querySelector(".new-chat"),
  regenerateButton: document.querySelector(".regenerate-chat"),

  documentPanel: document.getElementById("documentPanel"),
  documentPanelBody: document.getElementById("documentPanelBody"),
  documentToggle: document.getElementById("documentToggle"),
  documentCloseButton: document.getElementById("documentCloseButton"),
  documentDrawerBackdrop: document.getElementById("documentDrawerBackdrop"),
  knowledgeSelectionSummary: document.getElementById(
    "knowledgeSelectionSummary"
  ),
  chatKnowledgeTab: document.getElementById("chatKnowledgeTab"),
  globalKnowledgeTab: document.getElementById("globalKnowledgeTab"),
  chatKnowledgePanel: document.getElementById("chatKnowledgePanel"),
  globalKnowledgePanel: document.getElementById("globalKnowledgePanel"),
  documentCount: document.getElementById("documentCount"),
  documentInput: document.getElementById("documentInput"),
  documentUploadButton: document.getElementById("documentUploadButton"),
  documentUploadStatus: document.getElementById("documentUploadStatus"),
  documentList: document.getElementById("documentList"),

  useDocumentsToggle: document.getElementById("useDocumentsToggle"),
  strictDocumentsToggle: document.getElementById("strictDocumentsToggle"),
  documentSelectionSummary: document.getElementById(
    "documentSelectionSummary"
  ),
  selectAllDocumentsButton: document.getElementById(
    "selectAllDocumentsButton"
  ),

  useGlobalDocumentsToggle: document.getElementById(
    "useGlobalDocumentsToggle"
  ),
  globalDocumentCount: document.getElementById(
    "globalDocumentCount"
  ),
  globalDocumentInput: document.getElementById(
    "globalDocumentInput"
  ),
  globalDocumentUploadButton: document.getElementById(
    "globalDocumentUploadButton"
  ),
  globalDocumentUploadStatus: document.getElementById(
    "globalDocumentUploadStatus"
  ),
  globalDocumentList: document.getElementById(
    "globalDocumentList"
  ),
  globalDocumentSelectionSummary: document.getElementById(
    "globalDocumentSelectionSummary"
  ),
  selectAllGlobalDocumentsButton: document.getElementById(
    "selectAllGlobalDocumentsButton"
  ),

  websiteSourceCount: document.getElementById(
    "websiteSourceCount"
  ),
  websiteUrlInput: document.getElementById(
    "websiteUrlInput"
  ),
  websiteAddButton: document.getElementById(
    "websiteAddButton"
  ),
  websiteDiscoverButton: document.getElementById(
    "websiteDiscoverButton"
  ),
  websiteCrawlerMaxPages: document.getElementById(
    "websiteCrawlerMaxPages"
  ),
  websiteCrawlerMaxDepth: document.getElementById(
    "websiteCrawlerMaxDepth"
  ),
  websiteCrawlerUseSitemap: document.getElementById(
    "websiteCrawlerUseSitemap"
  ),
  websiteDiscoveryPanel: document.getElementById(
    "websiteDiscoveryPanel"
  ),
  websiteDiscoverySummary: document.getElementById(
    "websiteDiscoverySummary"
  ),
  websiteDiscoveryList: document.getElementById(
    "websiteDiscoveryList"
  ),
  websiteDiscoverySelectAll: document.getElementById(
    "websiteDiscoverySelectAll"
  ),
  websiteDiscoveryClearAll: document.getElementById(
    "websiteDiscoveryClearAll"
  ),
  websiteDiscoveryCancel: document.getElementById(
    "websiteDiscoveryCancel"
  ),
  websiteIndexSelectedButton: document.getElementById(
    "websiteIndexSelectedButton"
  ),
  websiteStatus: document.getElementById(
    "websiteStatus"
  ),
  websiteSourceList: document.getElementById(
    "websiteSourceList"
  ),
  websiteSelectionSummary: document.getElementById(
    "websiteSelectionSummary"
  ),
  selectAllWebsiteSourcesButton: document.getElementById(
    "selectAllWebsiteSourcesButton"
  ),

  socialSourceCount: document.getElementById("socialSourceCount"),
  socialUrlInput: document.getElementById("socialUrlInput"),
  socialTitleInput: document.getElementById("socialTitleInput"),
  socialManualText: document.getElementById("socialManualText"),
  socialManualCount: document.getElementById("socialManualCount"),
  socialManualValidation: document.getElementById("socialManualValidation"),
  socialManualDetails: document.getElementById("socialManualDetails"),
  socialFallbackHint: document.getElementById("socialFallbackHint"),
  socialOpenSourceButton: document.getElementById("socialOpenSourceButton"),
  socialPasteClipboardButton: document.getElementById("socialPasteClipboardButton"),
  socialAddButton: document.getElementById("socialAddButton"),
  socialManualAddButton: document.getElementById("socialManualAddButton"),
  socialStatus: document.getElementById("socialStatus"),
  socialSourceList: document.getElementById("socialSourceList"),
  socialSelectionSummary: document.getElementById("socialSelectionSummary"),
  selectAllSocialSourcesButton: document.getElementById(
    "selectAllSocialSourcesButton"
  )
};


export function addMessage(text, className) {
  const message = document.createElement("div");

  message.className = className;
  message.innerText = text;

  elements.chat.appendChild(message);
  elements.chat.scrollTop = elements.chat.scrollHeight;

  return message;
}


export function handleChatError(error, messageElement) {
  messageElement.classList.remove("loading");

  if (error.name === "AbortError") {
    messageElement.innerText = "[Generation stopped]";
    return;
  }

  console.error("Chat error:", error);

  messageElement.classList.add("error");
  messageElement.innerText =
    error.message ||
    "Something went wrong. Check the browser console or Flask terminal.";
}


export function readRagSourcesFromResponse(response) {
  const encodedSources = response.headers.get(
    "X-RAG-Sources"
  );

  if (!encodedSources) {
    return [];
  }

  try {
    const jsonText = decodeBase64Url(
      encodedSources
    );

    const parsed = JSON.parse(jsonText);

    return Array.isArray(parsed)
      ? parsed
      : [];

  } catch (error) {
    console.error(
      "Could not decode RAG source metadata:",
      error
    );

    return [];
  }
}


export function renderRagSources(
  container,
  sources,
  compact = false
) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return;
  }

  const existing = container.querySelector(
    ":scope > .rag-sources"
  );

  if (existing) {
    existing.remove();
  }

  const wrapper = document.createElement("details");
  wrapper.className =
    compact
      ? "rag-sources rag-sources-compact"
      : "rag-sources";

  try {
    wrapper.open = sessionStorage.getItem(
      "aiStudioRagSourcesOpen"
    ) === "true";
  } catch (_error) {
    wrapper.open = false;
  }

  const heading = document.createElement("summary");
  heading.className = "rag-sources-heading";
  heading.setAttribute(
    "aria-label",
    `${sources.length} knowledge ${
      sources.length === 1 ? "source" : "sources"
    } used. Toggle source details.`
  );

  const headingMain = document.createElement("span");
  headingMain.className = "rag-sources-heading-main";

  const chevron = document.createElement("span");
  chevron.className = "rag-sources-chevron";
  chevron.setAttribute("aria-hidden", "true");
  chevron.innerText = "›";

  const headingText = document.createElement("strong");
  headingText.innerText =
    `${sources.length} knowledge ${
      sources.length === 1 ? "source" : "sources"
    } used`;

  const typeCounts = sources.reduce((counts, source) => {
    const scope = source.source_scope || "chat";
    counts[scope] = (counts[scope] || 0) + 1;
    return counts;
  }, {});

  const countSummary = document.createElement("small");
  countSummary.className = "rag-sources-count-summary";
  countSummary.innerText = Object.entries(typeCounts)
    .map(([scope, count]) => `${scope}: ${count}`)
    .join(" · ");

  headingMain.appendChild(chevron);
  headingMain.appendChild(headingText);
  headingMain.appendChild(countSummary);

  const badge = document.createElement("span");
  badge.className = "rag-sources-badge";
  badge.innerText = "RAG";

  heading.appendChild(headingMain);
  heading.appendChild(badge);
  wrapper.appendChild(heading);

  const sourceList = document.createElement("div");
  sourceList.className = "rag-sources-list";

  sources.forEach((source, index) => {
    const details = document.createElement("details");
    details.className = "rag-source-item";

    const summary = document.createElement("summary");

    const sourceTitle = document.createElement("span");
    sourceTitle.className = "rag-source-title";

    const scopeLabels = {
      website: "Web",
      social: source.platform || "Social",
      global: "Global",
      attachment: "Attachment",
      vision: "Vision",
      chat: "Chat"
    };

    const scopeLabel = scopeLabels[source.source_scope] || "Chat";
    const scopeBadge = document.createElement("span");
    scopeBadge.className = `rag-source-scope rag-source-scope-${
      source.source_scope || "chat"
    }`;
    scopeBadge.innerText = scopeLabel;

    const sourceName = ["website", "social"].includes(source.source_scope)
      && source.source_url
      ? document.createElement("a")
      : document.createElement("span");

    sourceName.innerText =
      `[Source ${index + 1}] ${source.filename}`;

    if (sourceName.tagName === "A") {
      sourceName.href = source.source_url;
      sourceName.target = "_blank";
      sourceName.rel = "noopener noreferrer";
      sourceName.className = "rag-source-link";
    }

    sourceTitle.appendChild(scopeBadge);
    sourceTitle.appendChild(sourceName);

    const score = document.createElement("span");
    score.className = "rag-source-score";
    score.innerText =
      `${formatRelevanceScore(source.score)} relevant`;

    summary.appendChild(sourceTitle);
    summary.appendChild(score);

    const excerpt = document.createElement("p");
    excerpt.className = "rag-source-excerpt";
    excerpt.innerText =
      source.excerpt ||
      "No excerpt was returned.";

    const metadata = document.createElement("div");
    metadata.className = "rag-source-metadata";

    const metadataParts = [
      `Chunk ${Number(source.chunk_index) + 1}`
    ];

    if (
      ["website", "social"].includes(source.source_scope)
      && source.source_url
    ) {
      try {
        metadataParts.push(
          new URL(source.source_url).hostname
        );
      } catch {
        metadataParts.push("Indexed website");
      }
    }

    metadata.innerText = metadataParts.join(" · ");

    details.appendChild(summary);
    details.appendChild(excerpt);
    details.appendChild(metadata);

    sourceList.appendChild(details);
  });

  wrapper.appendChild(sourceList);
  wrapper.addEventListener("toggle", () => {
    try {
      sessionStorage.setItem(
        "aiStudioRagSourcesOpen",
        String(wrapper.open)
      );
    } catch (_error) {
      // Session storage may be unavailable in privacy-restricted browsers.
    }
  });

  container.appendChild(wrapper);
}


export function serializeMessageWithSources(
  text,
  sources
) {
  if (!Array.isArray(sources) || sources.length === 0) {
    return text;
  }

  const payload = JSON.stringify({
    sources
  });

  return (
    `${text}\n\n` +
    `<!--AI_STUDIO_META:${encodeBase64(payload)}-->`
  );
}


export function splitMessageMetadata(content) {
  const text = String(content ?? "");

  const match = text.match(
    MESSAGE_METADATA_PATTERN
  );

  if (!match) {
    return {
      text,
      sources: []
    };
  }

  try {
    const metadata = JSON.parse(
      decodeBase64(match[1])
    );

    return {
      text: text.replace(
        MESSAGE_METADATA_PATTERN,
        ""
      ),
      sources: Array.isArray(metadata.sources)
        ? metadata.sources
        : []
    };

  } catch (error) {
    console.error(
      "Could not read stored message metadata:",
      error
    );

    return {
      text,
      sources: []
    };
  }
}


function formatRelevanceScore(value) {
  const score = Number(value);

  if (!Number.isFinite(score)) {
    return "0%";
  }

  const percentage = Math.round(
    Math.max(0, Math.min(1, score)) * 100
  );

  return `${percentage}%`;
}


function encodeBase64(value) {
  const bytes = new TextEncoder().encode(value);
  let binary = "";

  bytes.forEach(byte => {
    binary += String.fromCharCode(byte);
  });

  return btoa(binary);
}


function decodeBase64(value) {
  const binary = atob(value);
  const bytes = Uint8Array.from(
    binary,
    character => character.charCodeAt(0)
  );

  return new TextDecoder().decode(bytes);
}


function decodeBase64Url(value) {
  const normalized = value
    .replaceAll("-", "+")
    .replaceAll("_", "/");

  const paddingLength =
    (4 - (normalized.length % 4)) % 4;

  return decodeBase64(
    normalized + "=".repeat(paddingLength)
  );
}
