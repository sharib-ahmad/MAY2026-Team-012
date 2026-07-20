// Backend-free data layer for the Recycler B2G Material Inventory Ledger
// (Epic 4). This is a SHARED marketplace — all recyclers read/write the
// same localStorage-backed pool, not a per-recycler queue — because
// Story 4.1-AC2 requires a real claim race between recyclers to be
// representable. Quality status (Story 4.2) is treated as assigned
// upstream by a worker/officer at drop-off time; recyclers only read it
// here, they don't set it, since that assignment UI belongs to the
// Collection Worker / Municipal Officer modules, not the Recycler one.
//
// Swap for real API calls (GET /batches, GET /analytics/recycler,
// POST /batches/:id/claim, POST /batches/:id/collect) once a backend
// exists — the page components should not need to change beyond
// swapping their imports back to lib/api.

const BATCHES_KEY = "gc_recycler_batches_v2";
const SEED_FLAG = "gc_recycler_batches_seeded_v2";

// Story 4.3-AC2: a claim that isn't marked "Collected" within this window
// auto-releases back to "Available". Spec calls for 48–72h; 60h sits
// mid-range.
const CLAIM_WINDOW_HOURS = 60;

function readList(key) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}
function writeList(key, list) {
  localStorage.setItem(key, JSON.stringify(list));
}
function uid() {
  return crypto.randomUUID();
}
function refCode(n) {
  return `MRF-${String(n).padStart(4, "0")}`;
}
function notFound() {
  return { response: { data: { detail: "Batch not found." } } };
}
function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}
function hoursAgo(h) {
  const d = new Date();
  d.setHours(d.getHours() - h);
  return d.toISOString();
}
function monthsAgo(m, dayOffset = 0) {
  const d = new Date();
  d.setMonth(d.getMonth() - m);
  d.setDate(Math.max(1, d.getDate() - dayOffset));
  return d.toISOString();
}
function randomBetween(min, max) {
  return Math.round((min + Math.random() * (max - min)) * 10) / 10;
}

// ── Demo fixtures ────────────────────────────────────────────────────
const MATERIALS = [
  { material_type: "Plastic (PET/HDPE)", min: 15, max: 60 },
  { material_type: "Paper & Cardboard", min: 20, max: 90 },
  { material_type: "E-waste", min: 5, max: 25 },
  { material_type: "Metal Scrap", min: 10, max: 40 },
  { material_type: "Glass", min: 10, max: 35 },
];

const WARDS = ["WARD-01", "WARD-02", "WARD-03", "WARD-04", "WARD-05"];

// Story 4.2: quality assigned by a worker or officer at/near the source,
// never by the recycler themselves.
const QUALITY_ASSIGNERS = [
  { role: "WORKER", name: "Rahul Deka" },
  { role: "WORKER", name: "Priya Sharma" },
  { role: "OFFICER", name: "Anjali Verma" },
];

const QUALITY_WEIGHTS = [
  { status: "CLEAN", weight: 45 },
  { status: "MOISTURE_AFFECTED", weight: 25 },
  { status: "MIXED", weight: 20 },
  { status: "UNSAFE", weight: 10 },
];

const CONTAMINATION_NOTES = {
  MOISTURE_AFFECTED: [
    "Rain exposure overnight — cardboard partially damp.",
    "Stored near a leaking tap; partial moisture damage.",
  ],
  MIXED: ["Plastic mixed with some wet kitchen waste.", "Unsorted mix of paper and food wrappers."],
  // Story 4.2-AC3: an "Unsafe" tag can never be saved without a note —
  // enforced here by construction since seed data never creates one
  // without picking from this list.
  UNSAFE: [
    "Broken glass shards found in the bag — handle with gloves.",
    "Used syringes spotted at drop point — do not sort by hand.",
    "Sharp metal edges present, laceration risk.",
  ],
};

