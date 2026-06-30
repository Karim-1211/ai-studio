import {
  fetchChatDocuments,
  uploadChatDocument,
  deleteDocumentFromDatabase,
  fetchGlobalDocuments,
  uploadGlobalDocument,
  deleteGlobalDocumentFromDatabase,
  fetchWebsiteSources,
  addWebsiteSource,
  refreshWebsiteSource,
  deleteWebsiteSourceFromDatabase,
  discoverWebsitePages,
  indexWebsitePages,
  refreshWebsiteDomain,
  deleteWebsiteDomain,
  fetchSocialSources,
  addSocialSource,
  refreshSocialSource,
  deleteSocialSourceFromDatabase
} from "./api.js";

import { elements } from "./ui.js";
import { getActiveChat } from "./sidebar.js";


const MAX_FILE_SIZE = 20 * 1024 * 1024;

// Manual fallback compatibility codes: "social_public_fetch_failed", "social_manual_required"

const ALLOWED_EXTENSIONS = new Set([
  "pdf",
  "docx",
  "txt",
  "png",
  "jpg",
  "jpeg",
  "webp"
]);

const IMAGE_EXTENSIONS = new Set([
  "png",
  "jpg",
  "jpeg",
  "webp"
]);

const STORAGE_KEYS = {
  useDocuments: "aiStudioUseDocuments",
  strictDocuments: "aiStudioStrictDocuments",
  useGlobalDocuments: "aiStudioUseGlobalDocuments",
  globalSelection: "aiStudioGlobalDocumentSelection",
  websiteSelection: "aiStudioWebsiteSourceSelection",
  socialSelection: "aiStudioSocialSourceSelection",
  drawerOpen: "aiStudioKnowledgeDrawerOpen",
  activeTab: "aiStudioKnowledgeActiveTab"
};

const CHAT_SELECTION_STORAGE_PREFIX =
  "aiStudioDocumentSelection:";

let initialized = false;
let loadSequence = 0;
let lastRenderedChatId = null;

const readyChatDocumentIdsByChat = new Map();
const selectedChatDocumentIdsByChat = new Map();

let readyGlobalDocumentIds = [];
let selectedGlobalDocumentIds = new Set();
let globalSelectionInitialized = false;

let readyWebsiteSourceIds = [];
let selectedWebsiteSourceIds = new Set();
let websiteSelectionInitialized = false;
let discoveredWebsitePages = [];
let discoveredWebsiteDomain = "";

let readySocialSourceIds = [];
let selectedSocialSourceIds = new Set();
let socialSelectionInitialized = false;


export function initializeDocumentManager() {
  if (initialized) {
    return;
  }

  initialized = true;

  elements.useDocumentsToggle.checked =
    readStoredBoolean(
      STORAGE_KEYS.useDocuments,
      true
    );

  elements.strictDocumentsToggle.checked =
    readStoredBoolean(
      STORAGE_KEYS.strictDocuments,
      true
    );

  elements.useGlobalDocumentsToggle.checked =
    readStoredBoolean(
      STORAGE_KEYS.useGlobalDocuments,
      true
    );

  setKnowledgeTab(
    localStorage.getItem(
      STORAGE_KEYS.activeTab
    ) === "global"
      ? "global"
      : "chat"
  );

  setDocumentDrawerOpen(
    readStoredBoolean(
      STORAGE_KEYS.drawerOpen,
      false
    ),
    false
  );

  elements.documentUploadButton.addEventListener(
    "click",
    () => {
      if (!getActiveChat()) {
        setStatus(
          "chat",
          "Create or select a chat before uploading documents.",
          "error"
        );
        return;
      }

      elements.documentInput.click();
    }
  );

  elements.globalDocumentUploadButton.addEventListener(
    "click",
    () => elements.globalDocumentInput.click()
  );

  elements.documentInput.addEventListener(
    "change",
    () => uploadSelectedDocuments("chat")
  );

  elements.globalDocumentInput.addEventListener(
    "change",
    () => uploadSelectedDocuments("global")
  );

  elements.websiteAddButton.addEventListener(
    "click",
    addWebsiteFromInput
  );

  elements.websiteDiscoverButton.addEventListener(
    "click",
    discoverWebsiteFromInput
  );

  elements.websiteDiscoverySelectAll.addEventListener(
    "click",
    () => setAllDiscoveredPagesSelected(true)
  );

  elements.websiteDiscoveryClearAll.addEventListener(
    "click",
    () => setAllDiscoveredPagesSelected(false)
  );

  elements.websiteDiscoveryCancel.addEventListener(
    "click",
    clearWebsiteDiscovery
  );

  elements.websiteIndexSelectedButton.addEventListener(
    "click",
    indexSelectedWebsitePages
  );

  elements.websiteUrlInput.addEventListener(
    "keydown",
    event => {
      if (event.key === "Enter") {
        event.preventDefault();
        addWebsiteFromInput();
      }
    }
  );

  elements.socialAddButton.addEventListener(
    "click",
    () => addSocialFromInput("public")
  );

  elements.socialManualAddButton.addEventListener(
    "click",
    () => addSocialFromInput("manual")
  );

  elements.socialOpenSourceButton.addEventListener(
    "click",
    openSocialSourceLink
  );

  elements.socialPasteClipboardButton.addEventListener(
    "click",
    pasteSocialClipboard
  );

  elements.socialUrlInput.addEventListener(
    "keydown",
    event => {
      if (event.key === "Enter") {
        event.preventDefault();
        addSocialFromInput("public");
      }
    }
  );

  elements.socialManualText.addEventListener(
    "input",
    () => {
      elements.socialManualDetails.classList.remove(
        "needs-attention"
      );
      updateSocialManualState();
    }
  );

  updateSocialManualState();

  elements.documentToggle.addEventListener(
    "click",
    toggleDocumentPanel
  );

  elements.documentCloseButton.addEventListener(
    "click",
    () => setDocumentDrawerOpen(false)
  );

  elements.documentDrawerBackdrop.addEventListener(
    "click",
    () => setDocumentDrawerOpen(false)
  );

  elements.chatKnowledgeTab.addEventListener(
    "click",
    () => setKnowledgeTab("chat")
  );

  elements.globalKnowledgeTab.addEventListener(
    "click",
    () => setKnowledgeTab("global")
  );

  document.addEventListener(
    "keydown",
    event => {
      if (
        event.key === "Escape"
        && elements.documentPanel.classList.contains(
          "drawer-open"
        )
      ) {
        setDocumentDrawerOpen(false);
        elements.documentToggle.focus();
      }
    }
  );

  elements.useDocumentsToggle.addEventListener(
    "change",
    () => {
      localStorage.setItem(
        STORAGE_KEYS.useDocuments,
        String(elements.useDocumentsToggle.checked)
      );
      updateDocumentControls();
    }
  );

  elements.strictDocumentsToggle.addEventListener(
    "change",
    () => {
      localStorage.setItem(
        STORAGE_KEYS.strictDocuments,
        String(elements.strictDocumentsToggle.checked)
      );
    }
  );

  elements.useGlobalDocumentsToggle.addEventListener(
    "change",
    () => {
      localStorage.setItem(
        STORAGE_KEYS.useGlobalDocuments,
        String(
          elements.useGlobalDocumentsToggle.checked
        )
      );
      updateDocumentControls();
    }
  );

  elements.selectAllDocumentsButton.addEventListener(
    "click",
    toggleSelectAllChatDocuments
  );

  elements.selectAllGlobalDocumentsButton.addEventListener(
    "click",
    toggleSelectAllGlobalDocuments
  );

  elements.selectAllWebsiteSourcesButton.addEventListener(
    "click",
    toggleSelectAllWebsiteSources
  );

  elements.selectAllSocialSourcesButton.addEventListener(
    "click",
    toggleSelectAllSocialSources
  );

  const observer = new MutationObserver(() => {
    const activeChatId =
      getActiveChat()?.id ?? null;

    if (activeChatId !== lastRenderedChatId) {
      loadDocumentsForActiveChat();
    }
  });

  observer.observe(
    elements.chatList,
    {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ["class"]
    }
  );
}


