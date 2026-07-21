import { useEffect, useState, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { listBatches, markCollected } from "../../../lib/mockRecyclerData";
import { Card, StatusPill, Modal, Table, Empty } from "../../../components/UI";
import QualityBadge from "./QualityBadge";
import { Truck, Clock, CheckCircle } from "lucide-react";

function timeRemaining(iso) {
  const ms = new Date(iso).getTime() - Date.now();
  if (ms <= 0) return "Expiring…";
  const hrs = Math.floor(ms / 3_600_000);
  const mins = Math.floor((ms % 3_600_000) / 60_000);
  return hrs > 0 ? `${hrs}h ${mins}m left` : `${mins}m left`;
}

export default function MyClaims({ focusBatchId, onFocusConsumed }) {
  const { user } = useAuth();
  const [claims, setClaims] = useState([]);
  const [selected, setSelected] = useState(null);
  const [actualWeight, setActualWeight] = useState("");
  const [err, setErr] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(() => {
    // Backend-free: reads straight out of localStorage — expired claims
    // are auto-released back to the community shelf before this list is
    // built (Story 4.3-AC2), so a claim that timed out simply won't
    // appear here anymore. Swap for
    // API.get('/batches', { params: { status: 'CLAIMED', mine: true } })
    // once a real backend exists.
    setClaims(listBatches({ status: "CLAIMED", mine: true, recyclerUser: user }));
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!focusBatchId) return;
    const match = listBatches({ mine: true, recyclerUser: user }).find(
      (b) => b.id === focusBatchId
    );
    if (match) openCollect(match);
    onFocusConsumed?.();
  }, [focusBatchId, onFocusConsumed, user]);

  const openCollect = (batch) => {
    setSelected(batch);
    setActualWeight(String(batch.approx_weight_kg));
    setErr("");
  };

  const collect = async (e) => {
    e.preventDefault();
    setErr("");
    setSubmitting(true);
    try {
      // Story 4.3-AC1: records recycler + timestamp on collection.
      // Story 4.3-AC3: rejected server-side if this recycler didn't
      // claim the batch — the mock layer enforces this, not just the UI.
      markCollected(user, selected.id, { actual_weight_kg: actualWeight });
      setSelected(null);
      load();
    } catch ({ response }) {
      setErr(response?.data?.detail || "Could not update this batch.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6 fade-in">
      <h1 className="text-xl font-bold flex items-center gap-2">
        <Truck size={20} /> My Claimed Batches
      </h1>

      <Card>
        {claims.length === 0 ? (
          <Empty
            icon={Truck}
            title="No active claims"
            description="Claim a batch from the Community Shelf to see it here. Unclaimed pickups auto-release after 60 hours."
          />
        ) : (
          <Table
            columns={[
              { key: "ref_code", label: "Ref" },
              { key: "material_type", label: "Material" },
              { key: "approx_weight_kg", label: "Approx (kg)", render: (v) => v?.toFixed(1) },
              { key: "source_ward", label: "Ward" },
              {
                key: "quality_status",
                label: "Quality",
                render: (v) => <QualityBadge status={v} />,
              },
              {
                key: "claim_expires_at",
                label: "Pickup Window",
                render: (v) => (
                  <span className="inline-flex items-center gap-1 text-xs text-amber-700">
                    <Clock size={12} /> {timeRemaining(v)}
                  </span>
                ),
              },
              { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
            ]}
            rows={claims}
            onRowClick={openCollect}
          />
        )}
      </Card>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={`Confirm Pickup — ${selected?.ref_code}`}
      >
        {selected && (
          <form onSubmit={collect} className="space-y-4">
            {err && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{err}</div>}
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-400">Material:</span>{" "}
                <span className="font-medium">{selected.material_type}</span>
              </div>
              <div>
                <span className="text-gray-400">Ward:</span>{" "}
                <span className="font-medium">{selected.source_ward}</span>
              </div>
              <div>
                <span className="text-gray-400">Approx:</span>{" "}
                <span className="font-medium">{selected.approx_weight_kg} kg</span>
              </div>
              <div>
                <span className="text-gray-400">Quality:</span>{" "}
                <QualityBadge status={selected.quality_status} />
              </div>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Actual Weight Collected (kg)
              </label>
              <input
                type="number"
                step="0.1"
                min="0"
                required
                className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
                value={actualWeight}
                onChange={(e) => setActualWeight(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-recycler text-white py-2.5 rounded-input font-medium hover:bg-recycler/90 transition flex items-center justify-center gap-2 disabled:opacity-60"
            >
              <CheckCircle size={16} /> {submitting ? "Saving…" : "Mark as Collected"}
            </button>
          </form>
        )}
      </Modal>
    </div>
  );
}
