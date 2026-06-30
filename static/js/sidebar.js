import {
  createChatInDatabase,
  saveMessageToDatabase,
  fetchChatsFromDatabase,
  fetchMessagesFromDatabase,
  updateChatInDatabase,
  deleteChatFromDatabase,
  fetchChatFolders,
  createChatFolder,
  deleteChatFolder,
  fetchChatTags,
  createChatTag,
  deleteChatTag,
  bulkUpdateChats
} from "./api.js";

import {
  elements,
  addMessage,
  renderRagSources,
  splitMessageMetadata
} from "./ui.js";

import {
  formatBotMessage
} from "./markdown.js";

import {
  createOptionReadButton,
  stopVoiceActivity
} from "./voice.js";

import {
  attachMessageActions
} from "./conversation.js";


export let chats = [];
export let activeChatId = null;

let chatFolders = [];
let chatTags = [];
let organizationInitialized = false;
let organizationView = "active";
let organizationFolderId = null;
let organizationTagId = null;
let bulkMode = false;
const selectedChatIds = new Set();


function normalizeChat(chat) {
  return {
    id: Number(chat.id),
    title: String(chat.title || "New Chat"),
    is_pinned: Boolean(chat.is_pinned),
    is_favorite: Boolean(chat.is_favorite),
    is_archived: Boolean(chat.is_archived),
    parent_chat_id: chat.parent_chat_id ? Number(chat.parent_chat_id) : null,
    branched_from_message_id: chat.branched_from_message_id
      ? Number(chat.branched_from_message_id)
      : null,
    branch_count: Number(chat.branch_count || 0),
    folder: chat.folder || null,
    tags: Array.isArray(chat.tags) ? chat.tags : [],
    created_at: chat.created_at || null,
    updated_at: chat.updated_at || null,
    messages: Array.isArray(chat.messages) ? chat.messages : []
  };
}


function chatMatchesOrganizationView(chat) {
  if (organizationView === "active" && chat.is_archived) {
    return false;
  }

  if (
    organizationView === "favorites"
    && (!chat.is_favorite || chat.is_archived)
  ) {
    return false;
  }

  if (organizationView === "archived" && !chat.is_archived) {
    return false;
  }

  if (
    organizationFolderId !== null
    && Number(chat.folder?.id) !== organizationFolderId
  ) {
    return false;
  }

  if (
    organizationTagId !== null
    && !chat.tags.some(tag => Number(tag.id) === organizationTagId)
  ) {
    return false;
  }

  return true;
}


export async function createChat() {
  organizationView = "active";
  organizationFolderId = null;
  organizationTagId = null;
  document.querySelectorAll("[data-chat-view]").forEach(button => {
    button.classList.toggle(
      "is-active",
      button.dataset.chatView === "active"
    );
  });
  const folderFilter = document.getElementById("chatFolderFilter");
  const tagFilter = document.getElementById("chatTagFilter");
  if (folderFilter) folderFilter.value = "";
  if (tagFilter) tagFilter.value = "";

  const savedChat =
    await createChatInDatabase();

  const newChat = normalizeChat(savedChat);
  newChat.messages = [];

  chats.unshift(newChat);
  activeChatId = savedChat.id;

  elements.chat.innerHTML = "";
  renderChatList();
  notifyChatChanged();
}


export async function loadChatsFromDatabase() {
  const previousActiveChatId =
    activeChatId;

  await loadChatOrganizationMetadata();

  const savedChats =
    await fetchChatsFromDatabase();

  chats = savedChats.map(chat => ({
    ...normalizeChat(chat),
    messages: []
  }));

  const previousChatStillVisible =
    chats.some(
      chat =>
        chat.id === previousActiveChatId
        && chatMatchesOrganizationView(chat)
    );

  if (previousChatStillVisible) {
    activeChatId = previousActiveChatId;
  } else {
    activeChatId = (
      chats.find(chatMatchesOrganizationView)?.id
      ?? chats[0]?.id
      ?? null
    );
  }

  if (activeChatId) {
    await loadChatMessages();
  } else {
    elements.chat.innerHTML = "";
  }

  renderChatList();
  notifyChatChanged();
}


export function getActiveChat() {
  return chats.find(
    chat =>
      chat.id === activeChatId
  );
}


