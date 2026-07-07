export const ROLE_HOME = {
  RESIDENT: '/resident/dashboard',
  COLLECTOR: '/collector/dashboard',
  MANAGER: '/manager/dashboard',
  RECYCLER: '/recycler/dashboard',
  ADMIN: '/admin/dashboard',
};

export function homePathForRole(role) {
  return ROLE_HOME[role] || '/login';
}