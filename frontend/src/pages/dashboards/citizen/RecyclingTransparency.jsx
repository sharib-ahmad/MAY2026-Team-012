import { useEffect, useState } from "react";
import { Card, Empty, StatusPill, Table, StatCard } from "../../../components/UI";
import {
  Recycle,
  Search,
  ArrowLeft,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Leaf,
  Landmark,
  Award,
  TrendingUp,
  Package,
  MapPin,
} from "lucide-react";
import { listUserPickups, getUserPickupTracking, getUserImpact } from "../../../lib/api";
import { useAuth } from "../../../context/AuthContext";

const WARD_MAP = {
  "W-01": "Gomti Nagar",
  "W-02": "Hazratganj",
  "W-03": "Alambagh",
  "W-04": "Indira Nagar",
  "W-05": "Chowk",
};

export default function RecyclingTransparency() {
  const { user } = useAuth();
  const [pickups, setPickups] = useState([]);
  const [searchRef, setSearchRef] = useState("");
  const [selectedPickup, setSelectedPickup] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [impact, setImpact] = useState(null);

  useEffect(() => {
    listUserPickups()
      .then(({ pickups: items }) => setPickups(items || []))
      .catch(() => setPickups([]));
    getUserImpact()
      .then(setImpact)
      .catch(() => {});
  }, []);

  const handleTrack = async (pickup) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getUserPickupTracking(pickup.id);
      setTracking(data);
      setSelectedPickup(pickup);
    } catch {
      setError("Unable to load pickup tracking. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    const query = searchRef.trim().toUpperCase();
    if (!query) return;

    const matched = pickups.find((p) => p.ref_code.toUpperCase() === query);
    if (matched) {
      handleTrack(matched);
    } else {
      setError(`No pickup found with REF ID "${query}". Please check the ID and try again.`);
      setSelectedPickup(null);
      setTracking(null);
    }
  };

  const handleClear = () => {
    setSelectedPickup(null);
    setTracking(null);
    setSearchRef("");
    setError(null);
  };

  const pickupCols = [
    {
      key: "ref_code",
      label: "Ref ID",
      render: (v) => <span className="font-mono text-xs font-semibold">{v}</span>,
    },
    { key: "category", label: "Category" },
    {
      key: "scheduled_date",
      label: "Scheduled Date",
      render: (v) => v && new Date(v).toLocaleDateString(),
    },
    {
      key: "status",
      label: "Status",
      render: (v) => <StatusPill status={v} />,
    },
    {
      key: "actions",
      label: "Traceability",
      render: (_, row) => (
        <button
          type="button"
          onClick={() => handleTrack(row)}
          className="text-xs font-semibold text-primary hover:text-primary-dark hover:underline"
        >
          Track &rarr;
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6 fade-in max-w-4xl mx-auto">
      {/* Title */}
      <div className="flex items-center justify-between border-b border-gray-100 pb-4">
        <div>
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Recycle className="text-primary" size={24} />
            Recycling Transparency
          </h1>
          <p className="text-xs text-gray-500 mt-1">
            Trace your waste custody and verified recycling milestones in real-time.
          </p>
        </div>
        {selectedPickup && (
          <button
            type="button"
            onClick={handleClear}
            className="flex items-center gap-1.5 text-xs text-primary hover:text-primary/80 font-medium"
          >
            <ArrowLeft size={14} /> Back to Search
          </button>
        )}
      </div>

      {/* Zone Scope Notice Banner */}
      {(() => {
        const wardCode = user?.ward_code || "W-01";
        const zoneName = user?.zone_name || WARD_MAP[wardCode] || "Gomti Nagar";
        const zoneLabel = `${zoneName} (Ward ${wardCode})`;

        return (
          <div className="bg-emerald-500/10 border border-emerald-500/30 rounded-2xl p-4 flex items-start gap-3 shadow-sm">
            <MapPin className="text-emerald-700 shrink-0 mt-0.5" size={22} />
            <div className="text-xs space-y-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-bold text-gray-900 text-sm">
                  Operational Scope:{" "}
                  <span className="text-emerald-800 font-extrabold">{zoneLabel}</span>
                </span>
                <span className="bg-emerald-600 text-white text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                  Zone Operations Data
                </span>
              </div>
              <p className="text-gray-700 leading-relaxed font-medium">
                Notice: The recycling milestones, waste custody timelines, and batch metrics below
                reflect aggregate operations for{" "}
                <strong className="text-gray-900">{zoneLabel}</strong>, not individual household
                totals.
              </p>
            </div>
          </div>
        );
      })()}

      {/* Impact stats top bar — mirrors the Impact page */}
      {impact && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Kg Diverted"
            value={impact.total_kg_diverted.toFixed(1)}
            icon={Leaf}
            color="text-green-600"
          />
          <StatCard
            label="CO₂ Saved (kg)"
            value={impact.co2_saved_kg.toFixed(1)}
            icon={Award}
            color="text-accent"
          />
          <StatCard
            label="Credits Balance"
            value={impact.credits_balance.toFixed(1)}
            icon={TrendingUp}
            color="text-manager"
          />
          <StatCard
            label="Total Pickups"
            value={impact.total_pickups}
            icon={Package}
            color="text-primary"
          />
        </div>
      )}

      {/* Tracking Search Interface */}
      {!selectedPickup ? (
        <div className="space-y-6">
          {/* Tracking Input Card */}
          <Card className="p-6">
            <form onSubmit={handleSearchSubmit} className="space-y-3">
              <label htmlFor="ref-search" className="block text-sm font-semibold text-gray-700">
                Track a Pickup by Reference ID
              </label>
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Search
                    size={16}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                  />
                  <input
                    id="ref-search"
                    type="text"
                    value={searchRef}
                    onChange={(e) => setSearchRef(e.target.value)}
                    placeholder="Enter Ref ID (e.g. COL-DAILY-0B308ECB)"
                    className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-4 py-2.5 text-sm text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
                  />
                </div>
                <button
                  type="submit"
                  disabled={loading || !searchRef.trim()}
                  className="bg-primary hover:bg-primary/95 text-white px-6 py-2.5 rounded-full text-sm font-medium transition shadow-sm disabled:opacity-60"
                >
                  {loading ? "Searching..." : "Track"}
                </button>
              </div>
              {error && (
                <p className="text-xs text-red-600 flex items-center gap-1 mt-1">
                  <AlertTriangle size={12} /> {error}
                </p>
              )}
            </form>
          </Card>

          {/* Educational Content related to recycling transparency */}
          <div className="grid gap-6 md:grid-cols-3">
            <div className="bg-[#3F5426]/5 rounded-2xl p-5 border border-[#3F5426]/10 space-y-2">
              <ShieldCheck className="text-[#3F5426]" size={20} />
              <h3 className="font-semibold text-sm text-gray-800">Verified Doorstep Weight</h3>
              <p className="text-xs text-gray-600 leading-relaxed">
                Every daily stop is pre-assigned a default weight of 3kg. The collector weighs and
                records the actual weight upon collection, which is instantly logged to prevent
                custody tampering.
              </p>
            </div>
            <div className="bg-amber-500/5 rounded-2xl p-5 border border-amber-500/10 space-y-2">
              <Landmark className="text-amber-600" size={20} />
              <h3 className="font-semibold text-sm text-gray-800">Municipal Batch Pooling</h3>
              <p className="text-xs text-gray-600 leading-relaxed">
                To guarantee sustainable processing, collected waste is pooled at the ward depot.
                When a category's waste exceeds 30kg, it is auto-batched and dispatched to certified
                recycling facilities.
              </p>
            </div>
            <div className="bg-primary/5 rounded-2xl p-5 border border-primary/10 space-y-2">
              <Leaf className="text-primary" size={20} />
              <h3 className="font-semibold text-sm text-gray-800">Eco-Credit Lifecycle</h3>
              <p className="text-xs text-gray-600 leading-relaxed">
                Unlike traditional waste platforms, eco-credits and CO2 points are only finalized
                and awarded to your ledger once the recycler verifies and processes the material
                batch.
              </p>
            </div>
          </div>

          {/* Recent Pickups List */}
          <Card title="Select a pickup to view detailed traceability">
            {pickups.length === 0 ? (
              <Empty
                icon={Recycle}
                title="No pickups recorded yet"
                description="Your pickup timeline and recycling verification will appear here once scheduled."
              />
            ) : (
              <Table columns={pickupCols} rows={pickups.slice(0, 10)} />
            )}
          </Card>
        </div>
      ) : (
        /* Detailed Tracking Timeline View */
        <Card className="p-6">
          <div className="space-y-6">
            <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between border-b border-gray-100 pb-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-400">
                  Tracking Reference
                </p>
                <h2 className="text-lg font-bold text-gray-800">{selectedPickup.ref_code}</h2>
              </div>
              <div className="flex gap-4 text-xs md:text-right">
                <div>
                  <p className="text-gray-400 font-medium">Category</p>
                  <p className="font-semibold text-gray-700">{selectedPickup.category}</p>
                </div>
                <div>
                  <p className="text-gray-400 font-medium">Recorded Weight</p>
                  <p className="font-semibold text-gray-700">
                    {selectedPickup.actual_weight !== null
                      ? `${selectedPickup.actual_weight} kg`
                      : "Pending weighing"}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 font-medium">Current Status</p>
                  <div className="mt-0.5">
                    <StatusPill status={selectedPickup.status} />
                  </div>
                </div>
              </div>
            </div>

            {/* Timeline Graphic */}
            <div className="space-y-4 max-w-xl">
              <h3 className="text-sm font-semibold text-gray-700">Recycling Custody Milestones</h3>
              <div className="space-y-4">
                {tracking && tracking.timeline && tracking.timeline.length > 0 ? (
                  tracking.timeline.map((evt, i) => {
                    const isLast = i === tracking.timeline.length - 1;
                    return (
                      <div key={evt.stage} className="flex gap-4">
                        <div className="flex flex-col items-center">
                          <div
                            className={`w-7 h-7 rounded-full flex items-center justify-center border ${
                              isLast
                                ? "bg-primary border-primary text-white shadow-sm"
                                : "bg-success border-success text-white"
                            }`}
                          >
                            {isLast && selectedPickup.status !== "COLLECTED" ? (
                              <Clock size={13} />
                            ) : (
                              <CheckCircle2 size={13} />
                            )}
                          </div>
                          {!isLast && <div className="w-0.5 flex-1 bg-gray-200 my-1" />}
                        </div>
                        <div className="pb-3 leading-relaxed">
                          <p className="font-semibold text-sm text-gray-800">{evt.label}</p>
                          <p className="text-xs text-gray-400 mt-0.5">
                            {new Date(evt.at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="flex gap-3 text-sm text-gray-500">
                    <Clock size={16} className="mt-0.5 text-primary animate-pulse" />
                    <p>Fetching latest routing logs...</p>
                  </div>
                )}
              </div>
            </div>

            {/* Extra Info note on transparency */}
            <div className="bg-gray-50 rounded-2xl p-4 border border-gray-100 text-xs text-gray-500 leading-relaxed max-w-2xl">
              <p className="font-semibold text-gray-600 mb-1">Honest Labeling Notice</p>
              As per the transparency guidelines, the recycling facility dispatch and material
              claiming operations in this platform version are recorded manually by municipal
              officers and verified recyclers. Independent automated sensor validation is planned
              for future releases.
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
