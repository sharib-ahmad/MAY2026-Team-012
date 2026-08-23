import { expect, test } from "@playwright/test";
import { ACCOUNTS, authenticateContext } from "./support";

test("a citizen complaint is resolved by the ward manager and the citizen sees the outcome", async ({
  browser,
  request,
}) => {
  const citizenContext = await browser.newContext();
  const managerContext = await browser.newContext();
  await authenticateContext(citizenContext, request, ACCOUNTS.complaintCitizen);
  await authenticateContext(managerContext, request, ACCOUNTS.manager);

  const citizen = await citizenContext.newPage();
  const manager = await managerContext.newPage();

  try {
    // 1. Citizen raises the complaint through the real UI.
    const description = `E2E overflow complaint ${Date.now()}`;
    await citizen.goto("/citizen/dashboard");
    await citizen.getByRole("button", { name: "Tickets" }).click();
    await citizen.getByRole("button", { name: "+ New Complaint" }).click();
    await citizen.getByRole("combobox").selectOption("OVERFLOW");
    await citizen.getByPlaceholder("Describe the issue…").fill(description);
    await citizen.getByRole("button", { name: "Submit Complaint" }).click();

    const banner = citizen.getByText("Complaint raised. Reference:");
    await expect(banner).toBeVisible();
    const refCode = (await banner.locator("strong").innerText()).trim();

    // 2. The authorised manager for the same ward sees it and resolves it.
    await manager.goto("/manager/dashboard");
    await manager.getByRole("button", { name: "Complaints" }).click();
    await manager.getByPlaceholder("Search ref, citizen…").fill(refCode);
    await manager.getByRole("cell", { name: refCode }).click();

    const dialog = manager.getByRole("dialog");
    await expect(dialog).toContainText(description);
    await dialog.getByRole("combobox").selectOption("RESOLVED");
    await dialog
      .getByPlaceholder("What action was taken on the ground?")
      .fill("Ward crew cleared the overflow.");
    await dialog.getByRole("button", { name: "Save update" }).click();
    await expect(dialog).toBeHidden();

    // 3. The citizen sees the resolved status, the manager note and the
    //    supported reopen affordance.
    await citizen.reload();
    await citizen.getByRole("button", { name: "Tickets" }).click();
    await citizen.getByPlaceholder("Search by reference, category, or note…").fill(refCode);
    await citizen.getByRole("cell", { name: refCode }).click();

    const ticketDialog = citizen.getByRole("dialog");
    await expect(ticketDialog).toContainText("RESOLVED");
    await expect(ticketDialog).toContainText("Ward crew cleared the overflow.");
    await expect(ticketDialog.getByRole("button", { name: "Reopen Complaint" })).toBeVisible();
  } finally {
    await citizenContext.close();
    await managerContext.close();
  }
});
