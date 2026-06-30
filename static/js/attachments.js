import {
  deleteMessageAttachment,
  uploadMessageAttachment
} from "./api.js";

import { elements } from "./ui.js";
import {
  createChat,
  getActiveChat
} from "./sidebar.js";


const MAX_FILES = 5;
const MAX_FILE_BYTES = 20 * 1024 * 1024;
const MAX_TOTAL_BYTES = 40 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set([
  "pdf",
  "docx",
  "txt",
  "png",
  "jpg",
  "jpeg",
  "webp"
]);

let initialized = false;
let pendingAttachments = [];
let pendingChatId = null;
let uploading = false;


export function initializeAttachmentManager() {
  if (initialized) {
    return;
  }

  initialized = true;

  elements.attachmentButton.addEventListener(
    "click",
    () => elements.attachmentInput.click()
  );

  elements.attachmentInput.addEventListener(
    "change",
    async () => {
      const files = Array.from(
        elements.attachmentInput.files || []
      );
      elements.attachmentInput.value = "";
      await addFiles(files);
    }
  );

  elements.inputArea.addEventListener(
    "dragover",
    event => {
      event.preventDefault();
      elements.inputArea.classList.add("is-dragging");
    }
  );

  elements.inputArea.addEventListener(
    "dragleave",
    event => {
      if (!elements.inputArea.contains(event.relatedTarget)) {
        elements.inputArea.classList.remove("is-dragging");
      }
    }
  );

  elements.inputArea.addEventListener(
    "drop",
    async event => {
      event.preventDefault();
      elements.inputArea.classList.remove("is-dragging");
      await addFiles(Array.from(event.dataTransfer?.files || []));
    }
  );

  elements.promptInput.addEventListener(
    "paste",
    async event => {
      const imageFiles = Array.from(
        event.clipboardData?.items || []
      )
        .filter(item => item.kind === "file" && item.type.startsWith("image/"))
        .map((item, index) => {
          const file = item.getAsFile();
          if (!file) {
            return null;
          }

          const extension = file.type === "image/webp"
            ? "webp"
            : file.type === "image/jpeg"
              ? "jpg"
              : "png";

          return new File(
            [file],
            `pasted-image-${Date.now()}-${index + 1}.${extension}`,
            { type: file.type || `image/${extension}` }
          );
        })
        .filter(Boolean);

      if (imageFiles.length > 0) {
        event.preventDefault();
        await addFiles(imageFiles);
      }
    }
  );

  document.addEventListener(
    "ai-studio-chat-changed",
    async () => {
      const activeChatId = getActiveChat()?.id ?? null;
      if (
        pendingAttachments.length > 0
        && pendingChatId !== activeChatId
      ) {
        await discardPendingAttachments();
      }
    }
  );

  renderPendingAttachments();
}


export function getPendingAttachmentIds() {
  const activeChatId = getActiveChat()?.id ?? null;
  if (pendingChatId !== activeChatId) {
    return [];
  }

  return pendingAttachments.map(item => item.id);
}


export function getPendingAttachments() {
  const activeChatId = getActiveChat()?.id ?? null;
  if (pendingChatId !== activeChatId) {
    return [];
  }

  return pendingAttachments.map(item => ({ ...item }));
}


export function consumePendingAttachments() {
  const attachments = getPendingAttachments();
  pendingAttachments = [];
  pendingChatId = null;
  renderPendingAttachments();
  return attachments;
}


export async function discardPendingAttachments() {
  const attachments = [...pendingAttachments];
  pendingAttachments = [];
  pendingChatId = null;
  renderPendingAttachments();

  await Promise.allSettled(
    attachments.map(item => deleteMessageAttachment(item.id))
  );
}


