import { useCallback, useEffect, useState } from "react";
import { CheckCircle, Inbox, XCircle } from "lucide-react";
import { Card, Empty, Modal, StatusPill, Table } from "../../../components/UI";
import { acceptRecyclerBatch, getRecyclerBatches, rejectRecyclerBatch } from "../../../lib/api";
import { BatchDetailPanel, formatBatchDate } from "./batchShared";

export default function AssignedBatches({ focusBatchId, onFocusConsumed }) {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [rejectTarget, setRejectTarget] = useState(null);
  const [rejectNote, setRejectNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const rows = await getRecyclerBatches();
      setBatches(rows.filter((batch) => batch.status === "ASSIGNED"));
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load assigned batches.");
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

  const accept = async (batch) => {
    setError("");
    setSubmitting(true);
    try {
      await acceptRecyclerBatch(batch.id);
      setSelected(null);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to accept this batch.");
    } finally {
      setSubmitting(false);
    }
  };

  const reject = async (event) => {
    event.preventDefault();
    if (!rejectTarget || !rejectNote.trim()) return;
    setError("");
    setSubmitting(true);
    try {
      await rejectRecyclerBatch(rejectTarget.id, rejectNote.trim());
      setRejectTarget(null);
      setRejectNote("");
      setSelected(null);
      await load();
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to reject this batch.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6 fade-in">
      <h1 className="text-xl font-bold flex items-center gap-2">
        <Inbox size={20} /> Assigned Batches
      </h1>

      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{error}</div>}

      <Card>
        {loading ? (
          <p className="text-sm text-gray-500">Loading assigned batches…</p>
        ) : batches.length === 0 ? (
          <Empty
            icon={Inbox}
            title="No assigned batches"
            description="When a ward manager assigns you a batch, it will appear here for review."
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
              {
                key: "assigned_at",
                label: "Assigned",
                render: (value) => formatBatchDate(value),
              },
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
        title={selected ? `Review batch ${selected.ref_code}` : "Batch details"}
      >
        {selected && (
          <div className="space-y-5">
            <BatchDetailPanel batch={selected} />
            <div className="flex flex-wrap gap-2 pt-2 border-t">
              <button
                type="button"
                disabled={submitting}
                onClick={() => accept(selected)}
                className="inline-flex items-center gap-1.5 rounded-input bg-[#C4611A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#A85216] disabled:opacity-50"
              >
                <CheckCircle size={15} /> Accept
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => {
                  setRejectTarget(selected);
                  setRejectNote("");
                }}
                className="inline-flex items-center gap-1.5 rounded-input border border-red-200 bg-red-50 px-4 py-2 text-sm font-semibold text-red-700 hover:bg-red-100 disabled:opacity-50"
              >
                <XCircle size={15} /> Reject
              </button>
            </div>
          </div>
        )}
      </Modal>

      <Modal
        open={!!rejectTarget}
        onClose={() => setRejectTarget(null)}
        title={rejectTarget ? `Reject ${rejectTarget.ref_code}` : "Reject batch"}
      >
        <form onSubmit={reject} className="space-y-4">
          <p className="text-sm text-gray-600">
            Provide a short note for the ward manager explaining why this batch cannot be processed.
          </p>
          <textarea
            value={rejectNote}
            onChange={(event) => setRejectNote(event.target.value)}
            rows={4}
            required
            maxLength={500}
            placeholder="Reason for rejection…"
            className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm"
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setRejectTarget(null)}
              className="rounded-input px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !rejectNote.trim()}
              className="rounded-input bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50"
            >
              {submitting ? "Submitting…" : "Submit rejection"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
