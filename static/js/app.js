import {
  elements,
  addMessage
} from "./ui.js";

import {
  initializeSettings,
  loadModels
} from "./settings.js";

import {
  createChat,
  getActiveChat,
  openChatById,
  saveMessage,
  loadChatsFromDatabase,
  initializeChatOrganization
} from "./sidebar.js";

import {
  initializeDocumentManager,
  loadDocumentsForActiveChat
} from "./documents.js";

import {
  generateNormalResponse
} from "./chat.js";

import {
  generateOptionCards
} from "./options.js";

import {
  initializeSystemStatus
} from "./system_status.js";

import {
  consumePendingAttachments,
  discardPendingAttachments,
  getPendingAttachmentIds,
  getPendingAttachments,
  initializeAttachmentManager,
  renderMessageAttachments
} from "./attachments.js";

import {
  initializeVoiceChat,
  stopVoiceActivity,
  stopVoiceInput
} from "./voice.js";

import {
  initializeWorkspaceTools
} from "./workspace.js";

import {
  initializePromptLibrary
} from "./prompts.js";

import {
  attachMessageActions
} from "./conversation.js";


let controller = null;
let isGenerating = false;
let lastPrompt = "";


function setSendButtonState(generating) {
  const label = generating
    ? "Stop generating"
    : "Send message";

  elements.sendButton.classList.toggle(
    "is-generating",
    generating
  );
  elements.sendButton.setAttribute(
    "aria-label",
    label
  );
  elements.sendButton.title = label;

  const labelElement = document.getElementById(
    "sendButtonLabel"
  );

  if (labelElement) {
    labelElement.textContent = label;
  }
}


function stopGeneration() {
  if (controller) {
    controller.abort();
  }
}


async function send() {
  stopVoiceInput();

  if (isGenerating) {
    stopGeneration();
    return;
  }

  const pendingAttachments = getPendingAttachments();
  const attachmentIds = getPendingAttachmentIds();

  let prompt = elements.promptInput.value.trim();

  if (!prompt && pendingAttachments.length === 0) {
    return;
  }

  if (!prompt) {
    prompt = "Please analyze the attached file or image and provide a helpful response.";
  }

  if (!elements.model.value) {
    alert(
      "No AI generation model is available. Check your active provider settings."
    );
    return;
  }

  if (!getActiveChat()) {
    await createChat();
    await loadDocumentsForActiveChat();
  }

  lastPrompt = prompt;

  controller = new AbortController();
  isGenerating = true;

  const userMessage = addMessage(
    prompt,
    "user"
  );

  renderMessageAttachments(
    userMessage,
    pendingAttachments
  );

  try {
    const savedUserMessage = await saveMessage(
      "user",
      prompt,
      pendingAttachments
    );

    attachMessageActions(
      userMessage,
      savedUserMessage,
      getActiveChat(),
      async (branch, draftText) => {
        await openChatById(branch.id, draftText);
      }
    );

    consumePendingAttachments();
  } catch (error) {
    userMessage.classList.add("error");
    userMessage.innerText =
      `Could not save the message: ${error.message || error}`;
    isGenerating = false;
    controller = null;
    return;
  }

  elements.promptInput.value = "";
  resizePrompt();
  elements.promptInput.disabled = true;

  elements.sendButton.disabled = false;
  setSendButtonState(true);

  try {
    if (
      elements.responseMode.value === "options"
    ) {
      await generateOptionCards(
        prompt,
        controller,
        attachmentIds
      );
    } else {
      await generateNormalResponse(
        prompt,
        controller,
        attachmentIds
      );
    }

  } finally {
    isGenerating = false;
    controller = null;

    elements.promptInput.disabled = false;
    elements.sendButton.disabled = false;
    setSendButtonState(false);

    elements.promptInput.focus();
  }
}


setSendButtonState(false);


elements.sendButton.addEventListener(
  "click",
  send
);


elements.promptInput.addEventListener(
  "keydown",
  event => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  }
);


elements.promptInput.addEventListener(
  "input",
  resizePrompt
);


elements.newChatButton.addEventListener(
  "click",
  async () => {
    if (isGenerating) {
      stopGeneration();
    }

    stopVoiceActivity();
    await discardPendingAttachments();
    await createChat();
    await loadDocumentsForActiveChat();
  }
);


elements.regenerateButton.addEventListener(
  "click",
  () => {
    if (!lastPrompt || isGenerating) {
      return;
    }

    elements.promptInput.value = lastPrompt;
    send();
  }
);


function resizePrompt() {
  elements.promptInput.style.height = "auto";
  elements.promptInput.style.height =
    `${Math.min(elements.promptInput.scrollHeight, 160)}px`;
}


initializeSettings();
initializeSystemStatus();
initializeAttachmentManager();
initializeVoiceChat();
initializeWorkspaceTools();
initializePromptLibrary();
await initializeChatOrganization();
await loadModels();
await loadChatsFromDatabase();

if (!getActiveChat()) {
  await createChat();
}

initializeDocumentManager();
await loadDocumentsForActiveChat();
