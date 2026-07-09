// Account status changes made from the admin panel (suspend / activate /
// approve) live in localStorage as an id → status map. The user records
// themselves come from two read-only sources — the JSON fixture and the
// accounts registered through mockAuth — so this overlay is what makes a
// status change stick across reloads. Swap for PATCH /api/admin/users/:id
// once a real backend exists.

const STATUSES_KEY = "gc_user_statuses";

export function listStatusOverrides() {
  try {
    const raw = localStorage.getItem(STATUSES_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

/** Persists the new status and returns the updated overrides map. */
export function setUserStatus(userId, status) {
  const next = { ...listStatusOverrides(), [userId]: status };
  localStorage.setItem(STATUSES_KEY, JSON.stringify(next));
  return next;
}