export function getDocumentRequestSettings() {
  const activeChatId =
    getActiveChat()?.id ?? null;

  const readyChatIds = activeChatId
    ? readyChatDocumentIdsByChat.get(activeChatId) || []
    : [];

  const selectedChatIds = activeChatId
    ? Array.from(
        getSelectedChatSet(activeChatId)
      ).filter(documentId =>
        readyChatIds.includes(documentId)
      )
    : [];

  const selectedGlobalIds = Array.from(
    selectedGlobalDocumentIds
  ).filter(documentId =>
    readyGlobalDocumentIds.includes(documentId)
  );

  const selectedWebsiteIds = Array.from(
    selectedWebsiteSourceIds
  ).filter(sourceId =>
    readyWebsiteSourceIds.includes(sourceId)
  );

  const selectedSocialIds = Array.from(
    selectedSocialSourceIds
  ).filter(sourceId =>
    readySocialSourceIds.includes(sourceId)
  );

  const useGlobalLibrary =
    elements.useGlobalDocumentsToggle.checked;

  const hasAvailableKnowledge =
    readyChatIds.length > 0
    || (
      useGlobalLibrary
      && (
        readyGlobalDocumentIds.length > 0
        || readyWebsiteSourceIds.length > 0
        || readySocialSourceIds.length > 0
      )
    );

  return {
    use_documents:
      elements.useDocumentsToggle.checked
      && hasAvailableKnowledge,

    strict_documents:
      elements.strictDocumentsToggle.checked,

    document_ids: selectedChatIds,

    use_global_documents:
      useGlobalLibrary
      && selectedGlobalIds.length > 0,

    global_document_ids:
      useGlobalLibrary
        ? selectedGlobalIds
        : [],

    use_website_sources:
      useGlobalLibrary
      && selectedWebsiteIds.length > 0,

    website_source_ids:
      useGlobalLibrary
        ? selectedWebsiteIds
        : [],

    use_social_sources:
      useGlobalLibrary
      && selectedSocialIds.length > 0,

    social_source_ids:
      useGlobalLibrary
        ? selectedSocialIds
        : []
  };
}


export async function loadDocumentsForActiveChat() {
  const activeChat = getActiveChat();
  const chatId = activeChat?.id ?? null;
  const sequence = ++loadSequence;

  lastRenderedChatId = chatId;
  elements.documentUploadButton.disabled = !chatId;

  elements.documentList.innerHTML = `
    <div class="document-loading">
      Loading chat documents...
    </div>
  `;

  elements.globalDocumentList.innerHTML = `
    <div class="document-loading">
      Loading global files...
    </div>
  `;

  elements.websiteSourceList.innerHTML = `
    <div class="document-loading">
      Loading website pages...
    </div>
  `;

  elements.socialSourceList.innerHTML = `
    <div class="document-loading">
      Loading social sources...
    </div>
  `;

  try {
    const [
      chatDocuments,
      globalDocuments,
      websiteSources,
      socialSources
    ] = await Promise.all([
      chatId
        ? fetchChatDocuments(chatId)
        : Promise.resolve([]),
      fetchGlobalDocuments(),
      fetchWebsiteSources(),
      fetchSocialSources()
    ]);

    if (
      sequence !== loadSequence
      || (getActiveChat()?.id ?? null) !== chatId
    ) {
      return;
    }

    if (chatId) {
      initializeChatSelection(
        chatId,
        chatDocuments
      );
      renderChatDocuments(
        chatId,
        chatDocuments
      );
    } else {
      readyChatDocumentIdsByChat.delete(chatId);
      elements.documentCount.innerText = "0 files";
      elements.documentList.innerHTML = "";
      renderEmptyState(
        elements.documentList,
        "Create or select a chat to manage chat documents."
      );
    }

    initializeGlobalSelection(globalDocuments);
    initializeWebsiteSelection(websiteSources);
    initializeSocialSelection(socialSources);

    renderGlobalDocuments(globalDocuments);
    renderWebsiteSources(websiteSources);
    renderSocialSources(socialSources);
    updateDocumentControls();

  } catch (error) {
    console.error(
      "Knowledge loading error:",
      error
    );

    if (sequence !== loadSequence) {
      return;
    }

    elements.documentList.innerHTML = "";
    elements.globalDocumentList.innerHTML = "";
    elements.websiteSourceList.innerHTML = "";
    elements.socialSourceList.innerHTML = "";

    renderEmptyState(
      elements.documentList,
      "Could not load chat documents.",
      true
    );

    renderEmptyState(
      elements.globalDocumentList,
      "Could not load global files.",
      true
    );

    renderEmptyState(
      elements.websiteSourceList,
      error.message || "Could not load website sources.",
      true
    );

    renderEmptyState(
      elements.socialSourceList,
      error.message || "Could not load social sources.",
      true
    );

    updateDocumentControls();
  }
}


async function uploadSelectedDocuments(scope) {
  const activeChat = getActiveChat();

  const input = scope === "global"
    ? elements.globalDocumentInput
    : elements.documentInput;

  const button = scope === "global"
    ? elements.globalDocumentUploadButton
    : elements.documentUploadButton;

  const files = Array.from(input.files || []);
  input.value = "";

  if (files.length === 0) {
    return;
  }

  if (scope === "chat" && !activeChat) {
    setStatus(
      "chat",
      "Create or select a chat before uploading documents.",
      "error"
    );
    return;
  }

  for (const file of files) {
    const validationError = validateFile(file);

    if (validationError) {
      setStatus(scope, validationError, "error");
      return;
    }
  }

  button.disabled = true;
  const extractionResults = [];

  try {
    for (
      let index = 0;
      index < files.length;
      index += 1
    ) {
      const file = files[index];
      const extension = getExtension(file.name);

      setStatus(
        scope,
        buildProcessingMessage(
          file.name,
          extension,
          index + 1,
          files.length
        ),
        "working"
      );

      let result;

      if (scope === "global") {
        result = await uploadGlobalDocument(file);

        const documentId = Number(
          result?.document?.id
        );

        if (Number.isInteger(documentId)) {
          selectedGlobalDocumentIds.add(documentId);
          saveGlobalSelection();
        }
      } else {
        result = await uploadChatDocument(
          activeChat.id,
          file
        );

        const documentId = Number(
          result?.document?.id
        );

        if (Number.isInteger(documentId)) {
          const selected = getSelectedChatSet(
            activeChat.id
          );

          selected.add(documentId);
          saveChatSelection(
            activeChat.id,
            selected
          );
        }
      }

      extractionResults.push(
        result?.extraction || {}
      );
    }

    await loadDocumentsForActiveChat();

    setStatus(
      scope,
      buildUploadSuccessMessage(
        files.length,
        extractionResults
      ),
      "success"
    );

  } catch (error) {
    console.error(
      `${scope} document upload error:`,
      error
    );

    await loadDocumentsForActiveChat();

    setStatus(
      scope,
      error.message || "Document upload failed.",
      "error"
    );
  } finally {
    button.disabled = false;
  }
}


async function addWebsiteFromInput() {
  const url = elements.websiteUrlInput.value.trim();

  if (!url) {
    setStatus(
      "website",
      "Enter a public website URL.",
      "error"
    );
    return;
  }

  try {
    const parsed = new URL(url);

    if (![
      "http:",
      "https:"
    ].includes(parsed.protocol)) {
      throw new Error();
    }
  } catch {
    setStatus(
      "website",
      "Enter a complete http:// or https:// URL.",
      "error"
    );
    return;
  }

  setWebsiteActionsDisabled(true);

  setStatus(
    "website",
    "Downloading, cleaning, embedding, and indexing the webpage...",
    "working"
  );

  try {
    const result = await addWebsiteSource(url);
    const sourceId = Number(result?.website?.id);

    if (Number.isInteger(sourceId)) {
      selectedWebsiteSourceIds.add(sourceId);
      saveWebsiteSelection();
    }

    elements.websiteUrlInput.value = "";
    await loadDocumentsForActiveChat();

    setStatus(
      "website",
      "Website page indexed and selected.",
      "success"
    );

  } catch (error) {
    console.error(
      "Website indexing error:",
      error
    );

    setStatus(
      "website",
      error.message || "Website indexing failed.",
      "error"
    );
  } finally {
    setWebsiteActionsDisabled(false);
  }
}


