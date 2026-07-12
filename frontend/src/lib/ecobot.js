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
    keywords: ["donate", "donation", "marketplace"],
    reply:
      "Got something still usable? List it on the Marketplace tab instead of throwing it out — other residents nearby can claim it.",
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

export const ECOBOT_SUGGESTIONS = [
  "How do I recycle e-waste?",
  "How do credits work?",
  "What can I donate?",
  "My pickup was missed",
];

export function ecoBotReply(message) {
  const lower = message.toLowerCase();
  const match = ECOBOT_TOPICS.find((t) => t.keywords.some((k) => lower.includes(k)));
  if (match) return match.reply;
  return "Good question! For now I can help most with segregation tips (plastic, paper, glass, metal, e-waste), scheduling pickups, credits, tracking, or the donation marketplace — try asking about one of those.";
}