// Other recyclers active in the same marketplace, so a freshly registered
// demo account sees batches genuinely claimed/collected by someone else
// (Story 4.1-AC2's race condition, and non-empty history for context).
const OTHER_RECYCLERS = [
  { recycler_id: "demo-recycler-b", recycler_name: "Ganesh Scrap Traders" },
  { recycler_id: "demo-recycler-c", recycler_name: "Uttarayan Recyclers" },
];

function pickQuality(n) {
  const roll = (n * 37) % 100;
  let acc = 0;
  for (const q of QUALITY_WEIGHTS) {
    acc += q.weight;
    if (roll < acc) return q.status;
  }
  return "CLEAN";
}
function noteFor(status, n) {
  if (status === "CLEAN") return null;
  const options = CONTAMINATION_NOTES[status];
  return options[n % options.length];
}

function makeBatch(n, mat, approxWeight, qStatus, status, overrides = {}) {
  return {
    id: uid(),
    ref_code: refCode(n),
    material_type: mat.material_type,
    approx_weight_kg: approxWeight,
    actual_weight_kg: null,
    source_ward: WARDS[n % WARDS.length],
    drop_date: daysAgo(0),
    quality_status: qStatus,
    quality_assigned_by: QUALITY_ASSIGNERS[n % QUALITY_ASSIGNERS.length],
    contamination_note: noteFor(qStatus, n),
    status, // AVAILABLE | CLAIMED | COLLECTED
    claimed_by: null,
    claimed_at: null,
    claim_expires_at: null,
    collected_by: null,
    collected_at: null,
    ...overrides,
  };
}

/**
 * Seeds the shared marketplace once per browser: resolved history so
 * Reports/trend charts aren't empty, a few batches claimed by OTHER
 * demo recyclers (some already past their claim window, so the very
 * first list() call visibly auto-releases them — Story 4.3-AC2), and a
 * dozen fresh AVAILABLE batches spanning every ward/material/quality
 * combination for the marketplace view. Safe to call repeatedly.
 */
function ensureGlobalSeed() {
  if (localStorage.getItem(SEED_FLAG)) return;
  const seeded = [];
  let n = 0;

  // Resolved history (6 months) — not tied to "me", since seeding runs
  // before any particular recycler is known to be logged in.
  for (let m = 5; m >= 1; m--) {
    const count = 2 + (m % 3);
    for (let i = 0; i < count; i++) {
      n += 1;
      const mat = MATERIALS[n % MATERIALS.length];
      const approx = randomBetween(mat.min, mat.max);
      const qStatus = pickQuality(n);
      const collector = OTHER_RECYCLERS[n % OTHER_RECYCLERS.length];
      seeded.push(
        makeBatch(n, mat, approx, qStatus, "COLLECTED", {
          drop_date: monthsAgo(m, 5),
          claimed_by: collector,
          claimed_at: monthsAgo(m, 4),
          collected_by: collector,
          collected_at: monthsAgo(m, 1),
          actual_weight_kg: Math.max(0, Number((approx - randomBetween(0.5, 3)).toFixed(1))),
        })
      );
    }
  }

  // Currently claimed by OTHER recyclers — half already past the claim
  // window (demonstrates auto-release), half still active (demonstrates
  // a live claim race when the current user tries to claim the same one).
  for (let i = 0; i < 4; i++) {
    n += 1;
    const mat = MATERIALS[n % MATERIALS.length];
    const approx = randomBetween(mat.min, mat.max);
    const qStatus = pickQuality(n);
    const claimer = OTHER_RECYCLERS[n % OTHER_RECYCLERS.length];
    const expired = i % 2 === 0;
    const claimedAt = expired ? hoursAgo(80) : hoursAgo(10);
    const expiresAt = new Date(
      new Date(claimedAt).getTime() + CLAIM_WINDOW_HOURS * 60 * 60 * 1000
    ).toISOString();
    seeded.push(
      makeBatch(n, mat, approx, qStatus, "CLAIMED", {
        drop_date: hoursAgo(expired ? 96 : 20),
        claimed_by: claimer,
        claimed_at: claimedAt,
        claim_expires_at: expiresAt,
      })
    );
  }

  // Fresh AVAILABLE batches for the marketplace.
  for (let i = 0; i < 12; i++) {
    n += 1;
    const mat = MATERIALS[n % MATERIALS.length];
    const approx = randomBetween(mat.min, mat.max);
    const qStatus = pickQuality(n);
    seeded.push(
      makeBatch(n, mat, approx, qStatus, "AVAILABLE", {
        drop_date: hoursAgo(2 + (n % 48)),
      })
    );
  }

  writeList(BATCHES_KEY, seeded);
  localStorage.setItem(SEED_FLAG, "1");
}