async function discoverWebsiteFromInput() {
  const url = elements.websiteUrlInput.value.trim();

  if (!isValidHttpUrl(url)) {
    setStatus(
      "website",
      "Enter a complete public http:// or https:// website URL.",
      "error"
    );
    return;
  }

  const maxPages = clampInteger(
    elements.websiteCrawlerMaxPages.value,
    1,
    100,
    25
  );
  const maxDepth = clampInteger(
    elements.websiteCrawlerMaxDepth.value,
    0,
    5,
    2
  );

  elements.websiteCrawlerMaxPages.value = String(maxPages);
  elements.websiteCrawlerMaxDepth.value = String(maxDepth);
  setWebsiteActionsDisabled(true);
  clearWebsiteDiscovery(false);

  setStatus(
    "website",
    "Checking sitemap.xml and discovering internal pages...",
    "working"
  );

  try {
    const result = await discoverWebsitePages({
      url,
      max_pages: maxPages,
      max_depth: maxDepth,
      use_sitemap: elements.websiteCrawlerUseSitemap.checked
    });

    discoveredWebsitePages = Array.isArray(result.pages)
      ? result.pages
      : [];
    discoveredWebsiteDomain = result.domain || "";

    renderWebsiteDiscovery(result);

    const availableCount = discoveredWebsitePages.filter(
      page => !page.already_indexed
    ).length;

    setStatus(
      "website",
      `${discoveredWebsitePages.length} page${discoveredWebsitePages.length === 1 ? "" : "s"} discovered. ${availableCount} available to index.`,
      "success"
    );
  } catch (error) {
    console.error("Website discovery error:", error);
    setStatus(
      "website",
      error.message || "Website discovery failed.",
      "error"
    );
  } finally {
    setWebsiteActionsDisabled(false);
  }
}


function renderWebsiteDiscovery(result) {
  elements.websiteDiscoveryList.innerHTML = "";
  elements.websiteDiscoveryPanel.hidden = false;

  const sitemapLabel = result.used_sitemap
    ? "Sitemap used"
    : "Link crawl";
  const skippedLabel = result.skipped_count
    ? ` · ${result.skipped_count} skipped`
    : "";

  elements.websiteDiscoverySummary.innerText =
    `${discoveredWebsitePages.length} pages · ${sitemapLabel}${skippedLabel}`;

  discoveredWebsitePages.forEach((page, index) => {
    const row = window.document.createElement("label");
    row.className = "website-discovery-item";

    if (page.already_indexed) {
      row.classList.add("is-indexed");
    }

    const checkbox = window.document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.discoveryIndex = String(index);
    checkbox.checked = !page.already_indexed;
    checkbox.disabled = Boolean(page.already_indexed);
    checkbox.addEventListener(
      "change",
      updateWebsiteDiscoverySelection
    );

    const content = window.document.createElement("span");
    content.className = "website-discovery-content";

    const title = window.document.createElement("strong");
    title.innerText = page.title || page.path || page.url;

    const metadata = window.document.createElement("span");
    metadata.innerText = page.already_indexed
      ? `${page.path || "/"} · Already indexed`
      : `${page.path || "/"} · ${page.source || "crawl"}`;

    content.appendChild(title);
    content.appendChild(metadata);

    row.appendChild(checkbox);
    row.appendChild(content);
    elements.websiteDiscoveryList.appendChild(row);
  });

  updateWebsiteDiscoverySelection();
}


function setAllDiscoveredPagesSelected(selected) {
  elements.websiteDiscoveryList
    .querySelectorAll('input[type="checkbox"]:not(:disabled)')
    .forEach(checkbox => {
      checkbox.checked = selected;
    });

  updateWebsiteDiscoverySelection();
}


function updateWebsiteDiscoverySelection() {
  const selectable = Array.from(
    elements.websiteDiscoveryList.querySelectorAll(
      'input[type="checkbox"]:not(:disabled)'
    )
  );
  const selected = selectable.filter(
    checkbox => checkbox.checked
  );

  elements.websiteIndexSelectedButton.disabled =
    selected.length === 0;

  elements.websiteIndexSelectedButton.innerText =
    selected.length > 0
      ? `Index ${selected.length} selected page${selected.length === 1 ? "" : "s"}`
      : "Index selected pages";
}


async function indexSelectedWebsitePages() {
  const selectedUrls = Array.from(
    elements.websiteDiscoveryList.querySelectorAll(
      'input[type="checkbox"]:checked:not(:disabled)'
    )
  )
    .map(checkbox => {
      const index = Number(checkbox.dataset.discoveryIndex);
      return discoveredWebsitePages[index]?.url || "";
    })
    .filter(Boolean);

  if (selectedUrls.length === 0) {
    setStatus(
      "website",
      "Select at least one discovered page.",
      "error"
    );
    return;
  }

  elements.websiteIndexSelectedButton.disabled = true;
  elements.websiteDiscoveryCancel.disabled = true;
  setWebsiteActionsDisabled(true);

  setStatus(
    "website",
    `Indexing ${selectedUrls.length} selected page${selectedUrls.length === 1 ? "" : "s"}. This can take a few minutes...`,
    "working"
  );

  try {
    const result = await indexWebsitePages(selectedUrls);
    const indexedSources = [
      ...(Array.isArray(result.created) ? result.created : []),
      ...(Array.isArray(result.existing) ? result.existing : [])
    ];

    indexedSources.forEach(source => {
      const sourceId = Number(source.id);
      if (Number.isInteger(sourceId)) {
        selectedWebsiteSourceIds.add(sourceId);
      }
    });

    saveWebsiteSelection();
    await loadDocumentsForActiveChat();
    clearWebsiteDiscovery();

    setStatus(
      "website",
      result.message || "Selected website pages were indexed.",
      result.failed_count ? "working" : "success"
    );
  } catch (error) {
    console.error("Website batch indexing error:", error);
    setStatus(
      "website",
      error.message || "The selected pages could not be indexed.",
      "error"
    );
  } finally {
    elements.websiteDiscoveryCancel.disabled = false;
    setWebsiteActionsDisabled(false);
    updateWebsiteDiscoverySelection();
  }
}


function clearWebsiteDiscovery(resetData = true) {
  elements.websiteDiscoveryPanel.hidden = true;
  elements.websiteDiscoveryList.innerHTML = "";
  elements.websiteDiscoverySummary.innerText = "0 pages";

  if (resetData) {
    discoveredWebsitePages = [];
    discoveredWebsiteDomain = "";
  }
}


function setWebsiteActionsDisabled(disabled) {
  elements.websiteAddButton.disabled = disabled;
  elements.websiteDiscoverButton.disabled = disabled;
  elements.websiteUrlInput.disabled = disabled;
}


function isValidHttpUrl(value) {
  if (!value) {
    return false;
  }

  try {
    const parsed = new URL(value);
    return ["http:", "https:"].includes(parsed.protocol);
  } catch {
    return false;
  }
}


function clampInteger(value, minimum, maximum, fallback) {
  const parsed = Number.parseInt(value, 10);
  const normalized = Number.isFinite(parsed)
    ? parsed
    : fallback;

  return Math.min(maximum, Math.max(minimum, normalized));
}


