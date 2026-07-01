import { sendChatRequest } from "./api.js";

import {
  elements,
  addMessage,
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
  applyQuotaGuardToResponseMode,
  getQuotaCooldownMessage,
  getQuotaCooldownRemainingMs,
  isQuotaErrorMessage,
  startQuotaCooldown
} from "./quota_guard.js";

import {
  getActiveChat,
  saveMessage,
  saveOptions
} from "./sidebar.js";

import {
  createOptionReadButton
} from "./voice.js";


export async function generateOptionCards(
  prompt,
  controller,
  attachmentIds = []
) {
  const wrapper =
    document.createElement("div");

  wrapper.className = "options-wrapper";

  elements.chat.appendChild(wrapper);

  const cards = [1, 2, 3].map(
    optionNumber =>
      createOptionCard(
        wrapper,
        optionNumber
      )
  );

  if (getQuotaCooldownRemainingMs() > 0) {
    const message = getQuotaCooldownMessage();
    cards.forEach(card => {
      card.card.classList.add("option-card-error");
      card.badge.innerText = "Cooldown";
      card.content.innerText = message;
    });
    applyQuotaGuardToResponseMode(elements.responseMode);
    return;
  }

  try {
    const result = await generateBatchOptions(
      prompt,
      cards,
      controller,
      attachmentIds
    );

    const parsedOptions = parseBatchOptions(
      result.text
    );

    parsedOptions.forEach(
      (optionText, index) => {
        const card = cards[index];

        renderOptionMarkdown(
          card.content,
          optionText
        );

        renderRagSources(
          card.card,
          result.sources,
          true
        );

        addOptionActions(
          card,
          optionText,
          result.sources
        );
      }
    );

    if (parsedOptions.length > 0) {
      saveOptions(parsedOptions);
    }

  } catch (error) {
    if (isQuotaErrorMessage(error?.message)) {
      startQuotaCooldown();
      applyQuotaGuardToResponseMode(elements.responseMode);
    }

    const safeMessage = error.name === "AbortError"
      ? "[Generation stopped]"
      : (
          isQuotaErrorMessage(error?.message)
            ? getQuotaCooldownMessage()
            : (
                error.message ||
                "The options could not be generated."
              )
        );

    cards.forEach(card => {
      card.card.classList.add(
        "option-card-error"
      );
      card.badge.innerText = "Failed";
      card.content.innerText = safeMessage;
    });
  }

  elements.chat.scrollTop =
    elements.chat.scrollHeight;
}


async function generateBatchOptions(
  prompt,
  cards,
  controller,
  attachmentIds = []
) {
  const activeChat = getActiveChat();

  const documentSettings =
    getDocumentRequestSettings();

  const generationSettings =
    getGenerationSettings();

  const response = await sendChatRequest(
    {
      prompt,
      model: elements.model.value,
      mode: "options_batch",
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
      `Option request failed with status ${response.status}.`
    );
  }

  if (!response.body) {
    throw new Error(
      "The server returned an empty option stream."
    );
  }

  const ragSources =
    readRagSourcesFromResponse(response);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let fullResponse = "";

  cards.forEach(card => {
    card.content.classList.add(
      "option-content-loading"
    );
    card.content.innerText =
      "Generating comparison options...";
  });

  while (true) {
    const result = await reader.read();

    if (result.done) {
      break;
    }

    fullResponse += decoder.decode(
      result.value,
      { stream: true }
    );

    const previewOptions = parseBatchOptions(
      fullResponse,
      false
    );

    previewOptions.forEach(
      (optionText, index) => {
        if (cards[index]) {
          cards[index].content.innerText =
            `${optionText} ▋`;
        }
      }
    );

    elements.chat.scrollTop =
      elements.chat.scrollHeight;
  }

  fullResponse += decoder.decode();

  cards.forEach(card => {
    card.content.classList.remove(
      "option-content-loading"
    );
  });

  if (!fullResponse.trim()) {
    throw new Error(
      "The model returned an empty options response."
    );
  }

  return {
    text: fullResponse.trim(),
    sources: ragSources
  };
}


