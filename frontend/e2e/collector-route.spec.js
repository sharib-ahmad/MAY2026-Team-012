import { expect, test } from "@playwright/test";
import { ACCOUNTS, authenticateContext, blockThirdPartyMapAssets } from "./support";

test("completing a stop updates the collector route UI without a page reload", async ({
  browser,
  request,
}) => {
  const context = await browser.newContext();
  await blockThirdPartyMapAssets(context);
  await authenticateContext(context, request, ACCOUNTS.collector);
  const page = await context.newPage();

  try {
    await page.goto("/collector/dashboard");
    await expect(page.getByRole("heading", { name: "My Pickups" })).toBeVisible();

    // Two seeded stops, both pending: 0% completion, two "Complete" actions,
    // and no stop marked collected yet.
    await expect(page.getByText("COL-E2E-STOP-1", { exact: true })).toBeVisible();
    await expect(page.getByText("COL-E2E-STOP-2", { exact: true })).toBeVisible();
    // Completion appears as both a stat and the progress-bar label.
    await expect(page.getByText("0%", { exact: true })).toHaveCount(2);
    const completeButtons = page.getByRole("button", { name: "Complete", exact: true });
    await expect(completeButtons).toHaveCount(2);
    await expect(page.getByText("COLLECTED", { exact: true })).toHaveCount(0);

    await completeButtons.first().click();

    // Same page instance — no navigation or reload — the stop list and the
    // progress indicators update in place.
    await expect(page.getByText("COLLECTED", { exact: true })).toHaveCount(1);
    await expect(page.getByRole("button", { name: "Complete", exact: true })).toHaveCount(1);
    await expect(page.getByText("50%", { exact: true })).toHaveCount(2);
    await expect(page.getByText("COL-E2E-STOP-1", { exact: true })).toBeVisible();
    await expect(page.getByText("COL-E2E-STOP-2", { exact: true })).toBeVisible();
  } finally {
    await context.close();
  }
});