async function addSocialFromInput(mode = "public") {
  const url = elements.socialUrlInput.value.trim();
  const title = elements.socialTitleInput.value.trim();
  const manualText = elements.socialManualText.value.trim();
  const useManualContent = mode === "manual";

  if (!url) {
    setStatus(
      "social",
      "Enter a complete public social-media URL.",
      "error"
    );
    elements.socialUrlInput.focus();
    return;
  }

  try {
    const parsed = new URL(url);

    if (!["http:", "https:"].includes(parsed.protocol)) {
      throw new Error();
    }
  } catch {
    setStatus(
      "social",
      "Enter a complete http:// or https:// social-media URL.",
      "error"
    );
    elements.socialUrlInput.focus();
    return;
  }

  if (useManualContent && manualText.length < 40) {
    elements.socialManualDetails.open = true;
    elements.socialManualDetails.classList.add(
      "needs-attention"
    );
    setStatus(
      "social",
      "Paste at least 40 readable characters from the social page or post.",
      "error"
    );
    elements.socialManualText.focus();
    return;
  }

  setSocialImportControlsDisabled(true);

  setStatus(
    "social",
    useManualContent
      ? "Embedding the pasted social content..."
      : "Reading and indexing the public social page...",
    "working"
  );

  try {
    const result = await addSocialSource({
      url,
      title,
      manualText: useManualContent ? manualText : "",
      importMode: useManualContent ? "manual" : "public"
    });

    if (result?.manual_required) {
      elements.socialManualDetails.open = true;
      elements.socialManualDetails.classList.add(
        "needs-attention"
      );
      elements.socialFallbackHint.innerText =
        result.message
        || "Automatic import is unavailable. Open the source, copy its visible content, paste it below, and index it.";

      if (
        !elements.socialTitleInput.value.trim()
        && result.suggested_title
      ) {
        elements.socialTitleInput.value = result.suggested_title;
      }

      setStatus(
        "social",
        result.platform === "Google Business Profile"
          ? "Google Business Profile needs a configured Places API key or pasted business details."
          : "This public profile did not expose readable content. Use Open source and Paste from clipboard below.",
        "working"
      );
      window.setTimeout(
        () => elements.socialOpenSourceButton.focus(),
        0
      );
      return;
    }

    const sourceId = Number(result?.social_source?.id);

    if (Number.isInteger(sourceId)) {
      selectedSocialSourceIds.add(sourceId);
      saveSocialSelection();
    }

    elements.socialUrlInput.value = "";
    elements.socialTitleInput.value = "";
    elements.socialManualText.value = "";
    updateSocialManualState();
    elements.socialManualDetails.open = false;
    elements.socialManualDetails.classList.remove(
      "needs-attention"
    );
    await loadDocumentsForActiveChat();

    setStatus(
      "social",
      useManualContent
        ? "Pasted social content indexed and selected."
        : "Public social page indexed and selected.",
      "success"
    );
  } catch (error) {
    console.error("Social indexing error:", error);

    if (
      !useManualContent
      && [
        "social_public_fetch_failed",
        "social_manual_required",
        "facebook_share_link_manual_required",
        "google_places_api_key_required",
        "google_business_query_missing"
      ].includes(error.code)
    ) {
      elements.socialManualDetails.open = true;
      elements.socialManualDetails.classList.add(
        "needs-attention"
      );
      elements.socialFallbackHint.innerText =
        error.message
        || "Automatic import is unavailable. Open the source, copy the visible About text, caption, description, post text, or business details, then paste and index it below.";

      setStatus(
        "social",
        "Manual import is ready below. This is a platform-access limitation, not an AI Studio database error.",
        "working"
      );

      window.setTimeout(
        () => elements.socialOpenSourceButton.focus(),
        0
      );
    } else {
      setStatus(
        "social",
        error.message
          || "The social source could not be indexed.",
        "error"
      );
    }
  } finally {
    setSocialImportControlsDisabled(false);
  }
}


function openSocialSourceLink() {
  const url = elements.socialUrlInput.value.trim();

  if (!isValidHttpUrl(url)) {
    setStatus(
      "social",
      "Enter a complete social-media or Google Maps URL first.",
      "error"
    );
    elements.socialUrlInput.focus();
    return;
  }

  window.open(url, "_blank", "noopener,noreferrer");
}


async function pasteSocialClipboard() {
  if (!navigator.clipboard?.readText) {
    setStatus(
      "social",
      "Clipboard reading is unavailable in this browser. Paste with Ctrl+V inside Visible social content.",
      "error"
    );
    elements.socialManualText.focus();
    return;
  }

  try {
    const clipboardText = (await navigator.clipboard.readText()).trim();

    if (!clipboardText) {
      setStatus(
        "social",
        "The clipboard does not contain readable text.",
        "error"
      );
      return;
    }

    elements.socialManualText.value = clipboardText.slice(0, 200000);
    elements.socialManualDetails.open = true;
    elements.socialManualDetails.classList.remove("needs-attention");
    updateSocialManualState();
    setStatus(
      "social",
      "Clipboard text added. Review it, then click Index pasted content.",
      "success"
    );
    elements.socialManualText.focus();
  } catch (error) {
    console.error("Clipboard read error:", error);
    setStatus(
      "social",
      "The browser did not allow clipboard access. Paste with Ctrl+V inside Visible social content.",
      "error"
    );
    elements.socialManualText.focus();
  }
}


function setSocialImportControlsDisabled(disabled) {
  elements.socialAddButton.disabled = disabled;
  elements.socialUrlInput.disabled = disabled;
  elements.socialTitleInput.disabled = disabled;
  elements.socialManualText.disabled = disabled;
  elements.socialOpenSourceButton.disabled = disabled;
  elements.socialPasteClipboardButton.disabled = disabled;

  if (disabled) {
    elements.socialManualAddButton.disabled = true;
  } else {
    updateSocialManualState();
  }
}


function updateSocialManualState() {
  const minimum = 40;
  const length = elements.socialManualText.value.trim().length;
  const remaining = Math.max(0, minimum - length);

  if (elements.socialManualCount) {
    elements.socialManualCount.innerText =
      `${length.toLocaleString()} / ${minimum}`;
  }

  if (elements.socialManualValidation) {
    elements.socialManualValidation.innerText =
      remaining > 0
        ? `Add ${remaining} more readable character${remaining === 1 ? "" : "s"}.`
        : "Ready to index pasted content.";
    elements.socialManualValidation.classList.toggle(
      "is-ready",
      remaining === 0
    );
  }

  elements.socialManualAddButton.disabled =
    length < minimum
    || elements.socialManualText.disabled;
}


function initializeChatSelection(chatId, documents) {
  const readyIds = documents
    .filter(item => item.status === "ready")
    .map(item => Number(item.id));

  readyChatDocumentIdsByChat.set(
    chatId,
    readyIds
  );

  const storedSelection =
    readStoredChatSelection(chatId);

  const selectedIds = storedSelection === null
    ? new Set(readyIds)
    : new Set(
        storedSelection.filter(id =>
          readyIds.includes(id)
        )
      );

  selectedChatDocumentIdsByChat.set(
    chatId,
    selectedIds
  );

  saveChatSelection(
    chatId,
    selectedIds
  );
}


function initializeGlobalSelection(documents) {
  readyGlobalDocumentIds = documents
    .filter(item => item.status === "ready")
    .map(item => Number(item.id));

  const storedSelection = readStoredIdArray(
    STORAGE_KEYS.globalSelection
  );

  if (!globalSelectionInitialized) {
    selectedGlobalDocumentIds =
      storedSelection === null
        ? new Set(readyGlobalDocumentIds)
        : new Set(
            storedSelection.filter(id =>
              readyGlobalDocumentIds.includes(id)
            )
          );
    globalSelectionInitialized = true;
  } else {
    selectedGlobalDocumentIds = new Set(
      Array.from(selectedGlobalDocumentIds)
        .filter(id =>
          readyGlobalDocumentIds.includes(id)
        )
    );
  }

  saveGlobalSelection();
}


function initializeWebsiteSelection(sources) {
  readyWebsiteSourceIds = sources
    .filter(item => item.status === "ready")
    .map(item => Number(item.id));

  const storedSelection = readStoredIdArray(
    STORAGE_KEYS.websiteSelection
  );

  if (!websiteSelectionInitialized) {
    selectedWebsiteSourceIds =
      storedSelection === null
        ? new Set(readyWebsiteSourceIds)
        : new Set(
            storedSelection.filter(id =>
              readyWebsiteSourceIds.includes(id)
            )
          );
    websiteSelectionInitialized = true;
  } else {
    selectedWebsiteSourceIds = new Set(
      Array.from(selectedWebsiteSourceIds)
        .filter(id =>
          readyWebsiteSourceIds.includes(id)
        )
    );
  }

  saveWebsiteSelection();
}


function initializeSocialSelection(sources) {
  readySocialSourceIds = sources
    .filter(item => item.status === "ready")
    .map(item => Number(item.id));

  const storedSelection = readStoredIdArray(
    STORAGE_KEYS.socialSelection
  );

  if (!socialSelectionInitialized) {
    selectedSocialSourceIds =
      storedSelection === null
        ? new Set(readySocialSourceIds)
        : new Set(
            storedSelection.filter(id =>
              readySocialSourceIds.includes(id)
            )
          );
    socialSelectionInitialized = true;
  } else {
    selectedSocialSourceIds = new Set(
      Array.from(selectedSocialSourceIds)
        .filter(id => readySocialSourceIds.includes(id))
    );
  }

  saveSocialSelection();
}


function renderChatDocuments(chatId, documents) {
  renderDocumentCollection({
    scope: "chat",
    ownerId: chatId,
    documents,
    listElement: elements.documentList,
    countElement: elements.documentCount,
    emptyMessage: "No documents are attached to this chat."
  });
}


function renderGlobalDocuments(documents) {
  renderDocumentCollection({
    scope: "global",
    ownerId: null,
    documents,
    listElement: elements.globalDocumentList,
    countElement: elements.globalDocumentCount,
    emptyMessage: "No reusable files are in the global library."
  });
}