export async function openChatById(chatId, draftText = "") {
  const parsedId = Number(chatId);
  if (!Number.isInteger(parsedId) || parsedId <= 0) {
    return;
  }

  await loadChatsFromDatabase();

  if (!chats.some(chat => chat.id === parsedId)) {
    return;
  }

  activeChatId = parsedId;
  await loadChatMessages();
  renderChatList();
  notifyChatChanged();

  if (draftText) {
    elements.promptInput.value = draftText;
    elements.promptInput.dispatchEvent(
      new Event("input", { bubbles: true })
    );
    elements.promptInput.focus();
  }
}


export async function saveMessage(
  role,
  content,
  attachments = []
) {
  const activeChat = getActiveChat();

  if (!activeChat) {
    return null;
  }

  const normalizedAttachments = Array.isArray(attachments)
    ? attachments
    : [];

  const localMessage = {
    id: null,
    role,
    content,
    model: elements.model.value,
    mode: elements.responseMode.value,
    attachments: normalizedAttachments
  };

  activeChat.messages.push(localMessage);

  if (
    role === "user"
    && activeChat.title === "New Chat"
  ) {
    const titleSource = String(content || "Attached file");
    const newTitle = titleSource.slice(0, 28);

    activeChat.title = newTitle;
    renderChatList();

    await updateChatInDatabase(
      activeChat.id,
      { title: newTitle }
    );
  }

  const saved = await saveMessageToDatabase(
    activeChat.id,
    {
      role,
      content,
      model: elements.model.value,
      mode: elements.responseMode.value,
      attachment_ids: normalizedAttachments.map(item => item.id)
    }
  );

  Object.assign(localMessage, saved);
  return saved;
}



export function saveOptions(options) {
  const activeChat =
    getActiveChat();

  if (!activeChat) {
    return;
  }

  activeChat.messages.push({
    role: "options",
    options
  });
}


