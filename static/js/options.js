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

  const generatedOptions = [];

  for (
    let index = 0;
    index < cards.length;
    index += 1
  ) {
    if (controller.signal.aborted) {
      cards[index].content.innerText =
        "[Generation stopped]";

      break;
    }

    try {
      const result =
        await generateSingleOption(
          prompt,
          index + 1,
          cards[index],
          controller,
          attachmentIds
        );

      if (result.text) {
        generatedOptions.push(result.text);

        addOptionActions(
          cards[index],
          result.text,
          result.sources
        );
      }

    } catch (error) {
      if (error.name === "AbortError") {
        cards[index].content.innerText =
          "[Generation stopped]";

        break;
      }

      console.error(
        `Option ${index + 1} error:`,
        error
      );

      cards[index].card.classList.add(
        "option-card-error"
      );

      cards[index].badge.innerText =
        "Failed";

      cards[index].content.innerText =
        error.message ||
        "This option could not be generated.";
    }
  }

  if (generatedOptions.length > 0) {
    saveOptions(generatedOptions);
  }

  elements.chat.scrollTop =
    elements.chat.scrollHeight;
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