function renderDocumentCollection({
  scope,
  ownerId,
  documents,
  listElement,
  countElement,
  emptyMessage
}) {
  const count = documents.length;

  countElement.innerText =
    `${count} ${count === 1 ? "file" : "files"}`;

  listElement.innerHTML = "";

  if (count === 0) {
    renderEmptyState(
      listElement,
      emptyMessage
    );
    return;
  }

  documents.forEach(documentItem => {
    listElement.appendChild(
      createDocumentItem(
        scope,
        ownerId,
        documentItem
      )
    );
  });
}


function createDocumentItem(
  scope,
  ownerId,
  documentItem
) {
  const item = window.document.createElement("article");
  item.className = "document-item";

  const checkbox = createSelectionCheckbox({
    label: `Use ${documentItem.original_filename}`,
    disabled: documentItem.status !== "ready",
    checked:
      documentItem.status === "ready"
      && isDocumentSelected(
        scope,
        ownerId,
        Number(documentItem.id)
      ),
    onChange: checked => {
      updateDocumentSelection(
        scope,
        ownerId,
        Number(documentItem.id),
        checked
      );
      updateDocumentControls();
    }
  });

  const icon = window.document.createElement("div");
  icon.className = "document-file-icon";

  if (IMAGE_EXTENSIONS.has(documentItem.file_type)) {
    icon.classList.add("document-file-icon-image");
  }

  icon.innerText = fileIcon(documentItem.file_type);

  const details = window.document.createElement("div");
  details.className = "document-details";

  const nameRow = window.document.createElement("div");
  nameRow.className = "document-name-row";

  const name = window.document.createElement("strong");
  name.className = "document-name";
  name.title = documentItem.original_filename;
  name.innerText = documentItem.original_filename;

  const status = createStatusBadge(
    documentItem.status
  );

  nameRow.appendChild(name);
  nameRow.appendChild(status);

  const metadata = window.document.createElement("div");
  metadata.className = "document-metadata";

  const metadataParts = [
    formatFileSize(documentItem.file_size)
  ];

  if (IMAGE_EXTENSIONS.has(documentItem.file_type)) {
    metadataParts.push("OCR image");
  }

  if (documentItem.status === "ready") {
    metadataParts.push(
      `${documentItem.chunk_count} searchable ${
        documentItem.chunk_count === 1
          ? "chunk"
          : "chunks"
      }`
    );
  }

  metadata.innerText = metadataParts.join(" · ");

  details.appendChild(nameRow);
  details.appendChild(metadata);

  if (documentItem.error_message) {
    details.appendChild(
      createErrorText(
        documentItem.error_message
      )
    );
  }

  const deleteButton = createIconButton({
    className: "document-delete-button",
    title:
      scope === "global"
        ? "Delete from global library"
        : "Delete from this chat",
    label: `Delete ${documentItem.original_filename}`,
    icon: trashIcon(),
    onClick: async button => {
      const locationText =
        scope === "global"
          ? "the global library"
          : "this chat";

      if (!confirm(
        `Delete "${documentItem.original_filename}" from ${locationText}?`
      )) {
        return;
      }

      button.disabled = true;

      try {
        if (scope === "global") {
          await deleteGlobalDocumentFromDatabase(
            documentItem.id
          );
          selectedGlobalDocumentIds.delete(
            Number(documentItem.id)
          );
          saveGlobalSelection();
        } else {
          await deleteDocumentFromDatabase(
            documentItem.id
          );
          const selected = getSelectedChatSet(ownerId);
          selected.delete(Number(documentItem.id));
          saveChatSelection(ownerId, selected);
        }

        await loadDocumentsForActiveChat();
        setStatus(
          scope,
          "Document deleted.",
          "success"
        );
      } catch (error) {
        setStatus(
          scope,
          error.message || "Could not delete the document.",
          "error"
        );
        button.disabled = false;
      }
    }
  });

  item.appendChild(checkbox);
  item.appendChild(icon);
  item.appendChild(details);
  item.appendChild(deleteButton);

  return item;
}


function renderWebsiteSources(sources) {
  const count = sources.length;

  elements.websiteSourceCount.innerText =
    `${count} ${count === 1 ? "page" : "pages"}`;

  elements.websiteSourceList.innerHTML = "";

  if (count === 0) {
    renderEmptyState(
      elements.websiteSourceList,
      "No website pages are indexed yet."
    );
    return;
  }

  const groupedSources = new Map();

  sources.forEach(source => {
    const domain = source.domain || "Website";

    if (!groupedSources.has(domain)) {
      groupedSources.set(domain, []);
    }

    groupedSources.get(domain).push(source);
  });

  Array.from(groupedSources.entries())
    .sort(([domainA], [domainB]) =>
      domainA.localeCompare(domainB)
    )
    .forEach(([domain, domainSources]) => {
      elements.websiteSourceList.appendChild(
        createWebsiteDomainGroup(domain, domainSources)
      );
    });
}


function createWebsiteDomainGroup(domain, sources) {
  const group = window.document.createElement("section");
  group.className = "website-domain-group";

  const header = window.document.createElement("div");
  header.className = "website-domain-header";

  const identity = window.document.createElement("div");
  identity.className = "website-domain-identity";

  const title = window.document.createElement("strong");
  title.innerText = domain;

  const count = window.document.createElement("span");
  count.innerText =
    `${sources.length} page${sources.length === 1 ? "" : "s"}`;

  identity.appendChild(title);
  identity.appendChild(count);

  const actions = window.document.createElement("div");
  actions.className = "website-domain-actions";

  const refreshButton = createIconButton({
    className: "website-source-action",
    title: `Refresh all pages from ${domain}`,
    label: `Refresh ${domain}`,
    icon: refreshIcon(),
    onClick: async button => {
      button.disabled = true;
      setStatus(
        "website",
        `Refreshing ${sources.length} page${sources.length === 1 ? "" : "s"} from ${domain}...`,
        "working"
      );

      try {
        const result = await refreshWebsiteDomain(domain);
        await loadDocumentsForActiveChat();
        setStatus(
          "website",
          result.message || "Website pages refreshed.",
          result.failures?.length ? "working" : "success"
        );
      } catch (error) {
        setStatus(
          "website",
          error.message || "The website pages could not be refreshed.",
          "error"
        );
        button.disabled = false;
      }
    }
  });

  const deleteButton = createIconButton({
    className: "website-source-action document-delete-button",
    title: `Delete all pages from ${domain}`,
    label: `Delete ${domain}`,
    icon: trashIcon(),
    onClick: async button => {
      if (!confirm(
        `Delete all ${sources.length} indexed page${sources.length === 1 ? "" : "s"} from ${domain}?`
      )) {
        return;
      }

      button.disabled = true;

      try {
        const result = await deleteWebsiteDomain(domain);
        const deletedIds = Array.isArray(result.deleted_ids)
          ? result.deleted_ids.map(Number)
          : sources.map(source => Number(source.id));

        deletedIds.forEach(sourceId =>
          selectedWebsiteSourceIds.delete(sourceId)
        );
        saveWebsiteSelection();
        await loadDocumentsForActiveChat();
        setStatus(
          "website",
          result.message || "Website pages deleted.",
          "success"
        );
      } catch (error) {
        setStatus(
          "website",
          error.message || "The website pages could not be deleted.",
          "error"
        );
        button.disabled = false;
      }
    }
  });

  actions.appendChild(refreshButton);
  actions.appendChild(deleteButton);
  header.appendChild(identity);
  header.appendChild(actions);

  const pageList = window.document.createElement("div");
  pageList.className = "website-domain-pages";

  sources.forEach(source => {
    pageList.appendChild(
      createWebsiteSourceItem(source)
    );
  });

  group.appendChild(header);
  group.appendChild(pageList);
  return group;
}


