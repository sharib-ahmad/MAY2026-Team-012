import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card, StatCard, BarChartCard, PieChartCard, LineChartCard } from "../../../components/UI";
import { Leaf, Award, TrendingUp, Download, Lock } from "lucide-react";
import { getUserImpact } from "../../../lib/api";

function buildReportHtml(user, data) {
  return `<!doctype html>
<html><head><meta charset="utf-8"><title>Verdeza Impact Report</title>
<style>body{font-family:sans-serif;padding:32px;color:#14171F}
h1{color:#0B4F4A}.stat{display:inline-block;margin:8px 24px 8px 0}
.stat b{font-size:24px;display:block}table{border-collapse:collapse;margin-top:16px}
td,th{border:1px solid #ddd;padding:6px 10px;font-size:13px;text-align:left}</style>
</head><body>
<h1>Sustainability Impact — ${user?.name || "Citizen"}</h1>
<p>Generated ${new Date().toLocaleString()}</p>
<div class="stat"><b>${data.total_kg_diverted.toFixed(1)} kg</b>Diverted</div>
<div class="stat"><b>${data.co2_saved_kg.toFixed(1)} kg</b>CO2 saved</div>
<div class="stat"><b>${data.credits_balance.toFixed(1)}</b>Credits</div>
<div class="stat"><b>${data.total_pickups}</b>Total pickups</div>
<table><tr><th>Category</th><th>Weight (kg)</th><th>Credits</th><th>CO2 (kg)</th></tr>
${data.by_category
  .map(
    (c) =>
      `<tr><td>${c.category}</td><td>${c.weight_kg.toFixed(1)}</td><td>${c.credits.toFixed(1)}</td><td>${c.co2_kg.toFixed(1)}</td></tr>`
  )
  .join("")}
</table>
</body></html>`;
}

// ── Hexagonal medal badge, in the style of Credly / diploma badges ──
// pointy-top hexagon, gold rim, circular emblem on top, name banded
// across the middle. Unearned badges render as a locked, desaturated
// silhouette of the same shape so progress still reads as a shape,
// not a blank gap.
function hexPoints(cx, cy, r) {
  return Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 180) * (-90 + i * 60);
    return `${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`;
  }).join(" ");
}