export function renderChatList() {
  elements.chatList.innerHTML = "";

  const searchText =
    elements.chatSearch.value
      .toLowerCase()
      .trim();

  const visibleChats = chats.filter(chat => {
    if (
      searchText
      && !chat.title.toLowerCase().includes(searchText)
    ) {
      return false;
    }

    return chatMatchesOrganizationView(chat);
  });

  updateOrganizerCount(visibleChats.length);

  if (visibleChats.length === 0) {
    const empty = document.createElement("div");
    empty.className = "chat-list-empty";
    empty.innerText = organizationView === "archived"
      ? "No archived chats."
      : "No chats match these filters.";
    elements.chatList.appendChild(empty);
    return;
  }

  visibleChats.forEach(chat => {
    const item = document.createElement("div");
    item.className = "chat-list-item";
    item.dataset.chatId = String(chat.id);
    item.draggable = !bulkMode;

    if (chat.id === activeChatId) {
      item.classList.add("active");
    }

    if (chat.is_archived) {
      item.classList.add("is-archived");
    }

    item.addEventListener("dragstart", event => {
      if (bulkMode) {
        event.preventDefault();
        return;
      }
      event.dataTransfer.setData("text/plain", String(chat.id));
      event.dataTransfer.effectAllowed = "move";
      item.classList.add("is-dragging");
    });

    item.addEventListener("dragend", () => {
      item.classList.remove("is-dragging");
    });

    if (bulkMode) {
      const selector = document.createElement("input");
      selector.type = "checkbox";
      selector.className = "chat-bulk-checkbox";
      selector.checked = selectedChatIds.has(chat.id);
      selector.setAttribute("aria-label", `Select ${chat.title}`);
      selector.addEventListener("click", event => {
        event.stopPropagation();
      });
      selector.addEventListener("change", () => {
        if (selector.checked) {
          selectedChatIds.add(chat.id);
        } else {
          selectedChatIds.delete(chat.id);
        }
        updateBulkToolbar();
      });
      item.appendChild(selector);
    }

    const titleBlock = document.createElement("div");
    titleBlock.className = "chat-title-block";

    const title = document.createElement("span");
    title.className = "chat-title";
    title.innerText = chat.title;
    title.title = chat.title;

    title.addEventListener(
      "click",
      async () => {
        if (bulkMode) {
          if (selectedChatIds.has(chat.id)) {
            selectedChatIds.delete(chat.id);
          } else {
            selectedChatIds.add(chat.id);
          }
          renderChatList();
          updateBulkToolbar();
          return;
        }

        stopVoiceActivity();
        activeChatId = chat.id;

        await loadChatMessages();
        renderChatList();
        notifyChatChanged();
      }
    );

    const titleRow = document.createElement("div");
    titleRow.className = "chat-title-row";
    titleRow.appendChild(title);

    const stateBadges = document.createElement("span");
    stateBadges.className = "chat-state-badges";

    if (chat.is_favorite) {
      const favoriteBadge = document.createElement("span");
      favoriteBadge.className = "chat-state-badge is-favorite";
      favoriteBadge.title = "Favorite";
      favoriteBadge.setAttribute("aria-label", "Favorite");
      favoriteBadge.textContent = "★";
      stateBadges.appendChild(favoriteBadge);
    }

    if (chat.is_pinned) {
      const pinBadge = document.createElement("span");
      pinBadge.className = "chat-state-badge is-pinned";
      pinBadge.title = "Pinned";
      pinBadge.setAttribute("aria-label", "Pinned");
      pinBadge.innerHTML = `
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M9 3h6v5l2 3v2l2 2v2H5v-2l2-2v-2l2-3V3Z"></path>
          <path d="M12 14v6"></path>
        </svg>
      `;
      stateBadges.appendChild(pinBadge);
    }

    if (chat.parent_chat_id) {
      const branchBadge = document.createElement("span");
      branchBadge.className = "chat-state-badge is-branch";
      branchBadge.title = "Conversation branch";
      branchBadge.setAttribute("aria-label", "Conversation branch");
      branchBadge.textContent = "↳";
      stateBadges.appendChild(branchBadge);
    }

    if (stateBadges.childElementCount > 0) {
      titleRow.appendChild(stateBadges);
    }

    titleBlock.appendChild(titleRow);

    const metadata = document.createElement("div");
    metadata.className = "chat-item-metadata";

    if (chat.folder) {
      const folderBadge = document.createElement("span");
      folderBadge.className = "chat-folder-badge";
      folderBadge.innerText = chat.folder.name;
      metadata.appendChild(folderBadge);
    }

    chat.tags.slice(0, 2).forEach(tag => {
      const tagBadge = document.createElement("span");
      tagBadge.className = `chat-tag-badge tag-${tag.color || "violet"}`;
      tagBadge.innerText = tag.name;
      metadata.appendChild(tagBadge);
    });

    if (chat.tags.length > 2) {
      const more = document.createElement("span");
      more.className = "chat-tag-more";
      more.innerText = `+${chat.tags.length - 2}`;
      metadata.appendChild(more);
    }

    if (metadata.childElementCount > 0) {
      titleBlock.appendChild(metadata);
    }

    const actions = document.createElement("div");
    actions.className = "chat-actions";

    const menuWrapper = document.createElement("div");
    menuWrapper.className = "chat-menu-wrapper";

    const menuBtn = document.createElement("button");
    menuBtn.className = "menu-btn";
    menuBtn.innerText = "⋯";
    menuBtn.title = "More options";

    const menu = document.createElement("div");
    menu.className = "chat-menu";

    const renameItem = createMenuItem(
      "Rename",
      async () => {
        const newTitle = prompt("Enter new chat title:", chat.title);
        if (!newTitle || !newTitle.trim()) {
          return;
        }
        await updateChatInDatabase(chat.id, {
          title: newTitle.trim()
        });
        await loadChatsFromDatabase();
        notifyChatChanged();
      }
    );

    const favoriteItem = createMenuItem(
      chat.is_favorite ? "Remove favorite" : "Add favorite",
      async () => {
        await updateChatInDatabase(chat.id, {
          is_favorite: !chat.is_favorite
        });
        await loadChatsFromDatabase();
      }
    );

    const pinItem = createMenuItem(
      chat.is_pinned ? "Unpin chat" : "Pin chat",
      async () => {
        await updateChatInDatabase(chat.id, {
          is_pinned: !chat.is_pinned
        });
        await loadChatsFromDatabase();
      }
    );
    pinItem.setAttribute("aria-pressed", String(chat.is_pinned));

    const archiveItem = createMenuItem(
      chat.is_archived ? "Restore chat" : "Archive chat",
      async () => {
        await updateChatInDatabase(chat.id, {
          is_archived: !chat.is_archived
        });
        await loadChatsFromDatabase();
      }
    );

    const moveItem = createMenuItem(
      "Move to folder",
      async () => {
        const names = chatFolders.map(folder => folder.name);
        const current = chat.folder?.name || "";
        const answer = prompt(
          `Enter a folder name, or leave blank for no folder.\nAvailable: ${names.join(", ") || "No folders yet"}`,
          current
        );
        if (answer === null) {
          return;
        }
        const normalized = answer.trim().toLowerCase();
        const folder = chatFolders.find(
          item => item.name.toLowerCase() === normalized
        );
        if (normalized && !folder) {
          alert("That folder does not exist. Create it from Organize first.");
          return;
        }
        await updateChatInDatabase(chat.id, {
          folder_id: folder ? folder.id : null
        });
        await loadChatsFromDatabase();
      }
    );

    const tagsItem = createMenuItem(
      "Edit tags",
      async () => {
        const available = chatTags.map(tag => tag.name);
        const current = chat.tags.map(tag => tag.name).join(", ");
        const answer = prompt(
          `Enter tag names separated by commas.\nAvailable: ${available.join(", ") || "No tags yet"}`,
          current
        );
        if (answer === null) {
          return;
        }
        const requested = answer
          .split(",")
          .map(value => value.trim().toLowerCase())
          .filter(Boolean);
        const tags = requested.map(name =>
          chatTags.find(tag => tag.name.toLowerCase() === name)
        );
        if (tags.some(tag => !tag)) {
          alert("One or more tags do not exist. Create them from Organize first.");
          return;
        }
        await updateChatInDatabase(chat.id, {
          tag_ids: tags.map(tag => tag.id)
        });
        await loadChatsFromDatabase();
      }
    );

    const copyItem = createMenuItem(
      "Copy chat",
      async () => {
        await loadMessagesIfNeeded(chat);

        const text = chat.messages
          .map(message => {
            if (message.role === "options") {
              return message.options
                .map(
                  (option, index) =>
                    `OPTION ${index + 1}:\n${option}`
                )
                .join("\n\n");
            }

            const parsed = splitMessageMetadata(message.content);
            const attachmentLine = Array.isArray(message.attachments)
              && message.attachments.length > 0
              ? `\nAttachments: ${message.attachments
                  .map(item => item.original_filename)
                  .join(", ")}\n`
              : "\n";

            return `${message.role.toUpperCase()}:${attachmentLine}${parsed.text}`;
          })
          .join("\n\n");

        await navigator.clipboard.writeText(text);
        alert("Chat copied to clipboard.");
      }
    );

    const exportTxtItem = createMenuItem(
      "Export TXT",
      () => {
        window.location.href = `/api/chats/${chat.id}/export/txt`;
      }
    );

    const exportMdItem = createMenuItem(
      "Export Markdown",
      () => {
        window.location.href = `/api/chats/${chat.id}/export/md`;
      }
    );

    const deleteItem = createMenuItem(
      "Delete",
      async () => {
        const confirmed = confirm(
          "Delete this chat and its uploaded files permanently?"
        );

        if (!confirmed) {
          return;
        }

        await deleteChatFromDatabase(chat.id);
        selectedChatIds.delete(chat.id);
        await loadChatsFromDatabase();
      }
    );
    deleteItem.classList.add("is-danger");

    menu.appendChild(renameItem);
    menu.appendChild(favoriteItem);
    menu.appendChild(pinItem);
    menu.appendChild(archiveItem);
    menu.appendChild(moveItem);
    menu.appendChild(tagsItem);
    menu.appendChild(copyItem);
    menu.appendChild(exportTxtItem);
    menu.appendChild(exportMdItem);
    menu.appendChild(deleteItem);

    menuBtn.addEventListener(
      "click",
      event => {
        event.stopPropagation();

        document
          .querySelectorAll(".chat-menu.show")
          .forEach(openMenu => {
            if (openMenu !== menu) {
              openMenu.classList.remove("show");
            }
          });

        menu.classList.toggle("show");
      }
    );

    menuWrapper.appendChild(menuBtn);
    menuWrapper.appendChild(menu);

    if (!bulkMode) {
      actions.appendChild(menuWrapper);
    }

    item.appendChild(titleBlock);
    item.appendChild(actions);

    elements.chatList.appendChild(item);
  });
}