/** Story 4.3-AC2: sweeps expired claims back to AVAILABLE. Called at the
 *  top of every read/write so no caller can see a stale locked batch. */
function releaseExpiredClaims() {
  const all = readList(BATCHES_KEY);
  const now = Date.now();
  let changed = false;
  const updated = all.map((b) => {
    if (
      b.status === "CLAIMED" &&
      b.claim_expires_at &&
      new Date(b.claim_expires_at).getTime() < now
    ) {
      changed = true;
      return {
        ...b,
        status: "AVAILABLE",
        claimed_by: null,
        claimed_at: null,
        claim_expires_at: null,
        auto_released_at: new Date().toISOString(),
      };
    }
    return b;
  });
  if (changed) writeList(BATCHES_KEY, updated);
  return updated;
}

/** GET /batches — the shared marketplace, optionally filtered by
 *  material type, source ward, and pickup-readiness status
 *  (Story 4.1-AC1). Pass `mine: true` with `recyclerUser` to scope to
 *  batches this recycler has claimed or collected. */
export function listBatches({ material_type, source_ward, status, mine, recyclerUser } = {}) {
  ensureGlobalSeed();
  let all = releaseExpiredClaims();

  if (material_type) all = all.filter((b) => b.material_type === material_type);
  if (source_ward) all = all.filter((b) => b.source_ward === source_ward);
  if (status) all = all.filter((b) => b.status === status);
  if (mine) {
    if (!recyclerUser) throw notFound();
    all = all.filter(
      (b) =>
        b.claimed_by?.recycler_id === recyclerUser.id ||
        b.collected_by?.recycler_id === recyclerUser.id
    );
  }

  return all.sort((a, b) => new Date(b.drop_date) - new Date(a.drop_date));
}

/** POST /batches/:id/claim
 *  Story 4.1-AC2: re-checks status against the freshest data right
 *  before writing, so two near-simultaneous claims can't both succeed —
 *  whoever's write lands second sees a rejection naming who won, not a
 *  silent double-claim. */
export function claimBatch(recyclerUser, id) {
  if (!recyclerUser) throw notFound();
  releaseExpiredClaims();
  const all = readList(BATCHES_KEY);
  const idx = all.findIndex((b) => b.id === id);
  if (idx === -1) throw notFound();

  if (all[idx].status !== "AVAILABLE") {
    throw {
      response: {
        data: {
          detail:
            all[idx].status === "CLAIMED"
              ? `Already claimed by ${all[idx].claimed_by?.recycler_name || "another recycler"} moments ago.`
              : "This batch has already been collected.",
          current_status: all[idx].status,
        },
      },
    };
  }

  const now = new Date();
  const expires = new Date(now.getTime() + CLAIM_WINDOW_HOURS * 60 * 60 * 1000);
  all[idx] = {
    ...all[idx],
    status: "CLAIMED",
    claimed_by: { recycler_id: recyclerUser.id, recycler_name: recyclerUser.name },
    claimed_at: now.toISOString(),
    claim_expires_at: expires.toISOString(),
  };
  writeList(BATCHES_KEY, all);
  return all[idx];
}

