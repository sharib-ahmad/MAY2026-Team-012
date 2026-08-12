import { useEffect, useState, useCallback, useRef } from "react";
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
  AlertTriangle,
} from "lucide-react";
import { usePolling } from "../../../hooks/usePolling";
import {
  completeCollectorStop,
  flagCollectorStop,
  getCollectorRoute,
  notifyCollectorStop,
  undoCollectorStop,
} from "../../../lib/api";

import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

const collectorIcon = L.divIcon({
  html: `<div style="width: 32px; height: 32px; background-color: #E53E3E; border: 2px solid white; border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; font-size: 16px; color: white; pointer-events: none;">🚚</div>`,
  className: "custom-collector-icon",
  iconSize: [32, 32],
  iconAnchor: [16, 16],
});

const stopIcon = new L.Icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const completedIcon = new L.Icon({
  iconUrl:
    "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

const depotIcon = L.divIcon({
  html: `<div style="font-size: 28px; line-height: 1; display: flex; align-items: center; justify-content: center; pointer-events: none;">🏢</div>`,
  className: "custom-depot-icon",
  iconSize: [30, 30],
  iconAnchor: [15, 15],
});

function FitMapBounds({ points }) {
  const map = useMap();
  const lastPointsRef = useRef("");

  useEffect(() => {
    if (points && points.length > 0) {
      const serialized = JSON.stringify(points);
      if (lastPointsRef.current !== serialized) {
        lastPointsRef.current = serialized;
        const bounds = L.latLngBounds(points);
        map.fitBounds(bounds, { padding: [40, 40] });
      }
    }
  }, [points, map]);
  return null;
}

// Story 1.5-AC1: a standard set of reasons plus a mandatory-free-text "Other".
const DELAY_TYPES = [
  {
    value: "HEAVY_TRAFFIC",
    label: "Running Late",
    template: "I will arrive approximately {min} minutes late.",
  },
  {
    value: "ROAD_BLOCKED",
    label: "Road Blocked",
    template: "A road blockage is delaying the pickup.",
  },
  {
    value: "VEHICLE_BREAKDOWN",
    label: "Vehicle Issue",
    template: "Vehicle issue. Your pickup has been delayed.",
  },
  {
    value: "WEATHER",
    label: "Weather Delay",
    template: "Weather conditions are delaying the pickup.",
  },
  {
    value: "WASTE_NOT_READY",
    label: "Waste Not Ready",
    template: "Citizen was not available at the location.",
  },
  { value: "OTHER", label: "Other", template: "" },
];

const DELAY_MIN_LEN = 5;
const DELAY_MAX_LEN = 200;
const ISSUE_MAX_LEN = 250;

const apiErrorMessage = (err, fallback) => {
  const detail = err.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((item) => item.msg || String(item)).join(" ");
  return typeof detail === "string" ? detail : err.message || fallback;
};

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
  const [currentTime, setCurrentTime] = useState(0);

  const [delayTarget, setDelayTarget] = useState(null);
  const [delayType, setDelayType] = useState("HEAVY_TRAFFIC");
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

  const load = useCallback(async () => {
    if (!user) return;
    try {
      const schedule = await getCollectorRoute();
      const transformedRoute = {
        ...schedule,
        ordered_pickups: schedule.ordered_pickups.map((stop) => ({
          ...stop,
          order: stop.pickup_order,
          collected_at: stop.completed_at,
        })),
      };
      setRoute(transformedRoute);
    } catch (err) {
      setActionErr(apiErrorMessage(err, "Failed to load your assigned collections."));
    }
    setLoading(false);
  }, [user]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [load]);
  usePolling(load, 30000);

  useEffect(() => {
    const intervalId = window.setInterval(() => setCurrentTime(Date.now()), 1000);
    return () => window.clearInterval(intervalId);
  }, []);

  // Story 1.4-AC2/AC6
  const handleCollect = async (id) => {
    setActionErr("");
    try {
      await completeCollectorStop(id);
      await load();
    } catch (err) {
      setActionErr(apiErrorMessage(err, "Failed to collect stop"));
    }
  };

  // Story 1.4-AC3: same-day undo for a mis-tap.
  const handleUndo = async (id) => {
    setActionErr("");
    try {
      await undoCollectorStop(id);
      await load();
    } catch (err) {
      setActionErr(apiErrorMessage(err, "Failed to undo collection"));
    }
  };

  const handleNavigate = (pickup) => {
    if (pickup.pickup_latitude == null || pickup.pickup_longitude == null) {
      setActionErr("The citizen location is not available for this pickup.");
      return;
    }
    if (route?.collector_latitude == null || route?.collector_longitude == null) {
      setActionErr("Your registered collector location is not available.");
      return;
    }
    const origin = `${route.collector_latitude},${route.collector_longitude}`;
    const destination = `${pickup.pickup_latitude},${pickup.pickup_longitude}`;
    window.open(
      `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${encodeURIComponent(origin)};${encodeURIComponent(destination)}`,
      "_blank",
      "noopener,noreferrer"
    );
  };

  const openDelay = (pickup) => {
    const t = DELAY_TYPES.find((d) => d.value === "HEAVY_TRAFFIC");
    setDelayTarget(pickup);
    setDelayType("HEAVY_TRAFFIC");
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
      await notifyCollectorStop(delayTarget.id, { reason: delayType, message: trimmed });
      setDelayOk(`Notification sent to ${delayTarget.citizen_name || "citizen"}.`);
      setTimeout(() => setDelayTarget(null), 1200);
      load();
    } catch (err) {
      setDelayErr(apiErrorMessage(err, "Failed to send notification"));
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
      const issueLabel = ISSUE_TYPES.find((type) => type.value === issueForm.issue_type)?.label;
      await flagCollectorStop(issueTarget.id, {
        description: issueLabel
          ? `${issueLabel}: ${issueForm.description.trim()}`
          : issueForm.description.trim(),
        severity: issueForm.severity,
      });
      setIssueOk("Flag recorded. A manager will review it.");
      setTimeout(() => setIssueTarget(null), 1500);
      load();
    } catch (err) {
      setIssueErr(apiErrorMessage(err, "Failed to record flag"));
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
  const flaggedCount = route?.flagged_count ?? 0;
  const completionPercentage =
    route?.pickup_count > 0 ? Math.round((completedCount / route.pickup_count) * 100) : 0;
  const totalLoadKg = pickups.reduce((sum, p) => sum + (p.estimated_weight || 0), 0);
  const canUndoWithinOneMinute = (iso) =>
    Boolean(currentTime && iso) && currentTime - new Date(iso).getTime() <= 60_000;
  const undoTimeRemaining = (iso) => {
    const seconds = Math.max(
      0,
      Math.ceil((60_000 - (currentTime - new Date(iso).getTime())) / 1000)
    );
    return `00:${String(seconds).padStart(2, "0")}`;
  };

  // Calculate direction arrows along the polyline path
  const routeGeometry = route?.route_geometry || [];
  const arrowInterval = 8; // Place an arrow every 8 coordinates
  const pathArrows = [];

  if (routeGeometry.length > 1) {
    for (let i = 0; i < routeGeometry.length - 1; i += arrowInterval) {
      const p1 = routeGeometry[i];
      const p2 = routeGeometry[Math.min(i + 2, routeGeometry.length - 1)];
      const lat1 = p1[0];
      const lon1 = p1[1];
      const lat2 = p2[0];
      const lon2 = p2[1];

      const midLat = (lat1 + lat2) / 2;
      const midLon = (lon1 + lon2) / 2;

      const dy = lat2 - lat1;
      const dx = lon2 - lon1;
      const angle = (Math.atan2(dy, dx) * 180) / Math.PI;
      const rotation = -angle; // Convert to CSS rotation

      pathArrows.push({
        id: `arrow-${i}`,
        position: [midLat, midLon],
        rotation: rotation,
      });
    }
  }

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col space-y-8 fade-in">
      {/* Section I — Field Operations */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs tracking-[0.2em] text-[#2947A3]/60 font-semibold uppercase">
            Section I · Field Operations
          </p>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[#1F3259] mt-1">
            My Pickups
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Your assigned bulk-pickup schedule — updates are auto-logged to the municipal registry.
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
            caption="scheduled"
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
              <p className="text-xs text-gray-400">of target</p>
            </div>
          </div>

          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div
              className="bg-gradient-to-r from-[#2947A3] to-[#2563EB] h-2 rounded-full transition-all duration-500"
              style={{ width: `${completionPercentage}%` }}
            />
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            <MiniStat icon={<Weight size={13} />} label="Total Load" value={`${totalLoadKg} kg`} />
            <MiniStat
              icon={<MapPin size={13} />}
              label="Total Distance"
              value={`${route.total_distance_km ?? 0} km`}
            />
            <MiniStat
              icon={<Clock size={13} />}
              label="Est. Duration"
              value={`${route.estimated_duration_min ?? 0} min`}
            />
            <MiniStat icon={<Flag size={13} />} label="Flagged" value={flaggedCount} />
            <MiniStat icon={<Clock size={13} />} label="Duty Hrs" value={DUTY_HOURS} />
          </div>

          {route.is_degraded && (
            <div className="mt-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs p-3 rounded-lg flex items-center gap-2">
              <AlertTriangle size={15} className="text-amber-600 flex-shrink-0" />
              <span>
                {route.degraded_notice ||
                  "Road routing service unavailable. Degraded fallback route is active."}
              </span>
            </div>
          )}
        </Card>
      )}

      {route &&
        (route.collector_latitude || route.ordered_pickups.some((p) => p.pickup_latitude)) && (
          <Card className="!p-4">
            <div className="mb-3">
              <h3 className="font-serif font-semibold text-[#1F3259]">Optimized Duty Route Map</h3>
              <p className="text-xs text-gray-500">
                Live optimized path connecting your assigned pickup stops.
              </p>
            </div>
            <div
              style={{ height: "350px", width: "100%", borderRadius: "8px", overflow: "hidden" }}
              className="border border-gray-200 shadow-sm"
            >
              <MapContainer
                center={
                  route.collector_latitude
                    ? [route.collector_latitude, route.collector_longitude]
                    : [26.8467, 80.9462]
                }
                zoom={13}
                scrollWheelZoom={true}
                style={{ height: "100%", width: "100%" }}
              >
                <TileLayer
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <FitMapBounds
                  points={[
                    ...(route.collector_latitude
                      ? [[route.collector_latitude, route.collector_longitude]]
                      : []),
                    ...(route.depot_latitude
                      ? [[route.depot_latitude, route.depot_longitude]]
                      : []),
                    ...route.ordered_pickups
                      .filter((p) => p.pickup_latitude != null && p.pickup_longitude != null)
                      .map((p) => [p.pickup_latitude, p.pickup_longitude]),
                  ]}
                />

                {route.depot_latitude && route.depot_longitude && (
                  <Marker position={[route.depot_latitude, route.depot_longitude]} icon={depotIcon}>
                    <Popup>
                      <div className="text-xs font-semibold">Municipal Office (Depot)</div>
                    </Popup>
                  </Marker>
                )}

                {route.collector_latitude && route.collector_longitude && (
                  <Marker
                    position={[route.collector_latitude, route.collector_longitude]}
                    icon={collectorIcon}
                    zIndexOffset={1000}
                  >
                    <Popup>
                      <div className="text-xs font-semibold">
                        Your Location (Collector / Vehicle)
                      </div>
                    </Popup>
                  </Marker>
                )}

                {route.ordered_pickups
                  .filter((p) => p.pickup_latitude != null && p.pickup_longitude != null)
                  .map((p) => {
                    const isCollected =
                      p.status === "COLLECTED" ||
                      p.status === "VERIFIED" ||
                      p.status === "CREDITED";
                    return (
                      <Marker
                        key={p.id}
                        position={[p.pickup_latitude, p.pickup_longitude]}
                        icon={isCollected ? completedIcon : stopIcon}
                      >
                        <Popup>
                          <div className="text-xs">
                            <div className="font-semibold text-[#1F3259]">
                              Stop #{p.pickup_order}: {p.citizen_name}
                            </div>
                            <div className="text-gray-500 mt-0.5">
                              Ref: {p.ref_code} ({p.category})
                            </div>
                            <div className="text-gray-500">{p.pickup_address}</div>
                            <div className="mt-1">
                              <StatusPill status={p.status} />
                            </div>
                          </div>
                        </Popup>
                      </Marker>
                    );
                  })}

                {route.route_geometry && route.route_geometry.length > 0 && (
                  <>
                    <Polyline
                      positions={route.route_geometry}
                      color="#16214D"
                      weight={4}
                      opacity={0.8}
                    />
                    {pathArrows.map((arrow) => (
                      <Marker
                        key={arrow.id}
                        position={arrow.position}
                        icon={L.divIcon({
                          html: `<div style="transform: rotate(${arrow.rotation}deg); font-size: 13px; color: #F2A93C; text-shadow: 0 0 3px #16214D, 0 0 1px #16214D; font-weight: bold; width: 14px; height: 14px; display: flex; align-items: center; justify-content: center; pointer-events: none;">➤</div>`,
                          className: "custom-route-arrow-icon",
                          iconSize: [14, 14],
                          iconAnchor: [7, 7],
                        })}
                        interactive={false}
                      />
                    ))}
                  </>
                )}
              </MapContainer>
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
          const canUndo = isCollected && canUndoWithinOneMinute(p.collected_at);
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
                        {p.citizen_name}
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
                  <button
                    type="button"
                    onClick={() => handleNavigate(p)}
                    className="text-xs bg-[#2947A3] hover:bg-[#1F3259] text-white px-3 py-1.5 rounded flex items-center gap-1 transition-colors"
                  >
                    <Navigation size={12} /> Navigate
                  </button>
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
                      <Undo2 size={12} /> Undo ({undoTimeRemaining(p.collected_at)})
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
      <div className="!mt-auto pt-6 border-t border-[#2947A3]/15 flex flex-wrap items-center justify-between gap-3">
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
          {delayType === "HEAVY_TRAFFIC" && (
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
                    const t = DELAY_TYPES.find((d) => d.value === "HEAVY_TRAFFIC");
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
            {delaySending ? "Sending…" : `Send to ${delayTarget?.citizen_name || "citizen"}`}
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
              maxLength={ISSUE_MAX_LEN}
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
