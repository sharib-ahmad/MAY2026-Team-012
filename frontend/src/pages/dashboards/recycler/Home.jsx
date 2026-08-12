import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { getRecyclerSummary, listBatches } from "../../../lib/mockRecyclerData";
// Hero carousel images — drop these three files into your assets folder
// (adjust the path below to match) and swap in real facility photos
// whenever you have them.
import heroSortingLine from "../../../assets/facility-sorting-line.webp";
import heroPaperConveyor from "../../../assets/facility-paper-conveyor.webp";
import heroBaledMaterials from "../../../assets/facility-baled-materials.webp";
import {
  Store,
  ShieldAlert,
  Truck,
  PackageCheck,
  ArrowUpRight,
  ArrowDownRight,
  PackagePlus,
  CircleDot,
} from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

// Terracotta/cream palette used only on this page — the shared
// StatCard/BarChartCard/LineChartCard in components/UI stay untouched so
// other role dashboards keep their existing look.
const CLAY = "#C2662D";
const MATERIAL_COLORS = ["#C2662D", "#D98246", "#F0C48A", "#3B2416"];

function StatCard({ icon: Icon, label, value, trend }) {
  const isUp = trend != null && trend >= 0;
  return (
    <div className="bg-white rounded-2xl shadow-sm p-4 flex items-start gap-3">
      <div className="w-10 h-10 rounded-full bg-[#FBEAE0] text-[#C2662D] flex items-center justify-center shrink-0">
        <Icon size={18} />
      </div>
      <div className="min-w-0">
        <div className="text-[10px] font-semibold tracking-wide text-gray-400 uppercase">
          {label}
        </div>
        <div className="text-2xl font-serif font-bold text-gray-900 mt-0.5">{value}</div>
        {trend != null && (
          <div
            className={`mt-0.5 inline-flex items-center gap-0.5 text-xs font-semibold ${
              isUp ? "text-green-600" : "text-red-500"
            }`}
          >
            {isUp ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
            {isUp ? "+" : "-"}
            {Math.abs(trend).toFixed(0)}%
          </div>
        )}
      </div>
    </div>
  );
}

function TrendCard({ data }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-4 sm:p-5 h-full">
      <h2 className="font-serif text-base font-bold text-gray-900 mb-4">
        My Monthly Collection Trend
      </h2>
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={CLAY} stopOpacity={0.45} />
                <stop offset="100%" stopColor={CLAY} stopOpacity={0.03} />
              </linearGradient>
            </defs>
            <CartesianGrid vertical={false} stroke="#EFEAE2" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12, fill: "#9CA3AF" }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "#9CA3AF" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v) => `${v} kg`}
            />
            <Tooltip
              formatter={(v) => [`${v} kg`, "Collected"]}
              contentStyle={{ borderRadius: 10, border: "1px solid #EFEAE2", fontSize: 13 }}
            />
            <Area
              type="monotone"
              dataKey="collected"
              stroke={CLAY}
              strokeWidth={2.5}
              fill="url(#trendFill)"
              dot={{ r: 4, stroke: CLAY, strokeWidth: 2, fill: "#fff" }}
              activeDot={{ r: 5 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function MaterialDonutCard({ data }) {
  const total = data.reduce((sum, d) => sum + d.value, 0);
  return (
    <div className="bg-white rounded-2xl shadow-sm p-4 sm:p-5">
      <h2 className="font-serif text-base font-bold text-gray-900 mb-3">Collections by Material</h2>
      {total === 0 ? (
        <p className="text-sm text-gray-400">No collections recorded yet.</p>
      ) : (
        <div className="flex items-center gap-5">
          <div className="relative w-36 h-36 shrink-0">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={44}
                  outerRadius={64}
                  paddingAngle={2}
                  stroke="none"
                >
                  {data.map((entry, i) => (
                    <Cell key={entry.name} fill={MATERIAL_COLORS[i % MATERIAL_COLORS.length]} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
              <div className="text-[10px] font-semibold text-gray-400 uppercase leading-tight">
                Total
              </div>
              <div className="text-[10px] font-semibold text-gray-400 uppercase leading-tight">
                Weight
              </div>
              <div className="font-serif font-bold text-gray-900 text-sm mt-0.5">
                {total.toFixed(1)} kg
              </div>
            </div>
          </div>
          <ul className="space-y-2 min-w-0">
            {data.map((d, i) => (
              <li key={d.name} className="flex items-center gap-2 text-sm text-gray-700">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: MATERIAL_COLORS[i % MATERIAL_COLORS.length] }}
                />
                <span className="truncate">{d.name}</span>
                <span className="text-gray-400 ml-auto pl-2 shrink-0">
                  {total ? Math.round((d.value / total) * 100) : 0}%
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

const HERO_SLIDES = [heroSortingLine, heroPaperConveyor, heroBaledMaterials];

// Mirrors the citizen portal's welcome banner (greeting + CTA over a
// photo, with dot indicators bottom-right) — same interaction pattern,
// recycler's own facility photos and single brand color for overlay/dots.
function HeroBanner({ name, onBrowseCommunityShelf }) {
  const [slide, setSlide] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setSlide((s) => (s + 1) % HERO_SLIDES.length);
    }, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="relative overflow-hidden rounded-2xl text-white h-64 sm:h-72">
      {HERO_SLIDES.map((src, i) => (
        <img
          key={src}
          src={src}
          alt=""
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-700 ${
            i === slide ? "opacity-100" : "opacity-0"
          }`}
        />
      ))}
      {/* Brand-color wash + black gradient for text legibility — no new hex added */}
      <div className="absolute inset-0" style={{ backgroundColor: "#C4611A", opacity: 0.55 }} />
      <div
        className="absolute inset-0"
        style={{
          background:
            "linear-gradient(100deg, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0.15) 55%, rgba(0,0,0,0.35) 100%)",
        }}
      />

      <div className="relative h-full flex flex-col justify-center px-6 sm:px-10 max-w-xl">
        <h1 className="font-serif text-2xl sm:text-3xl font-bold">
          {greeting()}, {name}!
        </h1>
        <p className="mt-2 text-white/85 text-sm sm:text-base">
          Every batch you claim keeps recyclable material out of landfill and{" "}
          <span className="font-semibold underline decoration-white/40 underline-offset-2">
            back into circulation.
          </span>
        </p>
        <button
          type="button"
          onClick={onBrowseCommunityShelf}
          className="mt-5 w-fit inline-flex items-center gap-2 bg-white font-semibold text-sm px-4 py-2.5 rounded-xl hover:bg-white/90 transition"
          style={{ color: "#C4611A" }}
        >
          <Store size={16} /> Browse Community Shelf
        </button>
      </div>

      {/* Slide indicators */}
      <div className="absolute bottom-4 right-5 flex items-center gap-1.5">
        {HERO_SLIDES.map((src, i) => (
          <button
            key={src}
            type="button"
            aria-label={`Show slide ${i + 1}`}
            onClick={() => setSlide(i)}
            className={`h-1.5 rounded-full transition-all ${
              i === slide ? "w-6 bg-white" : "w-1.5 bg-white/50 hover:bg-white/75"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

function ActivityFeed({ items, onOpen }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm p-4 sm:p-5">
      <h2 className="font-serif text-base font-bold text-gray-900 mb-3">Recent Activity</h2>
      <ul className="space-y-4">
        {items.map((item, i) => {
          const Icon = item.icon;
          const clickable = Boolean(item.batchId && onOpen);
          const Wrapper = clickable ? "button" : "div";
          return (
            <li key={i} className="flex items-start gap-3">
              <div className="flex flex-col items-center pt-1">
                <span
                  className="w-2 h-2 rounded-full shrink-0"
                  style={{ backgroundColor: item.tone === "danger" ? "#DC2626" : CLAY }}
                />
                {i < items.length - 1 && <span className="w-px flex-1 bg-gray-100 mt-1" />}
              </div>
              <Wrapper
                type={clickable ? "button" : undefined}
                onClick={clickable ? () => onOpen(item.tab, item.batchId) : undefined}
                className={`min-w-0 flex-1 pb-1 text-left ${clickable ? "cursor-pointer group" : ""}`}
              >
                <div className="text-[11px] text-gray-400">{item.time}</div>
                <div
                  className={`text-sm font-semibold text-gray-800 leading-tight ${
                    clickable ? "group-hover:text-[#C2662D] group-hover:underline" : ""
                  }`}
                >
                  {item.title}
                </div>
                {item.description && (
                  <div className="text-xs text-gray-400 mt-0.5">{item.description}</div>
                )}
              </Wrapper>
              <div className="w-7 h-7 rounded-full bg-[#FBEAE0] text-[#C2662D] flex items-center justify-center shrink-0">
                <Icon size={13} />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function formatActivityTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const startOfDay = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate());
  const diffDays = Math.round((startOfDay(new Date()) - startOfDay(d)) / 86_400_000);
  if (diffDays <= 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return d.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
}

// Available/Unsafe/Claimed are point-in-time counts with no history in
// mockRecyclerData, so rather than invent a % we snapshot yesterday's
// values in localStorage and diff against today's. Badges appear once a
// prior day's snapshot exists — real deltas, not placeholder numbers.
function useDailyTrends(summary, userId) {
  const trends = useMemo(() => {
    if (!summary || !userId) return {};
    const key = `gc_recycler_stat_snapshot_${userId}`;
    const today = new Date().toISOString().slice(0, 10);
    const current = {
      community_shelf_available: summary.community_shelf_available,
      community_shelf_unsafe: summary.community_shelf_unsafe,
      my_claimed: summary.my_claimed,
    };

    try {
      const raw = localStorage.getItem(key);
      const parsed = raw ? JSON.parse(raw) : null;
      if (parsed && parsed.date !== today) {
        const pct = (a, b) => (b ? ((a - b) / b) * 100 : null);
        return {
          community_shelf_available: pct(
            current.community_shelf_available,
            parsed.values?.community_shelf_available
          ),
          community_shelf_unsafe: pct(
            current.community_shelf_unsafe,
            parsed.values?.community_shelf_unsafe
          ),
          my_claimed: pct(current.my_claimed, parsed.values?.my_claimed),
        };
      }
      return {};
    } catch {
      // localStorage unavailable — badges simply stay hidden.
      return {};
    }
  }, [summary, userId]);

  useEffect(() => {
    if (!summary || !userId) return;
    const key = `gc_recycler_stat_snapshot_${userId}`;
    const today = new Date().toISOString().slice(0, 10);
    const current = {
      community_shelf_available: summary.community_shelf_available,
      community_shelf_unsafe: summary.community_shelf_unsafe,
      my_claimed: summary.my_claimed,
    };

    try {
      const raw = localStorage.getItem(key);
      const parsed = raw ? JSON.parse(raw) : null;
      if (!parsed || parsed.date !== today) {
        localStorage.setItem(key, JSON.stringify({ date: today, values: current }));
      }
    } catch {
      // localStorage unavailable — badges simply stay hidden.
    }
  }, [summary, userId]);

  return trends;
}

export default function RecyclerDashboard({ onOpenBatch }) {
  const { user } = useAuth();
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");
  const [recent, setRecent] = useState({
    available: null,
    unsafe: null,
    claimed: null,
    collected: null,
  });
  const dailyTrends = useDailyTrends(summary, user?.id);

  useEffect(() => {
    try {
      // Backend-free: computed straight from localStorage (see
      // lib/mockRecyclerData.js). Swap for API.get('/analytics/recycler')
      // once a real backend exists.
      setSummary(getRecyclerSummary(user));
    } catch ({ response }) {
      setError(response?.data?.detail || "Failed to load dashboard");
    }
  }, [user]);

  useEffect(() => {
    if (!user) return;
    // Pull the actual most-recent batch behind each stat so Recent Activity
    // can link straight to it, instead of just restating the counts above.
    const byDateDesc = (key) => (a, b) => new Date(b[key] || 0) - new Date(a[key] || 0);
    const available = listBatches({ status: "AVAILABLE" }).sort(byDateDesc("drop_date"));
    const unsafe = available.filter((b) => b.quality_status === "UNSAFE");
    const claimed = listBatches({ status: "CLAIMED", mine: true, recyclerUser: user }).sort(
      byDateDesc("claim_expires_at")
    );
    const collected = listBatches({ status: "COLLECTED", mine: true, recyclerUser: user }).sort(
      byDateDesc("collected_at")
    );
    setRecent({
      available: available[0] || null,
      unsafe: unsafe[0] || null,
      claimed: claimed[0] || null,
      collected: collected[0] || null,
    });
  }, [user, summary]);

  if (error) return <div className="p-8 text-red-600">{error}</div>;
  if (!summary) return <div className="p-8 text-gray-400">Loading…</div>;

  // Trend on "My Total Collected" is the only stat with a real historical
  // baseline (month-over-month from monthly_trend); the other three counts
  // are point-in-time snapshots, so no % delta is fabricated for them.
  const trendSeries = summary.monthly_trend || [];
  const totalTrendPct =
    trendSeries.length >= 2 && trendSeries[trendSeries.length - 2].collected
      ? ((trendSeries[trendSeries.length - 1].collected -
          trendSeries[trendSeries.length - 2].collected) /
          trendSeries[trendSeries.length - 2].collected) *
        100
      : null;

  const donutData = (summary.by_category || []).map((c) => ({
    name: c.category,
    value: c.weight_kg,
  }));

  const activity = [];
  if (recent.available) {
    const b = recent.available;
    activity.push({
      time: formatActivityTime(b.drop_date),
      title: `Batch #${b.ref_code} listed in community shelf`,
      description: `${b.material_type} · ${b.source_ward}`,
      icon: PackagePlus,
      tab: "communityshelf",
      batchId: b.id,
    });
  }
  if (recent.unsafe) {
    const b = recent.unsafe;
    activity.push({
      time: formatActivityTime(b.drop_date),
      title: `Batch #${b.ref_code} flagged unsafe`,
      description: "Marked by facility manager",
      icon: ShieldAlert,
      tone: "danger",
      tab: "communityshelf",
      batchId: b.id,
    });
  }
  if (recent.claimed) {
    const b = recent.claimed;
    activity.push({
      time: "Claimed",
      title: `Batch #${b.ref_code} awaiting pickup`,
      description: `${summary.my_claimed} active claim${summary.my_claimed === 1 ? "" : "s"} total`,
      icon: Truck,
      tab: "claims",
      batchId: b.id,
    });
  }
  if (recent.collected) {
    const b = recent.collected;
    activity.push({
      time: formatActivityTime(b.collected_at),
      title: `Batch #${b.ref_code} collected`,
      description: `${summary.my_collected} batch${summary.my_collected === 1 ? "" : "es"} collected so far`,
      icon: PackageCheck,
      tab: "reports",
      batchId: b.id,
    });
  }
  if (activity.length === 0) {
    activity.push({ time: "", title: "No recent activity yet", icon: CircleDot });
  }

  return (
    <div className="max-w-7xl mx-auto p-4 sm:p-6 space-y-6 fade-in">
      <HeroBanner
        name={user?.name || "there"}
        onBrowseCommunityShelf={() => onOpenBatch?.("communityshelf", null)}
      />

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Store}
          label="Available in Community Shelf"
          value={summary.community_shelf_available}
          trend={dailyTrends.community_shelf_available}
        />
        <StatCard
          icon={ShieldAlert}
          label="Flagged Unsafe"
          value={summary.community_shelf_unsafe}
          trend={dailyTrends.community_shelf_unsafe}
        />
        <StatCard
          icon={Truck}
          label="My Active Claims"
          value={summary.my_claimed}
          trend={dailyTrends.my_claimed}
        />
        <StatCard
          icon={PackageCheck}
          label="My Total Collected"
          value={`${summary.my_total_kg.toFixed(1)} kg`}
          trend={totalTrendPct}
        />
      </div>

      <div className="grid lg:grid-cols-3 gap-4 items-start">
        <div className="lg:col-span-2">
          <TrendCard data={trendSeries} />
        </div>
        <div className="space-y-4">
          <MaterialDonutCard data={donutData} />
          <ActivityFeed items={activity} onOpen={onOpenBatch} />
        </div>
      </div>

      {summary.my_collected === 0 && (
        <div className="bg-white rounded-2xl shadow-sm p-5">
          <p className="text-sm text-gray-500">
            You haven't collected any batches yet. Head to the{" "}
            <span className="font-medium">Community Shelf</span> tab to claim an available batch,
            then confirm pickup from <span className="font-medium">My Claims</span>.
          </p>
        </div>
      )}
    </div>
  );
}
