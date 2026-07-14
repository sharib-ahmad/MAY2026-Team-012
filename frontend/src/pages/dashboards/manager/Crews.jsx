import { useState } from "react";
import { UserCog } from "lucide-react";
import { Modal, StatusPill } from "../../../components/UI";
import { listWorkerAssignments, reassignWorker } from "../../../lib/mockOfficerData";
import DATA from "../../../data/municipal_officer_data.json";
import { Section, PaginatedTable, SearchInput, FilterSelect } from "./shared";

const WARD_OPTIONS = [
  { value: "ALL", label: "All wards" },
  ...DATA.wards.map((w) => ({ value: w.code, label: `${w.code} · ${w.name}` })),
];

const STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "ON_ROUTE", label: "On route" },
  { value: "AVAILABLE", label: "Available" },
  { value: "ON_LEAVE", label: "On leave" },
  { value: "SUSPENDED", label: "Suspended" },
];

const SHIFT_OPTIONS = [
  { value: "MORNING", label: "Morning" },
  { value: "EVENING", label: "Evening" },
];

const routeLabel = (id) => DATA.routes.find((r) => r.id === id)?.code || "Unassigned";

export default function Crews() {
  const [workers, setWorkers] = useState(listWorkerAssignments);
  const [wardFilter, setWardFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ ward_code: "", route_id: "", shift: "MORNING" });

  const q = query.trim().toLowerCase();
  const rows = workers.filter(
    (w) =>
      (wardFilter === "ALL" || w.ward_code === wardFilter) &&
      (statusFilter === "ALL" || w.status === statusFilter) &&
      (!q || w.name.toLowerCase().includes(q) || routeLabel(w.route_id).toLowerCase().includes(q))
  );

  const openReassign = (worker) => {
    setSelected(worker);
    setForm({ ward_code: worker.ward_code, route_id: worker.route_id || "", shift: worker.shift });
  };

  // Only offer routes belonging to the ward picked in the form.
  const wardRoutes = DATA.routes.filter((r) => r.ward_code === form.ward_code);

  const save = () => {
    setWorkers(reassignWorker(selected.id, form));
    setSelected(null);
  };

  return (
    <>
      <Section
        eyebrow="Crew management"
        title="Worker assignments"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <SearchInput value={query} onChange={setQuery} placeholder="Search worker, route…" />
            <FilterSelect value={wardFilter} onChange={setWardFilter} options={WARD_OPTIONS} />
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
            { key: "name", label: "Worker" },
            { key: "phone", label: "Phone" },
            {
              key: "crew_role",
              label: "Role",
              render: (v) => (
                <span className="text-xs">{v === "DRIVER" ? "Driver" : "Helper"}</span>
              ),
            },
            {
              key: "ward_code",
              label: "Ward",
              render: (v) => <span className="text-xs font-semibold text-[#3F5426]">{v}</span>,
            },
            {
              key: "route_id",
              label: "Route",
              render: (v) => <span className="font-mono-civic text-xs">{routeLabel(v)}</span>,
            },
            {
              key: "shift",
              label: "Shift",
              render: (v) => (
                <span className="text-xs">{v === "MORNING" ? "Morning" : "Evening"}</span>
              ),
            },
            { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
            {
              key: "actions",
              label: "Actions",
              render: (_, row) =>
                row.status === "SUSPENDED" ? null : (
                  <button
                    type="button"
                    onClick={() => openReassign(row)}
                    className="inline-flex items-center gap-1.5 rounded-input border border-gray-200 px-2.5 py-1 text-xs font-semibold text-[#3F5426] transition hover:bg-[#3F5426]/5 hover:border-[#3F5426]"
                  >
                    <UserCog size={13} /> Reassign
                  </button>
                ),
            },
          ]}
          rows={rows}
        />
      </Section>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Reassign ${selected.name}` : ""}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <p className="text-xs text-gray-500">
              Move this {selected.crew_role === "DRIVER" ? "driver" : "helper"} to another ward,
              route, or shift. The change applies from the next collection round.
            </p>

            <div className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Ward</label>
                <select
                  value={form.ward_code}
                  onChange={(e) => setForm({ ...form, ward_code: e.target.value, route_id: "" })}
                  className="w-full border border-gray-200 rounded-input bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#3F5426]/30"
                >
                  {DATA.wards.map((w) => (
                    <option key={w.code} value={w.code}>
                      {w.code} · {w.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-gray-500 mb-1">Route</label>
                <select
                  value={form.route_id}
                  onChange={(e) => setForm({ ...form, route_id: e.target.value })}
                  className="w-full border border-gray-200 rounded-input bg-white px-2.5 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#3F5426]/30"
                >
                  <option value="">Standby (no route)</option>
                  {wardRoutes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.code} · {r.shift === "MORNING" ? "Morning" : "Evening"}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-500 mb-1">Shift</label>
              <div className="flex gap-2">
                {SHIFT_OPTIONS.map((s) => (
                  <button
                    key={s.value}
                    type="button"
                    onClick={() => setForm({ ...form, shift: s.value })}
                    className={`rounded-input border px-3 py-1.5 text-xs font-semibold transition ${
                      form.shift === s.value
                        ? "border-[#3F5426] bg-[#3F5426]/10 text-[#3F5426]"
                        : "border-gray-200 text-gray-500 hover:border-gray-300"
                    }`}
                  >
                    {s.label}
                  </button>
                ))}
              </div>
            </div>

            <button
              type="button"
              onClick={save}
              className="rounded-input bg-[#3F5426] px-4 py-2 text-sm font-semibold text-white hover:bg-[#33441F]"
            >
              Save assignment
            </button>
          </div>
        )}
      </Modal>
    </>
  );
}
