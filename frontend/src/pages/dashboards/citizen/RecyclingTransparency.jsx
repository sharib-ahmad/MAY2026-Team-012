import { useMemo } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card, Empty } from "../../../components/UI";
import { Recycle, Info } from "lucide-react";
import { getRecyclingSummary } from "../../../lib/mockCitizenData";

export default function RecyclingTransparency() {
  const { user } = useAuth();
  const summary = useMemo(() => getRecyclingSummary(user), [user]);

  return (
    <div className="space-y-6 fade-in max-w-3xl mx-auto">
      <div>
        <h1 className="text-xl font-bold">Recycling Transparency</h1>
        <p className="text-sm text-gray-500 mt-1">
          {summary.zone_name} · {summary.month_label}
        </p>
      </div>

      {/* AC3: honest labeling — this is manually entered municipal data,
          not an automated or real-time verification. */}
      <div className="flex items-start gap-2 bg-amber-50 text-amber-800 text-xs rounded-input p-3">
        <Info size={14} className="mt-0.5 shrink-0" />
        <span>
          As reported by municipal records — recycling data in this MVP is entered manually by
          municipal staff and is not yet independently verified.
        </span>
      </div>

      {summary.entries.length === 0 ? (
        // AC2: explicit empty state, distinct from a blank/zero-looking value.
        <Card>
          <Empty
            icon={Recycle}
            title="No recycling activity recorded this month"
            description="Nothing has been logged as collected or dispatched from your zone yet this month."
          />
        </Card>
      ) : (
        <div className="space-y-3">
          {summary.entries.map((e) => (
            <Card key={e.material_type}>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <p className="font-medium text-sm">{e.material_type}</p>
                  <p className="text-xs text-gray-500 mt-1">Dispatched to {e.facility}</p>
                </div>
                <div className="text-right shrink-0">
                  <p className="font-semibold">{e.approx_volume_kg.toFixed(1)} kg</p>
                  <p className="text-xs text-gray-400">
                    {new Date(e.dispatch_date).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
