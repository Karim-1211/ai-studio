import { attachReadAloudButton } from "./voice.js";

export function formatBotMessage(message, markdownText) {
  try {
    if (typeof marked !== "undefined") {
      message.innerHTML = marked.parse(markdownText);
      message.classList.add("is-formatted");
    } else {
      message.innerText = markdownText;
      return;
    }

    const messageCopyButton = document.createElement("button");
    messageCopyButton.className = "copy-message-btn";
    messageCopyButton.innerText = "Copy Answer";

    messageCopyButton.addEventListener("click", async () => {
      await navigator.clipboard.writeText(markdownText);
      messageCopyButton.innerText = "Copied!";

      setTimeout(() => {
        messageCopyButton.innerText = "Copy Answer";
      }, 1500);
    });

    message.appendChild(messageCopyButton);
    attachReadAloudButton(message, markdownText);

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
    message.innerText = markdownText;
  }
}