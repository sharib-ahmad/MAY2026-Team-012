import { useEffect, useState, useCallback } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card, StatusPill, Modal } from "../../../components/UI";
import {
  MapPin,
  Navigation,
  CheckCircle,
  Undo2,
  Bell,
  ShieldCheck,
  CheckCircle2,
  Truck,
  Recycle,
  Weight,
  Flag,
  Clock,
  BadgeCheck,
} from "lucide-react";
import { usePolling } from "../../../hooks/usePolling";
import {
  getMyRoute,
  collectStop,
  undoCollectStop,
  delayStop,
  flagMixedWaste,
  markStopClean,
} from "../../../lib/mockCollectorData";

// Story 1.5-AC1: a standard set of reasons plus a mandatory-free-text "Other".
const DELAY_TYPES = [
  {
    value: "RUNNING_LATE",
    label: "Running Late",
    template: "I will arrive approximately {min} minutes late.",
  },
  { value: "TRAFFIC_DELAY", label: "Traffic Delay", template: "Heavy traffic is causing a delay." },
  {
    value: "VEHICLE_ISSUE",
    label: "Vehicle Issue",
    template: "Vehicle issue. Your pickup has been delayed.",
  },
  {
    value: "UNABLE_TO_REACH",
    label: "Unable to Reach",
    template: "I could not locate your address.",
  },
  {
    value: "RESIDENT_NOT_AVAILABLE",
    label: "Resident Not Available",
    template: "Resident was not available at the location.",
  },
  { value: "CUSTOM", label: "Other", template: "" },
];

const DELAY_MIN_LEN = 5;
const DELAY_MAX_LEN = 200;

const ISSUE_TYPES = [
  { value: "CONTAMINATION", label: "Mixed / Contaminated Waste" },
  { value: "WRONG_ITEM_COLLECTED", label: "Not Properly Segregated" },
  { value: "OTHER", label: "Other Unsafe Condition" },
];

// Duty hours aren't part of the route payload yet — surfaced here as a
// static shift window until the backend/mock exposes a real value.
const DUTY_HOURS = "08:00 – 17:00";