function createMenuItem(
  text,
  callback
) {
  const item =
    document.createElement("button");

  item.className =
    "chat-menu-item";

  item.innerText = text;

  item.addEventListener(
    "click",
    async event => {
      event.stopPropagation();

      closeAllMenus();
      await callback();
    }
  );

  return item;
}


function closeAllMenus() {
  document
    .querySelectorAll(
      ".chat-menu.show"
    )
    .forEach(menu => {
      menu.classList.remove("show");
    });
}


document.addEventListener(
  "click",
  closeAllMenus
);


async function loadMessagesIfNeeded(
  chat
) {
  if (chat.messages.length > 0) {
    return;
  }

  const savedMessages =
    await fetchMessagesFromDatabase(
      chat.id
    );

  chat.messages =
    savedMessages.map(message => ({
      id: Number(message.id),
      role: message.role,
      content: message.content,
      model: message.model || null,
      mode: message.mode || null,
      attachments: Array.isArray(message.attachments)
        ? message.attachments
        : []
    }));
}


export async function loadChatMessages() {
  const activeChat =
    getActiveChat();

  elements.chat.innerHTML = "";

  if (!activeChat) {
    return;
  }

  await loadMessagesIfNeeded(
    activeChat
  );

  activeChat.messages.forEach(
    message => {
      if (
        message.role === "options"
      ) {
        renderSavedOptionCards(
          message.options
        );

        return;
      }

      const parsed =
        splitMessageMetadata(
          message.content
        );

      const messageElement =
        addMessage(
          parsed.text,
          message.role
        );

      renderSavedAttachments(
        messageElement,
        message.attachments
      );

      if (message.role === "bot") {
        formatBotMessage(
          messageElement,
          parsed.text
        );

        renderRagSources(
          messageElement,
          parsed.sources
        );
      }

      attachMessageActions(
        messageElement,
        message,
        activeChat,
        async (branch, draftText) => {
          await openChatById(branch.id, draftText);
        }
      );
    }
  );
}


