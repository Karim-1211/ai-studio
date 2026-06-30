const VOICE_SETTINGS_KEY = "aiStudioVoiceSettingsV1";

const SpeechRecognitionClass =
  window.SpeechRecognition || window.webkitSpeechRecognition || null;

const speechSynthesisApi = window.speechSynthesis || null;

let recognition = null;
let isListening = false;
let recognitionBaseText = "";
let recognitionFinalText = "";
let activeUtterance = null;
let activeReadButton = null;
let clearStatusTimer = null;

const voiceState = loadVoiceSettings();


function loadVoiceSettings() {
  try {
    const saved = JSON.parse(
      localStorage.getItem(VOICE_SETTINGS_KEY) || "{}"
    );

    return {
      autoRead: saved.autoRead === true,
      language:
        typeof saved.language === "string" && saved.language.trim()
          ? saved.language.trim()
          : navigator.language || "en-US",
      rate:
        Number.isFinite(Number(saved.rate))
          ? Math.min(1.5, Math.max(0.75, Number(saved.rate)))
          : 1
    };
  } catch (_error) {
    return {
      autoRead: false,
      language: navigator.language || "en-US",
      rate: 1
    };
  }
}


function saveVoiceSettings() {
  localStorage.setItem(
    VOICE_SETTINGS_KEY,
    JSON.stringify(voiceState)
  );
}


function getVoiceElements() {
  return {
    promptInput: document.getElementById("prompt"),
    voiceInputButton: document.getElementById("voiceInputButton"),
    voiceOutputButton: document.getElementById("voiceOutputButton"),
    voiceStatus: document.getElementById("voiceStatus")
  };
}


function setVoiceStatus(message = "", tone = "") {
  const { voiceStatus } = getVoiceElements();

  if (!voiceStatus) {
    return;
  }

  if (clearStatusTimer) {
    window.clearTimeout(clearStatusTimer);
    clearStatusTimer = null;
  }

  voiceStatus.innerText = message;
  voiceStatus.classList.remove(
    "is-working",
    "is-success",
    "is-error"
  );

  if (tone) {
    voiceStatus.classList.add(`is-${tone}`);
  }

  if (message && tone !== "working") {
    clearStatusTimer = window.setTimeout(() => {
      voiceStatus.innerText = "";
      voiceStatus.classList.remove(
        "is-success",
        "is-error"
      );
    }, 4200);
  }
}


function updateVoiceButtons() {
  const {
    voiceInputButton,
    voiceOutputButton
  } = getVoiceElements();

  if (voiceInputButton) {
    voiceInputButton.classList.toggle(
      "is-listening",
      isListening
    );

    voiceInputButton.setAttribute(
      "aria-pressed",
      String(isListening)
    );

    voiceInputButton.title = isListening
      ? "Stop voice input"
      : "Start voice input";

    voiceInputButton.setAttribute(
      "aria-label",
      voiceInputButton.title
    );
  }

  if (voiceOutputButton) {
    voiceOutputButton.classList.toggle(
      "is-enabled",
      voiceState.autoRead
    );

    voiceOutputButton.setAttribute(
      "aria-pressed",
      String(voiceState.autoRead)
    );

    const title = voiceState.autoRead
      ? "Automatic read aloud is on"
      : "Automatic read aloud is off";

    voiceOutputButton.title = title;
    voiceOutputButton.setAttribute("aria-label", title);
  }
}


function joinTranscript(baseText, spokenText) {
  const parts = [baseText.trim(), spokenText.trim()].filter(Boolean);
  return parts.join(parts.length > 1 ? " " : "");
}


