const BRAND_NAMES = [
  "DeepTechArt",
  "Karimul",
  "AI Studio",
  "Gemini",
  "Ollama",
  "OpenAI",
  "OpenRouter",
  "Anthropic"
];

const JOIN_RULES = [
  [/\b(a|an|the|and|or|with|without|from|to|for|of|in|on|as|by|that|which|who)(?=(professional|digital|creative|technical|global|Swiss|data|marketing|agency|results|business|businesses|brands|services|clients|startups|established|affordable|pricing|reach|quality|SEO|Local|Social|Web|Email|Image|Video|B2B|B2C|Lead|Generation))/gi, "$1 "],
  [/\b(describing)(?=(DeepTechArt|Karimul|AI Studio|Gemini|Ollama))/g, "$1 "],
  [/\b(marketing)(?=(agency|services|strategy|content|campaigns))/gi, "$1 "],
  [/\b(digital)(?=(marketing|agency|services|strategy))/gi, "$1 "],
  [/\b(creative)(?=(agency|services|partner|content))/gi, "$1 "],
  [/\b(technical)(?=(partner|services|SEO|support))/gi, "$1 "],
  [/\b(global)(?=(brands|reach|clients|markets))/gi, "$1 "],
  [/\b(Swiss)(?=(businesses|quality|brands|market))/g, "$1 "],
  [/\b(data-driven)(?=(digital|marketing|services|strategy))/gi, "$1 "],
  [/\b(measurable)(?=(results|growth|outcomes))/gi, "$1 "],
  [/\b(affordable)(?=(pricing|solutions|services))/gi, "$1 "],
  [/\b(clients)(?=(from|across|worldwide))/gi, "$1 "],
  [/\b(startups)(?=(to|and|worldwide))/gi, "$1 "],
  [/\b(focusing)(?=(on|primarily))/gi, "$1 "],
  [/\b(increasing)(?=(visibility|traffic|leads|sales))/gi, "$1 "],
  [/\b(deliver)(?=(Swiss|measurable|professional))/gi, "$1 "],
  [/\b(include)(?=(SEO|Social|Web|Email|Image|Video|B2B))/gi, "$1 "],
  [/\b(including)(?=(clients|Swiss|global|e-commerce))/gi, "$1 "],
  [/\b(serving)(?=(both|Swiss|global))/gi, "$1 "]
];

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function normalizeAssistantText(text) {
  let value = String(text || "")
    .replace(/\r\n/g, "\n")
    .replace(/\r/g, "\n")
    .replace(/\u00a0/g, " ")
    .replace(/\t/g, " ");

  for (const [pattern, replacement] of JOIN_RULES) {
    value = value.replace(pattern, replacement);
  }

  for (const brand of BRAND_NAMES) {
    value = value.replace(
      new RegExp(`(?<=[a-z])(?=${escapeRegExp(brand)})`, "g"),
      " "
    );
  }

  value = value
    .replace(/(?<!\s)(\[Source\s+\d+\])/g, " $1")
    .replace(/(\[Source\s+\d+\])(?=\w)/g, "$1 ")
    .replace(/([.!?])(?=[A-Z0-9])/g, "$1 ")
    .replace(/([,;:])(?=[A-Za-z0-9])/g, "$1 ")
    .replace(/[ ]{2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();

  return value;
}
