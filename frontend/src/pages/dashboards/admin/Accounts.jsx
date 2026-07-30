import { useEffect, useMemo, useState } from "react";
import {
  Ban,
  CheckCircle2,
  ShieldCheck,
  Users,
  MapPin,
  AlertTriangle,
  Activity,
  Pencil,
  Trash2,
  X,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { StatusPill } from "../../../components/UI";
import API, { getAdminDashboard } from "../../../lib/api";
import { Section, PaginatedTable, SearchInput, FilterSelect } from "./shared";
import { formatDate } from "./format";

const ROLE_OPTIONS = [
  { value: "ALL", label: "All roles" },
  { value: "RESIDENT", label: "Resident" },
  { value: "COLLECTOR", label: "Collector" },
  { value: "RECYCLER", label: "Recycler" },
  { value: "MANAGER", label: "Manager" },
  { value: "ADMIN", label: "Admin" },
];

const STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "ACTIVE", label: "Active" },
  { value: "DISABLED", label: "Suspended" },
];

const roleLabel = (key) => {
  const labels = {
    RESIDENT: "Resident",
    COLLECTOR: "Collector",
    RECYCLER: "Recycler",
    MANAGER: "Manager",
    ADMIN: "Admin",
  };
  return labels[key] || key;
};

// One admin action per status: suspend an active account, reactivate a
// suspended one.
const STATUS_ACTIONS = {
  ACTIVE: { next: "DISABLED", label: "Suspend", icon: Ban, tone: "text-red-700 hover:bg-red-50" },
  DISABLED: {
    next: "ACTIVE",
    label: "Activate",
    icon: CheckCircle2,
    tone: "text-emerald-700 hover:bg-emerald-50",
  },
};

