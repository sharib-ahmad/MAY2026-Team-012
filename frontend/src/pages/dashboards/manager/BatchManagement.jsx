import { useCallback, useEffect, useMemo, useState } from "react";
import { Recycle, UserPlus } from "lucide-react";
import { Modal, StatusPill } from "../../../components/UI";
import { assignManagerBatch, getManagerBatches, getManagerRecyclers } from "../../../lib/api";
import { PaginatedTable, SearchInput, Section } from "./shared";
import { formatDate } from "./format";

export default function BatchManagement() {
  const [batches, setBatches] = useState([]);
  const [recyclers, setRecyclers] = useState([]);
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [batchRows, recyclerRows] = await Promise.all([
        getManagerBatches(),
        getManagerRecyclers(),
      ]);
      setBatches(batchRows);
      setRecyclers(recyclerRows);
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load batch data.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return batches.filter((batch) => {
      if (statusFilter && batch.status !== statusFilter) return false;
      if (!needle) return true;
      return [batch.ref_code, batch.waste_category, batch.zone_code, batch.status]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    });
  }, [batches, query, statusFilter]);

  const assign = async (batchId, recyclerId) => {
    if (!recyclerId) return;
    setError("");
    try {
      const updated = await assignManagerBatch(batchId, recyclerId);
      setBatches((items) => items.map((batch) => (batch.id === batchId ? updated : batch)));
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to assign this batch.");
    }
  };

  return (
    <Section
      eyebrow="Batch management"
      title="Assign recycler"
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="border border-gray-200 rounded-input bg-white px-2.5 py-1.5 text-xs"
          >
            <option value="">All statuses</option>
            <option value="COLLECTED">Awaiting assignment</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="PROCESSING">Processing</option>
            <option value="PROCESSED">Processed</option>
          </select>
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search ref, ward, category…"
          />
        </div>
      }
    >
      {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
      {loading ? (
        <p className="text-sm text-gray-500">Loading batches…</p>
      ) : (
        <PaginatedTable
          emptyMessage="No batches match your filters."
          columns={[
            {
              key: "ref_code",
              label: "Reference",
              render: (value) => <span className="font-mono-civic text-xs">{value}</span>,
            },
            { key: "waste_category", label: "Category" },
            {
              key: "declared_weight",
              label: "Weight",
              render: (value) => `${Number(value).toFixed(1)} kg`,
            },
            {
              key: "zone_code",
              label: "Ward",
              render: (value) => (
                <span className="text-xs font-semibold text-[#3F5426]">{value || "—"}</span>
              ),
            },
            { key: "pickup_count", label: "Pickups" },
            { key: "status", label: "Status", render: (value) => <StatusPill status={value} /> },
            {
              key: "assignment",
              label: "Recycler",
              render: (_, batch) => {
                if (batch.destination_recycler_name) {
                  return <span className="text-sm">{batch.destination_recycler_name}</span>;
                }
                if (batch.status !== "COLLECTED") return <span className="text-gray-400">—</span>;
                return (
                  <div className="flex items-center gap-2 min-w-[190px]">
                    <UserPlus size={14} className="text-[#3F5426] shrink-0" />
                    <select
                      defaultValue=""
                      onChange={(event) => assign(batch.id, event.target.value)}
                      className="w-full border border-gray-200 rounded-input bg-white px-2 py-1.5 text-xs"
                    >
                      <option value="">Assign recycler</option>
                      {recyclers.map((recycler) => (
                        <option key={recycler.id} value={recycler.id}>
                          {recycler.name}
                        </option>
                      ))}
                    </select>
                  </div>
                );
              },
            },
          ]}
          rows={rows}
          onRowClick={setSelected}
        />
      )}

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Batch ${selected.ref_code}` : "Batch details"}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-gray-400 uppercase">Status</p>
                <StatusPill status={selected.status} />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase">Category</p>
                <p className="font-medium">{selected.waste_category}</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase">Weight</p>
                <p className="font-medium">{Number(selected.declared_weight).toFixed(1)} kg</p>
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase">Ward</p>
                <p className="font-medium">{selected.zone_name || selected.zone_code || "—"}</p>
              </div>
            </div>
            {selected.rejection_reason && (
              <div className="rounded-input bg-red-50 border border-red-100 p-3 text-red-800">
                <p className="text-xs font-semibold uppercase mb-1">Recycler rejection note</p>
                <p>{selected.rejection_reason}</p>
                {selected.rejected_at && (
                  <p className="text-xs mt-2 text-red-600">{formatDate(selected.rejected_at)}</p>
                )}
              </div>
            )}
            <div>
              <p className="text-xs text-gray-400 uppercase mb-2">Pickup references</p>
              <div className="flex flex-wrap gap-1.5">
                {(selected.pickup_ref_codes || []).map((ref) => (
                  <span
                    key={ref}
                    className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-mono-civic"
                  >
                    <Recycle size={11} /> {ref}
                  </span>
                ))}
              </div>
            </div>
            <dl className="grid grid-cols-2 gap-2 text-xs text-gray-500">
              {selected.collected_at && (
                <>
                  <dt>Collected</dt>
                  <dd>{formatDate(selected.collected_at)}</dd>
                </>
              )}
              {selected.assigned_at && (
                <>
                  <dt>Assigned</dt>
                  <dd>{formatDate(selected.assigned_at)}</dd>
                </>
              )}
              {selected.processed_at && (
                <>
                  <dt>Processed</dt>
                  <dd>{formatDate(selected.processed_at)}</dd>
                </>
              )}
            </dl>
          </div>
        )}
      </Modal>
    </Section>
  );
}
