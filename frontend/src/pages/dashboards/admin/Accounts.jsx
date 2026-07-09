import { useMemo, useState } from "react";
import { StatusPill } from "../../../components/UI";
import { listUsers } from "../../../lib/mockAuth";
import { listZones } from "../../../lib/mockZones";
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

export default function Accounts() {
  const [roleFilter, setRoleFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [query, setQuery] = useState("");

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

  const q = query.trim().toLowerCase();
  const filtered = users.filter(
    (u) =>
      (roleFilter === "ALL" || u.role === roleFilter) &&
      (statusFilter === "ALL" || u.status === statusFilter) &&
      (!q ||
        u.name.toLowerCase().includes(q) ||
        u.email.toLowerCase().includes(q) ||
        zoneName(u.zone_id).toLowerCase().includes(q))
  );

  return (
    <Section
      eyebrow="Identity provisioning"
      title="User accounts"
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <SearchInput value={query} onChange={setQuery} placeholder="Search name, email, zone…" />
          <FilterSelect value={roleFilter} onChange={setRoleFilter} options={ROLE_OPTIONS} />
          <FilterSelect value={statusFilter} onChange={setStatusFilter} options={STATUS_OPTIONS} />
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
        ]}
        rows={filtered}
      />
    </Section>
  );
}
