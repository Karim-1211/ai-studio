import { sendChatRequest } from "./api.js";

import {
  elements,
  addMessage,
  handleChatError,
  readRagSourcesFromResponse,
  renderRagSources,
  serializeMessageWithSources
} from "./ui.js";

import {
  getDocumentRequestSettings
} from "./documents.js";

import {
  getGenerationSettings
} from "./settings.js";

import { formatBotMessage } from "./markdown.js";

import {
  isQuotaErrorMessage,
  startQuotaCooldown
} from "./quota_guard.js";

import {
  getActiveChat,
  openChatById,
  saveMessage
} from "./sidebar.js";

import {
  speakAssistantResponse
} from "./voice.js";

import {
  attachMessageActions
} from "./conversation.js";


export async function generateNormalResponse(
  prompt,
  controller,
  attachmentIds = []
) {
  const botMessage = addMessage(
    "AI is thinking",
    "bot loading"
  );

  try {
    const activeChat = getActiveChat();

    const documentSettings =
      getDocumentRequestSettings();

    const generationSettings =
      getGenerationSettings();

    const response = await sendChatRequest(
      {
        prompt,
        model: elements.model.value,
        mode: elements.responseMode.value,
        chat_id: activeChat?.id ?? null,
        attachment_ids: attachmentIds,
        ...generationSettings,
        ...documentSettings
      },
      controller.signal
    );

    if (!response.ok) {
      const errorText = await response.text();

      throw new Error(
        errorText ||
        `Chat request failed with status ${response.status}.`
      );
    }

    if (!response.body) {
      throw new Error(
        "The server returned an empty response stream."
      );
    }

    const ragSources =
      readRagSourcesFromResponse(response);

    botMessage.innerText = "";
    botMessage.classList.remove("loading");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let fullResponse = "";

    while (true) {
      const result = await reader.read();

      if (result.done) {
        break;
      }

      const chunk = decoder.decode(
        result.value,
        { stream: true }
      );

      fullResponse += chunk;

      botMessage.innerText =
        `${fullResponse} ▋`;

      elements.chat.scrollTop =
        elements.chat.scrollHeight;
    }

    fullResponse += decoder.decode();

    if (!fullResponse.trim()) {
      throw new Error(
        "The model returned an empty response."
      );
    }

    formatBotMessage(
      botMessage,
      fullResponse
    );

    renderRagSources(
      botMessage,
      ragSources
    );

    const savedBotMessage = await saveMessage(
      "bot",
      serializeMessageWithSources(
        fullResponse,
        ragSources
      )
    );

    attachMessageActions(
      botMessage,
      savedBotMessage,
      getActiveChat(),
      async (branch, draftText) => {
        await openChatById(branch.id, draftText);
      }
    );

    speakAssistantResponse(fullResponse);

    elements.chat.scrollTop =
      elements.chat.scrollHeight;

  } catch (error) {
    if (isQuotaErrorMessage(error?.message)) {
      startQuotaCooldown();
      error.message = (
        "Gemini is temporarily rate-limited. Please wait 1–2 minutes, " +
        "then try Single Answer again. Avoid repeated 3 Options requests on the free tier."
      );
    }

    handleChatError(
      error,
      botMessage
    );
  }
}
