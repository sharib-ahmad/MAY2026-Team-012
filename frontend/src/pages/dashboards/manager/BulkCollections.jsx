import { useMemo, useState } from "react";
import { UserPlus } from "lucide-react";
import { StatusPill } from "../../../components/UI";
import { assignManagerBulkPickup } from "../../../lib/api";
import { PaginatedTable, SearchInput, Section } from "./shared";
import { formatDate } from "./format";

export default function BulkCollections({ data }) {
  const [query, setQuery] = useState("");
  const [requests, setRequests] = useState(data.bulk_pickups || []);
  const [error, setError] = useState("");

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return requests;
    return requests.filter((request) =>
      [request.ref_code, request.ward_code, request.resident_name, request.status]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle))
    );
  }, [query, requests]);

  const assign = async (requestId, collectorId) => {
    if (!collectorId) return;
    setError("");
    try {
      const result = await assignManagerBulkPickup(requestId, collectorId);
      setRequests((items) =>
        items.map((request) =>
          request.id === requestId
            ? {
                ...request,
                status: result.status,
                assigned_collector_id: collectorId,
                assigned_collector_name: result.collector_name,
              }
            : request
        )
      );
    } catch (err) {
      setError(err.response?.data?.error?.message || "Unable to assign this pickup.");
    }
  };

  return (
    <Section
      eyebrow="Bulk collections"
      title="Assign collector"
      actions={
        <SearchInput value={query} onChange={setQuery} placeholder="Search ref, ward, resident…" />
      }
    >
      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
      <PaginatedTable
        emptyMessage="No bulk pickup requests match your search."
        columns={[
          {
            key: "ref_code",
            label: "Reference",
            render: (value) => <span className="font-mono-civic text-xs">{value}</span>,
          },
          {
            key: "ward_code",
            label: "Ward",
            render: (value) => (
              <span className="text-xs font-semibold text-[#3F5426]">{value}</span>
            ),
          },
          { key: "resident_name", label: "Resident" },
          { key: "estimated_weight", label: "Est. weight", render: (value) => `${value} kg` },
          { key: "requested_date", label: "Requested for", render: (value) => formatDate(value) },
          { key: "status", label: "Status", render: (value) => <StatusPill status={value} /> },
          {
            key: "assignment",
            label: "Collector",
            render: (_, request) => {
              if (request.assigned_collector_name)
                return <span className="text-sm">{request.assigned_collector_name}</span>;
              const collectors = data.workers.filter(
                (worker) =>
                  worker.role === "COLLECTION_WORKER" &&
                  worker.ward_code === request.ward_code &&
                  worker.status === "ACTIVE"
              );
              return (
                <div className="flex items-center gap-2 min-w-[190px]">
                  <UserPlus size={14} className="text-[#3F5426] shrink-0" />
                  <select
                    defaultValue=""
                    onChange={(event) => assign(request.id, event.target.value)}
                    className="w-full border border-gray-200 rounded-input bg-white px-2 py-1.5 text-xs"
                  >
                    <option value="">Assign collector</option>
                    {collectors.map((collector) => (
                      <option key={collector.id} value={collector.id}>
                        {collector.name}
                      </option>
                    ))}
                  </select>
                </div>
              );
            },
          },
        ]}
        rows={rows}
      />
    </Section>
  );
}