function buildRecognition() {
  if (!SpeechRecognitionClass) {
    return null;
  }

  const instance = new SpeechRecognitionClass();

  instance.continuous = true;
  instance.interimResults = true;
  instance.maxAlternatives = 1;
  instance.lang = voiceState.language;

  instance.addEventListener("start", () => {
    isListening = true;
    updateVoiceButtons();
    setVoiceStatus("Listening… speak naturally", "working");
  });

  instance.addEventListener("result", event => {
    const { promptInput } = getVoiceElements();

    if (!promptInput) {
      return;
    }

    let interimText = "";

    for (
      let index = event.resultIndex;
      index < event.results.length;
      index += 1
    ) {
      const transcript = event.results[index][0]?.transcript || "";

      if (event.results[index].isFinal) {
        recognitionFinalText = joinTranscript(
          recognitionFinalText,
          transcript
        );
      } else {
        interimText = joinTranscript(interimText, transcript);
      }
    }

    promptInput.value = joinTranscript(
      recognitionBaseText,
      joinTranscript(recognitionFinalText, interimText)
    );

    promptInput.dispatchEvent(
      new Event("input", { bubbles: true })
    );
  });

  instance.addEventListener("error", event => {
    const messages = {
      "not-allowed": "Microphone access was blocked by the browser.",
      "service-not-allowed": "Voice recognition is not available for this browser profile.",
      "audio-capture": "No working microphone was found.",
      "network": "Voice recognition could not reach the browser speech service.",
      "no-speech": "No speech was detected. Try again and speak closer to the microphone.",
      "aborted": "Voice input stopped."
    };

    const message = messages[event.error] || "Voice input could not continue.";
    const tone = event.error === "aborted" ? "success" : "error";

    setVoiceStatus(message, tone);
  });

  instance.addEventListener("end", () => {
    isListening = false;
    updateVoiceButtons();

    if (recognitionFinalText.trim()) {
      setVoiceStatus("Voice message added to the prompt.", "success");
    } else {
      setVoiceStatus("");
    }
  });

  return instance;
}


export function startVoiceInput() {
  const { promptInput } = getVoiceElements();

  if (!SpeechRecognitionClass) {
    setVoiceStatus(
      "Voice input is not supported in this browser. Use current Chrome or Edge.",
      "error"
    );
    return;
  }

  if (!promptInput || promptInput.disabled) {
    return;
  }

  if (!recognition) {
    recognition = buildRecognition();
  }

  recognitionBaseText = promptInput.value;
  recognitionFinalText = "";
  recognition.lang = voiceState.language;

  try {
    recognition.start();
  } catch (error) {
    if (error.name !== "InvalidStateError") {
      setVoiceStatus(
        error.message || "Voice input could not start.",
        "error"
      );
    }
  }
}


export function stopVoiceInput() {
  if (!recognition || !isListening) {
    return;
  }

  try {
    recognition.stop();
  } catch (_error) {
    isListening = false;
    updateVoiceButtons();
  }
}


function toggleVoiceInput() {
  if (isListening) {
    stopVoiceInput();
  } else {
    startVoiceInput();
  }
}


