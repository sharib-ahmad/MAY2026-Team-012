import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { listBatches } from "../../../lib/mockRecyclerData";
import { Card, StatCard, StatusPill, Table, Modal } from "../../../components/UI";
import QualityBadge from "./QualityBadge";
import { FileBarChart, Package, Scale, TrendingUp } from "lucide-react";

export default function Reports({ focusBatchId, onFocusConsumed }) {
  const { user } = useAuth();
  const [selected, setSelected] = useState(null);
  const collected = useMemo(
    () => listBatches({ status: "COLLECTED", mine: true, recyclerUser: user }),
    [user]
  );

  const focusedBatch = useMemo(() => {
    if (!focusBatchId) return null;
    return collected.find((b) => b.id === focusBatchId) ?? null;
  }, [focusBatchId, collected]);

  useEffect(() => {
    if (!focusBatchId) return;
    onFocusConsumed?.();
  }, [focusBatchId, onFocusConsumed]);

  const totalApprox = collected.reduce((s, b) => s + (b.approx_weight_kg || 0), 0);
  const totalActual = collected.reduce(
    (s, b) => s + (b.actual_weight_kg ?? b.approx_weight_kg ?? 0),
    0
  );
  const variance = totalActual - totalApprox;

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6 fade-in">
      <h1 className="text-xl font-bold flex items-center gap-2">
        <FileBarChart size={20} /> Collection History
      </h1>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Batches Collected"
          value={collected.length}
          icon={Package}
          color="text-recycler"
        />
        <StatCard
          label="Approx. Reported (kg)"
          value={totalApprox.toFixed(1)}
          icon={Scale}
          color="text-accent"
        />
        <StatCard
          label="Actual Weighed (kg)"
          value={totalActual.toFixed(1)}
          icon={Scale}
          color="text-success"
        />
        <StatCard
          label="Variance (kg)"
          value={variance.toFixed(1)}
          icon={TrendingUp}
          color={variance < 0 ? "text-warn" : "text-success"}
        />
      </div>

      <Card title="My Collected Batches">
        {collected.length === 0 ? (
          <p className="text-gray-400">
            No batches collected yet — claim one from the Marketplace to get started.
          </p>
        ) : (
          <Table
            columns={[
              { key: "ref_code", label: "Ref" },
              { key: "material_type", label: "Material" },
              { key: "source_ward", label: "Ward" },
              { key: "approx_weight_kg", label: "Approx (kg)", render: (v) => v?.toFixed(1) },
              {
                key: "actual_weight_kg",
                label: "Actual (kg)",
                render: (v) => v?.toFixed(1) ?? "—",
              },
              {
                key: "quality_status",
                label: "Quality",
                render: (v) => <QualityBadge status={v} />,
              },
              {
                key: "collected_at",
                label: "Collected",
                render: (v) => v && new Date(v).toLocaleDateString(),
              },
              { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
            ]}
            rows={collected}
            onRowClick={setSelected}
          />
        )}
      </Card>

      <Modal
        open={!!(selected ?? focusedBatch)}
        onClose={() => setSelected(null)}
        title={`Batch ${(selected ?? focusedBatch)?.ref_code}`}
      >
        {(selected ?? focusedBatch) && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-400">Material:</span>{" "}
                <span className="font-medium">{(selected ?? focusedBatch).material_type}</span>
              </div>
              <div>
                <span className="text-gray-400">Ward:</span>{" "}
                <span className="font-medium">{(selected ?? focusedBatch).source_ward}</span>
              </div>
              <div>
                <span className="text-gray-400">Approx Weight:</span>{" "}
                <span className="font-medium">
                  {(selected ?? focusedBatch).approx_weight_kg} kg
                </span>
              </div>
              <div>
                <span className="text-gray-400">Actual Weight:</span>{" "}
                <span className="font-medium">
                  {(selected ?? focusedBatch).actual_weight_kg ?? "—"} kg
                </span>
              </div>
              <div>
                <span className="text-gray-400">Quality:</span>{" "}
                <QualityBadge status={(selected ?? focusedBatch).quality_status} />
              </div>
              <div>
                <span className="text-gray-400">Status:</span>{" "}
                <StatusPill status={(selected ?? focusedBatch).status} />
              </div>
            </div>
            <p className="text-xs text-gray-400">
              Collected by {(selected ?? focusedBatch).collected_by?.recycler_name}
              {(selected ?? focusedBatch).collected_at &&
                ` on ${new Date((selected ?? focusedBatch).collected_at).toLocaleDateString()}`}
              .
            </p>
          </div>
        )}
      </Modal>
    </div>
  );
}
