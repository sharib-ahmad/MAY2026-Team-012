import { useMemo, useState } from "react";
import { Plus, CheckCircle2 } from "lucide-react";
import { StatusPill, Modal } from "../../../components/UI";
import { listZones, createZone, suggestWardCode } from "../../../lib/mockZones";
import { listUsers } from "../../../lib/mockAuth";
import DATA from "../../../data/admin_portal_data.json";
import { Section, PaginatedTable, SearchInput, FilterSelect } from "./shared";

const STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "ACTIVE", label: "Active" },
  { value: "PENDING", label: "Pending" },
];

function inputClass(hasError) {
  return `w-full border rounded-input px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0B4F4A]/30 ${
    hasError ? "border-red-300 focus:border-red-400" : "border-gray-200 focus:border-[#0B4F4A]/40"
  }`;
}

const EMPTY_FORM = { code: "", name: "", officer_id: "", status: "ACTIVE" };

export default function Wards() {
  const [zones, setZones] = useState(listZones);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [err, setErr] = useState("");
  const [created, setCreated] = useState(null);

  // Officers from the fixture plus any provisioned through the Create
  // Account tab, so a freshly created officer can be assigned right away.
  const officers = useMemo(() => {
    const fixtureManagers = DATA.users.filter((u) => u.role === "MANAGER");
    const fixtureEmails = new Set(fixtureManagers.map((u) => u.email));
    const registered = listUsers().filter(
      (u) => u.role === "MANAGER" && !fixtureEmails.has(u.email)
    );
    return [...fixtureManagers, ...registered];
  }, []);

  const officerName = (id) => officers.find((u) => u.id === id)?.name || "Unassigned";

  const openModal = () => {
    setForm({ ...EMPTY_FORM, code: suggestWardCode() });
    setFieldErrors({});
    setErr("");
    setOpen(true);
  };

  const updateField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) => ({ ...e, [key]: undefined }));
  };

  const submit = (e) => {
    e.preventDefault();
    setErr("");

    const errors = {};
    if (!form.code.trim()) errors.code = "Ward code is required.";
    if (!form.name.trim()) errors.name = "Ward name is required.";
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    try {
      const zone = createZone(form);
      setZones(listZones());
      setCreated(zone);
      setOpen(false);
    } catch (ex) {
      setErr(ex.message);
    }
  };

  const q = query.trim().toLowerCase();
  const filtered = zones.filter(
    (z) =>
      (statusFilter === "ALL" || z.status === statusFilter) &&
      (!q ||
        z.code.toLowerCase().includes(q) ||
        z.name.toLowerCase().includes(q) ||
        officerName(z.officer_id).toLowerCase().includes(q))
  );

  return (
    <Section
      eyebrow="Ward configuration"
      title="Zones"
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <SearchInput value={query} onChange={setQuery} placeholder="Search ward, officer…" />
          <FilterSelect value={statusFilter} onChange={setStatusFilter} options={STATUS_OPTIONS} />
          <button
            type="button"
            onClick={openModal}
            className="inline-flex items-center gap-1.5 rounded-input bg-[#0B4F4A] px-4 py-2 text-xs font-semibold text-white hover:bg-[#0B2F2C] transition"
          >
            <Plus size={14} /> Add ward
          </button>
        </div>
      }
    >
      {created && (
        <div className="mb-5 flex items-start gap-2 rounded-input border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
          <span>
            Ward created successfully. <span className="font-semibold">{created.name}</span> (
            <span className="font-mono-civic">{created.code}</span>) is now available for officer
            and citizen assignment.
          </span>
        </div>
      )}

      <PaginatedTable
        columns={[
          { key: "code", label: "Ward" },
          { key: "name", label: "Name" },
          { key: "officer_id", label: "Officer", render: (v) => officerName(v) },
          { key: "active_workers", label: "Workers" },
          { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
        ]}
        rows={filtered}
      />

      <Modal open={open} onClose={() => setOpen(false)} title="Add a new ward">
        {err && (
          <div className="mb-4 rounded-input border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {err}
          </div>
        )}
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
                Ward code
              </label>
              <input
                className={inputClass(fieldErrors.code)}
                value={form.code}
                onChange={(e) => updateField("code", e.target.value)}
                placeholder="e.g. WARD-06"
              />
              {fieldErrors.code && <p className="text-red-600 text-xs mt-1">{fieldErrors.code}</p>}
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
                Status
              </label>
              <select
                className={inputClass(false)}
                value={form.status}
                onChange={(e) => updateField("status", e.target.value)}
              >
                <option value="ACTIVE">Active</option>
                <option value="PENDING">Pending</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
              Ward name
            </label>
            <input
              className={inputClass(fieldErrors.name)}
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="e.g. Zone 6 - Aliganj"
            />
            {fieldErrors.name && <p className="text-red-600 text-xs mt-1">{fieldErrors.name}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
              Assigned officer (optional)
            </label>
            <select
              className={inputClass(false)}
              value={form.officer_id}
              onChange={(e) => updateField("officer_id", e.target.value)}
            >
              <option value="">Unassigned</option>
              {officers.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-input border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-600 hover:border-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-1.5 rounded-input bg-[#0B4F4A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0B2F2C] transition"
            >
              <Plus size={14} /> Create ward
            </button>
          </div>
        </form>
      </Modal>
    </Section>
  );
}
