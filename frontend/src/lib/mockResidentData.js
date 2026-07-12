// Backend-free data layer for the Resident portal. Everything a resident
// sees — pickups, tickets, donations/marketplace, impact stats, today's
// collection queue — lives in localStorage, keyed per browser. The very
// first time a given resident opens their dashboard we seed a handful of
// realistic demo records under their own user id (see ensureResidentSeed)
// so the experience feels alive immediately instead of starting empty.
// Swap the functions below for real API calls once a backend exists —
// nothing above this file (the resident pages) should need to change.

const PICKUPS_KEY = 'gc_resident_pickups';
const TICKETS_KEY = 'gc_resident_tickets';
const DONATIONS_KEY = 'gc_resident_donations';
const SEED_FLAG_PREFIX = 'gc_resident_seeded_';

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
  return `${prefix}-${String(n).padStart(4, '0')}`;
}
function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString();
}
function daysFromNow(n) {
  const d = new Date();
  d.setDate(d.getDate() + n);
  return d.toISOString();
}

const COLLECTOR_NAMES = ['Arun Deka', 'Priya Sharma', 'Bibek Sonowal'];

// ── Seeding ─────────────────────────────────────────────────────────
export function ensureResidentSeed(user) {
  if (!user) return;
  const flag = `${SEED_FLAG_PREFIX}${user.id}`;
  if (localStorage.getItem(flag)) return;

  const pickups = readList(PICKUPS_KEY);
  const now = Date.now();
  const seedPickups = [
    {
      id: uid(),
      user_id: user.id,
      ref_code: refCode('PK', pickups.length + 1),
      category: 'Mixed Dry',
      estimated_weight: 6.4,
      scheduled_date: daysAgo(1),
      time_slot: 'Morning (8-11)',
      notes: 'Two bags near the gate',
      status: 'COLLECTED',
      zone_name: user.zone_id ? `Zone ${user.zone_id}` : 'Zone 3',
      pickup_address: user.address || 'Home address',
      collector_name: COLLECTOR_NAMES[0],
      collector_phone: '+91 98765 43210',
      created_at: daysAgo(1),
    },
    {
      id: uid(),
      user_id: user.id,
      ref_code: refCode('PK', pickups.length + 2),
      category: 'E-waste',
      estimated_weight: 2.1,
      scheduled_date: daysAgo(6),
      time_slot: 'Evening (4-7)',
      notes: null,
      status: 'COLLECTED',
      zone_name: user.zone_id ? `Zone ${user.zone_id}` : 'Zone 3',
      pickup_address: user.address || 'Home address',
      collector_name: COLLECTOR_NAMES[1],
      collector_phone: '+91 98765 22334',
      created_at: daysAgo(6),
    },
    {
      id: uid(),
      user_id: user.id,
      ref_code: refCode('PK', pickups.length + 3),
      category: 'Paper',
      estimated_weight: 3.8,
      scheduled_date: daysAgo(13),
      time_slot: 'Midday (11-2)',
      notes: null,
      status: 'COLLECTED',
      zone_name: user.zone_id ? `Zone ${user.zone_id}` : 'Zone 3',
      pickup_address: user.address || 'Home address',
      collector_name: COLLECTOR_NAMES[0],
      collector_phone: '+91 98765 43210',
      created_at: daysAgo(13),
    },
    {
      id: uid(),
      user_id: user.id,
      ref_code: refCode('PK', pickups.length + 4),
      category: 'Daily Waste',
      estimated_weight: 5,
      scheduled_date: new Date(now).toISOString(),
      time_slot: 'Morning (8-11)',
      notes: 'Daily scheduled pickup',
      status: 'IN_PROGRESS',
      zone_name: user.zone_id ? `Zone ${user.zone_id}` : 'Zone 3',
      pickup_address: user.address || 'Home address',
      collector_name: COLLECTOR_NAMES[2],
      collector_phone: '+91 98765 90876',
      created_at: new Date(now).toISOString(),
      pickup_order: 7,
      is_daily_schedule: true,
    },
    {
      id: uid(),
      user_id: user.id,
      ref_code: refCode('PK', pickups.length + 5),
      category: 'Plastic',
      estimated_weight: 4.2,
      scheduled_date: daysFromNow(2),
      time_slot: 'Morning (8-11)',
      notes: null,
      status: 'REQUESTED',
      zone_name: user.zone_id ? `Zone ${user.zone_id}` : 'Zone 3',
      pickup_address: user.address || 'Home address',
      collector_name: null,
      collector_phone: null,
      created_at: new Date(now).toISOString(),
    },
  ];
  writeList(PICKUPS_KEY, [...pickups, ...seedPickups]);

  const tickets = readList(TICKETS_KEY);
  const seedTickets = [
    {
      id: uid(),
      user_id: user.id,
      ref_code: refCode('TK', tickets.length + 1),
      issue_type: 'MISSED_PICKUP',
      description: 'Collector skipped our lane last Tuesday morning.',
      severity: 'MEDIUM',
      status: 'RESOLVED',
      created_at: daysAgo(9),
      resolution_notes: 'Rescheduled and confirmed with the zone collector — should not recur.',
      resolver_name: 'Ward Manager',
      resolved_at: daysAgo(7),
    },
    {
      id: uid(),
      user_id: user.id,
      ref_code: refCode('TK', tickets.length + 2),
      issue_type: 'WRONG_ITEM_COLLECTED',
      description: 'A bag of e-waste was picked up along with dry waste by mistake.',
      severity: 'LOW',
      status: 'IN_REVIEW',
      created_at: daysAgo(2),
      resolution_notes: null,
      resolver_name: null,
      resolved_at: null,
    },
  ];
  writeList(TICKETS_KEY, [...tickets, ...seedTickets]);

  const donations = readList(DONATIONS_KEY);
  const seedMine = [
    {
      id: uid(),
      donor_id: user.id,
      donor_name: user.name,
      donor_phone: user.phone,
      donor_email: user.email,
      title: 'Study table & chair set',
      category: 'FURNITURE',
      condition: 'GOOD',
      description: 'Wooden study table with matching chair, minor scuffs, sturdy.',
      address: user.address || 'Pickup on request',
      images: [],
      status: 'AVAILABLE',
      created_at: daysAgo(4),
      updated_at: daysAgo(4),
    },
  ];
  // A shared, global marketplace pool of other residents' donations —
  // only seeded once ever, regardless of who logs in.
  const GLOBAL_SEED_FLAG = `${SEED_FLAG_PREFIX}global`;
  const globalSeed = !localStorage.getItem(GLOBAL_SEED_FLAG)
    ? [
        {
          id: uid(),
          donor_id: 'seed-1',
          donor_name: 'Meera Bora',
          donor_phone: '+91 90000 11111',
          donor_email: 'meera@example.com',
          title: 'Kids storybook bundle (12 books)',
          category: 'BOOKS',
          condition: 'LIKE_NEW',
          description: 'Assorted picture books, ages 4-8, barely used.',
          address: 'Ward 4, near the community hall',
          images: [],
          status: 'AVAILABLE',
          created_at: daysAgo(5),
          updated_at: daysAgo(5),
        },
        {
          id: uid(),
          donor_id: 'seed-2',
          donor_name: 'Rohit Baruah',
          donor_phone: '+91 90000 22222',
          donor_email: 'rohit@example.com',
          title: 'Working microwave oven',
          category: 'ELECTRONICS',
          condition: 'FAIR',
          description: '20L microwave, works fine, minor dent on the door.',
          address: 'Ward 2, opposite the market',
          images: [],
          status: 'AVAILABLE',
          created_at: daysAgo(8),
          updated_at: daysAgo(8),
        },
        {
          id: uid(),
          donor_id: 'seed-3',
          donor_name: 'Sanjana Gogoi',
          donor_phone: '+91 90000 33333',
          donor_email: 'sanjana@example.com',
          title: "Kid's bicycle (age 6-9)",
          category: 'BICYCLE',
          condition: 'GOOD',
          description: 'Well maintained, tyres recently replaced.',
          address: 'Ward 3, lane 5',
          images: [],
          status: 'AVAILABLE',
          created_at: daysAgo(2),
          updated_at: daysAgo(2),
        },
      ]
    : [];
  if (globalSeed.length) localStorage.setItem(GLOBAL_SEED_FLAG, '1');

  writeList(DONATIONS_KEY, [...donations, ...seedMine, ...globalSeed]);

  localStorage.setItem(flag, '1');
}

