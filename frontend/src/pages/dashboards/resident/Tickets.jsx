import { useMemo, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card, StatusPill, Modal, Empty, Table } from "../../../components/UI";
import { AlertCircle, Search, CheckCircle2 } from "lucide-react";
import { listMyTickets, createTicket } from "../../../lib/mockResidentData";
import { listZones } from "../../../lib/mockZones";

const DESCRIPTION_MIN = 10;
const DESCRIPTION_MAX = 500;

export default function Tickets() {
  const { user } = useAuth();
  const [version, setVersion] = useState(0);
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(null);
  const wards = useMemo(() => listZones(), []);
  const defaultWard = user?.zone_id ? `WARD-${String(user.zone_id).padStart(2, "0")}` : "";
  const [form, setForm] = useState({
    issue_type: "MISSED_PICKUP",
    description: "",
    severity: "MEDIUM",
    ward_code: wards.some((w) => w.code === defaultWard) ? defaultWard : "",
  });
  // Field-specific errors (AC2) instead of one generic "form invalid" message.
  const [fieldErrors, setFieldErrors] = useState({});
  const [lastSubmitted, setLastSubmitted] = useState(null); // AC1: show the generated ticket ID
  const [search, setSearch] = useState("");

  // version is a deliberate cache-bust counter for listMyTickets after localStorage updates
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const tickets = useMemo(() => listMyTickets(user.id), [user.id, version]);

  const filteredTickets = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return tickets;
    return tickets.filter((t) =>
      [t.ref_code, t.issue_type, t.status, t.description]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [tickets, search]);

  const submit = (e) => {
    e.preventDefault();
    // AC2 (Required field validation): issue type, ward, and description
    // are each checked independently, with field-specific messages.
    const errors = {};
    if (!form.issue_type) errors.issue_type = "Please select an issue type.";
    if (!form.ward_code) errors.ward_code = "Please select your ward.";
    const descLen = form.description.trim().length;
    if (descLen < DESCRIPTION_MIN) {
      errors.description = `Description must be at least ${DESCRIPTION_MIN} characters.`;
    } else if (descLen > DESCRIPTION_MAX) {
      errors.description = `Description must be ${DESCRIPTION_MAX} characters or fewer.`;
    }
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) return;

    const ticket = createTicket(user, form);
    setOpen(false);
    setForm({
      issue_type: "MISSED_PICKUP",
      description: "",
      severity: "MEDIUM",
      ward_code: defaultWard,
    });
    setFieldErrors({});
    setVersion((v) => v + 1);
    setLastSubmitted(ticket); // AC1: unique ticket ID generated and shown to the citizen
  };

  const cols = [
    { key: "ref_code", label: "Ref" },
    { key: "issue_type", label: "Type", render: (v) => v?.replace(/_/g, " ") },
    { key: "ward_code", label: "Ward", render: (v) => v || "—" },
    { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
    { key: "created_at", label: "Date", render: (v) => v && new Date(v).toLocaleDateString() },
  ];

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex-1 min-w-0">
          <h1 className="text-xl font-bold">My Tickets</h1>
          <div className="relative mt-3 max-w-sm w-full">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search tickets…"
              className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-4 py-2 text-sm text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
        </div>
        <button
          type="button"
          onClick={() => setOpen(true)}
          className="bg-primary text-white px-4 py-2 rounded-input text-sm font-medium hover:bg-primary/90"
        >
          + New Ticket
        </button>
      </div>

      {lastSubmitted && (
        <div className="bg-green-50 text-green-800 text-sm p-3 rounded-input flex items-center justify-between gap-3">
          <span className="flex items-center gap-2">
            <CheckCircle2 size={16} className="shrink-0" />
            Ticket submitted — your reference ID is{" "}
            <span className="font-semibold">{lastSubmitted.ref_code}</span>. Keep this for
            follow-up.
          </span>
          <button
            type="button"
            onClick={() => setLastSubmitted(null)}
            className="text-green-700 hover:text-green-900 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      <Card>
        {filteredTickets.length === 0 ? (
          <Empty
            icon={search ? Search : AlertCircle}
            title={search ? "No tickets found" : "No tickets"}
            description={
              search ? "Try a different search term." : "Raise a ticket if you have any issues"
            }
          />
        ) : (
          <Table columns={cols} rows={filteredTickets} onRowClick={setSelected} />
        )}
      </Card>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={`Ticket ${selected?.ref_code}`}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-gray-400">Type:</span>{" "}
                {selected.issue_type?.replace(/_/g, " ")}
              </div>
              <div>
                <span className="text-gray-400">Status:</span>{" "}
                <StatusPill status={selected.status} />
              </div>
              <div>
                <span className="text-gray-400">Severity:</span> {selected.severity || "—"}
              </div>
              <div>
                <span className="text-gray-400">Ward:</span> {selected.ward_code || "—"}
              </div>
              <div>
                <span className="text-gray-400">Created:</span>{" "}
                {new Date(selected.created_at).toLocaleDateString()}
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Description</p>
              <div className="bg-gray-50 rounded-input p-3">{selected.description}</div>
            </div>
            {selected.resolution_notes && (
              <div>
                <p className="text-xs font-medium text-gray-600 mb-1">Manager Resolution</p>
                <div className="bg-green-50 text-green-800 rounded-input p-3">
                  {selected.resolution_notes}
                  {selected.resolver_name && (
                    <p className="text-xs text-green-600 mt-2">
                      — {selected.resolver_name},{" "}
                      {selected.resolved_at && new Date(selected.resolved_at).toLocaleString()}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>

      <Modal
        open={open}
        onClose={() => {
          setOpen(false);
          setFieldErrors({});
        }}
        title="Raise a Ticket"
      >
        <form onSubmit={submit} className="space-y-4" noValidate>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Issue Type</label>
            <select
              className={`w-full border rounded-input px-3 py-2.5 text-sm ${
                fieldErrors.issue_type ? "border-red-300" : "border-gray-200"
              }`}
              value={form.issue_type}
              onChange={(e) => setForm({ ...form, issue_type: e.target.value })}
            >
              <option value="MISSED_PICKUP">Missed Pickup</option>
              <option value="OVERFLOW">Overflow</option>
              <option value="WRONG_ITEM_COLLECTED">Wrong Item Collected</option>
              <option value="CONTAMINATION">Contamination Issue</option>
              <option value="COLLECTOR_BEHAVIOR">Collector Behavior</option>
              <option value="OTHER">Other</option>
            </select>
            {fieldErrors.issue_type && (
              <p className="text-xs text-red-600 mt-1">{fieldErrors.issue_type}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Ward</label>
            <select
              className={`w-full border rounded-input px-3 py-2.5 text-sm ${
                fieldErrors.ward_code ? "border-red-300" : "border-gray-200"
              }`}
              value={form.ward_code}
              onChange={(e) => setForm({ ...form, ward_code: e.target.value })}
            >
              <option value="">Select your ward…</option>
              {wards.map((w) => (
                <option key={w.code} value={w.code}>
                  {w.code} — {w.name}
                </option>
              ))}
            </select>
            {fieldErrors.ward_code && (
              <p className="text-xs text-red-600 mt-1">{fieldErrors.ward_code}</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
            <select
              className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
              value={form.severity}
              onChange={(e) => setForm({ ...form, severity: e.target.value })}
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
            </select>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-xs font-medium text-gray-600">Description</label>
              <span className="text-[11px] text-gray-400">
                {form.description.length}/{DESCRIPTION_MAX}
              </span>
            </div>
            <textarea
              maxLength={DESCRIPTION_MAX}
              className={`w-full border rounded-input px-3 py-2.5 text-sm ${
                fieldErrors.description ? "border-red-300" : "border-gray-200"
              }`}
              rows={3}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Describe the issue and its location in detail…"
            />
            {fieldErrors.description && (
              <p className="text-xs text-red-600 mt-1">{fieldErrors.description}</p>
            )}
          </div>
          <button
            type="submit"
            className="w-full bg-primary text-white py-2.5 rounded-input font-medium hover:bg-primary/90"
          >
            Submit Ticket
          </button>
        </form>
      </Modal>
    </div>
  );
}
