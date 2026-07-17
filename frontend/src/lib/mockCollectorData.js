// Backend-free data layer for the Collector portal, scoped to exactly what
// User Stories 1.2, 1.4, 1.5 and 3.2 require. Daily-waste stops live in the
// SAME localStorage-backed list the Resident portal (mockResidentData.js)
// reads — marking a stop "collected" here is what makes it show COLLECTED
// on the resident's side (Story 1.4-AC4) and clears their delay banner
// (Story 1.2-AC3). Delay logs and mixed-waste flags are appended to their
// own append-only lists so the Manager's Route Tracking page can show full,
// per-event history (Story 1.5-AC3, Story 3.2-AC1/AC3/AC4) rather than just
// the latest value. Swap these for real API calls (GET /my-route,
// POST /stops/:id/collect, POST /stops/:id/undo-collect,
// POST /stops/:id/delay, POST /stops/:id/mixed-waste-flag) once a backend
// exists — Routes.jsx should not need to change.

const PICKUPS_KEY = "gc_resident_pickups";
const USERS_KEY = "gc_users";
const DELAY_LOGS_KEY = "gc_delay_logs";
const MIXED_WASTE_FLAGS_KEY = "gc_mixed_waste_flags";
const ROUTE_SEED_FLAG_PREFIX = "gc_collector_route_seeded_";

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
function refCode(prefix, n) {
  return `${prefix}-${String(n).padStart(4, "0")}`;
}
function notFound() {
  return { response: { data: { detail: "Pickup not found or no longer assigned to you." } } };
}
// Story 1.4-AC6: reject any update attempted by a collector who isn't the
// one this stop is assigned to.
function unauthorized() {
  return {
    response: { data: { detail: "You are not the assigned collector for this pickup." } },
  };
}

// Guwahati, Assam — used to scatter demo stops around a plausible center
// point so the "Navigate" links produce a real-looking route.
const BASE_LAT = 26.1445;
const BASE_LON = 91.7362;
function jitter(base, spread = 0.02) {
  return base + (Math.random() - 0.5) * spread;
}

function residentNameFor(userId) {
  const user = readList(USERS_KEY).find((u) => u.id === userId);
  return user?.name || "Resident";
}

// Turns "zone-1" / "1" style zone ids into the "WARD-01" codes the
// Manager portal's fixture data already uses, so live entries line up
// with DATA.wards instead of introducing a second ward-naming scheme.
function wardCodeFor(collectorUser) {
  const digits = String(collectorUser?.zone_id || "").match(/\d+/);
  return `WARD-${String(digits ? digits[0] : 3).padStart(2, "0")}`;
}