function createWebsiteSourceItem(source) {
  const item = window.document.createElement("article");
  item.className = "document-item website-source-item";

  const sourceId = Number(source.id);

  const checkbox = createSelectionCheckbox({
    label: `Use ${source.title}`,
    disabled: source.status !== "ready",
    checked:
      source.status === "ready"
      && selectedWebsiteSourceIds.has(sourceId),
    onChange: checked => {
      if (checked) {
        selectedWebsiteSourceIds.add(sourceId);
      } else {
        selectedWebsiteSourceIds.delete(sourceId);
      }

      saveWebsiteSelection();
      updateDocumentControls();
    }
  });

  const icon = window.document.createElement("div");
  icon.className =
    "document-file-icon website-file-icon";
  icon.innerText = "WEB";

  const details = window.document.createElement("div");
  details.className = "document-details";

  const nameRow = window.document.createElement("div");
  nameRow.className = "document-name-row";

  const link = window.document.createElement("a");
  link.className = "document-name website-source-link";
  link.href = source.canonical_url || source.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.title = source.canonical_url || source.url;
  link.innerText = source.title || source.domain;

  nameRow.appendChild(link);
  nameRow.appendChild(
    createStatusBadge(source.status)
  );

  const metadata = window.document.createElement("div");
  metadata.className = "document-metadata";

  const parts = [source.domain || "Website"];

  if (source.status === "ready") {
    parts.push(
      `${source.chunk_count} searchable ${
        source.chunk_count === 1
          ? "chunk"
          : "chunks"
      }`
    );
  }

  if (source.fetched_at) {
    parts.push(
      `Indexed ${formatDate(source.fetched_at)}`
    );
  }

  metadata.innerText = parts.join(" · ");

  details.appendChild(nameRow);
  details.appendChild(metadata);

  if (source.error_message) {
    details.appendChild(
      createErrorText(source.error_message)
    );
  }

  const actions = window.document.createElement("div");
  actions.className = "website-source-actions";

  const refreshButton = createIconButton({
    className: "website-source-action",
    title: "Refresh website content",
    label: `Refresh ${source.title}`,
    icon: refreshIcon(),
    onClick: async button => {
      button.disabled = true;

      setStatus(
        "website",
        `Refreshing ${source.title}...`,
        "working"
      );

      try {
        await refreshWebsiteSource(source.id);
        await loadDocumentsForActiveChat();
        setStatus(
          "website",
          "Website page refreshed successfully.",
          "success"
        );
      } catch (error) {
        setStatus(
          "website",
          error.message || "Website refresh failed.",
          "error"
        );
        button.disabled = false;
      }
    }
  });

  const deleteButton = createIconButton({
    className:
      "website-source-action document-delete-button",
    title: "Delete website source",
    label: `Delete ${source.title}`,
    icon: trashIcon(),
    onClick: async button => {
      if (!confirm(
        `Delete the indexed website "${source.title}"?`
      )) {
        return;
      }

      button.disabled = true;

      try {
        await deleteWebsiteSourceFromDatabase(
          source.id
        );
        selectedWebsiteSourceIds.delete(sourceId);
        saveWebsiteSelection();
        await loadDocumentsForActiveChat();
        setStatus(
          "website",
          "Website source deleted.",
          "success"
        );
      } catch (error) {
        setStatus(
          "website",
          error.message || "Could not delete the website source.",
          "error"
        );
        button.disabled = false;
      }
    }
  });

  actions.appendChild(refreshButton);
  actions.appendChild(deleteButton);

  item.appendChild(checkbox);
  item.appendChild(icon);
  item.appendChild(details);
  item.appendChild(actions);

  return item;
}


function renderSocialSources(sources) {
  const count = sources.length;

  elements.socialSourceCount.innerText =
    `${count} ${count === 1 ? "link" : "links"}`;
  elements.socialSourceList.innerHTML = "";

  if (count === 0) {
    renderEmptyState(
      elements.socialSourceList,
      "No social-media or business-profile sources are indexed yet."
    );
    return;
  }

  sources.forEach(source => {
    elements.socialSourceList.appendChild(
      createSocialSourceItem(source)
    );
  });
}


function createSocialSourceItem(source) {
  const item = window.document.createElement("article");
  item.className = "document-item social-source-item";

  const sourceId = Number(source.id);
  const sourceTitle = source.title || source.domain || "Social source";

  const checkbox = createSelectionCheckbox({
    label: `Use ${sourceTitle}`,
    disabled: source.status !== "ready",
    checked:
      source.status === "ready"
      && selectedSocialSourceIds.has(sourceId),
    onChange: checked => {
      if (checked) {
        selectedSocialSourceIds.add(sourceId);
      } else {
        selectedSocialSourceIds.delete(sourceId);
      }

      saveSocialSelection();
      updateDocumentControls();
    }
  });

  const icon = window.document.createElement("div");
  icon.className = "document-file-icon social-file-icon";
  icon.innerText = socialPlatformLabel(source.platform);

  const details = window.document.createElement("div");
  details.className = "document-details";

  const nameRow = window.document.createElement("div");
  nameRow.className = "document-name-row";

  const link = window.document.createElement("a");
  link.className = "document-name website-source-link social-source-link";
  link.href = source.canonical_url || source.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.title = source.canonical_url || source.url;
  link.innerText = sourceTitle;

  nameRow.appendChild(link);
  nameRow.appendChild(createStatusBadge(source.status));

  const metadata = window.document.createElement("div");
  metadata.className = "document-metadata";

  const parts = [socialPlatformName(source.platform)];
  const extractionLabels = {
    manual: "Pasted text",
    public_page: "Public page",
    google_places_api: "Google Places API"
  };
  parts.push(
    extractionLabels[source.extraction_method]
    || "Public profile"
  );

  if (source.status === "ready") {
    parts.push(
      `${source.chunk_count} searchable ${
        source.chunk_count === 1 ? "chunk" : "chunks"
      }`
    );
  }

  if (source.fetched_at) {
    parts.push(`Indexed ${formatDate(source.fetched_at)}`);
  }

  metadata.innerText = parts.join(" · ");
  details.appendChild(nameRow);
  details.appendChild(metadata);

  if (source.error_message) {
    details.appendChild(createErrorText(source.error_message));
  }

  const actions = window.document.createElement("div");
  actions.className = "website-source-actions social-source-actions";

  if (source.extraction_method !== "manual") {
    const refreshButton = createIconButton({
      className: "website-source-action",
      title: "Refresh social content",
      label: `Refresh ${sourceTitle}`,
      icon: refreshIcon(),
      onClick: async button => {
        button.disabled = true;
        setStatus(
          "social",
          `Refreshing ${sourceTitle}...`,
          "working"
        );

        try {
          await refreshSocialSource(source.id);
          await loadDocumentsForActiveChat();
          setStatus(
            "social",
            "Social source refreshed successfully.",
            "success"
          );
        } catch (error) {
          setStatus(
            "social",
            error.message || "Social source refresh failed.",
            "error"
          );
          button.disabled = false;
        }
      }
    });
    actions.appendChild(refreshButton);
  }

  const deleteButton = createIconButton({
    className: "website-source-action document-delete-button",
    title: "Delete social source",
    label: `Delete ${sourceTitle}`,
    icon: trashIcon(),
    onClick: async button => {
      if (!confirm(`Delete the social source "${sourceTitle}"?`)) {
        return;
      }

      button.disabled = true;

      try {
        await deleteSocialSourceFromDatabase(source.id);
        selectedSocialSourceIds.delete(sourceId);
        saveSocialSelection();
        await loadDocumentsForActiveChat();
        setStatus("social", "Social source deleted.", "success");
      } catch (error) {
        setStatus(
          "social",
          error.message || "Could not delete the social source.",
          "error"
        );
        button.disabled = false;
      }
    }
  });

  actions.appendChild(deleteButton);

  item.appendChild(checkbox);
  item.appendChild(icon);
  item.appendChild(details);
  item.appendChild(actions);
  return item;
}


function createSelectionCheckbox({
  label,
  disabled,
  checked,
  onChange
}) {
  const control = window.document.createElement("label");
  control.className = "document-select-control";

  const checkbox = window.document.createElement("input");
  checkbox.type = "checkbox";
  checkbox.className = "document-select-checkbox";
  checkbox.disabled = disabled;
  checkbox.checked = checked;
  checkbox.setAttribute("aria-label", label);

  const visual = window.document.createElement("span");
  visual.className = "document-select-visual";

  checkbox.addEventListener(
    "change",
    () => onChange(checkbox.checked)
  );

  control.appendChild(checkbox);
  control.appendChild(visual);

  return control;
}


function createStatusBadge(statusValue) {
  const status = window.document.createElement("span");
  status.className =
    `document-status status-${statusValue}`;
  status.innerText = statusLabel(statusValue);
  return status;
}