export function renderMessageAttachments(container, attachments) {
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


async function addFiles(files) {
  if (uploading || files.length === 0) {
    return;
  }

  if (pendingAttachments.length + files.length > MAX_FILES) {
    setAttachmentStatus(
      `You can attach up to ${MAX_FILES} files to one message.`,
      "error"
    );
    return;
  }

  for (const file of files) {
    const error = validateFile(file);
    if (error) {
      setAttachmentStatus(error, "error");
      return;
    }
  }

  const pendingBytes = pendingAttachments.reduce(
    (total, item) => total + Number(item.file_size || 0),
    0
  );
  const newBytes = files.reduce(
    (total, file) => total + Number(file.size || 0),
    0
  );

  if (pendingBytes + newBytes > MAX_TOTAL_BYTES) {
    setAttachmentStatus(
      "The total attachment size for one message cannot exceed 40 MB.",
      "error"
    );
    return;
  }

  let activeChat = getActiveChat();
  if (!activeChat) {
    await createChat();
    activeChat = getActiveChat();
  }

  if (!activeChat) {
    setAttachmentStatus("A chat could not be created.", "error");
    return;
  }

  if (
    pendingChatId !== null
    && pendingChatId !== activeChat.id
  ) {
    await discardPendingAttachments();
  }

  pendingChatId = activeChat.id;
  uploading = true;
  elements.attachmentButton.disabled = true;

  try {
    for (let index = 0; index < files.length; index += 1) {
      const file = files[index];
      setAttachmentStatus(
        `Preparing ${file.name} (${index + 1}/${files.length})...`,
        "working"
      );

      const result = await uploadMessageAttachment(activeChat.id, file);
      pendingAttachments.push(result.attachment);
      renderPendingAttachments();
    }

    setAttachmentStatus(
      `${files.length} ${files.length === 1 ? "attachment" : "attachments"} ready.`,
      "success"
    );
  } catch (error) {
    setAttachmentStatus(
      error.message || "The attachment could not be uploaded.",
      "error"
    );
  } finally {
    uploading = false;
    elements.attachmentButton.disabled = false;
  }
}


function renderPendingAttachments() {
  elements.attachmentPreviewList.innerHTML = "";
  elements.attachmentPreviewList.hidden = pendingAttachments.length === 0;

  pendingAttachments.forEach(attachment => {
    const chip = document.createElement("div");
    chip.className = "attachment-preview-chip";

    if (attachment.attachment_kind === "image" && attachment.preview_url) {
      const image = document.createElement("img");
      image.src = attachment.preview_url;
      image.alt = "";
      chip.appendChild(image);
    } else {
      const icon = document.createElement("span");
      icon.className = "attachment-preview-icon";
      icon.innerText = attachment.file_type === "pdf" ? "PDF" : "FILE";
      chip.appendChild(icon);
    }

    const text = document.createElement("span");
    text.className = "attachment-preview-name";
    text.title = attachment.original_filename;
    text.innerText = attachment.original_filename;

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "attachment-remove-button";
    removeButton.setAttribute(
      "aria-label",
      `Remove ${attachment.original_filename}`
    );
    removeButton.innerText = "×";
    removeButton.addEventListener(
      "click",
      async () => {
        removeButton.disabled = true;
        try {
          await deleteMessageAttachment(attachment.id);
          pendingAttachments = pendingAttachments.filter(
            item => item.id !== attachment.id
          );
          if (pendingAttachments.length === 0) {
            pendingChatId = null;
          }
          renderPendingAttachments();
          setAttachmentStatus("Attachment removed.", "success");
        } catch (error) {
          removeButton.disabled = false;
          setAttachmentStatus(
            error.message || "Attachment could not be removed.",
            "error"
          );
        }
      }
    );

    chip.appendChild(text);
    chip.appendChild(removeButton);
    elements.attachmentPreviewList.appendChild(chip);
  });
}


function validateFile(file) {
  const extension = String(file.name || "")
    .split(".")
    .pop()
    .toLowerCase();

  if (!ALLOWED_EXTENSIONS.has(extension)) {
    return `${file.name}: use PDF, DOCX, TXT, PNG, JPG, JPEG, or WebP.`;
  }

  if (file.size > MAX_FILE_BYTES) {
    return `${file.name}: the maximum size is 20 MB.`;
  }

  return "";
}


function setAttachmentStatus(message, state = "") {
  elements.attachmentStatus.innerText = message;
  elements.attachmentStatus.className =
    `attachment-status ${state ? `is-${state}` : ""}`.trim();
}
