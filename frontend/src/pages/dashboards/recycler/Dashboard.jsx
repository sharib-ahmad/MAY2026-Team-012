import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Cog, Inbox } from "lucide-react";
import { Card } from "../../../components/UI";
import { getRecyclerBatches } from "../../../lib/api";

function SummaryCard({ icon: Icon, label, value, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="rounded-card bg-white p-5 text-left shadow-soft transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <Icon size={20} className="text-[#C4611A]" />
      <p className="mt-3 text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </button>
  );
}

export default function Dashboard({ onOpenBatch }) {
  const [batches, setBatches] = useState([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setBatches(await getRecyclerBatches());
    } catch (err) {
      setError(err.response?.data?.error?.message || "Unable to load your batches.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const assigned = batches.filter((batch) => batch.status === "ASSIGNED");
  const processing = batches.filter((batch) => batch.status === "PROCESSING");
  const processed = batches.filter((batch) => batch.status === "PROCESSED");

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-4 sm:p-6 fade-in">
      <div>
        <p className="text-sm font-semibold text-[#C4611A]">Recycler workspace</p>
        <h1 className="mt-1 text-2xl font-bold text-gray-900">Batch dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Review assignments and keep material moving.</p>
      </div>
      {error && <p className="rounded-input bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      <div className="grid gap-4 sm:grid-cols-3">
        <SummaryCard
          icon={Inbox}
          label="Awaiting review"
          value={assigned.length}
          onClick={() => onOpenBatch?.("assigned-batches")}
        />
        <SummaryCard
          icon={Cog}
          label="In processing"
          value={processing.length}
          onClick={() => onOpenBatch?.("batch-processing")}
        />
        <SummaryCard
          icon={CheckCircle2}
          label="Processed batches"
          value={processed.length}
          onClick={() => onOpenBatch?.("processed-batches")}
        />
      </div>
      <Card title="Latest batch activity">
        {batches.length === 0 ? (
          <p className="py-6 text-sm text-gray-500">No batches have been assigned yet.</p>
        ) : (
          <div className="space-y-3">
            {batches.slice(0, 5).map((batch) => (
              <button
                key={batch.id}
                type="button"
                onClick={() =>
                  onOpenBatch?.(
                    batch.status === "PROCESSED" ? "processed-batches" : "assigned-batches",
                    batch.id
                  )
                }
                className="flex w-full items-center justify-between rounded-input border border-gray-100 px-3 py-2 text-left hover:bg-gray-50"
              >
                <span>
                  <span className="font-mono text-sm font-semibold">{batch.ref_code}</span>
                  <span className="ml-2 text-sm text-gray-500">{batch.waste_category}</span>
                </span>
                <span className="text-sm font-semibold text-[#C4611A]">
                  {batch.status.replace(/_/g, " ")}
                </span>
              </button>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