function renderSavedOptionCards(
  options
) {
  const wrapper =
    document.createElement("div");

  wrapper.className =
    "options-wrapper";

  elements.chat.appendChild(wrapper);

  options.forEach(
    (option, index) => {
      const card =
        document.createElement("div");

      card.className =
        "option-card";

      const title =
        document.createElement("h3");

      title.innerText =
        `Option ${index + 1}`;

      const content =
        document.createElement("div");

      content.className =
        "option-content";

      if (
        typeof marked !== "undefined"
      ) {
        content.innerHTML =
          marked.parse(option);
      } else {
        content.innerText = option;
      }

      const actions =
        document.createElement("div");

      actions.className =
        "option-actions";

      const copyButton =
        document.createElement("button");

      copyButton.innerText = "Copy";

      copyButton.addEventListener(
        "click",
        async () => {
          await navigator.clipboard
            .writeText(option);

          copyButton.innerText =
            "Copied!";

          setTimeout(() => {
            copyButton.innerText =
              "Copy";
          }, 1500);
        }
      );

      const useButton =
        document.createElement("button");

      useButton.innerText = "Use This";

      useButton.addEventListener(
        "click",
        () => {
          const selectedMessage =
            addMessage(
              option,
              "bot"
            );

          formatBotMessage(
            selectedMessage,
            option
          );

          saveMessage(
            "bot",
            option
          );
        }
      );

      const readButton = createOptionReadButton(option);

      actions.appendChild(copyButton);
      actions.appendChild(readButton);
      actions.appendChild(useButton);

      card.appendChild(title);
      card.appendChild(content);
      card.appendChild(actions);

      wrapper.appendChild(card);
    }
  );

  elements.chat.scrollTop =
    elements.chat.scrollHeight;
}


