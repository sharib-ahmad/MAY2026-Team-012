import { StatusPill } from "../../../components/UI";

export function formatBatchDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function BatchDetailPanel({ batch }) {
  if (!batch) return null;

  return (
    <div className="space-y-4 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <p className="text-xs text-gray-400 uppercase">Status</p>
          <StatusPill status={batch.status} />
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase">Category</p>
          <p className="font-medium">{batch.waste_category}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase">Weight</p>
          <p className="font-medium">{Number(batch.declared_weight).toFixed(1)} kg</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase">Ward</p>
          <p className="font-medium">{batch.zone_name || batch.zone_code || "—"}</p>
        </div>
        <div>
          <p className="text-xs text-gray-400 uppercase">Pickups</p>
          <p className="font-medium">{batch.pickup_count}</p>
        </div>
      </div>

      <div>
        <p className="text-xs text-gray-400 uppercase mb-2">Pickup references</p>
        <div className="flex flex-wrap gap-1.5">
          {(batch.pickup_ref_codes || []).map((ref) => (
            <span
              key={ref}
              className="inline-flex rounded-full bg-[#FBEAE0] px-2 py-0.5 text-xs font-mono text-[#C4611A]"
            >
              {ref}
            </span>
          ))}
        </div>
      </div>

      <dl className="grid grid-cols-2 gap-2 text-xs text-gray-500">
        {batch.assigned_at && (
          <>
            <dt>Assigned</dt>
            <dd>{formatBatchDate(batch.assigned_at)}</dd>
          </>
        )}
        {batch.collected_at && (
          <>
            <dt>Collected</dt>
            <dd>{formatBatchDate(batch.collected_at)}</dd>
          </>
        )}
        {batch.processed_at && (
          <>
            <dt>Processed</dt>
            <dd>{formatBatchDate(batch.processed_at)}</dd>
          </>
        )}
      </dl>
    </div>
  );
}
