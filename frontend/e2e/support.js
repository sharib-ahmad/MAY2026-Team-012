import { expect } from "@playwright/test";

// Identities created by backend/scripts/seed_e2e.py. Each journey owns its own
// ward, users and rows, so no test mutates data another test reads.
export const E2E_PASSWORD = "E2ePassw0rd!";

export const ACCOUNTS = {
  authCitizen: "e2e-auth-citizen@verdeza.test",
  complaintCitizen: "e2e-complaint-citizen@verdeza.test",
  manager: "e2e-manager@verdeza.test",
  collector: "e2e-collector@verdeza.test",
};

/**
 * Seed an authenticated session into a browser context the same way the app
 * stores it after login, so journeys 2 and 3 do not re-test the login screen.
 * Nothing is written to disk, so no auth-state file or secret is committed.
 */
export async function authenticateContext(context, request, email) {
  const response = await request.post("/api/v1/auth/login", {
    data: { email, password: E2E_PASSWORD },
  });
  expect(response.ok(), `login failed for ${email}`).toBeTruthy();
  const session = JSON.stringify(await response.json());
  await context.addInitScript((value) => {
    window.localStorage.setItem("gc_token", value);
  }, session);
}

/**
 * The collector route renders a Leaflet map. Map tiles and marker images come
 * from third-party hosts that are not under test, so they are blocked to keep
 * the journey about our own application behaviour.
 */
export async function blockThirdPartyMapAssets(context) {
  await context.route(/^https?:\/\/(?!127\.0\.0\.1|localhost)/, (route) => route.abort());
}
