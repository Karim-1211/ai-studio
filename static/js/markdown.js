import { attachReadAloudButton } from "./voice.js";
import { normalizeAssistantText } from "./text_quality.js";

export function formatBotMessage(message, markdownText) {
  const normalizedMarkdownText = normalizeAssistantText(markdownText);

  try {
    if (typeof marked !== "undefined") {
      message.innerHTML = marked.parse(normalizedMarkdownText);
      message.classList.add("is-formatted");
    } else {
      message.innerText = normalizedMarkdownText;
      return;
    }

    const messageCopyButton = document.createElement("button");
    messageCopyButton.className = "copy-message-btn";
    messageCopyButton.innerText = "Copy Answer";

    messageCopyButton.addEventListener("click", async () => {
      await navigator.clipboard.writeText(normalizedMarkdownText);
      messageCopyButton.innerText = "Copied!";

      setTimeout(() => {
        messageCopyButton.innerText = "Copy Answer";
      }, 1500);
    });

    message.appendChild(messageCopyButton);
    attachReadAloudButton(message, normalizedMarkdownText);

    if (typeof hljs !== "undefined") {
      message.querySelectorAll("pre code").forEach(block => {
        hljs.highlightElement(block);

        const pre = block.parentElement;
        const copyButton = document.createElement("button");

        copyButton.className = "copy-btn";
        copyButton.innerText = "Copy";

        copyButton.addEventListener("click", async () => {
          await navigator.clipboard.writeText(block.innerText);
          copyButton.innerText = "Copied!";

          setTimeout(() => {
            copyButton.innerText = "Copy";
          }, 1500);
        });

        pre.appendChild(copyButton);
      });
    }
  } catch (error) {
    console.error("Markdown formatting error:", error);
    message.innerText = normalizedMarkdownText;
  }
}