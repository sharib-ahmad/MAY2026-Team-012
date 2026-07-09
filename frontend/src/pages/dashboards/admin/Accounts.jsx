import { useMemo, useState } from "react";
import { StatusPill } from "../../../components/UI";
import { listUsers } from "../../../lib/mockAuth";
import DATA from "../../../data/admin_portal_data.json";
import { Section, PaginatedTable } from "./shared";
import { formatDate } from "./format";

const ROLE_FILTERS = ["ALL", ...DATA.roles.map((r) => r.key)];

const roleLabel = (key) => DATA.roles.find((r) => r.key === key)?.label || key;
const zoneName = (id) => DATA.zones.find((z) => z.id === id)?.name || "—";

export default function Accounts() {
  const [roleFilter, setRoleFilter] = useState("ALL");

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

  const filtered = roleFilter === "ALL" ? users : users.filter((u) => u.role === roleFilter);

  return (
    <Section
      eyebrow="Identity provisioning"
      title="User accounts"
      actions={
        <select
          value={roleFilter}
          onChange={(e) => setRoleFilter(e.target.value)}
          className="border border-gray-200 rounded-input bg-white px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[#0B4F4A]/30"
        >
          {ROLE_FILTERS.map((r) => (
            <option key={r} value={r}>
              {r === "ALL" ? "All roles" : roleLabel(r)}
            </option>
          ))}
        </select>
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
