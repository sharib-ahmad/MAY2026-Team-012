import { useCallback, useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { Card, Empty, Modal, StatusPill, Table } from "../../../components/UI";
import { getRecyclerBatches } from "../../../lib/api";
import { BatchDetailPanel, formatBatchDate } from "./batchShared";

export default function ProcessedBatches({ focusBatchId, onFocusConsumed }) {
  const [batches, setBatches] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await getRecyclerBatches();
      setBatches(rows.filter((batch) => batch.status === "PROCESSED"));
    } catch (err) {
      setError(err.response?.data?.error?.message || "Unable to load processed batches.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (!focusBatchId) return;
    const batch = batches.find((item) => item.id === focusBatchId);
    if (batch) setSelected(batch);
    onFocusConsumed?.();
  }, [batches, focusBatchId, onFocusConsumed]);

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 fade-in">
      <h1 className="flex items-center gap-2 text-xl font-bold">
        <CheckCircle2 size={20} /> Processed Batches
      </h1>
      {error && <p className="rounded-input bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <Card>
        {loading ? (
          <p className="text-sm text-gray-500">Loading processed batches…</p>
        ) : batches.length === 0 ? (
          <Empty
            icon={CheckCircle2}
            title="No processed batches"
            description="Completed batches will remain available here for review."
          />
        ) : (
          <Table
            rows={batches}
            onRowClick={setSelected}
            columns={[
              { key: "ref_code", label: "Reference" },
              { key: "waste_category", label: "Category" },
              {
                key: "declared_weight",
                label: "Weight (kg)",
                render: (value) => Number(value).toFixed(1),
              },
              { key: "pickup_count", label: "Pickups" },
              { key: "processed_at", label: "Processed", render: formatBatchDate },
              { key: "status", label: "Status", render: (value) => <StatusPill status={value} /> },
            ]}
          />
        )}
      </Card>
      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Processed batch ${selected.ref_code}` : "Processed batch"}
      >
        {selected && <BatchDetailPanel batch={selected} />}
      </Modal>
    </div>
  );
}
