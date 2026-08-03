// There is no server behind /api/auth/* yet, so this module plays that
// role entirely inside the browser: it keeps registered users, hashed
// passwords, and sessions in localStorage. AuthContext is the only file
// that talks to this module — swap it for real axios calls to /api/auth/*
// once a backend exists and nothing else in the app should need to change.

import { listStatusOverrides } from "./mockUserStatus";

const USERS_KEY = "gc_users";
const TOKEN_TTL_MS = 2 * 60 * 60 * 1000; // 2 hours

function readUsers() {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function writeUsers(users) {
  localStorage.setItem(USERS_KEY, JSON.stringify(users));
}

function bytesToHex(buffer) {
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function randomSalt() {
  return bytesToHex(crypto.getRandomValues(new Uint8Array(16)).buffer);
}

// SHA-256 the password together with a per-user salt. This runs in the
// browser via the native Web Crypto API — no external crypto library needed.
async function hashPassword(password, salt) {
  const data = new TextEncoder().encode(`${salt}:${password}`);
  const digest = await crypto.subtle.digest("SHA-256", data);
  return bytesToHex(digest);
}

function toBase64Url(obj) {
  return btoa(JSON.stringify(obj)).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(str) {
  const padded = str.replace(/-/g, "+").replace(/_/g, "/");
  return JSON.parse(atob(padded));
}

// Builds a JWT-shaped (but unsigned — there's no server secret to sign
// with) token, so the rest of the app can keep treating it like a real
// access token: decode the middle segment.
function issueTokens(user) {
  const now = Date.now();
  const payload = { sub: user.id, role: user.role, iat: now, exp: now + TOKEN_TTL_MS };
  return {
    access_token: `local.${toBase64Url(payload)}.unsigned`,
    refresh_token: `refresh.${toBase64Url({ sub: user.id, iat: now })}.unsigned`,
  };
}

function decodeToken(token) {
  const parts = String(token).split(".");
  if (parts.length !== 3) return null;
  try {
    return fromBase64Url(parts[1]);
  } catch {
    return null;
  }
}

// Never let the password hash/salt leak out to the UI layer.
function toPublicUser(user) {
  const safe = { ...user };
  delete safe.passwordHash;
  delete safe.salt;
  return safe;
}

export async function register({ name, email, password, phone, address, zone_id, role }) {
  const users = readUsers();
  const normalizedEmail = String(email).trim().toLowerCase();

  if (users.some((u) => u.email === normalizedEmail)) {
    throw { response: { data: { detail: "An account with this email already exists." } } };
  }

  const salt = randomSalt();
  const passwordHash = await hashPassword(password, salt);

  const user = {
    id: crypto.randomUUID(),
    name: name.trim(),
    email: normalizedEmail,
    phone: phone || null,
    address: address || null,
    zone_id: zone_id || null,
    role,
    passwordHash,
    salt,
    createdAt: new Date().toISOString(),
  };

  writeUsers([...users, user]);
  return { ...issueTokens(user), user: toPublicUser(user) };
}

export async function login(email, password) {
  const users = readUsers();
  const normalizedEmail = String(email).trim().toLowerCase();
  const user = users.find((u) => u.email === normalizedEmail);

  // Same error for "no such user" and "wrong password" — don't reveal
  // which one it was.
  if (!user) {
    throw { response: { data: { detail: "Invalid email or password." } } };
  }

  const hash = await hashPassword(password, user.salt);
  if (hash !== user.passwordHash) {
    throw { response: { data: { detail: "Invalid email or password." } } };
  }

  // Story 5.1-AC2: a suspended account must be blocked from logging in,
  // not just hidden from an admin's account list.
  if (listStatusOverrides()[user.id] === "SUSPENDED") {
    throw {
      response: { data: { detail: "This account has been suspended by an administrator." } },
    };
  }

  return { ...issueTokens(user), user: toPublicUser(user) };
}

// The local replacement for "GET /auth/me" — restores a session purely
// from the token sitting in localStorage.
export function getSessionUser(accessToken) {
  const claims = decodeToken(accessToken);
  if (!claims || claims.exp < Date.now()) return null;

  // Story 5.1-AC2: re-checked on every session restore, so a suspension
  // takes effect immediately rather than only blocking the next login.
  if (listStatusOverrides()[claims.sub] === "SUSPENDED") return null;

  const user = readUsers().find((u) => u.id === claims.sub);
  return user ? toPublicUser(user) : null;
}

// Lets the admin panel list every registered account without exposing
// password material.
export function listUsers() {
  return readUsers().map(toPublicUser);
}

// Managers are only authorized to act on complaints from their own wards
// (Story 2.3 AC3). The demo manager gets a subset of the five fixture
// wards so the view-only path is reachable in testing.
const MANAGER_ASSIGNED_WARDS = ["WARD-01", "WARD-02", "WARD-03"];

// Browsers seeded before ward authorization existed hold managers without
// assigned_wards — patch them in place so the rule applies there too.
function backfillManagerWards(users) {
  if (!users.some((u) => u.role === "MUNICIPAL_OFFICER" && !u.assigned_wards)) return;
  writeUsers(
    users.map((u) =>
      u.role === "MUNICIPAL_OFFICER" && !u.assigned_wards
        ? { ...u, assigned_wards: MANAGER_ASSIGNED_WARDS }
        : u
    )
  );
}

// Registration only offers Citizen / Collector / Recycler (see Register.jsx),
// so Manager and Admin accounts can't be created through the UI. Seed a
// couple of demo logins once, on first run, so those dashboards are still
// reachable for testing. Safe to delete this call once a real backend
// with proper role provisioning exists.
export function seedDemoAccountsOnce() {
  const existing = readUsers();
  if (existing.length > 0) {
    backfillManagerWards(existing);
    return;
  }

  const seeds = [
    {
      name: "Demo Manager",
      email: "manager@verdeza.test",
      role: "MUNICIPAL_OFFICER",
      assigned_wards: MANAGER_ASSIGNED_WARDS,
    },
    { name: "Demo Admin", email: "admin@verdeza.test", role: "SYSTEM_ADMIN" },
  ];

  Promise.all(
    seeds.map(async (seed) => {
      const salt = randomSalt();
      const passwordHash = await hashPassword("password123", salt);
      return {
        id: crypto.randomUUID(),
        name: seed.name,
        email: seed.email,
        phone: null,
        address: null,
        zone_id: null,
        role: seed.role,
        assigned_wards: seed.assigned_wards || null,
        passwordHash,
        salt,
        createdAt: new Date().toISOString(),
      };
    })
  ).then(writeUsers);
}