function parseBatchOptions(
  text,
  requireAll = true
) {
  const cleaned = String(text || "").trim();

  if (!cleaned) {
    return [];
  }

  const matches = [...cleaned.matchAll(
    /(?:^|\n)#{1,3}\s*Option\s*(\d)\s*\n([\s\S]*?)(?=(?:\n#{1,3}\s*Option\s*\d\s*\n)|$)/gi
  )];

  let options = matches
    .sort((a, b) => Number(a[1]) - Number(b[1]))
    .map(match => match[2].trim())
    .filter(Boolean)
    .slice(0, 3);

  if (
    options.length === 0 &&
    cleaned.includes("Option 1")
  ) {
    options = cleaned
      .split(/Option\s*\d\s*:?/i)
      .map(part => part.trim())
      .filter(Boolean)
      .slice(0, 3);
  }

  if (
    options.length === 0 &&
    !requireAll
  ) {
    return [cleaned];
  }

  if (
    requireAll &&
    options.length < 3
  ) {
    const fallbackChunks = cleaned
      .split(/\n\s*---\s*\n|\n\s*\*\*Option\s*\d\*\*\s*\n/i)
      .map(part => part.trim())
      .filter(Boolean)
      .slice(0, 3);

    if (fallbackChunks.length > options.length) {
      options = fallbackChunks;
    }
  }

  return options.slice(0, 3);
}


async function generateSingleOption(
  prompt,
  optionNumber,
  cardParts,
  controller,
  attachmentIds = []
) {
  const activeChat = getActiveChat();

  const documentSettings =
    getDocumentRequestSettings();

  const generationSettings =
    getGenerationSettings();

  const response = await sendChatRequest(
    {
      prompt,
      model: elements.model.value,
      mode: "options",
      option_number: optionNumber,
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
      `Option request failed with status ${response.status}.`
    );
  }

  if (!response.body) {
    throw new Error(
      "The server returned an empty option stream."
    );
  }

  const ragSources =
    readRagSourcesFromResponse(response);

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let fullResponse = "";

  cardParts.content.classList.add(
    "option-content-loading"
  );

  while (true) {
    const result = await reader.read();

    if (result.done) {
      break;
    }

    fullResponse += decoder.decode(
      result.value,
      { stream: true }
    );

    cardParts.content.innerText =
      `${fullResponse} ▋`;

    elements.chat.scrollTop =
      elements.chat.scrollHeight;
  }

  fullResponse += decoder.decode();

  cardParts.content.classList.remove(
    "option-content-loading"
  );

  renderOptionMarkdown(
    cardParts.content,
    fullResponse
  );

  renderRagSources(
    cardParts.card,
    ragSources,
    true
  );

  return {
    text: fullResponse.trim(),
    sources: ragSources
  };
}


function createOptionCard(
  wrapper,
  optionNumber
) {
  const card =
    document.createElement("article");

  card.className = "option-card";

  const heading =
    document.createElement("div");

  heading.className = "option-heading";

  const title =
    document.createElement("h3");

  title.innerText =
    `Option ${optionNumber}`;

  const badge =
    document.createElement("span");

  badge.innerText = "Generating";

  heading.appendChild(title);
  heading.appendChild(badge);

  const content =
    document.createElement("div");

  content.className = "option-content";
  content.innerText = "Waiting...";

  const actions =
    document.createElement("div");

  actions.className = "option-actions";

  card.appendChild(heading);
  card.appendChild(content);
  card.appendChild(actions);

  wrapper.appendChild(card);

  return {
    card,
    heading,
    badge,
    content,
    actions
  };
}


function addOptionActions(
  cardParts,
  optionText,
  sources
) {
  cardParts.badge.innerText = "Ready";
  cardParts.actions.innerHTML = "";

  const copyButton =
    document.createElement("button");

  copyButton.type = "button";
  copyButton.innerText = "Copy";

  copyButton.addEventListener(
    "click",
    async () => {
      await navigator.clipboard.writeText(
        optionText
      );

      copyButton.innerText = "Copied";

      setTimeout(() => {
        copyButton.innerText = "Copy";
      }, 1400);
    }
  );

  const useButton =
    document.createElement("button");

  useButton.type = "button";
  useButton.innerText = "Use This";

  useButton.addEventListener(
    "click",
    async () => {
      const selectedMessage = addMessage(
        optionText,
        "bot"
      );

      formatBotMessage(
        selectedMessage,
        optionText
      );

      renderRagSources(
        selectedMessage,
        sources
      );

      await saveMessage(
        "bot",
        serializeMessageWithSources(
          optionText,
          sources
        )
      );
    }
  );

  const readButton = createOptionReadButton(optionText);

  cardParts.actions.appendChild(
    copyButton
  );

  cardParts.actions.appendChild(
    readButton
  );

  cardParts.actions.appendChild(
    useButton
  );
}


function renderOptionMarkdown(
  element,
  text
) {
  if (
    typeof marked !== "undefined"
    && typeof marked.parse === "function"
  ) {
    element.innerHTML =
      marked.parse(text);
  } else {
    element.innerText = text;
  }

  if (typeof hljs !== "undefined") {
    element
      .querySelectorAll("pre code")
      .forEach(block => {
        hljs.highlightElement(block);
      });
  }
}