function cleanSpeechText(text) {
  return String(text || "")
    .replace(/<!--AI_STUDIO_META:[A-Za-z0-9+/=]+-->/g, "")
    .replace(/```[\s\S]*?```/g, " Code block omitted from read aloud. ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*>\s?/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+[.)]\s+/gm, "")
    .replace(/[*_~]+/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .slice(0, 15000);
}


function restoreActiveReadButton() {
  if (!activeReadButton) {
    return;
  }

  activeReadButton.innerText = "Read aloud";
  activeReadButton.classList.remove("is-speaking");
  activeReadButton = null;
}


export function stopSpeaking() {
  if (speechSynthesisApi) {
    speechSynthesisApi.cancel();
  }

  activeUtterance = null;
  restoreActiveReadButton();
  setVoiceStatus("Speech stopped.", "success");
}


export function speakText(text, options = {}) {
  const cleanedText = cleanSpeechText(text);

  if (!speechSynthesisApi || typeof SpeechSynthesisUtterance === "undefined") {
    setVoiceStatus(
      "Read aloud is not supported in this browser.",
      "error"
    );
    return false;
  }

  if (!cleanedText) {
    return false;
  }

  speechSynthesisApi.cancel();
  restoreActiveReadButton();

  const utterance = new SpeechSynthesisUtterance(cleanedText);
  utterance.lang = voiceState.language;
  utterance.rate = voiceState.rate;
  utterance.pitch = 1;

  const browserVoices = speechSynthesisApi.getVoices();
  const matchingVoice = browserVoices.find(voice =>
    voice.lang?.toLowerCase() === voiceState.language.toLowerCase()
  ) || browserVoices.find(voice =>
    voice.lang?.toLowerCase().startsWith(
      voiceState.language.split("-")[0].toLowerCase()
    )
  );

  if (matchingVoice) {
    utterance.voice = matchingVoice;
  }

  activeUtterance = utterance;
  activeReadButton = options.button || null;

  if (activeReadButton) {
    activeReadButton.innerText = "Stop";
    activeReadButton.classList.add("is-speaking");
  }

  utterance.addEventListener("start", () => {
    setVoiceStatus("Reading the assistant response aloud…", "working");
  });

  utterance.addEventListener("end", () => {
    activeUtterance = null;
    restoreActiveReadButton();
    setVoiceStatus("Read aloud finished.", "success");
  });

  utterance.addEventListener("error", event => {
    activeUtterance = null;
    restoreActiveReadButton();

    if (event.error !== "canceled" && event.error !== "interrupted") {
      setVoiceStatus("The browser could not read this response aloud.", "error");
    }
  });

  speechSynthesisApi.speak(utterance);
  return true;
}


export function speakAssistantResponse(text) {
  if (!voiceState.autoRead) {
    return;
  }

  speakText(text);
}


export function attachReadAloudButton(container, text) {
  if (!container || container.querySelector(":scope > .voice-read-button")) {
    return;
  }

  const button = document.createElement("button");
  button.type = "button";
  button.className = "voice-read-button";
  button.innerText = "Read aloud";
  button.title = "Read this response aloud";

  button.addEventListener("click", () => {
    if (activeReadButton === button && speechSynthesisApi?.speaking) {
      stopSpeaking();
      return;
    }

    speakText(text, { button });
  });

  container.appendChild(button);
}


export function createOptionReadButton(text) {
  const button = document.createElement("button");
  button.type = "button";
  button.innerText = "Read";

  button.addEventListener("click", () => {
    if (activeReadButton === button && speechSynthesisApi?.speaking) {
      stopSpeaking();
      return;
    }

    speakText(text, { button });
  });

  return button;
}


function toggleAutomaticReadAloud() {
  if (speechSynthesisApi?.speaking) {
    stopSpeaking();
    return;
  }

  voiceState.autoRead = !voiceState.autoRead;
  saveVoiceSettings();
  updateVoiceButtons();

  setVoiceStatus(
    voiceState.autoRead
      ? "Automatic read aloud enabled."
      : "Automatic read aloud disabled.",
    "success"
  );
}


export function stopVoiceActivity() {
  stopVoiceInput();

  if (speechSynthesisApi?.speaking) {
    speechSynthesisApi.cancel();
    activeUtterance = null;
    restoreActiveReadButton();
  }
}


export function initializeVoiceChat() {
  const {
    voiceInputButton,
    voiceOutputButton
  } = getVoiceElements();

  if (!voiceInputButton || !voiceOutputButton) {
    return;
  }

  voiceInputButton.addEventListener("click", toggleVoiceInput);
  voiceOutputButton.addEventListener("click", toggleAutomaticReadAloud);

  if (!SpeechRecognitionClass) {
    voiceInputButton.classList.add("is-unavailable");
    voiceInputButton.title =
      "Voice input is unavailable in this browser. Use current Chrome or Edge.";
  }

  if (!speechSynthesisApi) {
    voiceOutputButton.classList.add("is-unavailable");
    voiceOutputButton.title = "Read aloud is unavailable in this browser.";
  }

  updateVoiceButtons();

  window.addEventListener("beforeunload", stopVoiceActivity);

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && isListening) {
      stopVoiceInput();
    }
  });
}
