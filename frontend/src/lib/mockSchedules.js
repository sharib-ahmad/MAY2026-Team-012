// Backend-free data source for the "Schedule Look-up" page (Story 1.1).
// Ward records themselves come from mockZones.js (created via the admin
// panel). This module only holds the morning/evening collection windows
// published per ward — a separate concern, since a ward can exist before
// its schedule has been configured (see AC4's "not published yet" state).
// Swap for a real GET /wards/:code/schedule call once a backend exists.
import { listZones } from "./mockZones";

// Demo schedules exist for the first two seeded wards only, so that
// searching any other valid ward code genuinely exercises the "no schedule
// published yet" empty state (AC4) rather than always finding data.
const SCHEDULES = {
  "WARD-01": [
    { waste_type: "Wet Waste", morning: "6:30 AM – 8:00 AM", evening: null },
    { waste_type: "Dry Waste", morning: null, evening: "5:00 PM – 6:30 PM" },
    { waste_type: "Recyclable", morning: null, evening: "5:00 PM – 6:30 PM (Tue & Fri only)" },
  ],
  "WARD-02": [
    { waste_type: "Wet Waste", morning: "7:00 AM – 8:30 AM", evening: null },
    { waste_type: "Dry Waste", morning: "7:00 AM – 8:30 AM", evening: null },
    { waste_type: "Recyclable", morning: null, evening: "4:30 PM – 6:00 PM (Wed & Sat only)" },
  ],
};

/**
 * Looks up the published schedule for a ward code.
 * Returns one of three shapes so the UI can tell the three states apart:
 *  - { found: false }                       → AC2, ward code doesn't exist
 *  - { found: true, published: false, ... }  → AC4, ward exists, no schedule yet
 *  - { found: true, published: true, windows, ward } → AC1, happy path
 */
export function getWardSchedule(rawCode) {
  const code = String(rawCode || "")
    .trim()
    .toUpperCase();
  if (!code) return { found: false };

  const ward = listZones().find((z) => z.code?.toUpperCase() === code);
  if (!ward) return { found: false };

  const windows = SCHEDULES[ward.code?.toUpperCase()];
  if (!windows) return { found: true, published: false, ward };

  return { found: true, published: true, ward, windows };
}

export function listWardCodes() {
  return listZones().map((z) => ({ code: z.code, name: z.name }));
}
