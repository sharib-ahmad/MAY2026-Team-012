import { expect, test } from "@playwright/test";
import { ACCOUNTS, E2E_PASSWORD } from "./support";

test("citizen login routes to the citizen dashboard and survives a page reload", async ({
  page,
}) => {
  await page.goto("/login");

  await page.getByPlaceholder("you@example.com").fill(ACCOUNTS.authCitizen);
  await page.getByPlaceholder("••••••••").fill(E2E_PASSWORD);
  await page.getByRole("button", { name: "Sign In" }).click();

  // Role-based routing: a CITIZEN lands on the citizen dashboard.
  await expect(page).toHaveURL(/\/citizen\/dashboard$/);
  await expect(page.getByRole("button", { name: "Tickets" })).toBeVisible();

  await page.reload();

  // The stored session is restored rather than bouncing back to /login…
  await expect(page).toHaveURL(/\/citizen\/dashboard$/);
  await expect(page.getByRole("button", { name: "Tickets" })).toBeVisible();

  // …and the restored token is still accepted by the API, so an authenticated
  // view renders after the reload.
  await page.getByRole("button", { name: "Tickets" }).click();
  await expect(page.getByRole("heading", { name: "My Tickets" })).toBeVisible();
  await expect(page.getByRole("button", { name: "+ New Complaint" })).toBeVisible();
});