export default function CollectorRoutes() {
  const { user } = useAuth();
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(true);
  const [collectorPos, setCollectorPos] = useState(null);

  const [delayTarget, setDelayTarget] = useState(null);
  const [delayType, setDelayType] = useState("RUNNING_LATE");
  const [delayComment, setDelayComment] = useState("");
  const [delayCommentTouched, setDelayCommentTouched] = useState(false);
  const [delayMinutes, setDelayMinutes] = useState("20");
  const [delayErr, setDelayErr] = useState("");
  const [delayOk, setDelayOk] = useState("");
  const [delaySending, setDelaySending] = useState(false);

  const [issueTarget, setIssueTarget] = useState(null);
  const [issueForm, setIssueForm] = useState({
    issue_type: "CONTAMINATION",
    description: "",
    severity: "ROUTINE",
  });
  const [issueErr, setIssueErr] = useState("");
  const [issueOk, setIssueOk] = useState("");
  const [issueSending, setIssueSending] = useState(false);

  const [actionErr, setActionErr] = useState("");

  const load = useCallback(() => {
    if (!user) return;
    try {
      // Backend-free: reads/writes the collector's route straight out of
      // localStorage (see lib/mockCollectorData.js). Swap for
      // API.get('/my-route', { params }) once a real backend exists.
      const schedule = getMyRoute(user);
      const transformedRoute = {
        ordered_pickups: schedule.stops.map((stop) => ({
          id: stop.id,
          ref_code: `DP-${stop.pickup_order}`,
          status: stop.status,
          order: stop.pickup_order,
          resident_name: stop.resident_name,
          category: stop.category || "Daily Waste",
          estimated_weight: stop.estimated_weight || 5,
          pickup_address: stop.address,
          zone_name: schedule.zone_name,
          time_slot: "Morning (8-11)",
          pickup_latitude: stop.latitude,
          pickup_longitude: stop.longitude,
          collected_at: stop.collected_at,
          navigate_url: `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${collectorPos?.lat || 26.1445},${collectorPos?.lon || 91.7362};${stop.latitude},${stop.longitude}`,
        })),
        total_distance_km: 0,
        estimated_duration_min: schedule.total_stops * 10,
        route_geometry: [],
        pickup_count: schedule.total_stops,
        zone_name: schedule.zone_name,
      };
      setRoute(transformedRoute);
    } catch (err) {
      console.error("Failed to load route:", err);
    }
    setLoading(false);
  }, [collectorPos, user]);

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (p) => setCollectorPos({ lat: p.coords.latitude, lon: p.coords.longitude }),
        () => window.setTimeout(load, 0),
        { enableHighAccuracy: true }
      );
    } else {
      window.setTimeout(load, 0);
    }
  }, [load]);

  useEffect(() => {
    if (!collectorPos) return;
    const id = window.setTimeout(load, 0);
    return () => window.clearTimeout(id);
  }, [collectorPos, load]);
  usePolling(load, 30000);

  // Story 1.4-AC2/AC6
  const handleCollect = (id) => {
    setActionErr("");
    try {
      collectStop(user, id);
      load();
    } catch (err) {
      setActionErr(err.response?.data?.detail || "Failed to collect stop");
    }
  };

  // Story 1.4-AC3: same-day undo for a mis-tap.
  const handleUndo = (id) => {
    setActionErr("");
    try {
      undoCollectStop(user, id);
      load();
    } catch (err) {
      setActionErr(err.response?.data?.detail || "Failed to undo collection");
    }
  };

  // Story 3.2-AC4: explicit "checked, no issue found" — distinct from a
  // point nobody has looked at yet.
  const handleMarkClean = (id) => {
    setActionErr("");
    try {
      markStopClean(user, id);
      load();
    } catch (err) {
      setActionErr(err.response?.data?.detail || "Failed to record check");
    }
  };

  const openDelay = (pickup) => {
    const t = DELAY_TYPES.find((d) => d.value === "RUNNING_LATE");
    setDelayTarget(pickup);
    setDelayType("RUNNING_LATE");
    setDelayComment(t?.template.replace("{min}", delayMinutes) || "");
    setDelayCommentTouched(false);
    setDelayErr("");
    setDelayOk("");
  };

  const openIssue = (pickup) => {
    setIssueTarget(pickup);
    setIssueForm({ issue_type: "CONTAMINATION", description: "", severity: "ROUTINE" });
    setIssueErr("");
    setIssueOk("");
  };

  // Story 1.5-AC2: 5–200 character message; Story 1.5-AC4: "Other" cannot
  // submit with no text (covered by the same min-length check).
  const sendDelay = async (e) => {
    e.preventDefault();
    if (!delayTarget || delaySending) return;
    const trimmed = delayComment.trim();
    if (trimmed.length < DELAY_MIN_LEN || trimmed.length > DELAY_MAX_LEN) {
      setDelayErr(`Message must be between ${DELAY_MIN_LEN} and ${DELAY_MAX_LEN} characters.`);
      return;
    }
    setDelayErr("");
    setDelayOk("");
    setDelaySending(true);
    try {
      // Minutes only make sense for "Running Late", and guard against a
      // non-numeric value producing NaN.
      const parsedMinutes = parseInt(delayMinutes, 10);
      const estimatedMinutes =
        delayType === "RUNNING_LATE" && !Number.isNaN(parsedMinutes) ? parsedMinutes : null;

      delayStop(user, delayTarget.id, {
        delay_type: delayType,
        comment: trimmed,
        estimated_delay_minutes: estimatedMinutes,
      });
      setDelayOk(`Notification sent to ${delayTarget.resident_name || "resident"}.`);
      setTimeout(() => setDelayTarget(null), 1200);
      load();
    } catch (err) {
      setDelayErr(err.response?.data?.detail || err.message || "Failed to send notification");
    }
    setDelaySending(false);
  };

  // Story 3.2-AC2: severity must be exactly Routine or Hazardous.
  const submitIssue = async (e) => {
    e.preventDefault();
    if (!issueTarget || issueSending) return;
    if (issueForm.description.trim().length < 10) {
      setIssueErr("Description must be at least 10 characters.");
      return;
    }
    setIssueErr("");
    setIssueOk("");
    setIssueSending(true);
    try {
      flagMixedWaste(user, issueTarget.id, {
        issue_type: issueForm.issue_type,
        description: issueForm.description.trim(),
        severity: issueForm.severity,
      });
      setIssueOk("Flag recorded. A manager will review it.");
      setTimeout(() => setIssueTarget(null), 1500);
      load();
    } catch (err) {
      setIssueErr(err.response?.data?.detail || "Failed to record flag");
    }
    setIssueSending(false);
  };

  // Calculate progress statistics
  const pickups = route?.ordered_pickups || [];
  const completedCount = pickups.filter(
    (p) => p.status === "COLLECTED" || p.status === "VERIFIED" || p.status === "CREDITED"
  ).length;
  const pendingCount = pickups.filter(
    (p) => p.status === "PENDING" || p.status === "ASSIGNED" || p.status === "IN_PROGRESS"
  ).length;
  const flaggedCount = pickups.filter((p) => p.status === "FLAGGED").length;
  const completionPercentage =
    route?.pickup_count > 0 ? Math.round((completedCount / route.pickup_count) * 100) : 0;
  const totalLoadKg = pickups.reduce((sum, p) => sum + (p.estimated_weight || 0), 0);
  const wetRecycStops = pickups.filter((p) => p.category && p.category !== "Daily Waste").length;
  const today = new Date();
  const isToday = (iso) => {
    if (!iso) return false;
    const d = new Date(iso);
    return (
      d.getFullYear() === today.getFullYear() &&
      d.getMonth() === today.getMonth() &&
      d.getDate() === today.getDate()
    );
  };

  return (
    <div className="space-y-8 fade-in">
      {/* Section I — Field Operations */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.2em] text-[#2947A3]/60 font-semibold uppercase">
            Section I · Field Operations
          </p>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[#1F3259] mt-1">
            Today&apos;s Collection Flow
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Your daily pickup schedule in sequence — updates are auto-logged to the municipal
            registry.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded-full border border-[#BFDBFE] bg-[#EFF6FF] text-[#1D4ED8] px-3 py-1 text-xs font-medium">
          <ShieldCheck size={13} /> Verified by Government of Uttar Pradesh
        </span>
      </div>

      {actionErr && (
        <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{actionErr}</div>
      )}

      {route && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard
            accent="#2947A3"
            icon={<Truck size={16} />}
            label="Total Pickups"
            value={route.pickup_count}
            caption="scheduled today"
          />
          <StatCard
            accent="#2563EB"
            icon={<CheckCircle2 size={16} />}
            label="Completed"
            value={completedCount}
            caption="collected + clean"
          />
          <StatCard
            accent="#F2A93C"
            icon={<Clock size={16} />}
            label="Pending"
            value={pendingCount}
            caption="awaiting action"
          />
          <StatCard
            accent="#2947A3"
            icon={<BadgeCheck size={16} />}
            label="Completion"
            value={`${completionPercentage}%`}
            caption={`${totalLoadKg} kg on route`}
          />
        </div>
      )}

      {route && (
        <Card className="!p-5">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-[#EFF6FF] text-[#2947A3] flex items-center justify-center">
                <Recycle size={18} />
              </div>
              <div>
                <p className="text-[11px] tracking-widest text-gray-400 uppercase">
                  Route Progress
                </p>
                <p className="font-serif text-lg font-semibold text-[#1F3259]">
                  {route.zone_name || "Ward 07 · Route R-14"}
                </p>
              </div>
            </div>
            <div className="text-right">
              <p className="font-serif text-2xl font-bold text-[#2947A3]">
                {completionPercentage}%
              </p>
              <p className="text-xs text-gray-400">of daily target</p>
            </div>
          </div>

          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div
              className="bg-gradient-to-r from-[#2947A3] to-[#2563EB] h-2 rounded-full transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            <MiniStat
              icon={<Recycle size={13} />}
              label="Wet + Recyc"
              value={`${wetRecycStops} stops`}
            />
            <MiniStat icon={<Weight size={13} />} label="Total Load" value={`${totalLoadKg} kg`} />
            <MiniStat icon={<Flag size={13} />} label="Flagged" value={flaggedCount} />
            <MiniStat icon={<Clock size={13} />} label="Duty Hrs" value={DUTY_HOURS} />
          </div>
        </Card>
      )}

      {loading && !route && (
        <div className="text-center py-12 text-gray-400">
          <p>Loading your route…</p>
        </div>
      )}

      {/* Section II — Duty Register */}
      <div className="flex flex-wrap items-end justify-between gap-3 pt-2">
        <div>
          <p className="text-xs tracking-[0.2em] text-[#2947A3]/60 font-semibold uppercase">
            Section II · Duty Register
          </p>
          <h2 className="font-serif text-xl sm:text-2xl font-bold text-[#1F3259] mt-1">
            Assigned Pickup Points
          </h2>
        </div>
        <p className="text-sm text-gray-400">
          {route?.pickup_count || 0} entries · sorted by sequence
        </p>
      </div>

      <div className="space-y-3">
        {pickups.map((p) => {
          const isCollected =
            p.status === "COLLECTED" || p.status === "VERIFIED" || p.status === "CREDITED";
          const canUndo = isCollected && isToday(p.collected_at);
          return (
            <Card
              key={p.id}
              className={`!p-4 border-l-4 ${isCollected ? "border-l-emerald-500" : "border-l-[#2947A3]"}`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="flex flex-col items-center gap-1 flex-shrink-0">
                    <div
                      className={`w-11 h-11 rounded-full flex items-center justify-center ${
                        isCollected ? "bg-emerald-500 text-white" : "bg-[#2947A3] text-white"
                      }`}
                    >
                      {isCollected ? (
                        <CheckCircle2 size={19} />
                      ) : (
                        <span className="text-sm font-bold">{p.order}</span>
                      )}
                    </div>
                    <span className="text-[10px] font-semibold bg-[#1F3259] text-white px-1.5 py-0.5 rounded">
                      {p.ref_code}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-serif font-semibold text-[#0B3D38]">
                        {p.resident_name}
                      </span>
                      <StatusPill status={p.status} />
                    </div>
                    <p className="text-sm text-gray-600 mt-1 flex items-center gap-1">
                      <Recycle size={12} className="text-gray-400" /> {p.category} ·
                      <Weight size={12} className="text-gray-400 ml-1" />{" "}
                      {p.estimated_weight ?? "?"} kg
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5 flex items-center gap-1">
                      <MapPin size={11} /> {p.pickup_address || p.zone_name} · {p.time_slot}
                    </p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {p.navigate_url && (
                    <a
                      href={p.navigate_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs bg-[#2947A3] hover:bg-[#1F3259] text-white px-3 py-1.5 rounded flex items-center gap-1 transition-colors"
                    >
                      <Navigation size={12} /> Navigate
                    </a>
                  )}
                  {!isCollected && (
                    <>
                      <button
                        type="button"
                        onClick={() => openDelay(p)}
                        className="text-xs bg-[#2947A3] hover:bg-[#1F3259] text-white px-3 py-1.5 rounded flex items-center gap-1 transition-colors"
                      >
                        <Bell size={12} /> Notify
                      </button>
                      <button
                        type="button"
                        onClick={() => handleCollect(p.id)}
                        className="text-xs bg-[#2947A3] hover:bg-[#1F3259] text-white px-3 py-1.5 rounded flex items-center gap-1 transition-colors"
                      >
                        <CheckCircle size={12} /> Complete
                      </button>
                      <button
                        type="button"
                        onClick={() => handleMarkClean(p.id)}
                        className="text-xs border border-emerald-200 text-emerald-700 px-3 py-1.5 rounded flex items-center gap-1 hover:bg-emerald-50 transition-colors"
                      >
                        <ShieldCheck size={12} /> Mark Clean
                      </button>
                      <button
                        type="button"
                        onClick={() => openIssue(p)}
                        className="text-xs border border-red-200 text-red-600 px-3 py-1.5 rounded flex items-center gap-1 hover:bg-red-50 transition-colors"
                      >
                        <Flag size={12} /> Flag Waste
                      </button>
                    </>
                  )}
                  {canUndo && (
                    <button
                      type="button"
                      onClick={() => handleUndo(p.id)}
                      className="text-xs border border-gray-200 px-3 py-1.5 rounded flex items-center gap-1 text-gray-600 hover:bg-gray-50 transition-colors"
                    >
                      <Undo2 size={12} /> Undo
                    </button>
                  )}
                </div>
              </div>
            </Card>
          );
        })}
        {!loading && !pickups.length && (
          <div className="text-center py-12 text-gray-400">
            <MapPin size={32} className="mx-auto mb-2 opacity-50" />
            <p>No pickups scheduled for today</p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="pt-6 mt-6 border-t border-[#2947A3]/15 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-[#2947A3] flex items-center justify-center">
            <Recycle size={13} className="text-white" />
          </div>
          <div>
            <p className="text-xs font-semibold text-[#1F3259]">Verdeza</p>
            <p className="text-[11px] text-gray-400">
              © 2026 Ministry of Housing &amp; Urban Affairs · Portal v2.4
            </p>
          </div>
        </div>
        <p className="text-[11px] text-gray-400">Helpline · 000-111-1969 · toll-free</p>
      </div>

      <Modal
        open={!!delayTarget}
        onClose={() => setDelayTarget(null)}
        title={`Notify — ${delayTarget?.ref_code}`}
      >
        <form onSubmit={sendDelay} className="space-y-4">
          {delayErr && (
            <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{delayErr}</div>
          )}
          {delayOk && (
            <div className="bg-green-50 text-green-700 text-sm p-3 rounded-input">{delayOk}</div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Delay Reason</label>
            <select
              className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm"
              value={delayType}
              onChange={(e) => {
                setDelayType(e.target.value);
                const t = DELAY_TYPES.find((d) => d.value === e.target.value);
                if (t?.template) {
                  setDelayComment(t.template.replace("{min}", delayMinutes));
                  setDelayCommentTouched(false);
                } else {
                  setDelayComment("");
                  setDelayCommentTouched(false);
                }
              }}
            >
              {DELAY_TYPES.map((d) => (
                <option key={d.value} value={d.value}>
                  {d.label}
                </option>
              ))}
            </select>
          </div>
          {delayType === "RUNNING_LATE" && (
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Minutes late</label>
              <input
                type="number"
                min="5"
                className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm"
                value={delayMinutes}
                onChange={(e) => {
                  setDelayMinutes(e.target.value);
                  if (!delayCommentTouched) {
                    const t = DELAY_TYPES.find((d) => d.value === "RUNNING_LATE");
                    if (t?.template) setDelayComment(t.template.replace("{min}", e.target.value));
                  }
                }}
              />
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Message ({delayComment.trim().length}/{DELAY_MAX_LEN})
            </label>
            <textarea
              required
              minLength={DELAY_MIN_LEN}
              maxLength={DELAY_MAX_LEN}
              rows={3}
              className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm"
              value={delayComment}
              onChange={(e) => {
                setDelayComment(e.target.value);
                setDelayCommentTouched(true);
              }}
            />
          </div>
          <button
            type="submit"
            disabled={delaySending}
            className="w-full bg-[#F2A93C] hover:bg-[#e09a2c] text-white py-2.5 rounded-input font-medium disabled:opacity-50 transition-colors"
          >
            {delaySending ? "Sending…" : `Send to ${delayTarget?.resident_name || "resident"}`}
          </button>
        </form>
      </Modal>

      <Modal
        open={!!issueTarget}
        onClose={() => setIssueTarget(null)}
        title={`Flag Mixed Waste — ${issueTarget?.ref_code}`}
      >
        <form onSubmit={submitIssue} className="space-y-4">
          {issueErr && (
            <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{issueErr}</div>
          )}
          {issueOk && (
            <div className="bg-green-50 text-green-700 text-sm p-3 rounded-input">{issueOk}</div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">What's wrong</label>
            <select
              className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm"
              value={issueForm.issue_type}
              onChange={(e) => setIssueForm({ ...issueForm, issue_type: e.target.value })}
            >
              {ISSUE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Severity</label>
            <div className="flex gap-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="severity"
                  value="ROUTINE"
                  checked={issueForm.severity === "ROUTINE"}
                  onChange={() => setIssueForm({ ...issueForm, severity: "ROUTINE" })}
                />
                Routine
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="severity"
                  value="HAZARDOUS"
                  checked={issueForm.severity === "HAZARDOUS"}
                  onChange={() => setIssueForm({ ...issueForm, severity: "HAZARDOUS" })}
                />
                Hazardous
              </label>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Description</label>
            <textarea
              required
              minLength={10}
              rows={4}
              className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm"
              value={issueForm.description}
              onChange={(e) => setIssueForm({ ...issueForm, description: e.target.value })}
            />
          </div>
          <button
            type="submit"
            disabled={issueSending}
            className="w-full bg-[#2947A3] hover:bg-[#1F3259] text-white py-2.5 rounded-input font-medium disabled:opacity-50 transition-colors"
          >
            {issueSending ? "Submitting…" : "Submit Flag"}
          </button>
        </form>
      </Modal>
    </div>
  );
}

function StatCard({ accent, icon, label, value, caption }) {
  return (
    <Card className="!p-0 overflow-hidden">
      <div className="h-1" style={{ backgroundColor: accent }} />
      <div className="p-4">
        <p className="text-[11px] font-semibold tracking-widest uppercase text-gray-400 flex items-center gap-1.5">
          <span style={{ color: accent }}>{icon}</span> {label}
        </p>
        <p className="font-serif text-2xl font-bold mt-2" style={{ color: accent }}>
          {value}
        </p>
        <p className="text-xs text-gray-400 mt-0.5">{caption}</p>
      </div>
    </Card>
  );
}

function MiniStat({ icon, label, value }) {
  return (
    <div className="flex items-center justify-between rounded-input border border-gray-100 bg-[#EFF6FF] px-3 py-2">
      <span className="text-xs text-gray-500 flex items-center gap-1.5">
        {icon} {label}
      </span>
      <span className="text-xs font-semibold text-[#1F3259]">{value}</span>
    </div>
  );
}
