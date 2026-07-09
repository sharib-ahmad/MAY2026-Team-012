// Ward records created through the admin panel live in localStorage,
// merged with the fixture wards from admin_portal_data.json — the same
// pattern mockAuth.js uses for user accounts. Swap for real /zones API
// calls once a backend exists.
import DATA from "../data/admin_portal_data.json";

const ZONES_KEY = "gc_zones";

function readCreated() {
  try {
    const raw = localStorage.getItem(ZONES_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function listZones() {
  return [...DATA.zones, ...readCreated()];
}

export function suggestWardCode() {
  return `WARD-${String(listZones().length + 1).padStart(2, "0")}`;
}

export function createZone({ name, code, officer_id, status }) {
  const zones = listZones();
  const normalizedCode = code.trim().toUpperCase();
  const normalizedName = name.trim();

  if (zones.some((z) => z.code === normalizedCode)) {
    throw new Error(`A ward with code ${normalizedCode} already exists.`);
  }
  if (zones.some((z) => z.name.toLowerCase() === normalizedName.toLowerCase())) {
    throw new Error(`A ward named "${normalizedName}" already exists.`);
  }

  const zone = {
    id: crypto.randomUUID(),
    code: normalizedCode,
    name: normalizedName,
    officer_id: officer_id || null,
    active_workers: 0,
    status: status || "PENDING",
    created_at: new Date().toISOString(),
  };
  localStorage.setItem(ZONES_KEY, JSON.stringify([...readCreated(), zone]));
  return zone;
}
