import { useEffect, useState, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import {
  listBatches,
  claimBatch,
  MATERIAL_OPTIONS,
  WARD_OPTIONS,
} from "../../../lib/mockRecyclerData";
import { Card, StatusPill, Modal, Table, Empty } from "../../../components/UI";
import QualityBadge from "./QualityBadge";
import { Package, Info, ShieldAlert } from "lucide-react";

const STATUS_FILTERS = [
  { value: "AVAILABLE", label: "Available" },
  { value: "CLAIMED", label: "Claimed" },
  { value: "COLLECTED", label: "Collected" },
  { value: "", label: "All statuses" },
];

export default function CommunityShelf({ focusBatchId, onFocusConsumed }) {
  const { user } = useAuth();
  const [filters, setFilters] = useState({
    material_type: "",
    source_ward: "",
    status: "AVAILABLE",
  });
  const [batches, setBatches] = useState([]);
  const [selected, setSelected] = useState(null);
  const [claiming, setClaiming] = useState(false);
  const [claimErr, setClaimErr] = useState("");

  const load = useCallback(() => {
    // Backend-free: reads the shared community shelf pool out of
    // localStorage (see lib/mockRecyclerData.js). Swap for
    // API.get('/batches', { params: filters }) once a real backend exists.
    setBatches(
      listBatches({
        material_type: filters.material_type || undefined,
        source_ward: filters.source_ward || undefined,
        status: filters.status || undefined,
      })
    );
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (!focusBatchId) return;
    // Look this batch up unfiltered — it may not match the currently
    // selected community shelf filters — then hand focus back once opened.
    const match = listBatches({}).find((b) => b.id === focusBatchId);
    if (match) setSelected(match);
    onFocusConsumed?.();
  }, [focusBatchId, onFocusConsumed]);

  const claim = async (batch) => {
    setClaiming(true);
    setClaimErr("");
    try {
      // Story 4.1-AC2: the mock layer re-validates against the freshest
      // status right before writing, so a race with another recycler
      // surfaces here as a rejection rather than a silent double-claim.
      claimBatch(user, batch.id);
      setSelected(null);
      load();
    } catch ({ response }) {
      setClaimErr(
        response?.data?.detail || "Could not claim this batch — it may have just been taken."
      );
      load(); // refresh so the stale "Available" row updates immediately
    } finally {
      setClaiming(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6 fade-in">
      <div>
        <h1 className="text-xl font-bold">Batch Community Shelf</h1>
        {/* Story 4.1-AC3: honest labeling — this is manually entered municipal
            data, not an automated or recycler-verified feed. */}
        <p className="mt-1 flex items-start gap-1.5 text-xs text-gray-500">
          <Info size={13} className="mt-0.5 shrink-0" />
          Batch details are municipally reported — not yet recycler-verified.
        </p>
      </div>

      <Card>
        <div className="flex flex-wrap gap-3 mb-4">
          <select
            value={filters.material_type}
            onChange={(e) => setFilters((f) => ({ ...f, material_type: e.target.value }))}
            className="border border-gray-200 rounded-input px-3 py-2 text-sm"
          >
            <option value="">All materials</option>
            {MATERIAL_OPTIONS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <select
            value={filters.source_ward}
            onChange={(e) => setFilters((f) => ({ ...f, source_ward: e.target.value }))}
            className="border border-gray-200 rounded-input px-3 py-2 text-sm"
          >
            <option value="">All wards</option>
            {WARD_OPTIONS.map((w) => (
              <option key={w} value={w}>
                {w}
              </option>
            ))}
          </select>
          <select
            value={filters.status}
            onChange={(e) => setFilters((f) => ({ ...f, status: e.target.value }))}
            className="border border-gray-200 rounded-input px-3 py-2 text-sm"
          >
            {STATUS_FILTERS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>

        {claimErr && (
          <div className="mb-4 flex items-center gap-2 bg-red-50 text-red-700 text-sm p-3 rounded-input">
            <ShieldAlert size={15} /> {claimErr}
          </div>
        )}

        {batches.length === 0 ? (
          <Empty
            icon={Package}
            title="No matching batches"
            description="Try a different material, ward, or status filter"
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
                key: "drop_date",
                label: "Dropped",
                render: (v) => v && new Date(v).toLocaleDateString(),
              },
              { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
            ]}
            rows={batches}
            onRowClick={setSelected}
          />
        )}
      </Card>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={`Batch ${selected?.ref_code}`}
      >
        {selected && (
          <div className="space-y-4">
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
                <span className="text-gray-400">Approx Weight:</span>{" "}
                <span className="font-medium">{selected.approx_weight_kg} kg</span>
              </div>
              <div>
                <span className="text-gray-400">Dropped:</span>{" "}
                <span className="font-medium">
                  {new Date(selected.drop_date).toLocaleDateString()}
                </span>
              </div>
              <div>
                <span className="text-gray-400">Status:</span>{" "}
                <StatusPill status={selected.status} />
              </div>
              <div>
                <span className="text-gray-400">Quality:</span>{" "}
                <QualityBadge status={selected.quality_status} />
              </div>
            </div>

            {/* Story 4.2-AC1: who assigned the quality tag, explicitly recorded. */}
            <p className="text-xs text-gray-400">
              Quality assessed by{" "}
              {selected.quality_assigned_by?.role === "OFFICER"
                ? "Municipal Officer"
                : "Collection Worker"}{" "}
              {selected.quality_assigned_by?.name}.
            </p>

            {/* Story 4.2-AC3: contamination note is mandatory for Unsafe batches. */}
            {selected.contamination_note && (
              <div
                className={`text-sm p-3 rounded-input ${selected.quality_status === "UNSAFE" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-800"}`}
              >
                {selected.contamination_note}
              </div>
            )}

            {selected.status === "CLAIMED" && (
              <p className="text-sm text-gray-500">
                Claimed by {selected.claimed_by?.recycler_name}
                {selected.claim_expires_at &&
                  ` · pickup window ends ${new Date(selected.claim_expires_at).toLocaleString()}`}
              </p>
            )}
            {selected.status === "COLLECTED" && (
              <p className="text-sm text-gray-500">
                Collected by {selected.collected_by?.recycler_name} on{" "}
                {new Date(selected.collected_at).toLocaleDateString()}
                {selected.actual_weight_kg != null &&
                  ` · ${selected.actual_weight_kg} kg confirmed`}
              </p>
            )}

            {selected.status === "AVAILABLE" && (
              <button
                type="button"
                disabled={claiming}
                onClick={() => claim(selected)}
                className="w-full bg-recycler text-white py-2.5 rounded-input font-medium hover:bg-recycler/90 transition disabled:opacity-60"
              >
                {claiming ? "Claiming…" : "Claim This Batch"}
              </button>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
}
