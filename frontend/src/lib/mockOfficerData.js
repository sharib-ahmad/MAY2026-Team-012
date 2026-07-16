// Officer-side complaint handling without a backend. Complaints come
// from two sources: the read-only municipal_officer_data.json fixture
// and the live tickets residents file from their portal (stored in
// localStorage under gc_resident_tickets). Officer actions — status
// changes and resolution notes — persist to localStorage: fixture
// complaints via an id → patch override map, resident tickets by
// writing back into the shared ticket store so the citizen sees the
// resolution on their side. Swap for /api/officer/* calls once a real
// backend exists.

import DATA from "../data/municipal_officer_data.json";

const RESIDENT_TICKETS_KEY = "gc_resident_tickets";
const USERS_KEY = "gc_users";
const OVERRIDES_KEY = "gc_officer_complaint_overrides";

function readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function listOverrides() {
  return readJson(OVERRIDES_KEY, {});
}

// Resident tickets don't carry ward or citizen info — resolve both from
// the registered account that filed them.
function ticketReporter(userId) {
  const user = readJson(USERS_KEY, []).find((u) => u.id === userId);
  const ward = DATA.wards.find((w) => w.id === user?.zone_id);
  return {
    citizen_name: user?.name || "Registered resident",
    ward_code: ward?.code || "UNASSIGNED",
  };
}

function normalizeTicket(ticket) {
  return {
    id: ticket.id,
    ref_code: ticket.ref_code,
    issue_type: ticket.issue_type,
    description: ticket.description,
    severity: ticket.severity || "MEDIUM",
    status: ticket.status,
    created_at: ticket.created_at,
    resolution_notes: ticket.resolution_notes,
    resolver_name: ticket.resolver_name,
    resolved_at: ticket.resolved_at,
    status_history: ticket.status_history || [],
    citizen_type: "HOUSEHOLD",
    source: "PORTAL",
    ...ticketReporter(ticket.user_id),
  };
}

/** Fixture complaints (with any officer overrides applied) merged with
 *  every ticket residents have filed in this browser, newest first. */
export function listComplaints() {
  const overrides = listOverrides();
  const fixture = DATA.complaints.map((c) => ({
    ...c,
    source: "FIXTURE",
    ...(overrides[c.id] || {}),
  }));
  const tickets = readJson(RESIDENT_TICKETS_KEY, []).map(normalizeTicket);
  return [...tickets, ...fixture].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

/** True when an officer restricted to a ward list is looking at a
 *  complaint from a real ward outside it. Complaints whose ward could
 *  not be resolved ("UNASSIGNED") stay actionable by everyone, as does
 *  everything for officers without a ward list (e.g. admins). */
export function isOutsideAssignedWards(complaint, assignedWards) {
  if (!Array.isArray(assignedWards)) return false;
  const isRealWard = DATA.wards.some((w) => w.code === complaint.ward_code);
  return isRealWard && !assignedWards.includes(complaint.ward_code);
}

/** Persists an officer's status update / resolution for one complaint
 *  and returns the refreshed complaint list. Throws if the complaint's
 *  ward is outside the officer's assigned wards — the UI already hides
 *  the form in that case, this is the data-layer backstop. */
export function updateComplaint(complaint, { status, note, officerName, assignedWards }) {
  if (isOutsideAssignedWards(complaint, assignedWards)) {
    throw new Error(
      `${complaint.ward_code} is outside your assigned wards, so this complaint can't be updated.`
    );
  }

  // Audit trail (Story 2.3 AC4): every actual status change is recorded
  // with who made it and when. `by` rather than `officer` so citizen
  // reopens from the resident portal fit the same shape.
  const history =
    status !== complaint.status
      ? [
          ...(complaint.status_history || []),
          { from: complaint.status, to: status, by: officerName, at: new Date().toISOString() },
        ]
      : complaint.status_history || [];

  const patch = {
    status,
    resolution_notes: note || complaint.resolution_notes || null,
    resolver_name: note ? officerName : complaint.resolver_name || null,
    resolved_at: status === "RESOLVED" ? new Date().toISOString() : null,
    status_history: history,
  };

  if (complaint.source === "PORTAL") {
    const tickets = readJson(RESIDENT_TICKETS_KEY, []);
    const next = tickets.map((t) => (t.id === complaint.id ? { ...t, ...patch } : t));
    localStorage.setItem(RESIDENT_TICKETS_KEY, JSON.stringify(next));
  } else {
    const next = { ...listOverrides(), [complaint.id]: patch };
    localStorage.setItem(OVERRIDES_KEY, JSON.stringify(next));
  }
  return listComplaints();
}

// ── Crew assignments ────────────────────────────────────────────────
// Officer reassignments (worker → ward/route) persist as an id → patch
// map layered over the read-only worker fixture.

const CREW_OVERRIDES_KEY = "gc_officer_crew_overrides";

function listCrewOverrides() {
  return readJson(CREW_OVERRIDES_KEY, {});
}

/** Fixture workers with any officer reassignments applied. */
export function listWorkerAssignments() {
  const overrides = listCrewOverrides();
  return DATA.workers.map((w) => ({ ...w, ...(overrides[w.id] || {}) }));
}

/** Moves a worker to another ward/route and returns the refreshed roster. */
export function reassignWorker(workerId, { ward_code, route_id, shift }) {
  const next = {
    ...listCrewOverrides(),
    [workerId]: { ward_code, route_id: route_id || null, shift },
  };
  localStorage.setItem(CREW_OVERRIDES_KEY, JSON.stringify(next));
  return listWorkerAssignments();
}
