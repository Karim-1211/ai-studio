import {
  downloadWorkspaceBackup,
  restoreWorkspaceBackup
} from "./api.js";


let initialized = false;


export function initializeWorkspaceTools() {
  if (initialized) {
    return;
  }

  initialized = true;

  const backupButton = document.getElementById("workspaceBackupButton");
  const restoreButton = document.getElementById("workspaceRestoreButton");
  const restoreInput = document.getElementById("workspaceRestoreInput");

  backupButton?.addEventListener("click", async () => {
    const originalText = backupButton.innerText;
    backupButton.disabled = true;
    backupButton.innerText = "Preparing backup…";

    try {
      const blob = await downloadWorkspaceBackup();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      const stamp = new Date().toISOString().replace(/[:.]/g, "-");
      anchor.href = url;
      anchor.download = `ai-studio-workspace-${stamp}.zip`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      alert(error.message || "Workspace backup could not be created.");
    } finally {
      backupButton.disabled = false;
      backupButton.innerText = originalText;
    }
  });

  restoreButton?.addEventListener("click", () => {
    restoreInput?.click();
  });

  restoreInput?.addEventListener("change", async () => {
    const file = restoreInput.files?.[0];
    if (!file) {
      return;
    }

    const confirmed = confirm(
      "Restore this backup into your current workspace? Existing data will be kept and restored items will be added."
    );

    if (!confirmed) {
      restoreInput.value = "";
      return;
    }

    const originalText = restoreButton.innerText;
    restoreButton.disabled = true;
    restoreButton.innerText = "Restoring…";

    try {
      const result = await restoreWorkspaceBackup(file);
      const summary = result.summary || {};
      alert(
        `Workspace restored.\n\nChats: ${summary.chats || 0}\nMessages: ${summary.messages || 0}\nDocuments: ${(summary.documents || 0) + (summary.global_documents || 0)}\nWebsite sources: ${summary.website_sources || 0}\nSocial sources: ${summary.social_sources || 0}`
      );
      window.location.reload();
    } catch (error) {
      alert(error.message || "Workspace backup could not be restored.");
    } finally {
      restoreInput.value = "";
      restoreButton.disabled = false;
      restoreButton.innerText = originalText;
    }
  });
}
