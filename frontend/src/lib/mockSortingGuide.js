// Backend-free data layer for the Sorting Guide's content (Story 3.1-AC2).
// Item text per stream (Wet/Dry/Recyclable) is editable by a System Admin
// and persisted in localStorage, so it's no longer hardcoded with no
// update mechanism. Icon/color are still fixed per stream key — only the
// item bullet lists are admin-editable. Swap for a real
// GET/PUT /content/sorting-guide pair once a backend exists.

const CONTENT_KEY = "gc_sorting_guide_content";

const DEFAULT_STREAMS = {
  wet: [
    "Fruit & vegetable peels",
    "Cooked/uncooked food scraps",
    "Tea leaves & coffee grounds",
    "Eggshells",
    "Garden trimmings, flowers, leaves",
  ],
  dry: [
    "Paper, cardboard & cartons",
    "Plastic wrappers & packaging",
    "Cloth, rags & footwear",
    "Broken ceramics & glass",
    "Rubber & thermocol",
  ],
  recyclable: [
    "Clean plastic bottles & containers (PET/HDPE)",
    "Metal cans & foil",
    "Glass bottles & jars",
    "Newspaper, office paper, cardboard (dry & clean)",
    "E-waste — batteries, cables, small electronics (bag separately)",
  ],
};

export function getSortingGuideItems() {
  try {
    const raw = localStorage.getItem(CONTENT_KEY);
    return raw ? { ...DEFAULT_STREAMS, ...JSON.parse(raw) } : DEFAULT_STREAMS;
  } catch {
    return DEFAULT_STREAMS;
  }
}

/** PUT /content/sorting-guide — admin-only in the UI layer (CreateAccount's
 *  RBAC already restricts who can reach the admin panel at all). */
export function updateSortingGuideItems(streamKey, items) {
  const current = getSortingGuideItems();
  const next = { ...current, [streamKey]: items };
  localStorage.setItem(CONTENT_KEY, JSON.stringify(next));
  return next;
}