// Platform health hero — moved here from the dashboard shell so it lives
// with the page it summarizes rather than as a full-bleed band sitting
// above the sidebar. Same teal/amber styling as before.
function PlatformHealthHero({ name, stats }) {
  return (
    <div className="rounded-2xl overflow-hidden mb-6">
      <div className="bg-[#0B4F4A] px-5 sm:px-8 pt-7 pb-5">
        <div className="inline-flex items-center gap-2 rounded-full border border-amber-300/40 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-200">
          <ShieldCheck size={13} /> {name || "System Admin"}
        </div>
        <h1 className="font-display mt-3 text-2xl sm:text-3xl font-semibold text-white leading-[1.1]">
          Platform health &amp; access control.
        </h1>
      </div>
      <div className="bg-[#0B4F4A] px-5 sm:px-8 pb-7 grid grid-cols-2 sm:grid-cols-4 divide-x divide-white/15">
        {[
          [Users, stats.registered_users, "registered users", "All users"],
          [MapPin, stats.wards_configured, "wards configured", "System zones"],
          [AlertTriangle, stats.errors_in_24h, "errors in 24h", "System errors"],
          [Activity, `${stats.system_uptime_hours}h`, "system uptime", "Hours running"],
        ].map(([Icon, value, label, sub]) => (
          <div key={label} className="px-3 sm:px-5 py-1">
            <Icon size={15} className="text-amber-300" />
            <p className="font-display mt-1.5 text-xl sm:text-2xl font-semibold text-white">
              {value}
            </p>
            <p className="text-[11px] uppercase tracking-wide text-white/70 mt-0.5">{label}</p>
            <p className="font-mono-civic text-[10px] text-white/45 mt-1">{sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Accounts() {
  const { user } = useAuth();
  const [roleFilter, setRoleFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [editingUser, setEditingUser] = useState(null);
  const [editForm, setEditForm] = useState({ name: "", email: "", phone: "", role: "" });

  const handleSuspendUser = async (userId, currentStatus) => {
    try {
      const newStatus = currentStatus === "ACTIVE" ? "DISABLED" : "ACTIVE";
      await API.patch(`/v1/admin/user/${userId}/status`, { status: newStatus });
      // Refresh dashboard data
      const data = await getAdminDashboard();
      setDashboardData(data);
    } catch (err) {
      console.error("Failed to update user status:", err);
      alert(
        "Failed to update user status: " +
          (err.response?.data?.error?.message || err.response?.data?.detail || err.message)
      );
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!confirm("Are you sure you want to delete this user?")) return;
    try {
      await API.delete(`/v1/admin/user/${userId}`);
      // Refresh dashboard data
      const data = await getAdminDashboard();
      setDashboardData(data);
    } catch (err) {
      console.error("Failed to delete user:", err);
      alert(
        "Failed to delete user: " +
          (err.response?.data?.error?.message || err.response?.data?.detail || err.message)
      );
    }
  };

  const handleEditUser = (userId) => {
    const userToEdit = dashboardData.users.find((u) => String(u.id) === String(userId));
    if (userToEdit) {
      setEditingUser(userToEdit);
      setEditForm({
        name: userToEdit.name,
        email: userToEdit.email,
        phone: userToEdit.phone,
        role: userToEdit.role,
      });
    }
  };

  const handleSaveEdit = async () => {
    if (!editForm.name || !editForm.name.trim()) {
      alert("Name cannot be empty.");
      return;
    }
    if (!editForm.email || !editForm.email.trim()) {
      alert("Email cannot be empty.");
      return;
    }
    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!emailRegex.test(editForm.email.trim())) {
      alert("Please enter a valid email address.");
      return;
    }
    if (!editForm.phone || !editForm.phone.trim()) {
      alert("Phone number cannot be empty.");
      return;
    }

    try {
      await API.patch(`/v1/admin/user/${editingUser.id}`, editForm);
      // Refresh dashboard data
      const data = await getAdminDashboard();
      setDashboardData(data);
      setEditingUser(null);
    } catch (err) {
      console.error("Failed to update user:", err);
      alert(
        "Failed to update user: " +
          (err.response?.data?.error?.message || err.response?.data?.detail || err.message)
      );
    }
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const data = await getAdminDashboard();
        setDashboardData(data);
      } catch (err) {
        setError(err.message || "Failed to load dashboard data");
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const filtered = useMemo(() => {
    if (!dashboardData?.users) return [];

    const q = query.trim().toLowerCase();

    return dashboardData.users.filter(
      (u) =>
        (roleFilter === "ALL" || u.role === roleFilter) &&
        (statusFilter === "ALL" || u.status === statusFilter) &&
        (!q ||
          u.name.toLowerCase().includes(q) ||
          u.email.toLowerCase().includes(q) ||
          (u.zone_name && u.zone_name.toLowerCase().includes(q)))
    );
  }, [dashboardData, roleFilter, statusFilter, query]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-gray-500">Loading dashboard data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-red-500">Error: {error}</div>
      </div>
    );
  }

  return (
    <>
      <PlatformHealthHero name={user?.name} stats={dashboardData?.stats || {}} />

      <Section
        eyebrow="Identity provisioning"
        title="User accounts"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <SearchInput
              value={query}
              onChange={setQuery}
              placeholder="Search name, email, zone…"
            />
            <FilterSelect value={roleFilter} onChange={setRoleFilter} options={ROLE_OPTIONS} />
            <FilterSelect
              value={statusFilter}
              onChange={setStatusFilter}
              options={STATUS_OPTIONS}
            />
          </div>
        }
      >
        <PaginatedTable
          columns={[
            { key: "name", label: "Name" },
            { key: "email", label: "Email" },
            { key: "role", label: "Role", render: (v) => roleLabel(v) },
            { key: "zone_code", label: "Zone", render: (v) => v || "—" },
            { key: "last_login_at", label: "Last login", render: (v) => formatDate(v) },
            { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
            {
              key: "actions",
              label: "Actions",
              render: (_, row) => {
                const action = STATUS_ACTIONS[row.status];
                if (!action) return null;
                const Icon = action.icon;
                return (
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => handleEditUser(row.id)}
                      className="inline-flex items-center gap-1.5 rounded-input border border-gray-200 px-2.5 py-1 text-xs font-semibold text-gray-700 hover:bg-gray-50 transition"
                      title="Edit user"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteUser(row.id)}
                      className="inline-flex items-center gap-1.5 rounded-input border border-gray-200 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-50 transition"
                      title="Delete user"
                    >
                      <Trash2 size={13} />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSuspendUser(row.id, row.status)}
                      className={`inline-flex items-center gap-1.5 rounded-input border border-gray-200 px-2.5 py-1 text-xs font-semibold transition ${action.tone}`}
                      title={action.label}
                    >
                      <Icon size={13} /> {action.label}
                    </button>
                  </div>
                );
              },
            },
          ]}
          rows={filtered}
        />
      </Section>

      {/* Edit User Modal */}
      {editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl shadow-lg w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h3 className="text-lg font-semibold text-gray-800">Edit User</h3>
              <button
                type="button"
                onClick={() => setEditingUser(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X size={20} />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={editForm.name}
                  onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={editForm.email}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="text"
                  value={editForm.phone}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                <select
                  value={editForm.role}
                  onChange={(e) => setEditForm({ ...editForm, role: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                >
                  <option value="RESIDENT">Resident</option>
                  <option value="COLLECTOR">Collector</option>
                  <option value="RECYCLER">Recycler</option>
                  <option value="MANAGER">Manager</option>
                  <option value="ADMIN">Admin</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-3 px-6 py-4 border-t">
              <button
                type="button"
                onClick={() => setEditingUser(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveEdit}
                className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 rounded-lg transition"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
