const QUOTA_STORAGE_KEY = "aiStudioGeminiQuotaCooldownUntil";
const DEFAULT_COOLDOWN_MS = 2 * 60 * 1000;

export function isQuotaErrorMessage(message) {
  const text = String(message || "").toLowerCase();
  return (
    text.includes("rate limit") ||
    text.includes("too many requests") ||
    text.includes("429") ||
    text.includes("quota")
  );
}

export function startQuotaCooldown(durationMs = DEFAULT_COOLDOWN_MS) {
  const until = Date.now() + Number(durationMs || DEFAULT_COOLDOWN_MS);
  localStorage.setItem(QUOTA_STORAGE_KEY, String(until));
  return until;
}

export function getQuotaCooldownRemainingMs() {
  const raw = Number(localStorage.getItem(QUOTA_STORAGE_KEY) || 0);
  if (!raw || Number.isNaN(raw)) {
    return 0;
  }

  const remaining = raw - Date.now();
  if (remaining <= 0) {
    localStorage.removeItem(QUOTA_STORAGE_KEY);
    return 0;
  }

  return remaining;
}

export function getQuotaCooldownMessage() {
  const remainingMs = getQuotaCooldownRemainingMs();
  const remainingSeconds = Math.max(1, Math.ceil(remainingMs / 1000));

  return (
    `Gemini is temporarily rate-limited. Please wait about ${remainingSeconds} ` +
    `second${remainingSeconds === 1 ? "" : "s"} before trying again. ` +
    "Use Single Answer for testing and avoid repeated 3 Options requests on the free tier."
  );
}

export function applyQuotaGuardToResponseMode(responseModeElement) {
  if (!responseModeElement) {
    return;
  }

  const remainingMs = getQuotaCooldownRemainingMs();
  if (remainingMs > 0 && responseModeElement.value === "options") {
    responseModeElement.value = "single";
    responseModeElement.dispatchEvent(new Event("change", { bubbles: true }));
  }
}