// ── Pickups ─────────────────────────────────────────────────────────
export function listMyPickups(userId) {
  return readList(PICKUPS_KEY)
    .filter((p) => p.user_id === userId)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

export function getPickup(id) {
  return readList(PICKUPS_KEY).find((p) => p.id === id) || null;
}

export function createPickup(user, payload) {
  const all = readList(PICKUPS_KEY);
  const pickup = {
    id: uid(),
    user_id: user.id,
    ref_code: refCode('PK', all.length + 1),
    status: 'REQUESTED',
    collector_name: null,
    collector_phone: null,
    zone_name: user.zone_id ? `Zone ${user.zone_id}` : 'Zone 3',
    created_at: new Date().toISOString(),
    ...payload,
  };
  writeList(PICKUPS_KEY, [...all, pickup]);
  return pickup;
}

// Statuses where cancelling still makes sense — once a collector is en
// route (or the job is already finished/cancelled), it's too late.
const CANCELLABLE_STATUSES = ['REQUESTED', 'SCHEDULED', 'ASSIGNED'];

export function cancelPickup(id) {
  const all = readList(PICKUPS_KEY);
  const pickup = all.find((p) => p.id === id);
  if (!pickup) {
    return Promise.reject(new Error('Pickup not found.'));
  }
  if (!CANCELLABLE_STATUSES.includes(pickup.status)) {
    return Promise.reject(new Error('This pickup can no longer be cancelled.'));
  }

  const next = all.map((p) =>
    p.id === id ? { ...p, status: 'CANCELLED', cancelled_at: new Date().toISOString() } : p
  );
  writeList(PICKUPS_KEY, next);
  return Promise.resolve(next.find((p) => p.id === id));
}

// ── Tickets ─────────────────────────────────────────────────────────
export function listMyTickets(userId) {
  return readList(TICKETS_KEY)
    .filter((t) => t.user_id === userId)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

export function getTicket(id) {
  return readList(TICKETS_KEY).find((t) => t.id === id) || null;
}

export function createTicket(user, payload) {
  const all = readList(TICKETS_KEY);
  const ticket = {
    id: uid(),
    user_id: user.id,
    ref_code: refCode('TK', all.length + 1),
    status: 'OPEN',
    resolution_notes: null,
    resolver_name: null,
    resolved_at: null,
    created_at: new Date().toISOString(),
    ...payload,
  };
  writeList(TICKETS_KEY, [...all, ticket]);
  return ticket;
}

// ── Donations / Marketplace ────────────────────────────────────────
export function listMarketplace(userId, { search = '', category = '' } = {}) {
  return readList(DONATIONS_KEY)
    .filter((d) => d.status === 'AVAILABLE' && d.donor_id !== userId)
    .filter((d) => !category || d.category === category)
    .filter(
      (d) => !search || `${d.title} ${d.description}`.toLowerCase().includes(search.toLowerCase())
    )
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

export function listMyDonations(userId) {
  return readList(DONATIONS_KEY)
    .filter((d) => d.donor_id === userId)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
}

// AC1 (Story 6.1): a new listing starts life as "Pending Approval" and only
// becomes publicly claimable once a Municipal Officer approves it (Story
// 6.2). There's no officer/moderation portal wired up yet in this build, so
// — same pattern already used below for claim auto-completion — we
// auto-approve shortly after submission purely so the demo has something to
// show in the Marketplace. Swap this timeout for the real officer-approval
// flow once that portal exists; nothing else about the resident-facing
// status lifecycle needs to change.
export function createDonation(user, payload) {
  const all = readList(DONATIONS_KEY);
  const donation = {
    id: uid(),
    donor_id: user.id,
    donor_name: user.name,
    donor_phone: user.phone,
    donor_email: user.email,
    status: 'PENDING_APPROVAL',
    images: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...payload,
  };
  writeList(DONATIONS_KEY, [...all, donation]);

  setTimeout(() => {
    const current = readList(DONATIONS_KEY);
    const still = current.find((d) => d.id === donation.id);
    // Only auto-approve if the resident hasn't withdrawn it in the meantime.
    if (still && still.status === 'PENDING_APPROVAL') {
      writeList(
        DONATIONS_KEY,
        current.map((d) => (d.id === donation.id ? { ...d, status: 'AVAILABLE', updated_at: new Date().toISOString() } : d))
      );
    }
  }, 8000);

  return donation;
}

// AC5 (Story 6.1): a citizen can withdraw their own listing while it is
// still "Pending Approval" — status becomes "Withdrawn" and it drops out of
// the (future) officer review queue immediately, since that queue only ever
// reads PENDING_APPROVAL rows.
export function withdrawDonation(donationId, userId) {
  const all = readList(DONATIONS_KEY);
  const donation = all.find((d) => d.id === donationId);
  if (!donation) return Promise.reject(new Error('Listing not found.'));
  if (donation.donor_id !== userId) return Promise.reject(new Error('You can only withdraw your own listing.'));
  if (donation.status !== 'PENDING_APPROVAL') {
    return Promise.reject(new Error('Only a listing still pending approval can be withdrawn.'));
  }
  const next = all.map((d) =>
    d.id === donationId ? { ...d, status: 'WITHDRAWN', updated_at: new Date().toISOString() } : d
  );
  writeList(DONATIONS_KEY, next);
  return Promise.resolve(next.find((d) => d.id === donationId));
}

export function claimDonation(donationId, user) {
  const all = readList(DONATIONS_KEY);
  const next = all.map((d) =>
    d.id === donationId
      ? {
          ...d,
          status: 'CLAIM_REQUESTED',
          claimant_id: user.id,
          claimant_name: user.name,
          updated_at: new Date().toISOString(),
        }
      : d
  );
  writeList(DONATIONS_KEY, next);
  // Demo-only: auto-approve claims shortly after so "My Claims" has
  // something to show without needing a donor-side approval flow.
  setTimeout(() => {
    const current = readList(DONATIONS_KEY);
    writeList(
      DONATIONS_KEY,
      current.map((d) => (d.id === donationId ? { ...d, status: 'COMPLETED' } : d))
    );
  }, 6000);
  return next.find((d) => d.id === donationId);
}

export function listMyClaims(userId, filter = '') {
  return readList(DONATIONS_KEY)
    .filter((d) => d.claimant_id === userId)
    .filter((d) => !filter || d.status === filter)
    .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at));
}

// ── Impact / analytics ─────────────────────────────────────────────
const BADGES = [
  { code: 'FIRST_PICKUP', name: 'First Pickup', icon: '🌱', min: 1 },
  { code: 'FIVE_PICKUPS', name: '5 Pickups', icon: '♻️', min: 5 },
  { code: 'TEN_PICKUPS', name: '10 Pickups', icon: '🏆', min: 10 },
  { code: 'FIFTY_KG', name: '50kg Diverted', icon: '🌍', minKg: 50 },
];

export function getMyImpact(userId) {
  const pickups = listMyPickups(userId).filter((p) => p.status === 'COLLECTED');
  const total_pickups = pickups.length;
  const total_kg_diverted = pickups.reduce((sum, p) => sum + (p.estimated_weight || 0), 0);
  const co2_saved_kg = total_kg_diverted * 1.3;
  const credits_balance = total_kg_diverted * 2.5;

  const byCategory = {};
  pickups.forEach((p) => {
    const cat = p.category || 'Other';
    byCategory[cat] = byCategory[cat] || { category: cat, weight_kg: 0, credits: 0, co2_kg: 0 };
    byCategory[cat].weight_kg += p.estimated_weight || 0;
    byCategory[cat].credits += (p.estimated_weight || 0) * 2.5;
    byCategory[cat].co2_kg += (p.estimated_weight || 0) * 1.3;
  });

  const monthly_trend = Array.from({ length: 6 }).map((_, i) => {
    const d = new Date();
    d.setMonth(d.getMonth() - (5 - i));
    const month = d.toLocaleString('default', { month: 'short' });
    const monthPickups = pickups.filter((p) => {
      const pd = new Date(p.created_at);
      return pd.getMonth() === d.getMonth() && pd.getFullYear() === d.getFullYear();
    });
    return {
      month,
      weight_kg: Number(monthPickups.reduce((s, p) => s + (p.estimated_weight || 0), 0).toFixed(1)),
    };
  });

  const badges = BADGES.map((b) => ({
    code: b.code,
    name: b.name,
    icon: b.icon,
    earned: b.minKg ? total_kg_diverted >= b.minKg : total_pickups >= b.min,
  }));

  return {
    total_pickups,
    total_kg_diverted,
    co2_saved_kg,
    credits_balance,
    by_category: Object.values(byCategory),
    monthly_trend,
    badges,
  };
}

// ── Recycling transparency (Story 1.6) ───────────────────────────────
// All recycling batch data is manually entered by municipal staff — there
// is no recycler-verification or automated weigh-in yet. A handful of
// zones have demo records for the current month; every other zone (and any
// zone in a future month) correctly reports no activity rather than
// fabricating numbers, so the empty state (AC2) is genuine, not just
// theoretical.
const RECYCLING_DEMO_ZONES = new Set(['Zone 1', 'Zone 3']);

export function getRecyclingSummary(user) {
  const zoneName = user?.zone_id ? `Zone ${user.zone_id}` : 'Zone 3';
  const now = new Date();
  const monthLabel = now.toLocaleString('default', { month: 'long', year: 'numeric' });

  if (!RECYCLING_DEMO_ZONES.has(zoneName)) {
    return { zone_name: zoneName, month_label: monthLabel, entries: [] };
  }

  const entries = [
    {
      material_type: 'Paper & Cardboard',
      approx_volume_kg: 128.4,
      dispatch_date: daysAgo(6),
      facility: 'Guwahati Regional Recycling Facility',
    },
    {
      material_type: 'Plastic (PET/HDPE)',
      approx_volume_kg: 74.2,
      dispatch_date: daysAgo(3),
      facility: 'Guwahati Regional Recycling Facility',
    },
    {
      material_type: 'E-waste',
      approx_volume_kg: 19.6,
      dispatch_date: daysAgo(11),
      facility: 'Assam E-Waste Processing Unit',
    },
  ];

  return { zone_name: zoneName, month_label: monthLabel, entries };
}

export function listNotifications(userId) {
  const pickups = listMyPickups(userId);
  const notifs = [];
  pickups.slice(0, 3).forEach((p) => {
    if (p.status === 'COLLECTED') {
      notifs.push({
        id: `n-${p.id}`,
        title: 'Pickup collected',
        body: `${p.category} pickup (${p.ref_code}) was collected by ${p.collector_name || 'your collector'}.`,
        created_at: p.created_at,
      });
    } else if (p.status === 'IN_PROGRESS') {
      notifs.push({
        id: `n-${p.id}`,
        title: 'Collector on the way',
        body: `${p.collector_name || 'Your collector'} is working through your zone right now.`,
        created_at: p.created_at,
      });
    } else if (p.status === 'REQUESTED') {
      notifs.push({
        id: `n-${p.id}`,
        title: 'Pickup requested',
        body: `Your ${p.category} pickup (${p.ref_code}) is awaiting collector assignment.`,
        created_at: p.created_at,
      });
    }
  });
  return notifs;
}

// ── Today's collection queue (mocked, no live map) ─────────────────
export function getTodayQueue(userId) {
  const todays = listMyPickups(userId).find((p) => p.is_daily_schedule);
  if (!todays) return null;
  const pickup_number = todays.pickup_order || 7;
  return {
    resident_id: userId,
    pickup_number,
    houses_before: Math.max(pickup_number - 3, 0),
    last_completed_house: Math.max(pickup_number - 3, 0),
    next_expected_house: pickup_number - 1,
    status: todays.status,
  };
}

export function getZoneFlow(userId) {
  const queue = getTodayQueue(userId);
  const myOrder = queue?.pickup_number || 7;
  const names = [
    'Deka Residence',
    'Sharma Household',
    'Green Villa',
    'Baruah Family',
    'Sonowal House',
    'Lake View Apartments',
    'You',
    'Gogoi Residence',
    'Riverside Cottage',
    'Hilltop Bungalow',
  ];
  const stops = names.map((name, i) => {
    const order = i + 1;
    return {
      id: `stop-${order}`,
      pickup_order: order,
      resident_name: order === myOrder ? 'You' : name,
      address: order === myOrder ? 'Your address' : `House #${order}, Zone 3`,
      status: order < myOrder - 2 ? 'COLLECTED' : 'PENDING',
    };
  });
  return {
    total_stops: stops.length,
    stops,
  };
}

export function getMyTodayStop(userId) {
  const flow = getZoneFlow(userId);
  return flow.stops.find((s) => s.resident_name === 'You') || null;
}

// ── Single-pickup live tracking ─────────────────────────────────────
// Scoped to exactly one pickup — used by "Track Live Pickup" so a
// resident only ever sees their own pickup's progress, never the whole
// zone's queue.
const STAGE_ORDER = ['REQUESTED', 'ASSIGNED', 'IN_PROGRESS', 'COLLECTED'];

export function getPickupTracking(pickup) {
  const stageIndex = STAGE_ORDER.indexOf(pickup.status);
  const stopsRemaining = stageIndex >= 0 ? Math.max(STAGE_ORDER.length - 1 - stageIndex, 0) : 0;
  const etaMinutes = pickup.status === 'COLLECTED' ? 0 : Math.max(stopsRemaining * 12, 5);

  const created = new Date(pickup.created_at);
  const timeline = [
    { stage: 'REQUESTED', label: 'Pickup requested', at: created },
    pickup.status !== 'REQUESTED'
      ? { stage: 'ASSIGNED', label: `Assigned to ${pickup.collector_name || 'a collector'}`, at: new Date(created.getTime() + 20 * 60000) }
      : null,
    ['IN_PROGRESS', 'COLLECTED'].includes(pickup.status)
      ? { stage: 'IN_PROGRESS', label: 'Collector en route to your area', at: new Date(created.getTime() + 45 * 60000) }
      : null,
    pickup.status === 'COLLECTED'
      ? { stage: 'COLLECTED', label: 'Pickup collected', at: new Date(created.getTime() + 90 * 60000) }
      : null,
  ].filter(Boolean);

  return {
    pickup_id: pickup.id,
    ref_code: pickup.ref_code,
    status: pickup.status,
    stops_remaining: stopsRemaining,
    estimated_arrival: pickup.status === 'COLLECTED' ? null : `~${etaMinutes} min`,
    timeline,
  };
}

// ── Public "Track" lookup (by ref code, no backend) ─────────────────
// Searches this browser's local pickups and tickets for an exact
// ref-code match and returns a single result — never a list — so a
// search only ever surfaces the one ID that was searched for.
export function getTrackResult(code) {
  const needle = String(code).trim().toUpperCase();
  if (!needle) return null;

  const pickup = readList(PICKUPS_KEY).find((p) => p.ref_code?.toUpperCase() === needle);
  if (pickup) {
    const tracking = getPickupTracking(pickup);
    return {
      entity_type: 'PICKUP',
      code: pickup.ref_code,
      ref_code: pickup.ref_code,
      status: pickup.status,
      category: pickup.category,
      weight: pickup.estimated_weight,
      co2_saved: pickup.status === 'COLLECTED' ? (pickup.estimated_weight || 0) * 1.3 : null,
      credits: pickup.status === 'COLLECTED' ? (pickup.estimated_weight || 0) * 2.5 : null,
      scheduled_date: pickup.scheduled_date,
      collector_name: pickup.collector_name,
      notes: pickup.notes,
      verified: true,
      timeline: tracking.timeline.map((t, i) => ({
        id: `${pickup.id}-${i}`,
        event_type: t.stage,
        created_at: t.at.toISOString(),
        note: t.label,
        hash: `${pickup.id}${i}`.padEnd(16, '0'),
      })),
      created_at: pickup.created_at,
      last_updated: pickup.created_at,
    };
  }

  const ticket = readList(TICKETS_KEY).find((t) => t.ref_code?.toUpperCase() === needle);
  if (ticket) {
    return {
      entity_type: 'TICKET',
      code: ticket.ref_code,
      status: ticket.status,
      issue_type: ticket.issue_type,
      description: ticket.description,
      resolution_notes: ticket.resolution_notes,
      resolver_name: ticket.resolver_name,
      created_at: ticket.created_at,
      last_updated: ticket.resolved_at || ticket.created_at,
    };
  }

  return null;
}
