import { branchChatFromMessage } from "./api.js";


let branchDialog = null;
let branchDialogResolve = null;


function ensureBranchDialog() {
  if (branchDialog) return branchDialog;

  const backdrop = document.createElement("div");
  backdrop.className = "conversation-dialog-backdrop";
  backdrop.hidden = true;
  backdrop.innerHTML = `
    <section class="conversation-dialog" role="dialog" aria-modal="true" aria-labelledby="conversationDialogTitle">
      <header>
        <div>
          <span>Conversation branch</span>
          <h2 id="conversationDialogTitle">Edit message in a new branch</h2>
        </div>
        <button type="button" data-dialog-close aria-label="Close">×</button>
      </header>
      <label>
        <span>Branch title</span>
        <input type="text" data-branch-title maxlength="255">
      </label>
      <label>
        <span>Edited message</span>
        <textarea data-branch-content rows="8" maxlength="50000"></textarea>
      </label>
      <p data-branch-status role="status" aria-live="polite"></p>
      <footer>
        <button type="button" data-dialog-cancel>Cancel</button>
        <button type="button" data-dialog-confirm>Create branch</button>
      </footer>
    </section>
  `;

  document.body.appendChild(backdrop);

  const finish = value => {
    backdrop.hidden = true;
    document.body.classList.remove("conversation-dialog-open");
    if (branchDialogResolve) branchDialogResolve(value);
    branchDialogResolve = null;
  };

  backdrop.querySelector("[data-dialog-close]").addEventListener("click", () => finish(null));
  backdrop.querySelector("[data-dialog-cancel]").addEventListener("click", () => finish(null));
  backdrop.addEventListener("click", event => {
    if (event.target === backdrop) finish(null);
  });
  backdrop.querySelector("[data-dialog-confirm]").addEventListener("click", () => {
    const title = backdrop.querySelector("[data-branch-title]").value.trim();
    const content = backdrop.querySelector("[data-branch-content]").value.trim();
    const status = backdrop.querySelector("[data-branch-status]");
    if (!content) {
      status.textContent = "The edited message cannot be empty.";
      status.classList.add("is-error");
      return;
    }
    finish({ title, content });
  });

  document.addEventListener("keydown", event => {
    if (event.key === "Escape" && !backdrop.hidden) finish(null);
  });

  branchDialog = backdrop;
  return backdrop;
}


function requestEditedBranch(defaultTitle, content) {
  const dialog = ensureBranchDialog();
  dialog.querySelector("[data-branch-title]").value = defaultTitle;
  dialog.querySelector("[data-branch-content]").value = content;
  const status = dialog.querySelector("[data-branch-status]");
  status.textContent = "The original conversation remains unchanged.";
  status.classList.remove("is-error");
  dialog.hidden = false;
  document.body.classList.add("conversation-dialog-open");
  window.setTimeout(() => dialog.querySelector("[data-branch-content]").focus(), 30);

  return new Promise(resolve => {
    branchDialogResolve = resolve;
  });
}


function createActionButton(label, title, iconPath) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "message-action-button";
  button.title = title;
  button.setAttribute("aria-label", title);
  button.innerHTML = `
    <svg viewBox="0 0 24 24" aria-hidden="true">${iconPath}</svg>
    <span>${label}</span>
  `;
  return button;
}


async function createBranch({ chat, message, includeTarget, title, onOpenBranch, draftText }) {
  const branch = await branchChatFromMessage(chat.id, {
    message_id: message.id,
    include_target: includeTarget,
    title: title || undefined
  });
  await onOpenBranch(branch, draftText || "");
}


export function attachMessageActions(
  messageElement,
  message,
  chat,
  onOpenBranch
) {
  if (!messageElement || !message?.id || !chat?.id || typeof onOpenBranch !== "function") {
    return;
  }

  if (messageElement.querySelector(":scope > .message-action-bar")) return;

  const role = message.role === "assistant" ? "bot" : message.role;
  if (!["user", "bot"].includes(role)) return;

  const actions = document.createElement("div");
  actions.className = "message-action-bar";

  const branchButton = createActionButton(
    "Branch",
    "Continue this conversation in a new branch",
    '<path d="M6 4v7a4 4 0 0 0 4 4h8"></path><path d="m15 12 3 3-3 3"></path><circle cx="6" cy="4" r="2"></circle>'
  );

  branchButton.addEventListener("click", async () => {
    branchButton.disabled = true;
    try {
      await createBranch({
        chat,
        message,
        includeTarget: true,
        title: `Branch: ${chat.title}`,
        onOpenBranch
      });
    } catch (error) {
      window.alert(error.message || "Could not create the branch.");
    } finally {
      branchButton.disabled = false;
    }
  });

  actions.appendChild(branchButton);

  if (role === "user") {
    const editButton = createActionButton(
      "Edit in branch",
      "Edit this message without changing the original conversation",
      '<path d="M4 20h4l10.5-10.5a2.8 2.8 0 0 0-4-4L4 16v4Z"></path><path d="m13.5 6.5 4 4"></path>'
    );

    editButton.addEventListener("click", async () => {
      const result = await requestEditedBranch(
        `Edited branch: ${chat.title}`,
        String(message.content || "")
      );
      if (!result) return;

      editButton.disabled = true;
      try {
        await createBranch({
          chat,
          message,
          includeTarget: false,
          title: result.title,
          onOpenBranch,
          draftText: result.content
        });
      } catch (error) {
        window.alert(error.message || "Could not create the edited branch.");
      } finally {
        editButton.disabled = false;
      }
    });

    actions.prepend(editButton);
  }

  messageElement.appendChild(actions);
}
