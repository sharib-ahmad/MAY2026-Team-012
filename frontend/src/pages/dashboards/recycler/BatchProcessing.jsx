import { useCallback, useEffect, useState } from "react";
import { Cog, PackageCheck } from "lucide-react";
import { Card, Empty, Modal, StatusPill, Table } from "../../../components/UI";
import { getRecyclerBatches, processRecyclerBatch } from "../../../lib/api";
import { BatchDetailPanel } from "./batchShared";

export default function BatchProcessing({ focusBatchId, onFocusConsumed }) {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const rows = await getRecyclerBatches();
      setBatches(rows.filter((batch) => batch.status === "PROCESSING"));
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load processing batches.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!focusBatchId) return;
    const match = batches.find((batch) => batch.id === focusBatchId);
    if (match) setSelected(match);
    onFocusConsumed?.();
  }, [focusBatchId, batches, onFocusConsumed]);

  const markProcessed = async (batch) => {
    setError("");
    setSubmitting(true);
    try {
      await processRecyclerBatch(batch.id);
      setSelected(null);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to mark this batch as processed.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6 fade-in">
      <h1 className="text-xl font-bold flex items-center gap-2">
        <Cog size={20} /> Batch Processing
      </h1>

      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{error}</div>}

      <Card>
        {loading ? (
          <p className="text-sm text-gray-500">Loading processing batches…</p>
        ) : batches.length === 0 ? (
          <Empty
            icon={Cog}
            title="No batches in processing"
            description="Accepted batches appear here until you mark them processed and credits are issued."
          />
        ) : (
          <Table
            columns={[
              { key: "ref_code", label: "Ref" },
              { key: "waste_category", label: "Category" },
              {
                key: "declared_weight",
                label: "Weight (kg)",
                render: (value) => Number(value).toFixed(1),
              },
              { key: "zone_code", label: "Ward" },
              { key: "pickup_count", label: "Pickups" },
              { key: "status", label: "Status", render: (value) => <StatusPill status={value} /> },
            ]}
            rows={batches}
            onRowClick={setSelected}
          />
        )}
      </Card>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Process batch ${selected.ref_code}` : "Batch details"}
      >
        {selected && (
          <div className="space-y-5">
            <BatchDetailPanel batch={selected} />
            <p className="text-sm text-gray-600">
              Marking this batch processed will credit every citizen whose pickup is included and
              complete their tracking timeline.
            </p>
            <button
              type="button"
              disabled={submitting}
              onClick={() => markProcessed(selected)}
              className="inline-flex items-center gap-1.5 rounded-input bg-[#C4611A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#A85216] disabled:opacity-50"
            >
              <PackageCheck size={15} />
              {submitting ? "Processing…" : "Mark processed"}
            </button>
          </div>
        )}
      </Modal>
    </div>
  );
}
