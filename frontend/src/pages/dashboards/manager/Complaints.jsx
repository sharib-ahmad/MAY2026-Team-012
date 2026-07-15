import { useMemo, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { Modal, StatusPill } from "../../../components/UI";
import { listComplaints, updateComplaint } from "../../../lib/mockOfficerData";
import DATA from "../../../data/municipal_officer_data.json";
import { Section, PaginatedTable, SearchInput, FilterSelect, SeverityPill } from "./shared";
import { formatDate } from "./format";

const WARD_OPTIONS = [
  { value: "ALL", label: "All wards" },
  ...DATA.wards.map((w) => ({ value: w.code, label: `${w.code} · ${w.name}` })),
];

const STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "OPEN", label: "Open" },
  { value: "IN_REVIEW", label: "In review" },
  { value: "ESCALATED", label: "Escalated" },
  { value: "RESOLVED", label: "Resolved" },
];

const SORT_OPTIONS = [
  { value: "NEWEST", label: "Newest first" },
  { value: "OLDEST", label: "Oldest first" },
  { value: "WARD", label: "By ward code" },
  { value: "STATUS", label: "By status" },
];

// Workflow order, not alphabetical: unhandled tickets surface first.
const STATUS_SORT_ORDER = { OPEN: 0, IN_REVIEW: 1, ESCALATED: 2, RESOLVED: 3 };

// Officer can move a ticket forward, escalate it, or close it out.
const NEXT_STATUS_OPTIONS = ["IN_REVIEW", "ESCALATED", "RESOLVED"];

const typeLabel = (t) =>
  String(t || "OTHER")
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/^\w/, (c) => c.toUpperCase());

export default function Complaints() {
  const { user } = useAuth();
  const [complaints, setComplaints] = useState(listComplaints);
  const [wardFilter, setWardFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [sortBy, setSortBy] = useState("NEWEST");
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [nextStatus, setNextStatus] = useState("RESOLVED");
  const [note, setNote] = useState("");
  const [error, setError] = useState("");

  const issueOptions = useMemo(
    () => [
      { value: "ALL", label: "All issue types" },
      ...[...new Set(complaints.map((c) => c.issue_type))].map((t) => ({
        value: t,
        label: typeLabel(t),
      })),
    ],
    [complaints]
  );
  const [issueFilter, setIssueFilter] = useState("ALL");

  const q = query.trim().toLowerCase();
  const rows = complaints
    .filter(
      (c) =>
        (wardFilter === "ALL" || c.ward_code === wardFilter) &&
        (statusFilter === "ALL" || c.status === statusFilter) &&
        (issueFilter === "ALL" || c.issue_type === issueFilter) &&
        (!q ||
          c.ref_code?.toLowerCase().includes(q) ||
          c.citizen_name?.toLowerCase().includes(q) ||
          c.description?.toLowerCase().includes(q))
    )
    .sort((a, b) => {
      if (sortBy === "WARD") return a.ward_code.localeCompare(b.ward_code);
      const newestFirst = new Date(b.created_at) - new Date(a.created_at);
      if (sortBy === "STATUS") {
        return (
          (STATUS_SORT_ORDER[a.status] ?? 99) - (STATUS_SORT_ORDER[b.status] ?? 99) || newestFirst
        );
      }
      return sortBy === "OLDEST" ? -newestFirst : newestFirst;
    });

  const openDetail = (row) => {
    setSelected(row);
    setNextStatus("RESOLVED");
    setNote(row.resolution_notes || "");
    setError("");
  };

  const save = () => {
    if (nextStatus === "RESOLVED" && !note.trim()) {
      setError("A short resolution note is required to close a complaint.");
      return;
    }
    setComplaints(
      updateComplaint(selected, {
        status: nextStatus,
        note: note.trim(),
        officerName: user?.name || "Municipal Officer",
      })
    );
    setSelected(null);
  };

  return (
    <>
      <Section
        eyebrow="Public grievances"
        title="Citizen complaints"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <SearchInput value={query} onChange={setQuery} placeholder="Search ref, citizen…" />
            <FilterSelect value={wardFilter} onChange={setWardFilter} options={WARD_OPTIONS} />
            <FilterSelect
              value={statusFilter}
              onChange={setStatusFilter}
              options={STATUS_OPTIONS}
            />
            <FilterSelect value={issueFilter} onChange={setIssueFilter} options={issueOptions} />
            <FilterSelect value={sortBy} onChange={setSortBy} options={SORT_OPTIONS} />
          </div>
        }
      >
        <PaginatedTable
          onRowClick={openDetail}
          columns={[
            {
              key: "ref_code",
              label: "Ref",
              render: (v) => <span className="font-mono-civic text-xs">{v}</span>,
            },
            {
              key: "ward_code",
              label: "Ward",
              render: (v) => <span className="text-xs font-semibold text-[#3F5426]">{v}</span>,
            },
            { key: "citizen_name", label: "Citizen" },
            { key: "issue_type", label: "Issue", render: (v) => typeLabel(v) },
            { key: "severity", label: "Severity", render: (v) => <SeverityPill severity={v} /> },
            { key: "created_at", label: "Submitted", render: (v) => formatDate(v) },
            { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
          ]}
          rows={rows}
        />
      </Section>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Complaint ${selected.ref_code}` : ""}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <p>
                <span className="text-gray-400">Ward</span>
                <br />
                <span className="font-semibold text-[#3F5426]">{selected.ward_code}</span>
              </p>
              <p>
                <span className="text-gray-400">Citizen</span>
                <br />
                {selected.citizen_name} · {typeLabel(selected.citizen_type)}
              </p>
              <p>
                <span className="text-gray-400">Issue</span>
                <br />
                {typeLabel(selected.issue_type)} <SeverityPill severity={selected.severity} />
              </p>
              <p>
                <span className="text-gray-400">Submitted</span>
                <br />
                {formatDate(selected.created_at)}
              </p>
            </div>

            <p className="rounded-input bg-gray-50 border border-gray-100 p-3 text-gray-700">
              {selected.description}
            </p>

            {selected.status === "RESOLVED" ? (
              <div className="rounded-input border border-green-100 bg-green-50 p-3">
                <p className="flex items-center gap-1.5 text-xs font-semibold text-green-800">
                  <CheckCircle2 size={13} /> Resolved {formatDate(selected.resolved_at)}
                  {selected.resolver_name ? ` by ${selected.resolver_name}` : ""}
                </p>
                <p className="text-green-900 mt-1">{selected.resolution_notes}</p>
              </div>
            ) : (
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">
                    Update status
                  </label>
                  <FilterSelect
                    value={nextStatus}
                    onChange={setNextStatus}
                    options={NEXT_STATUS_OPTIONS.map((s) => ({
                      value: s,
                      label: typeLabel(s),
                    }))}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-gray-500 mb-1">
                    Resolution note
                  </label>
                  <textarea
                    value={note}
                    onChange={(e) => setNote(e.target.value)}
                    rows={3}
                    placeholder="What action was taken on the ground?"
                    className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#3F5426]/30"
                  />
                  {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
                </div>
                <button
                  type="button"
                  onClick={save}
                  className="rounded-input bg-[#3F5426] px-4 py-2 text-sm font-semibold text-white hover:bg-[#33441F]"
                >
                  Save update
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </>
  );
}