function renderSavedAttachments(container, attachments) {
  if (!Array.isArray(attachments) || attachments.length === 0) {
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "message-attachments";

  attachments.forEach(attachment => {
    const item = document.createElement("div");
    item.className = "message-attachment";

    if (attachment.attachment_kind === "image" && attachment.preview_url) {
      const image = document.createElement("img");
      image.src = attachment.preview_url;
      image.alt = attachment.original_filename;
      image.loading = "lazy";
      item.appendChild(image);
    } else {
      const icon = document.createElement("span");
      icon.className = "message-attachment-icon";
      icon.innerText = attachment.file_type === "pdf" ? "PDF" : "FILE";
      item.appendChild(icon);
    }

    const name = document.createElement("span");
    name.className = "message-attachment-name";
    name.title = attachment.original_filename;
    name.innerText = attachment.original_filename;
    item.appendChild(name);
    wrapper.appendChild(item);
  });

  container.prepend(wrapper);
}


export async function initializeChatOrganization() {
  if (organizationInitialized) {
    return;
  }

  organizationInitialized = true;

  const organizerToggle = document.getElementById("chatOrganizerToggle");
  const organizerPanel = document.getElementById("chatOrganizerPanel");
  const folderFilter = document.getElementById("chatFolderFilter");
  const tagFilter = document.getElementById("chatTagFilter");
  const folderName = document.getElementById("chatFolderName");
  const folderAdd = document.getElementById("chatFolderAdd");
  const tagName = document.getElementById("chatTagName");
  const tagColor = document.getElementById("chatTagColor");
  const tagAdd = document.getElementById("chatTagAdd");
  const bulkToggle = document.getElementById("chatBulkModeToggle");
  const bulkCancel = document.getElementById("chatBulkCancel");
  const bulkAction = document.getElementById("chatBulkAction");
  const bulkTarget = document.getElementById("chatBulkTarget");
  const bulkApply = document.getElementById("chatBulkApply");

  organizerToggle?.addEventListener("click", event => {
    event.stopPropagation();
    const open = organizerPanel.hidden;
    organizerPanel.hidden = !open;
    organizerToggle.setAttribute("aria-expanded", String(open));
  });

  organizerPanel?.addEventListener("click", event => {
    event.stopPropagation();
  });

  document.addEventListener("click", () => {
    if (organizerPanel && !organizerPanel.hidden) {
      organizerPanel.hidden = true;
      organizerToggle?.setAttribute("aria-expanded", "false");
    }
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && organizerPanel && !organizerPanel.hidden) {
      organizerPanel.hidden = true;
      organizerToggle?.setAttribute("aria-expanded", "false");
      organizerToggle?.focus();
    }
  });

  document.querySelectorAll("[data-chat-view]").forEach(button => {
    button.addEventListener("click", () => {
      organizationView = button.dataset.chatView || "active";
      document.querySelectorAll("[data-chat-view]").forEach(item => {
        item.classList.toggle(
          "is-active",
          item.dataset.chatView === organizationView
        );
      });
      renderChatList();
    });
  });

  folderFilter?.addEventListener("change", () => {
    organizationFolderId = folderFilter.value
      ? Number(folderFilter.value)
      : null;
    renderChatList();
  });

  tagFilter?.addEventListener("change", () => {
    organizationTagId = tagFilter.value
      ? Number(tagFilter.value)
      : null;
    renderChatList();
  });

  folderAdd?.addEventListener("click", async () => {
    const name = folderName.value.trim();
    if (!name) {
      setOrganizationStatus("Enter a folder name.", true);
      folderName.focus();
      return;
    }
    try {
      await createChatFolder(name);
      folderName.value = "";
      await loadChatOrganizationMetadata();
      setOrganizationStatus("Folder created.");
    } catch (error) {
      setOrganizationStatus(error.message || "Folder could not be created.", true);
    }
  });

  folderName?.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      folderAdd.click();
    }
  });

  tagAdd?.addEventListener("click", async () => {
    const name = tagName.value.trim();
    if (!name) {
      setOrganizationStatus("Enter a tag name.", true);
      tagName.focus();
      return;
    }
    try {
      await createChatTag(name, tagColor.value);
      tagName.value = "";
      await loadChatOrganizationMetadata();
      setOrganizationStatus("Tag created.");
    } catch (error) {
      setOrganizationStatus(error.message || "Tag could not be created.", true);
    }
  });

  tagName?.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      tagAdd.click();
    }
  });

  bulkToggle?.addEventListener("click", () => {
    bulkMode = !bulkMode;
    selectedChatIds.clear();
    document.getElementById("chatBulkToolbar").hidden = !bulkMode;
    bulkToggle.innerText = bulkMode
      ? "Exit multi-select"
      : "Select multiple chats";
    renderChatList();
    updateBulkToolbar();
  });

  bulkCancel?.addEventListener("click", () => {
    bulkMode = false;
    selectedChatIds.clear();
    document.getElementById("chatBulkToolbar").hidden = true;
    if (bulkToggle) {
      bulkToggle.innerText = "Select multiple chats";
    }
    renderChatList();
  });

  bulkAction?.addEventListener("change", () => {
    updateBulkTargetOptions();
  });

  bulkApply?.addEventListener("click", async () => {
    if (selectedChatIds.size === 0) {
      setOrganizationStatus("Select at least one chat.", true);
      return;
    }

    const action = bulkAction.value;
    if (!action) {
      setOrganizationStatus("Choose a bulk action.", true);
      return;
    }

    if (
      action === "delete"
      && !confirm(`Delete ${selectedChatIds.size} selected chat(s) permanently?`)
    ) {
      return;
    }

    const payload = {
      action,
      chat_ids: Array.from(selectedChatIds)
    };

    if (action === "move") {
      payload.folder_id = bulkTarget.value
        ? Number(bulkTarget.value)
        : null;
    }

    if (["add_tag", "remove_tag"].includes(action)) {
      if (!bulkTarget.value) {
        setOrganizationStatus("Choose a tag.", true);
        return;
      }
      payload.tag_id = Number(bulkTarget.value);
    }

    try {
      const result = await bulkUpdateChats(payload);
      setOrganizationStatus(`${result.affected} chat(s) updated.`);
      selectedChatIds.clear();
      await loadChatsFromDatabase();
      updateBulkToolbar();
    } catch (error) {
      setOrganizationStatus(error.message || "Bulk action failed.", true);
    }
  });

  await loadChatOrganizationMetadata();
  updateBulkTargetOptions();
}