function createErrorText(message) {
  const errorText = window.document.createElement("p");
  errorText.className = "document-error-message";
  errorText.innerText = message;
  return errorText;
}


function createIconButton({
  className,
  title,
  label,
  icon,
  onClick
}) {
  const button = window.document.createElement("button");
  button.type = "button";
  button.className = className;
  button.title = title;
  button.setAttribute("aria-label", label);
  button.innerHTML = icon;

  button.addEventListener(
    "click",
    () => onClick(button)
  );

  return button;
}


function updateDocumentSelection(
  scope,
  ownerId,
  documentId,
  selected
) {
  if (scope === "global") {
    if (selected) {
      selectedGlobalDocumentIds.add(documentId);
    } else {
      selectedGlobalDocumentIds.delete(documentId);
    }

    saveGlobalSelection();
    return;
  }

  const selectedSet = getSelectedChatSet(ownerId);

  if (selected) {
    selectedSet.add(documentId);
  } else {
    selectedSet.delete(documentId);
  }

  saveChatSelection(ownerId, selectedSet);
}


function isDocumentSelected(
  scope,
  ownerId,
  documentId
) {
  if (scope === "global") {
    return selectedGlobalDocumentIds.has(documentId);
  }

  return getSelectedChatSet(ownerId).has(documentId);
}


function toggleSelectAllChatDocuments() {
  const chatId = getActiveChat()?.id;

  if (!chatId) {
    return;
  }

  const readyIds =
    readyChatDocumentIdsByChat.get(chatId) || [];

  const allSelected =
    readyIds.length > 0
    && readyIds.every(id =>
      getSelectedChatSet(chatId).has(id)
    );

  const nextSelection = allSelected
    ? new Set()
    : new Set(readyIds);

  selectedChatDocumentIdsByChat.set(
    chatId,
    nextSelection
  );

  saveChatSelection(chatId, nextSelection);
  updateCheckboxes(
    elements.documentList,
    !allSelected
  );
  updateDocumentControls();
}


function toggleSelectAllGlobalDocuments() {
  const allSelected =
    readyGlobalDocumentIds.length > 0
    && readyGlobalDocumentIds.every(id =>
      selectedGlobalDocumentIds.has(id)
    );

  selectedGlobalDocumentIds = allSelected
    ? new Set()
    : new Set(readyGlobalDocumentIds);

  saveGlobalSelection();
  updateCheckboxes(
    elements.globalDocumentList,
    !allSelected
  );
  updateDocumentControls();
}


function toggleSelectAllWebsiteSources() {
  const allSelected =
    readyWebsiteSourceIds.length > 0
    && readyWebsiteSourceIds.every(id =>
      selectedWebsiteSourceIds.has(id)
    );

  selectedWebsiteSourceIds = allSelected
    ? new Set()
    : new Set(readyWebsiteSourceIds);

  saveWebsiteSelection();
  updateCheckboxes(
    elements.websiteSourceList,
    !allSelected
  );
  updateDocumentControls();
}


function toggleSelectAllSocialSources() {
  const allSelected =
    readySocialSourceIds.length > 0
    && readySocialSourceIds.every(id =>
      selectedSocialSourceIds.has(id)
    );

  selectedSocialSourceIds = allSelected
    ? new Set()
    : new Set(readySocialSourceIds);

  saveSocialSelection();
  updateCheckboxes(elements.socialSourceList, !allSelected);
  updateDocumentControls();
}


function updateCheckboxes(container, checked) {
  container
    .querySelectorAll(
      ".document-select-checkbox:not(:disabled)"
    )
    .forEach(checkbox => {
      checkbox.checked = checked;
    });
}


function updateDocumentControls() {
  const chatId = getActiveChat()?.id ?? null;

  const readyChatIds = chatId
    ? readyChatDocumentIdsByChat.get(chatId) || []
    : [];

  const selectedChat = chatId
    ? getSelectedChatSet(chatId)
    : new Set();

  const selectedReadyChatCount = readyChatIds
    .filter(id => selectedChat.has(id)).length;
  const selectedReadyGlobalCount = readyGlobalDocumentIds
    .filter(id => selectedGlobalDocumentIds.has(id)).length;
  const selectedReadyWebsiteCount = readyWebsiteSourceIds
    .filter(id => selectedWebsiteSourceIds.has(id)).length;
  const selectedReadySocialCount = readySocialSourceIds
    .filter(id => selectedSocialSourceIds.has(id)).length;

  const hasChatDocuments = readyChatIds.length > 0;
  const hasGlobalFiles = readyGlobalDocumentIds.length > 0;
  const hasWebsites = readyWebsiteSourceIds.length > 0;
  const hasSocialSources = readySocialSourceIds.length > 0;
  const hasGlobalKnowledge =
    hasGlobalFiles || hasWebsites || hasSocialSources;
  const hasAnyKnowledge = hasChatDocuments || hasGlobalKnowledge;

  elements.useDocumentsToggle.disabled = !hasAnyKnowledge;
  elements.useGlobalDocumentsToggle.disabled =
    !hasGlobalKnowledge || !elements.useDocumentsToggle.checked;
  elements.strictDocumentsToggle.disabled =
    !hasAnyKnowledge || !elements.useDocumentsToggle.checked;

  elements.selectAllDocumentsButton.disabled = !hasChatDocuments;
  elements.selectAllGlobalDocumentsButton.disabled = !hasGlobalFiles;
  elements.selectAllWebsiteSourcesButton.disabled = !hasWebsites;
  elements.selectAllSocialSourcesButton.disabled = !hasSocialSources;

  elements.documentSelectionSummary.innerText = hasChatDocuments
    ? `${selectedReadyChatCount} of ${readyChatIds.length} selected`
    : "0 selected";
  elements.globalDocumentSelectionSummary.innerText = hasGlobalFiles
    ? `${selectedReadyGlobalCount} of ${readyGlobalDocumentIds.length} selected`
    : "0 selected";
  elements.websiteSelectionSummary.innerText = hasWebsites
    ? `${selectedReadyWebsiteCount} of ${readyWebsiteSourceIds.length} selected`
    : "0 selected";
  elements.socialSelectionSummary.innerText = hasSocialSources
    ? `${selectedReadySocialCount} of ${readySocialSourceIds.length} selected`
    : "0 selected";

  elements.selectAllDocumentsButton.innerText =
    hasChatDocuments && selectedReadyChatCount === readyChatIds.length
      ? "Clear selection" : "Select all";
  elements.selectAllGlobalDocumentsButton.innerText =
    hasGlobalFiles && selectedReadyGlobalCount === readyGlobalDocumentIds.length
      ? "Clear selection" : "Select all";
  elements.selectAllWebsiteSourcesButton.innerText =
    hasWebsites && selectedReadyWebsiteCount === readyWebsiteSourceIds.length
      ? "Clear selection" : "Select all";
  elements.selectAllSocialSourcesButton.innerText =
    hasSocialSources && selectedReadySocialCount === readySocialSourceIds.length
      ? "Clear selection" : "Select all";

  const globalEnabled = elements.useGlobalDocumentsToggle.checked;
  const enabledScopes = [];

  if (selectedReadyChatCount > 0) {
    enabledScopes.push(`${selectedReadyChatCount} chat`);
  }
  if (globalEnabled && selectedReadyGlobalCount > 0) {
    enabledScopes.push(`${selectedReadyGlobalCount} global`);
  }
  if (globalEnabled && selectedReadyWebsiteCount > 0) {
    enabledScopes.push(`${selectedReadyWebsiteCount} web`);
  }
  if (globalEnabled && selectedReadySocialCount > 0) {
    enabledScopes.push(`${selectedReadySocialCount} social`);
  }

  elements.knowledgeSelectionSummary.innerText =
    !elements.useDocumentsToggle.checked
      ? "Knowledge use is off"
      : enabledScopes.length > 0
        ? `${enabledScopes.join(" · ")} selected`
        : "No ready sources selected";

  elements.documentPanel.classList.toggle(
    "documents-disabled",
    !elements.useDocumentsToggle.checked || !hasAnyKnowledge
  );
  elements.globalKnowledgePanel.classList.toggle(
    "scope-disabled",
    !globalEnabled || !elements.useDocumentsToggle.checked
  );
}