function HexBadge({ icon, name, earned, featured }) {
  const uid = useMemo(() => name.replace(/\s+/g, "-").toLowerCase(), [name]);
  const cx = 70;
  const cy = 92;
  const r = 58;

  return (
    <div className="flex flex-col items-center w-[132px] shrink-0">
      <div className={`relative ${earned ? "" : "opacity-45 grayscale"}`}>
        <svg width="140" height="170" viewBox="0 0 140 170">
          <defs>
            <linearGradient id={`hexfill-${uid}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={earned ? "#1E3A8A" : "#9CA3AF"} />
              <stop offset="55%" stopColor={earned ? "#1D4ED8" : "#9CA3AF"} />
              <stop offset="100%" stopColor={earned ? "#1E3A8A" : "#6B7280"} />
            </linearGradient>
            <linearGradient id={`hexrim-${uid}`} x1="0" y1="0" x2="1" y2="1">
              <stop offset="0%" stopColor={earned ? "#F5D57A" : "#D1D5DB"} />
              <stop offset="50%" stopColor={earned ? "#C9962C" : "#9CA3AF"} />
              <stop offset="100%" stopColor={earned ? "#F5D57A" : "#D1D5DB"} />
            </linearGradient>
            <radialGradient id={`medallion-${uid}`} cx="35%" cy="30%" r="75%">
              <stop offset="0%" stopColor={earned ? "#FDE9B0" : "#E5E7EB"} />
              <stop offset="100%" stopColor={earned ? "#C9962C" : "#9CA3AF"} />
            </radialGradient>
          </defs>

          {/* hexagon body */}
          <polygon
            points={hexPoints(cx, cy, r)}
            fill={`url(#hexfill-${uid})`}
            stroke={`url(#hexrim-${uid})`}
            strokeWidth="4"
            strokeLinejoin="round"
          />
          <polygon
            points={hexPoints(cx, cy, r - 8)}
            fill="none"
            stroke={earned ? "rgba(255,255,255,0.25)" : "rgba(255,255,255,0.15)"}
            strokeWidth="1.5"
          />

          {/* name band */}
          <foreignObject x="14" y="76" width="112" height="60">
            <div className="w-full h-full flex items-center justify-center text-center px-1">
              <span
                className={`text-[11px] font-bold uppercase tracking-wide leading-tight ${
                  earned ? "text-white" : "text-gray-100"
                }`}
              >
                {name}
              </span>
            </div>
          </foreignObject>

          {/* top medallion emblem */}
          <circle
            cx={cx}
            cy={30}
            r="26"
            fill={`url(#medallion-${uid})`}
            stroke={earned ? "#8A6116" : "#9CA3AF"}
            strokeWidth="2"
          />
          <circle
            cx={cx}
            cy={30}
            r="20"
            fill="none"
            stroke={earned ? "#FFF6DF" : "#F3F4F6"}
            strokeWidth="1"
            strokeDasharray="2 2"
            opacity="0.7"
          />
          <foreignObject x={cx - 16} y={14} width="32" height="32">
            <div className="w-full h-full flex items-center justify-center text-xl">
              {earned ? icon : <Lock size={16} className="text-gray-500" strokeWidth={2.5} />}
            </div>
          </foreignObject>
        </svg>

        {/* ribbon banner for the standout / most recent badge */}
        {earned && featured && (
          <div className="absolute left-1/2 -translate-x-1/2 -bottom-1 w-[104px]">
            <div className="relative">
              <div
                className="absolute left-[-14px] top-0 w-0 h-0"
                style={{
                  borderTop: "11px solid transparent",
                  borderBottom: "11px solid transparent",
                  borderRight: "14px solid #8A6116",
                }}
              />
              <div
                className="absolute right-[-14px] top-0 w-0 h-0"
                style={{
                  borderTop: "11px solid transparent",
                  borderBottom: "11px solid transparent",
                  borderLeft: "14px solid #8A6116",
                }}
              />
              <div className="bg-gradient-to-b from-amber-300 to-amber-600 text-center py-1.5 shadow-sm">
                <span className="text-[10px] font-bold tracking-widest text-[#3D2C05]">EARNED</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function Impact() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [exportStatus, setExportStatus] = useState("");

  useEffect(() => {
    let active = true;
    getUserImpact()
      .then((impact) => active && setData(impact))
      .catch(() => active && setLoadError("Unable to load your impact data."));
    return () => {
      active = false;
    };
  }, []);

  if (!data) {
    return (
      <div className="space-y-6 fade-in">
        <h1 className="text-xl font-bold">My Sustainability Impact</h1>
        <Card>
          <p className="text-center text-gray-400 py-10 text-sm">
            {loadError || "Loading your impact data…"}
          </p>
        </Card>
      </div>
    );
  }

  const earnedBadges = data.badges.filter((b) => b.earned);
  const featuredCode = earnedBadges.length ? earnedBadges[earnedBadges.length - 1].code : null;

  const exportHtml = () => {
    setExportStatus("Generating report…");
    const html = buildReportHtml(user, data);
    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `verdeza-impact-${user.id.slice(0, 8)}.html`;
    a.click();
    URL.revokeObjectURL(url);
    setExportStatus("Report downloaded!");
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">My Sustainability Impact</h1>
        <button
          type="button"
          onClick={exportHtml}
          className="bg-white border border-gray-200 text-gray-600 px-4 py-2 rounded-input text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
        >
          <Download size={14} /> Export to HTML
        </button>
      </div>
      {exportStatus && <p className="text-sm text-gray-500">{exportStatus}</p>}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Kg Diverted"
          value={data.total_kg_diverted.toFixed(1)}
          icon={Leaf}
          color="text-green-600"
        />
        <StatCard
          label="CO₂ Saved (kg)"
          value={data.co2_saved_kg.toFixed(1)}
          icon={Award}
          color="text-accent"
        />
        <StatCard
          label="Credits Balance"
          value={data.credits_balance.toFixed(1)}
          icon={TrendingUp}
          color="text-manager"
        />
        <StatCard label="Total Pickups" value={data.total_pickups} color="text-primary" />
      </div>

      <Card
        title="Badges"
        actions={
          <span className="text-xs font-medium text-gray-400">
            {earnedBadges.length}/{data.badges.length} earned
          </span>
        }
      >
        <div className="flex gap-5 flex-wrap pt-2 pb-1">
          {data.badges.map((b) => (
            <HexBadge
              key={b.code}
              icon={b.icon}
              name={b.name}
              earned={b.earned}
              featured={b.earned && b.code === featuredCode}
            />
          ))}
        </div>
      </Card>

      {data.by_category.length > 0 ? (
        <>
          <div className="grid lg:grid-cols-2 gap-4">
            <PieChartCard data={data.by_category} title="By Category" />
            <LineChartCard
              data={data.monthly_trend}
              lines={[{ key: "weight_kg", name: "Weight (kg)" }]}
              title="Monthly Trend"
            />
          </div>
          <div className="grid lg:grid-cols-2 gap-4">
            <BarChartCard
              data={data.by_category}
              dataKey="credits"
              nameKey="category"
              title="Credits by Category"
            />
            <BarChartCard
              data={data.by_category}
              dataKey="co2_kg"
              nameKey="category"
              title="CO₂ by Category"
            />
          </div>
        </>
      ) : (
        <Card>
          <p className="text-center text-gray-400 py-10 text-sm">
            Complete a pickup to start seeing your impact broken down here.
          </p>
        </Card>
      )}
    </div>
  );
}
