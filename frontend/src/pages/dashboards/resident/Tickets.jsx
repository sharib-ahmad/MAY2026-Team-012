import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Search } from "lucide-react";

import { Card, Empty, Modal, StatusPill, Table } from "../../../components/UI";
import { createUserTicket, listUserTickets } from "../../../lib/api";

const ISSUE_TYPES = ["MISSED_PICKUP", "OVERFLOW", "MIXED_WASTE", "DELAY", "OTHER"];

export default function Tickets() {
  const [tickets, setTickets] = useState([]);
  const [openNewComplaint, setOpenNewComplaint] = useState(false);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState("");
  const [form, setForm] = useState({ issue_type: "MISSED_PICKUP", description: "" });
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(null);

  useEffect(() => {
    listUserTickets()
      .then(({ tickets: items }) => setTickets(items))
      .catch(() => setTickets([]));
  }, []);

  const filteredTickets = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return tickets;
    return tickets.filter((ticket) =>
      [ticket.ref_code, ticket.issue_type, ticket.description]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [search, tickets]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    try {
      const ticket = await createUserTicket(form);
      setTickets((current) => [ticket, ...current]);
      setSubmitted(ticket);
      window.dispatchEvent(new Event("resident-notifications-updated"));
      setOpenNewComplaint(false);
      setForm({ issue_type: "MISSED_PICKUP", description: "" });
    } catch (requestError) {
      setError(
        requestError.response?.data?.error?.message ||
          requestError.response?.data?.detail ||
          "Unable to raise complaint."
      );
    }
  };

  const columns = [
    { key: "ref_code", label: "Ref" },
    { key: "issue_type", label: "Category", render: (value) => value.replace(/_/g, " ") },
    { key: "status", label: "Status", render: (value) => <StatusPill status={value} /> },
    { key: "created_at", label: "Date", render: (value) => new Date(value).toLocaleDateString() },
  ];

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-xl font-bold">My Tickets</h1>
          <p className="text-sm text-gray-500 mt-1">Track and manage your complaints.</p>
        </div>
        <button
          type="button"
          onClick={() => {
            setError("");
            setOpenNewComplaint(true);
          }}
          className="bg-primary text-white px-4 py-2.5 rounded-input text-sm font-medium hover:bg-primary/90"
        >
          + New Complaint
        </button>
      </div>

      <div className="relative max-w-md">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search by reference, category, or note…"
          className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-4 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      {submitted && (
        <div className="flex items-center gap-2 rounded-input bg-green-50 p-3 text-sm text-green-800">
          <CheckCircle2 size={16} /> Complaint raised. Reference:{" "}
          <strong>{submitted.ref_code}</strong>
        </div>
      )}

      <Card title="All tickets">
        {filteredTickets.length ? (
          <Table columns={columns} rows={filteredTickets} onRowClick={setSelected} />
        ) : (
          <Empty
            icon={search ? Search : AlertCircle}
            title={search ? "No tickets found" : "No tickets"}
            description={
              search ? "Try another search term." : "Create a complaint when you need help."
            }
          />
        )}
      </Card>

      <Modal
        open={openNewComplaint}
        onClose={() => setOpenNewComplaint(false)}
        title="Raise a Complaint"
      >
        <form onSubmit={submit} className="space-y-4">
          {error && <p className="rounded-input bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
            <select
              className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
              value={form.issue_type}
              onChange={(event) => setForm({ ...form, issue_type: event.target.value })}
            >
              {ISSUE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Note / description
            </label>
            <textarea
              required
              minLength={10}
              maxLength={500}
              rows={4}
              value={form.description}
              onChange={(event) => setForm({ ...form, description: event.target.value })}
              placeholder="Describe the issue…"
              className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
            />
          </div>
          <button
            type="submit"
            className="w-full bg-primary text-white py-2.5 rounded-input font-medium hover:bg-primary/90"
          >
            Submit Complaint
          </button>
        </form>
      </Modal>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={`Ticket ${selected?.ref_code}`}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <p>
                <span className="text-gray-400">Category:</span>{" "}
                {selected.issue_type.replace(/_/g, " ")}
              </p>
              <p>
                <span className="text-gray-400">Status:</span>{" "}
                <StatusPill status={selected.status} />
              </p>
              <p>
                <span className="text-gray-400">Created:</span>{" "}
                {new Date(selected.created_at).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-600 mb-1">Note</p>
              <div className="rounded-input bg-gray-50 p-3">{selected.description}</div>
            </div>
            {selected.ward_name && (
              <div>
                <p className="text-xs font-medium text-gray-600 mb-1">Assigned Ward</p>
                <div className="rounded-input bg-gray-50 p-3 space-y-1">
                  <p className="font-medium">
                    {selected.ward_code} — {selected.ward_name}
                  </p>
                  {selected.ward_sectors && (
                    <p className="text-gray-600">Sectors: {selected.ward_sectors}</p>
                  )}
                  <p className="text-gray-600">
                    Manager: {selected.ward_manager_name || "Not assigned"}
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