function validateFile(file) {
  const extension = getExtension(file.name);

  if (!ALLOWED_EXTENSIONS.has(extension)) {
    return (
      `${file.name}: only PDF, DOCX, TXT, `
      + "PNG, JPG, JPEG, and WebP files are supported."
    );
  }

  if (file.size > MAX_FILE_SIZE) {
    return (
      `${file.name}: the maximum file size is 20 MB.`
    );
  }

  if (file.size === 0) {
    return `${file.name}: the file is empty.`;
  }

  return null;
}


function buildProcessingMessage(
  filename,
  extension,
  currentIndex,
  totalFiles
) {
  const position = `${currentIndex} of ${totalFiles}`;

  if (IMAGE_EXTENSIONS.has(extension)) {
    return `Uploading and running OCR ${position}: ${filename}`;
  }

  if (extension === "pdf") {
    return (
      "Uploading, checking text, and using OCR if needed "
      + `${position}: ${filename}`
    );
  }

  return `Uploading and indexing ${position}: ${filename}`;
}


function buildUploadSuccessMessage(
  fileCount,
  extractionResults
) {
  const ocrCount = extractionResults.filter(
    result => result?.ocr_used
  ).length;

  const hybridCount = extractionResults.filter(
    result => result?.method === "hybrid"
  ).length;

  if (fileCount === 1 && ocrCount === 1) {
    return hybridCount === 1
      ? "Document read with native extraction and OCR, indexed, and selected."
      : "Document read with OCR, indexed, and selected.";
  }

  if (ocrCount > 0) {
    return (
      `${fileCount} documents indexed and selected. `
      + `${ocrCount} used OCR.`
    );
  }

  return fileCount === 1
    ? "Document uploaded, indexed, and selected."
    : `${fileCount} documents uploaded, indexed, and selected.`;
}


function renderEmptyState(
  listElement,
  message,
  isError = false
) {
  const empty = window.document.createElement("div");
  empty.className = isError
    ? "document-empty document-error-state"
    : "document-empty";
  empty.innerText = message;
  listElement.appendChild(empty);
}


function toggleDocumentPanel() {
  setDocumentDrawerOpen(
    !elements.documentPanel.classList.contains(
      "drawer-open"
    )
  );
}


function setDocumentDrawerOpen(
  isOpen,
  persist = true
) {
  elements.documentPanel.classList.toggle(
    "drawer-open",
    isOpen
  );

  elements.documentPanelBody.setAttribute(
    "aria-hidden",
    String(!isOpen)
  );

  elements.documentToggle.setAttribute(
    "aria-expanded",
    String(isOpen)
  );

  elements.documentDrawerBackdrop.hidden = !isOpen;

  document.body.classList.toggle(
    "knowledge-drawer-open",
    isOpen
  );

  if (persist) {
    localStorage.setItem(
      STORAGE_KEYS.drawerOpen,
      String(isOpen)
    );
  }

  if (isOpen) {
    window.setTimeout(
      () => elements.documentCloseButton.focus(),
      180
    );
  }
}


function setKnowledgeTab(tabName) {
  const normalizedTab =
    tabName === "global"
      ? "global"
      : "chat";

  const chatActive = normalizedTab === "chat";

  elements.chatKnowledgeTab.classList.toggle(
    "is-active",
    chatActive
  );

  elements.globalKnowledgeTab.classList.toggle(
    "is-active",
    !chatActive
  );

  elements.chatKnowledgeTab.setAttribute(
    "aria-selected",
    String(chatActive)
  );

  elements.globalKnowledgeTab.setAttribute(
    "aria-selected",
    String(!chatActive)
  );

  elements.chatKnowledgePanel.hidden = !chatActive;
  elements.globalKnowledgePanel.hidden = chatActive;

  localStorage.setItem(
    STORAGE_KEYS.activeTab,
    normalizedTab
  );
}


function setStatus(scope, message, type = "") {
  let element;

  if (scope === "global") {
    element = elements.globalDocumentUploadStatus;
  } else if (scope === "website") {
    element = elements.websiteStatus;
  } else if (scope === "social") {
    element = elements.socialStatus;
  } else {
    element = elements.documentUploadStatus;
  }

  element.innerText = message;
  element.className =
    `document-upload-status ${
      type ? `is-${type}` : ""
    }`;
}


function getSelectedChatSet(chatId) {
  if (!selectedChatDocumentIdsByChat.has(chatId)) {
    selectedChatDocumentIdsByChat.set(
      chatId,
      new Set()
    );
  }

  return selectedChatDocumentIdsByChat.get(chatId);
}


function saveChatSelection(chatId, selectedSet) {
  selectedChatDocumentIdsByChat.set(
    chatId,
    selectedSet
  );

  localStorage.setItem(
    `${CHAT_SELECTION_STORAGE_PREFIX}${chatId}`,
    JSON.stringify(Array.from(selectedSet))
  );
}


function readStoredChatSelection(chatId) {
  return readStoredIdArray(
    `${CHAT_SELECTION_STORAGE_PREFIX}${chatId}`
  );
}


function saveGlobalSelection() {
  localStorage.setItem(
    STORAGE_KEYS.globalSelection,
    JSON.stringify(
      Array.from(selectedGlobalDocumentIds)
    )
  );
}


function saveWebsiteSelection() {
  localStorage.setItem(
    STORAGE_KEYS.websiteSelection,
    JSON.stringify(
      Array.from(selectedWebsiteSourceIds)
    )
  );
}


function saveSocialSelection() {
  localStorage.setItem(
    STORAGE_KEYS.socialSelection,
    JSON.stringify(Array.from(selectedSocialSourceIds))
  );
}


function readStoredIdArray(key) {
  const rawValue = localStorage.getItem(key);

  if (rawValue === null) {
    return null;
  }

  try {
    const parsed = JSON.parse(rawValue);

    return Array.isArray(parsed)
      ? parsed
          .map(Number)
          .filter(Number.isInteger)
      : null;
  } catch {
    return null;
  }
}


function readStoredBoolean(key, fallback) {
  const value = localStorage.getItem(key);

  if (value === null) {
    return fallback;
  }

  return value === "true";
}


function getExtension(filename) {
  const parts = filename.toLowerCase().split(".");
  return parts.length > 1 ? parts.pop() : "";
}


function fileIcon(fileType) {
  if (fileType === "pdf") {
    return "PDF";
  }

  if (fileType === "docx") {
    return "DOC";
  }

  if (fileType === "png") {
    return "PNG";
  }

  if (fileType === "jpg" || fileType === "jpeg") {
    return "JPG";
  }

  if (fileType === "webp") {
    return "WEBP";
  }

  return "TXT";
}


function statusLabel(status) {
  if (status === "ready") {
    return "Ready";
  }

  if (status === "failed") {
    return "Failed";
  }

  return "Processing";
}


function formatFileSize(bytes) {
  const size = Number(bytes) || 0;

  if (size < 1024) {
    return `${size} B`;
  }

  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }

  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}


function formatDate(value) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "recently";
  }

  return new Intl.DateTimeFormat(
    undefined,
    {
      year: "numeric",
      month: "short",
      day: "numeric"
    }
  ).format(date);
}


function socialPlatformLabel(platform) {
  const labels = {
    facebook: "FB",
    instagram: "IG",
    x: "X",
    twitter: "X",
    tiktok: "TT",
    linkedin: "IN",
    youtube: "YT",
    threads: "TH",
    bluesky: "BS",
    "google business profile": "GBP"
  };
  return labels[String(platform || "").toLowerCase()] || "SOC";
}


function socialPlatformName(platform) {
  const names = {
    facebook: "Facebook",
    instagram: "Instagram",
    x: "X",
    twitter: "X",
    tiktok: "TikTok",
    linkedin: "LinkedIn",
    youtube: "YouTube",
    threads: "Threads",
    bluesky: "Bluesky",
    "google business profile": "Google Business Profile"
  };
  const normalized = String(platform || "").toLowerCase();
  return names[normalized] || "Social media";
}


function trashIcon() {
  return `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M4 7h16"></path>
      <path d="M9 7V4h6v3"></path>
      <path d="M6 7l1 13h10l1-13"></path>
      <path d="M10 11v5"></path>
      <path d="M14 11v5"></path>
    </svg>
  `;
}


function refreshIcon() {
  return `
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 6v5h-5"></path>
      <path d="M4 18v-5h5"></path>
      <path d="M6.1 9a7 7 0 0 1 11.4-2.5L20 9"></path>
      <path d="M17.9 15a7 7 0 0 1-11.4 2.5L4 15"></path>
    </svg>
  `;
}
