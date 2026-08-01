export const ROLE_HOME = {
  CITIZEN: "/resident/dashboard",
  COLLECTION_WORKER: "/collector/dashboard",
  MUNICIPAL_OFFICER: "/manager/dashboard",
  RECYCLER: "/recycler/dashboard",
  SYSTEM_ADMIN: "/admin/dashboard",
};

export function homePathForRole(role) {
  return ROLE_HOME[role] || "/login";
}