async function loadChatOrganizationMetadata() {
  try {
    const [folders, tags] = await Promise.all([
      fetchChatFolders(),
      fetchChatTags()
    ]);
    chatFolders = Array.isArray(folders) ? folders : [];
    chatTags = Array.isArray(tags) ? tags : [];
    renderOrganizationControls();
  } catch (error) {
    console.error("Could not load chat organization metadata:", error);
    setOrganizationStatus(
      error.message || "Could not load folders and tags.",
      true
    );
  }
}


function renderOrganizationControls() {
  const folderFilter = document.getElementById("chatFolderFilter");
  const tagFilter = document.getElementById("chatTagFilter");
  const folderList = document.getElementById("chatFolderList");
  const tagList = document.getElementById("chatTagList");

  if (folderFilter) {
    const selected = organizationFolderId === null
      ? ""
      : String(organizationFolderId);
    folderFilter.innerHTML = '<option value="">All folders</option>';
    chatFolders.forEach(folder => {
      const option = document.createElement("option");
      option.value = String(folder.id);
      option.innerText = `${folder.name} (${folder.chat_count})`;
      folderFilter.appendChild(option);
    });
    folderFilter.value = selected;
  }

  if (tagFilter) {
    const selected = organizationTagId === null
      ? ""
      : String(organizationTagId);
    tagFilter.innerHTML = '<option value="">All tags</option>';
    chatTags.forEach(tag => {
      const option = document.createElement("option");
      option.value = String(tag.id);
      option.innerText = `${tag.name} (${tag.chat_count})`;
      tagFilter.appendChild(option);
    });
    tagFilter.value = selected;
  }

  if (folderList) {
    folderList.innerHTML = "";

    const unfiled = createFolderDropItem(null, "No folder");
    folderList.appendChild(unfiled);

    chatFolders.forEach(folder => {
      const row = createFolderDropItem(folder.id, folder.name, folder.chat_count);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "chat-organizer-remove";
      remove.innerText = "×";
      remove.title = `Delete ${folder.name}`;
      remove.addEventListener("click", async event => {
        event.stopPropagation();
        if (!confirm(`Delete folder "${folder.name}"? Chats will remain available.`)) {
          return;
        }
        try {
          await deleteChatFolder(folder.id);
          if (organizationFolderId === Number(folder.id)) {
            organizationFolderId = null;
          }
          await loadChatOrganizationMetadata();
          await loadChatsFromDatabase();
        } catch (error) {
          setOrganizationStatus(error.message || "Folder could not be deleted.", true);
        }
      });
      row.appendChild(remove);
      folderList.appendChild(row);
    });
  }

  if (tagList) {
    tagList.innerHTML = "";
    chatTags.forEach(tag => {
      const row = document.createElement("div");
      row.className = "chat-organizer-list-item";
      const filter = document.createElement("button");
      filter.type = "button";
      filter.className = `chat-tag-filter-chip tag-${tag.color || "violet"}`;
      filter.innerText = `${tag.name} · ${tag.chat_count}`;
      filter.addEventListener("click", () => {
        organizationTagId = Number(tag.id);
        if (tagFilter) {
          tagFilter.value = String(tag.id);
        }
        renderChatList();
      });
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "chat-organizer-remove";
      remove.innerText = "×";
      remove.title = `Delete ${tag.name}`;
      remove.addEventListener("click", async () => {
        if (!confirm(`Delete tag "${tag.name}"?`)) {
          return;
        }
        try {
          await deleteChatTag(tag.id);
          if (organizationTagId === Number(tag.id)) {
            organizationTagId = null;
          }
          await loadChatOrganizationMetadata();
          await loadChatsFromDatabase();
        } catch (error) {
          setOrganizationStatus(error.message || "Tag could not be deleted.", true);
        }
      });
      row.appendChild(filter);
      row.appendChild(remove);
      tagList.appendChild(row);
    });
  }

  updateBulkTargetOptions();
}


