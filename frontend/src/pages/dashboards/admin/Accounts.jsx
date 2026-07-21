import { useMemo, useState } from "react";
import {
  Ban,
  CheckCircle2,
  ShieldCheck,
  Users,
  MapPin,
  AlertTriangle,
  Activity,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { StatusPill } from "../../../components/UI";
import { listUsers } from "../../../lib/mockAuth";
import { listZones } from "../../../lib/mockZones";
import { listStatusOverrides, setUserStatus } from "../../../lib/mockUserStatus";
import DATA from "../../../data/admin_portal_data.json";
import { Section, PaginatedTable, SearchInput, FilterSelect } from "./shared";
import { formatDate } from "./format";

const ROLE_OPTIONS = [
  { value: "ALL", label: "All roles" },
  ...DATA.roles.map((r) => ({ value: r.key, label: r.label })),
];

const STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "ACTIVE", label: "Active" },
  { value: "SUSPENDED", label: "Suspended" },
  { value: "PENDING", label: "Pending" },
];

const roleLabel = (key) => DATA.roles.find((r) => r.key === key)?.label || key;
const zoneName = (id) => listZones().find((z) => z.id === id)?.name || "—";

// One admin action per status: suspend an active account, reactivate a
// suspended one, approve a pending one.
const STATUS_ACTIONS = {
  ACTIVE: { next: "SUSPENDED", label: "Suspend", icon: Ban, tone: "text-red-700 hover:bg-red-50" },
  SUSPENDED: {
    next: "ACTIVE",
    label: "Activate",
    icon: CheckCircle2,
    tone: "text-emerald-700 hover:bg-emerald-50",
  },
  PENDING: {
    next: "ACTIVE",
    label: "Approve",
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
          [Users, stats.total_users, "registered users", `${stats.active_users} active`],
          [
            MapPin,
            stats.total_zones,
            "wards configured",
            `${stats.pending_users} pending accounts`,
          ],
          [
            AlertTriangle,
            stats.errors_last_24h,
            "errors in 24h",
            `${stats.open_complaints} open complaints`,
          ],
          [Activity, `${stats.system_uptime_pct}%`, "system uptime", "last 30 days"],
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
  const [statusOverrides, setStatusOverrides] = useState(listStatusOverrides);

  // Demo users from the JSON fixture plus every account actually
  // registered in localStorage (citizens via /register, officers and
  // admins via the Create Account tab). The seeded demo logins exist in
  // both places, so drop localStorage entries whose email the fixture
  // already covers.
  const users = useMemo(() => {
    const fixtureEmails = new Set(DATA.users.map((u) => u.email));
    const registered = listUsers()
      .filter((u) => !fixtureEmails.has(u.email))
      .map((u) => ({
        ...u,
        status: "ACTIVE",
        created_at: u.createdAt,
        last_login_at: null,
      }));
    return [...registered, ...DATA.users];
  }, []);

  // Layer persisted admin status changes over the read-only sources.
  const withStatus = users.map((u) => ({ ...u, status: statusOverrides[u.id] ?? u.status }));

  const q = query.trim().toLowerCase();
  const filtered = withStatus.filter(
    (u) =>
      (roleFilter === "ALL" || u.role === roleFilter) &&
      (statusFilter === "ALL" || u.status === statusFilter) &&
      (!q ||
        u.name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        zoneName(u.zone_id).toLowerCase().includes(q))
  );

  return (
    <>
      <PlatformHealthHero name={user?.name} stats={DATA.stats} />

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
            { key: "zone_id", label: "Zone", render: (v) => zoneName(v) },
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
                  <button
                    type="button"
                    onClick={() => setStatusOverrides(setUserStatus(row.id, action.next))}
                    className={`inline-flex items-center gap-1.5 rounded-input border border-gray-200 px-2.5 py-1 text-xs font-semibold transition ${action.tone}`}
                  >
                    <Icon size={13} /> {action.label}
                  </button>
                );
              },
            },
          ]}
          rows={filtered}
        />
      </Section>
    </>
  );
}