function isSameDay(isoA, isoB) {
  const a = new Date(isoA);
  const b = new Date(isoB);
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

const DEMO_STOPS = [
  "Deka Residence",
  "Sharma Household",
  "Green Villa",
  "Baruah Family",
  "Sonowal House",
  "Lake View Apartments",
  "Gogoi Residence",
  "Riverside Cottage",
];

const DEMO_CATEGORIES = [
  { category: "Daily Waste", weight: 5 },
  { category: "Wet Waste", weight: 7 },
  { category: "Recyclable", weight: 4 },
  { category: "Daily Waste", weight: 5 },
  { category: "Wet Waste", weight: 8 },
  { category: "Recyclable", weight: 3 },
  { category: "Daily Waste", weight: 5 },
  { category: "Recyclable", weight: 6 },
];

/**
 * Populates a starter daily route the first time a given collector opens
 * their dashboard, so the page isn't empty before any resident has logged
 * in on this browser. Safe to call on every load — a no-op once seeded.
 */
function ensureCollectorSeed(collectorUser) {
  const flag = `${ROUTE_SEED_FLAG_PREFIX}${collectorUser.id}`;
  if (localStorage.getItem(flag)) return;

  const pickups = readList(PICKUPS_KEY);
  const zoneName = collectorUser.zone_id ? `Zone ${collectorUser.zone_id}` : "Zone 3";
  const now = new Date().toISOString();
  let n = pickups.length;

  const dailyStops = DEMO_STOPS.map((name, i) => {
    n += 1;
    const categoryInfo = DEMO_CATEGORIES[i % DEMO_CATEGORIES.length];
    return {
      id: uid(),
      user_id: `demo-resident-${collectorUser.id}-${i}`,
      ref_code: refCode("PK", n),
      category: categoryInfo.category,
      estimated_weight: categoryInfo.weight,
      scheduled_date: now,
      time_slot: "Morning (8-11)",
      notes: null,
      status: "PENDING",
      zone_name: zoneName,
      pickup_address: `House #${i + 1}, ${zoneName}`,
      resident_name: name,
      collector_id: collectorUser.id,
      collector_name: collectorUser.name,
      collector_phone: collectorUser.phone || null,
      created_at: now,
      pickup_order: i + 1,
      is_daily_schedule: true,
      latitude: jitter(BASE_LAT),
      longitude: jitter(BASE_LON),
    };
  });

  writeList(PICKUPS_KEY, [...pickups, ...dailyStops]);
  localStorage.setItem(flag, "1");
}

/** GET /my-route — today's ordered daily-waste stops for this collector.
 *  Story 1.4-AC1: only this collector's own stops are ever returned. */
export function getMyRoute(collectorUser) {
  if (!collectorUser) throw notFound();
  ensureCollectorSeed(collectorUser);

  const pickups = readList(PICKUPS_KEY);

  // Auto-claim any unassigned daily stop (e.g. one seeded by a resident
  // logging in on this browser before any collector had) for whoever's
  // dashboard loads first.
  let changed = false;
  const claimed = pickups.map((p) => {
    if (p.is_daily_schedule && !p.collector_id) {
      changed = true;
      return {
        ...p,
        collector_id: collectorUser.id,
        collector_name: collectorUser.name,
        collector_phone: collectorUser.phone || p.collector_phone || null,
      };
    }
    return p;
  });
  if (changed) writeList(PICKUPS_KEY, claimed);

  const mine = claimed
    .filter((p) => p.is_daily_schedule && p.collector_id === collectorUser.id)
    .sort((a, b) => (a.pickup_order || 0) - (b.pickup_order || 0));

  const zoneName =
    mine[0]?.zone_name || (collectorUser.zone_id ? `Zone ${collectorUser.zone_id}` : "Zone 3");

  return {
    zone_name: zoneName,
    total_stops: mine.length,
    stops: mine.map((p) => ({
      id: p.id,
      pickup_order: p.pickup_order,
      status: p.status,
      category: p.category,
      estimated_weight: p.estimated_weight,
      resident_name: p.resident_name || residentNameFor(p.user_id),
      address: p.pickup_address,
      latitude: p.latitude,
      longitude: p.longitude,
      collected_at: p.collected_at || null,
    })),
  };
}

function getOwnedPickup(collectorUser, id) {
  const pickups = readList(PICKUPS_KEY);
  const idx = pickups.findIndex((p) => p.id === id);
  if (idx === -1) throw notFound();
  if (pickups[idx].collector_id !== collectorUser.id) throw unauthorized();
  return { pickups, idx };
}

/** POST /stops/:id/collect
 *  Story 1.4-AC2: records who collected it and when.
 *  Story 1.4-AC6: rejected if the caller isn't the assigned collector. */
export function collectStop(collectorUser, id) {
  const { pickups, idx } = getOwnedPickup(collectorUser, id);
  pickups[idx] = {
    ...pickups[idx],
    status: "COLLECTED",
    collected_at: new Date().toISOString(),
    collected_by: { id: collectorUser.id, name: collectorUser.name },
  };
  writeList(PICKUPS_KEY, pickups);
  return pickups[idx];
}

/** POST /stops/:id/undo-collect
 *  Story 1.4-AC3: lets a worker correct a mis-tap, but only within the
 *  same working day it was marked collected on. */
export function undoCollectStop(collectorUser, id) {
  const { pickups, idx } = getOwnedPickup(collectorUser, id);
  const pickup = pickups[idx];
  if (pickup.status !== "COLLECTED" || !pickup.collected_at) {
    throw { response: { data: { detail: "This stop has not been marked collected." } } };
  }
  if (!isSameDay(pickup.collected_at, new Date().toISOString())) {
    throw {
      response: {
        data: { detail: "This stop was collected on a previous day and can no longer be undone." },
      },
    };
  }
  pickups[idx] = { ...pickup, status: "PENDING", collected_at: null, collected_by: null };
  writeList(PICKUPS_KEY, pickups);
  return pickups[idx];
}

const DELAY_MIN_LEN = 5;
const DELAY_MAX_LEN = 200;

/** POST /stops/:id/delay
 *  Story 1.5-AC2: comment must be 5–200 characters.
 *  Story 1.5-AC3: logged with worker, timestamp, route point and reason —
 *  appended to an event history the Manager portal reads (see
 *  listDelayLogs), not just overwritten as a single "latest" value.
 *  Story 1.2-AC1: also stamped onto the pickup itself so the resident
 *  portal can show a live delay banner; Story 1.2-AC3: clearing/replacing
 *  this on the next status change is what lets that banner update instead
 *  of staying stuck. In-app only for MVP — SMS/push delivery is explicitly
 *  out of scope (Story 1.2-AC4). */
export function delayStop(collectorUser, id, { delay_type, comment, estimated_delay_minutes }) {
  const trimmed = String(comment || "").trim();
  if (trimmed.length < DELAY_MIN_LEN || trimmed.length > DELAY_MAX_LEN) {
    throw {
      response: {
        data: {
          detail: `Message must be between ${DELAY_MIN_LEN} and ${DELAY_MAX_LEN} characters.`,
        },
      },
    };
  }
  const { pickups, idx } = getOwnedPickup(collectorUser, id);
  const pickup = pickups[idx];
  const now = new Date().toISOString();

  pickups[idx] = {
    ...pickup,
    last_delay: {
      delay_type,
      comment: trimmed,
      estimated_delay_minutes: estimated_delay_minutes ?? null,
      notified_at: now,
    },
  };
  writeList(PICKUPS_KEY, pickups);

  const logs = readList(DELAY_LOGS_KEY);
  writeList(DELAY_LOGS_KEY, [
    {
      id: uid(),
      route_code: pickup.ref_code,
      ward_code: wardCodeFor(collectorUser),
      worker_id: collectorUser.id,
      worker_name: collectorUser.name,
      reason: delay_type,
      note: trimmed,
      logged_at: now,
    },
    ...logs,
  ]);

  return pickups[idx];
}

/** Read-only — Manager's Route Tracking "Delay logs" panel merges this
 *  with its fixture data (Story 1.5-AC3). */
export function listDelayLogs() {
  return readList(DELAY_LOGS_KEY);
}

const MIXED_WASTE_SEVERITIES = new Set(["ROUTINE", "HAZARDOUS"]);

/** POST /stops/:id/mixed-waste-flag
 *  Story 3.2-AC1: route point, date and worker ID are recorded.
 *  Story 3.2-AC2: severity must be exactly ROUTINE or HAZARDOUS.
 *  Story 3.2-AC3: HAZARDOUS flags are what listMixedWasteFlags sorts to
 *  the front for the Manager's dashboard. */
export function flagMixedWaste(collectorUser, id, { issue_type, description, severity }) {
  if (!MIXED_WASTE_SEVERITIES.has(severity)) {
    throw {
      response: { data: { detail: 'Severity must be "ROUTINE" or "HAZARDOUS".' } },
    };
  }
  const { pickups, idx } = getOwnedPickup(collectorUser, id);
  const pickup = pickups[idx];
  const now = new Date().toISOString();

  const flags = readList(MIXED_WASTE_FLAGS_KEY);
  const flag = {
    id: uid(),
    route_code: pickup.ref_code,
    ward_code: wardCodeFor(collectorUser),
    point_label: `${pickup.resident_name} — ${pickup.pickup_address}`,
    issue_type,
    severity,
    note: description,
    worker_id: collectorUser.id,
    worker_name: collectorUser.name,
    flagged_at: now,
  };

  pickups[idx] = {
    ...pickup,
    status: "FLAGGED",
    last_flagged_at: now,
  };
  writeList(PICKUPS_KEY, pickups);
  writeList(MIXED_WASTE_FLAGS_KEY, [flag, ...flags]);
  return flag;
}

/** POST /stops/:id/mark-clean
 *  Story 3.2-AC4: an explicit "checked, no issue found" record, so its
 *  presence in listMixedWasteFlags is distinguishable from a point that
 *  simply has no entry at all (never reviewed). */
export function markStopClean(collectorUser, id) {
  const { pickups, idx } = getOwnedPickup(collectorUser, id);
  const pickup = pickups[idx];
  const now = new Date().toISOString();

  const flags = readList(MIXED_WASTE_FLAGS_KEY);
  const flag = {
    id: uid(),
    route_code: pickup.ref_code,
    ward_code: wardCodeFor(collectorUser),
    point_label: `${pickup.resident_name} — ${pickup.pickup_address}`,
    issue_type: null,
    severity: "CLEAN",
    note: null,
    worker_id: collectorUser.id,
    worker_name: collectorUser.name,
    flagged_at: now,
  };
  writeList(MIXED_WASTE_FLAGS_KEY, [flag, ...flags]);
  return flag;
}

/** Read-only — Manager's Route Tracking "Mixed-waste flags" panel merges
 *  this with its fixture data, HAZARDOUS entries sorted first (Story
 *  3.2-AC3), so a worker's explicit "no issue" check (Story 3.2-AC4) and
 *  an untouched point (nothing in this list) stay distinguishable. */
export function listMixedWasteFlags() {
  return readList(MIXED_WASTE_FLAGS_KEY);
}
