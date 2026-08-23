import { defineConfig, devices } from "@playwright/test";

// The end-to-end journeys run the real Vite dev server against the real
// FastAPI backend, pointed at an explicitly test-only database. The backend
// server command reseeds that database first, so every run starts from the
// same deterministic fixture set (see backend/scripts/seed_e2e.py).
const PYTHON = process.env.E2E_PYTHON || "python3";
const DATABASE_URL =
  process.env.E2E_DATABASE_URL ||
  "postgresql+psycopg://verdeza:verdeza@localhost:5433/verdeza_e2e_test";

const backendEnv = {
  APP_ENV: "test",
  DATABASE_URL,
  SECRET_KEY: "e2e-only-secret-at-least-32-characters-long-000",
  // Left empty on purpose: no third-party routing provider is called in tests.
  ORS_API_KEY: "",
};

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `${PYTHON} scripts/seed_e2e.py && ${PYTHON} -m uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      cwd: "../backend",
      url: "http://127.0.0.1:8000/health",
      env: backendEnv,
      reuseExistingServer: false,
      timeout: 180_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