function createFolderDropItem(folderId, name, count = null) {
  const row = document.createElement("div");
  row.className = "chat-organizer-list-item chat-folder-drop-target";
  row.dataset.folderId = folderId === null ? "" : String(folderId);

  const filter = document.createElement("button");
  filter.type = "button";
  filter.className = "chat-folder-filter-chip";
  filter.innerText = count === null ? name : `${name} · ${count}`;
  filter.addEventListener("click", () => {
    organizationFolderId = folderId === null ? null : Number(folderId);
    const select = document.getElementById("chatFolderFilter");
    if (select) {
      select.value = folderId === null ? "" : String(folderId);
    }
    renderChatList();
  });
  row.appendChild(filter);

  row.addEventListener("dragover", event => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    row.classList.add("is-drag-over");
  });

  row.addEventListener("dragleave", () => {
    row.classList.remove("is-drag-over");
  });

  row.addEventListener("drop", async event => {
    event.preventDefault();
    row.classList.remove("is-drag-over");
    const chatId = Number(event.dataTransfer.getData("text/plain"));
    if (!Number.isInteger(chatId)) {
      return;
    }
    try {
      await updateChatInDatabase(chatId, {
        folder_id: folderId
      });
      setOrganizationStatus(`Chat moved to ${name}.`);
      await loadChatsFromDatabase();
    } catch (error) {
      setOrganizationStatus(error.message || "Chat could not be moved.", true);
    }
  });

  return row;
}


function updateOrganizerCount(visibleCount) {
  const count = document.getElementById("chatOrganizerCount");
  if (count) {
    count.innerText = `${visibleCount}`;
  }
}


function setOrganizationStatus(message, isError = false) {
  const status = document.getElementById("chatOrganizationStatus");
  if (!status) {
    return;
  }
  status.innerText = message || "";
  status.classList.toggle("is-error", Boolean(isError));
}


function updateBulkToolbar() {
  const count = document.getElementById("chatBulkCount");
  if (count) {
    count.innerText = String(selectedChatIds.size);
  }
}


function updateBulkTargetOptions() {
  const action = document.getElementById("chatBulkAction")?.value || "";
  const target = document.getElementById("chatBulkTarget");

  if (!target) {
    return;
  }

  target.innerHTML = "";
  target.hidden = !["move", "add_tag", "remove_tag"].includes(action);

  if (action === "move") {
    target.appendChild(new Option("No folder", ""));
    chatFolders.forEach(folder => {
      target.appendChild(new Option(folder.name, String(folder.id)));
    });
  }

  if (["add_tag", "remove_tag"].includes(action)) {
    target.appendChild(new Option("Choose tag", ""));
    chatTags.forEach(tag => {
      target.appendChild(new Option(tag.name, String(tag.id)));
    });
  }
}


function notifyChatChanged() {
  document.dispatchEvent(
    new CustomEvent("ai-studio-chat-changed", {
      detail: { chatId: activeChatId }
    })
  );
}


elements.chatSearch.addEventListener(
  "input",
  renderChatList
);
