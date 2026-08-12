// Local, backend-free knowledge base for EcoBot. Keyword-matched replies
// stand in for a real AI backend until one is connected.
export const ECOBOT_TOPICS = [
  {
    keywords: ["plastic"],
    reply:
      "Rinse plastic containers before putting them out, and keep bottle caps on — loose caps are too small for the sorting line to catch.",
  },
  {
    keywords: ["e-waste", "ewaste", "electronic", "battery"],
    reply:
      "E-waste (batteries, chargers, old phones) should never go with regular dry waste — schedule a dedicated E-waste pickup from the Schedule tab.",
  },
  {
    keywords: ["glass"],
    reply:
      "Wrap broken glass in newspaper or a sturdy bag before it goes out, and label it so your collector handles it carefully.",
  },
  {
    keywords: ["paper", "cardboard"],
    reply:
      "Flatten cardboard boxes and keep paper dry — wet paper is usually rejected at the recycling facility.",
  },
  {
    keywords: ["metal", "can", "tin"],
    reply:
      "A quick rinse on metal cans and tins before collection keeps the whole batch cleaner and easier to recycle.",
  },
  {
    keywords: ["pickup", "schedule", "collect"],
    reply:
      "You can schedule a pickup any time from the Schedule Pickup tab — pick a category, date, and time slot that works for you.",
  },
  {
    keywords: ["credit", "reward", "point"],
    reply:
      "Credits build up automatically for every collected pickup — check the Impact tab to see your running balance and badges.",
  },
  {
    keywords: ["donate", "donation", "community shelf"],
    reply:
      "Got something still usable? List it on the Community Shelf tab instead of throwing it out — other citizens nearby can claim it.",
  },
  {
    keywords: ["missed", "late", "not collected"],
    reply:
      "Sorry about that — please raise a ticket from the Tickets tab with the 'Missed Pickup' issue type and we'll flag it to your zone manager.",
  },
  {
    keywords: ["track", "status", "where"],
    reply:
      'Head to My Pickups, open a pickup, and tap "Track Live Pickup" to see how many stops are left before yours.',
  },
  {
    keywords: ["compost", "organic", "wet waste", "kitchen waste"],
    reply:
      "Wet/organic waste is best composted at home if you can — it keeps the smelliest waste out of collection bags entirely.",
  },
  {
    keywords: ["co2", "carbon", "environment", "impact"],
    reply:
      "Every kilogram you divert from landfill saves roughly 1.3kg of CO₂ — your running total is on the Impact tab.",
  },
];

export function ecoBotReply(message) {
  const lower = message.toLowerCase();
  const match = ECOBOT_TOPICS.find((t) => t.keywords.some((k) => lower.includes(k)));
  if (match) return match.reply;
  return "Good question! For now I can help most with segregation tips (plastic, paper, glass, metal, e-waste), scheduling pickups, credits, tracking, or the donation community shelf — try asking about one of those.";
}

/**
 * Safely parse a basic markdown string and output styled HTML.
 * Supports bold (**text**), inline code (`code`), lists (- item or * item), and line breaks.
 */
export function formatMarkdown(text) {
  if (!text) return "";

  // 1. Escape HTML entities to prevent XSS
  let html = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  // 2. Format bold: **text** -> <strong>text</strong>
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // 3. Format inline code: `code` -> <code class="bg-black/[0.08] px-1.5 py-0.5 rounded font-mono text-[11px]">$1</code>
  html = html.replace(
    /`(.*?)`/g,
    '<code class="bg-black/[0.08] px-1.5 py-0.5 rounded font-mono text-[11px]">$1</code>'
  );

  // 4. Format list items: Lines starting with * or -
  const lines = html.split("\n");
  let inList = false;
  const processedLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const match = line.match(/^(\s*)([-*]|\d+\.)\s+(.*)$/);
    if (match) {
      if (!inList) {
        processedLines.push('<ul class="list-disc list-inside pl-2 space-y-1 my-1.5">');
        inList = true;
      }
      processedLines.push(`<li class="text-sm text-gray-700">${match[3]}</li>`);
    } else {
      if (inList) {
        processedLines.push("</ul>");
        inList = false;
      }
      processedLines.push(line);
    }
  }
  if (inList) {
    processedLines.push("</ul>");
  }

  html = processedLines.join("\n");

  // 5. Break paragraphs on double newlines, replace single newlines with <br/>
  const paragraphs = html.split("\n\n");
  const processedParagraphs = paragraphs.map((p) => {
    const trimmed = p.trim();
    if (!trimmed) return "";
    if (trimmed.startsWith("<ul") || trimmed.startsWith("<ol") || trimmed.startsWith("</ul")) {
      return trimmed;
    }
    return `<p class="mb-2 last:mb-0">${trimmed.replace(/\n/g, "<br/>")}</p>`;
  });

  return processedParagraphs.filter(Boolean).join("");
}