/** POST /batches/:id/collect
 *  Story 4.3-AC1: records recycler + timestamp on collection.
 *  Story 4.3-AC3: rejected if the caller isn't the one who claimed it. */
export function markCollected(recyclerUser, id, { actual_weight_kg } = {}) {
  if (!recyclerUser) throw notFound();
  releaseExpiredClaims();
  const all = readList(BATCHES_KEY);
  const idx = all.findIndex((b) => b.id === id);
  if (idx === -1) throw notFound();

  if (all[idx].status !== "CLAIMED") {
    throw {
      response: {
        data: {
          detail:
            all[idx].status === "AVAILABLE"
              ? "Your claim on this batch expired and it returned to the marketplace."
              : "This batch is not awaiting pickup confirmation.",
        },
      },
    };
  }
  if (all[idx].claimed_by?.recycler_id !== recyclerUser.id) {
    throw { response: { data: { detail: "You can only update batches you have claimed." } } };
  }

  const hasOverride =
    actual_weight_kg !== undefined && actual_weight_kg !== "" && actual_weight_kg !== null;
  const weight = hasOverride ? Number(actual_weight_kg) : all[idx].approx_weight_kg;
  if (hasOverride && !(weight >= 0)) {
    throw { response: { data: { detail: "Actual weight must be a positive number." } } };
  }

  all[idx] = {
    ...all[idx],
    status: "COLLECTED",
    collected_by: { recycler_id: recyclerUser.id, recycler_name: recyclerUser.name },
    collected_at: new Date().toISOString(),
    actual_weight_kg: weight,
  };
  writeList(BATCHES_KEY, all);
  return all[idx];
}

/** GET /analytics/recycler — marketplace snapshot + this recycler's own
 *  claim/collection activity for the dashboard. */
export function getRecyclerSummary(recyclerUser) {
  if (!recyclerUser) throw notFound();
  const all = listBatches({});

  const marketplaceAvailable = all.filter((b) => b.status === "AVAILABLE").length;
  const marketplaceUnsafe = all.filter(
    (b) => b.status === "AVAILABLE" && b.quality_status === "UNSAFE"
  ).length;
  const myClaimed = all.filter(
    (b) => b.status === "CLAIMED" && b.claimed_by?.recycler_id === recyclerUser.id
  );
  const myCollected = all.filter(
    (b) => b.status === "COLLECTED" && b.collected_by?.recycler_id === recyclerUser.id
  );
  const myTotalKg = myCollected.reduce(
    (s, b) => s + (b.actual_weight_kg ?? b.approx_weight_kg ?? 0),
    0
  );

  const byMaterial = {};
  myCollected.forEach((b) => {
    const key = b.material_type;
    byMaterial[key] = (byMaterial[key] || 0) + (b.actual_weight_kg ?? b.approx_weight_kg ?? 0);
  });
  const by_category = Object.entries(byMaterial).map(([category, weight_kg]) => ({
    category,
    weight_kg: Number(weight_kg.toFixed(1)),
  }));

  const monthly_trend = [];
  for (let m = 5; m >= 0; m--) {
    const d = new Date();
    d.setMonth(d.getMonth() - m);
    const inMonth = myCollected.filter((b) => {
      const bd = new Date(b.collected_at);
      return bd.getMonth() === d.getMonth() && bd.getFullYear() === d.getFullYear();
    });
    monthly_trend.push({
      month: d.toLocaleString("default", { month: "short" }),
      collected: inMonth.length,
    });
  }

  return {
    marketplace_available: marketplaceAvailable,
    marketplace_unsafe: marketplaceUnsafe,
    my_claimed: myClaimed.length,
    my_collected: myCollected.length,
    my_total_kg: Number(myTotalKg.toFixed(1)),
    by_category,
    monthly_trend,
  };
}

export const MATERIAL_OPTIONS = MATERIALS.map((m) => m.material_type);
export const WARD_OPTIONS = WARDS;
