import { useEffect, useMemo, useState } from "react";
import { Card, StatusPill } from "../../../components/UI";
import { MapPin, CheckCircle2, Clock, User, Truck } from "lucide-react";
import { getUserDashboard } from "../../../lib/api";

// Smooth a series of points into a single SVG path using Catmull-Rom -> Bezier.
function smoothPath(points) {
  if (points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x},${points[0].y}`;
  let d = `M ${points[0].x},${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i - 1] || points[i];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2] || p2;
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${c1x},${c1y} ${c2x},${c2y} ${p2.x},${p2.y}`;
  }
  return d;
}

const SPACING = 150;
const MARGIN_X = 70;
const WAVE_CENTER = 150;
const WAVE_AMPLITUDE = 55;
const SVG_HEIGHT = 300;

export default function CollectionFlow() {
  const [flow, setFlow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);

  useEffect(() => {
    getUserDashboard()
      .then((data) => {
        setFlow(data.flow);
        setLoading(false);
      })
      .catch(() => {
        setLoading(false);
      });
  }, []);

  const myStop = useMemo(() => {
    if (!flow || !flow.stops) return null;
    return flow.stops.find((s) => s.citizen_name === "You") || null;
  }, [flow]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12 text-gray-500">
        <Clock size={32} className="animate-spin mx-auto mb-2 opacity-50" />
        <p>Loading collection flow...</p>
      </div>
    );
  }

  if (!flow || flow.stops.length === 0) {
    return (
      <div className="max-w-4xl mx-auto fade-in">
        <div className="text-center py-12 text-gray-400">
          <MapPin size={32} className="mx-auto mb-2 opacity-50" />
          <p>No collection scheduled for today</p>
        </div>
      </div>
    );
  }

  const completedCount = flow.stops.filter((s) => s.status === "COLLECTED").length;
  const pendingCount = flow.stops.filter((s) => s.status === "PENDING").length;
  const totalStops = flow.total_stops || flow.stops.length;
  const completionPercentage = totalStops > 0 ? Math.round((completedCount / totalStops) * 100) : 0;

  const myStopIndex = myStop ? flow.stops.findIndex((s) => s.id === myStop.id) : -1;
  const pickupsBeforeMe = myStopIndex >= 0 ? myStopIndex : 0;

  const lastCompletedIndex =
    flow.stops
      .map((s, i) => ({ ...s, index: i }))
      .filter((s) => s.status === "COLLECTED")
      .sort((a, b) => b.pickup_order - a.pickup_order)[0]?.index ?? -1;

  // --- Layout: position every stop along a gentle winding "road" ---
  const points = flow.stops.map((stop, i) => ({
    x: MARGIN_X + i * SPACING,
    y: WAVE_CENTER + WAVE_AMPLITUDE * Math.sin(i * 0.85),
    stop,
    index: i,
  }));
  const svgWidth = MARGIN_X * 2 + SPACING * (points.length - 1);

  const roadPath = smoothPath(points);
  const progressPoints = points.slice(0, Math.max(lastCompletedIndex + 1, 0));
  const progressPath = progressPoints.length >= 2 ? smoothPath(progressPoints) : "";

  // Truck sits between the last completed stop and the next pending one.
  let truck;
  if (lastCompletedIndex >= 0 && lastCompletedIndex < points.length - 1) {
    const a = points[lastCompletedIndex];
    const b = points[lastCompletedIndex + 1];
    truck = { x: a.x + (b.x - a.x) * 0.5, y: a.y + (b.y - a.y) * 0.5 };
  } else if (lastCompletedIndex >= points.length - 1) {
    truck = { x: points[points.length - 1].x, y: points[points.length - 1].y };
  } else {
    truck = { x: points[0].x - 45, y: points[0].y };
  }

  const selectedStop =
    points.find((p) => p.stop.id === selectedId)?.stop ??
    (myStop ? flow.stops.find((s) => s.id === myStop.id) : null);

  return (
    <div className="max-w-4xl mx-auto space-y-6 fade-in">
      <div>
        <h1 className="text-xl font-bold">Collection Progress</h1>
        <p className="text-sm text-gray-500">Track today's waste collection in your area</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="!p-3 text-center">
          <p className="text-2xl font-bold text-accent">{totalStops}</p>
          <p className="text-xs text-gray-500">Total Pickups</p>
        </Card>
        <Card className="!p-3 text-center">
          <p className="text-2xl font-bold text-success">{completedCount}</p>
          <p className="text-xs text-gray-500">Completed</p>
        </Card>
        <Card className="!p-3 text-center">
          <p className="text-2xl font-bold text-warn">{pendingCount}</p>
          <p className="text-xs text-gray-500">Pending</p>
        </Card>
        <Card className="!p-3 text-center">
          <p className="text-2xl font-bold text-accent">{completionPercentage}%</p>
          <p className="text-xs text-gray-500">Completion</p>
        </Card>
      </div>

      {/* Route diagram */}
      <Card className="!p-4 sm:!p-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-gray-700">Today's Collection Route</h2>
          {myStop && lastCompletedIndex >= 0 && lastCompletedIndex < myStopIndex && (
            <span className="text-xs text-blue-700 flex items-center gap-1">
              <Clock size={12} /> {pickupsBeforeMe} stops before you
            </span>
          )}
          {myStop && lastCompletedIndex >= myStopIndex && myStop.status === "PENDING" && (
            <span className="text-xs text-green-700 flex items-center gap-1">
              <CheckCircle2 size={12} /> Collector is almost at your stop
            </span>
          )}
        </div>

        <div className="overflow-x-auto -mx-2 px-2 pb-2">
          <svg
            width={svgWidth}
            height={SVG_HEIGHT}
            viewBox={`0 0 ${svgWidth} ${SVG_HEIGHT}`}
            className="block"
          >
            {/* base road */}
            <path
              d={roadPath}
              fill="none"
              stroke="#E5E7EB"
              strokeWidth={10}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
            <path
              d={roadPath}
              fill="none"
              stroke="#FFFFFF"
              strokeWidth={2}
              strokeDasharray="8 10"
              strokeLinecap="round"
            />
            {/* collected portion, highlighted */}
            {progressPath && (
              <path
                d={progressPath}
                fill="none"
                stroke="#16A34A"
                strokeWidth={10}
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity={0.9}
              />
            )}

            {/* truck marker */}
            <g transform={`translate(${truck.x}, ${truck.y})`}>
              <circle r={17} fill="#0B2F2C" opacity={0.08}>
                <animate attributeName="r" values="15;20;15" dur="2s" repeatCount="indefinite" />
                <animate
                  attributeName="opacity"
                  values="0.12;0.02;0.12"
                  dur="2s"
                  repeatCount="indefinite"
                />
              </circle>
              <circle r={14} fill="#0B2F2C" />
              <foreignObject x={-8} y={-8} width={16} height={16}>
                <Truck size={16} color="white" strokeWidth={2.2} />
              </foreignObject>
            </g>

            {/* stops */}
            {points.map(({ x, y, stop }) => {
              const isCompleted = stop.status === "COLLECTED";
              const isMine = myStop && stop.id === myStop.id;
              const isSelected = selectedStop && stop.id === selectedStop.id;
              const labelBelow = y < WAVE_CENTER;
              return (
                <g
                  key={stop.id}
                  transform={`translate(${x}, ${y})`}
                  className="cursor-pointer"
                  onClick={() => setSelectedId(stop.id)}
                >
                  {isMine && (
                    <circle r={17} fill="none" stroke="#2563EB" strokeWidth={2}>
                      <animate
                        attributeName="r"
                        values="15;20;15"
                        dur="1.8s"
                        repeatCount="indefinite"
                      />
                      <animate
                        attributeName="opacity"
                        values="0.9;0.1;0.9"
                        dur="1.8s"
                        repeatCount="indefinite"
                      />
                    </circle>
                  )}
                  <circle
                    r={13}
                    fill={isCompleted ? "#16A34A" : isMine ? "#2563EB" : "#FFFFFF"}
                    stroke={isCompleted ? "#16A34A" : isMine ? "#2563EB" : "#D1D5DB"}
                    strokeWidth={isSelected ? 3 : 2}
                  />
                  {isCompleted ? (
                    <foreignObject x={-7} y={-7} width={14} height={14}>
                      <CheckCircle2 size={14} color="white" />
                    </foreignObject>
                  ) : (
                    <text
                      textAnchor="middle"
                      dy="4"
                      fontSize="11"
                      fontWeight="700"
                      fill={isMine ? "#FFFFFF" : "#6B7280"}
                    >
                      {stop.pickup_order}
                    </text>
                  )}
                  <text
                    textAnchor="middle"
                    y={labelBelow ? 32 : -22}
                    fontSize="11"
                    fontWeight={isSelected ? "700" : "500"}
                    fill={isSelected ? "#0B2F2C" : "#9CA3AF"}
                  >
                    {isMine ? "You" : stop.citizen_name.split(" ")[0]}
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        <div className="flex flex-wrap items-center gap-4 mt-3 pt-3 border-t border-gray-50 text-xs text-gray-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-success" /> Collected
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> Your pickup
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full border-2 border-gray-300 bg-white" /> Pending
          </span>
          <span className="flex items-center gap-1.5">
            <Truck size={12} /> Collector's current position
          </span>
        </div>
      </Card>

      {/* Selected stop detail */}
      {selectedStop && (
        <Card
          className={`!p-4 transition-colors ${
            myStop && selectedStop.id === myStop.id ? "bg-blue-50 border-blue-200" : ""
          }`}
        >
          <div className="flex items-start gap-3">
            <div
              className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center ${
                selectedStop.status === "COLLECTED"
                  ? "bg-success text-white"
                  : myStop && selectedStop.id === myStop.id
                    ? "bg-blue-600 text-white"
                    : "bg-gray-200 text-gray-600"
              }`}
            >
              {selectedStop.status === "COLLECTED" ? (
                <CheckCircle2 size={18} />
              ) : myStop && selectedStop.id === myStop.id ? (
                <User size={18} />
              ) : (
                <span className="text-sm font-bold">{selectedStop.pickup_order}</span>
              )}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="font-medium">
                  Pickup #{selectedStop.pickup_order} — {selectedStop.citizen_name}
                  {myStop && selectedStop.id === myStop.id && (
                    <span className="text-blue-600 ml-2">(You)</span>
                  )}
                </h3>
                <StatusPill status={selectedStop.status} />
              </div>
              <p className="text-xs text-gray-400 mt-0.5">{selectedStop.address}</p>

              {myStop && selectedStop.id === myStop.id && (
                <div className="mt-2 space-y-1 text-sm">
                  <p className="text-gray-600">Pickups before you: {pickupsBeforeMe}</p>
                  {lastCompletedIndex >= 0 && lastCompletedIndex < myStopIndex && (
                    <p className="text-blue-700 flex items-center gap-1">
                      <Clock size={14} />
                      Collector has completed pickup #{
                        flow.stops[lastCompletedIndex].pickup_order
                      }. {pickupsBeforeMe} pickups remain before yours.
                    </p>
                  )}
                  {lastCompletedIndex >= myStopIndex && myStop.status === "PENDING" && (
                    <p className="text-green-700 flex items-center gap-1">
                      <CheckCircle2 size={14} />
                      Collector is approaching your area. Your pickup is coming up soon!
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}
