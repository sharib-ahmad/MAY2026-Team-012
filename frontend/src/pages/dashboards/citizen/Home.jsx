import { useMemo, useState, useEffect, useCallback, useRef } from "react";
import {
  PackagePlus,
  Leaf,
  Award,
  Clock,
  MapPin,
  Gift,
  AlertCircle,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  Lock,
  Route,
} from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { Card, StatusPill, Empty, CountUp } from "../../../components/UI";
import { getUserDashboard } from "../../../lib/api";
import heroBg from "../../../assets/eco-banner-bg.webp";
// NOTE: add these two files to the assets folder (any doorstep-pickup /
// sorting-facility / community-drive photo works). Until then they'll just
// 404 like any other missing asset import — swap the paths for whatever
// images you have on hand.
import heroBg2 from "../../../assets/eco-banner-sorting.webp";
import heroBg3 from "../../../assets/eco-banner-community.webp";

const HERO_SLIDES = [heroBg, heroBg2, heroBg3];

// Hex badge helper copied from Impact page
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

export default function Home({ onNavigate }) {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState({
    pickups: [],
    impact: {
      total_pickups: 0,
      total_kg_diverted: 0,
      credits_balance: 0,
      co2_saved_kg: 0,
      badges: [],
    },
    queue: null,
    flow: { stops: [] },
  });

  useEffect(() => {
    getUserDashboard()
      .then(setDashboard)
      .catch(() => {});
  }, []);

  const { pickups, impact, queue, flow } = dashboard;

  const recent = pickups.slice(0, 5);
  const nextPickup = pickups.find((p) => p.status === "REQUESTED" || p.status === "ASSIGNED");
  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const earnedBadges = impact.badges.filter((b) => b.earned);
  const featuredCode = earnedBadges.length ? earnedBadges[earnedBadges.length - 1].code : null;

  return (
    <div className="space-y-6">
      {/* Hero banner carousel */}
      <HeroCarousel>
        <div>
          <h1 className="font-display text-3xl sm:text-4xl font-semibold text-white leading-tight">
            {greeting}, {user?.name?.split(" ")[0] || "there"}!
          </h1>
          <p className="text-white/70 mt-2 max-w-md">
            Every pickup you schedule keeps waste out of landfill and{" "}
            <span className="text-amber-300 font-medium">closer to being reused.</span>
          </p>

          {queue ? (
            <div className="mt-6 flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-3 bg-white/10 rounded-2xl px-4 py-3">
                <div className="w-9 h-9 rounded-full bg-amber-400/20 flex items-center justify-center text-amber-300">
                  <Clock size={16} />
                </div>
                <div className="leading-tight">
                  <p className="text-[11px] uppercase tracking-wide text-white/50">
                    Today's collection
                  </p>
                  <p className="text-white font-semibold">
                    Pickup #{queue.pickup_number} · <StatusPill status={queue.status} />
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => onNavigate("pickups")}
                className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-5 py-3 rounded-2xl font-medium transition"
              >
                Track collection <ArrowRight size={16} />
              </button>
            </div>
          ) : (
            <div className="mt-6 flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => onNavigate("schedule")}
                className="inline-flex items-center gap-2 bg-primary hover:bg-primary/90 text-white px-5 py-3 rounded-2xl font-medium transition"
              >
                <PackagePlus size={16} /> Schedule a pickup
              </button>
              {nextPickup && (
                <div className="text-white/60 text-sm">
                  Next up: <span className="text-white">{nextPickup.category}</span> ·{" "}
                  {nextPickup.scheduled_date &&
                    new Date(nextPickup.scheduled_date).toLocaleDateString()}
                </div>
              )}
            </div>
          )}
        </div>
      </HeroCarousel>

      {/* Stat cards with animated counters */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <AnimatedStat
          label="Total pickups"
          value={impact.total_pickups}
          icon={PackagePlus}
          color="text-primary"
        />
        <AnimatedStat
          label="Kg recycled"
          value={impact.total_kg_diverted}
          decimals={1}
          suffix=" kg"
          icon={Leaf}
          color="text-green-600"
        />
        <AnimatedStat
          label="Reward credits"
          value={impact.credits_balance}
          icon={Award}
          color="text-manager"
          sub={`≈ ₹${impact.credits_balance.toFixed(0)} value`}
        />
        <AnimatedStat
          label="CO₂ saved"
          value={impact.co2_saved_kg}
          decimals={1}
          suffix=" kg"
          icon={Clock}
          color="text-accent"
        />
      </div>

      <div className="grid lg:grid-cols-2 gap-4">
        {/* Today's timeline / flow */}
        <Card
          title="Today's collection flow"
          actions={
            <button
              type="button"
              onClick={() => onNavigate("flow")}
              className="text-primary text-xs font-medium"
            >
              View full →
            </button>
          }
          className="hover-lift"
        >
          {flow.stops.length === 0 ? (
            <Empty
              icon={Route}
              title="No collection scheduled today"
              description="Your collection flow will appear here when a daily schedule is published."
            />
          ) : (
            <div className="space-y-3">
              {flow.stops.slice(0, 5).map((stop) => (
                <div key={stop.id} className="flex items-center gap-3">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold shrink-0 ${
                      stop.status === "COLLECTED"
                        ? "bg-success text-white"
                        : stop.citizen_name === "You"
                          ? "bg-primary text-white"
                          : "bg-gray-200 text-gray-500"
                    }`}
                  >
                    {stop.status === "COLLECTED" ? <CheckCircle2 size={13} /> : stop.pickup_order}
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium truncate">
                      {stop.citizen_name}
                      {stop.citizen_name === "You" && (
                        <span className="text-primary text-xs ml-1">(you)</span>
                      )}
                    </p>
                    <p className="text-xs text-gray-400 truncate">{stop.address}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Recent activity */}
        <Card
          title="Recent pickups"
          actions={
            <button
              type="button"
              onClick={() => onNavigate("pickups")}
              className="text-primary text-xs font-medium"
            >
              View all →
            </button>
          }
          className="hover-lift"
        >
          {recent.length === 0 ? (
            <Empty
              icon={PackagePlus}
              title="No pickups yet"
              description="Schedule your first pickup to get started"
            />
          ) : (
            <div className="space-y-2">
              {recent.map((p) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0"
                >
                  <div className="min-w-0">
                    <p className="font-medium text-sm truncate">
                      {p.ref_code} — {p.category}
                    </p>
                    <p className="text-xs text-gray-400 truncate">
                      {p.scheduled_date && new Date(p.scheduled_date).toLocaleDateString()}
                      {p.collector_name && ` · ${p.collector_name}`}
                    </p>
                  </div>
                  <StatusPill status={p.status} />
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <QuickAction
          icon={PackagePlus}
          label="Schedule pickup"
          color="text-primary"
          onClick={() => onNavigate("schedule")}
        />
        <QuickAction
          icon={Gift}
          label="Donate an item"
          color="text-manager"
          onClick={() => onNavigate("donations")}
        />
        <QuickAction
          icon={AlertCircle}
          label="Raise a ticket"
          color="text-accent"
          onClick={() => onNavigate("tickets")}
        />
        <QuickAction
          icon={MapPin}
          label="Browse Community Shelf"
          color="text-recycler"
          onClick={() => onNavigate("communityshelf")}
        />
      </div>

      {/* Badges (Impact-style hex badges) — placed last on the dashboard */}
      <div>
        <Card
          title="Badges"
          actions={
            <span className="text-xs font-medium text-gray-400">
              {earnedBadges.length}/{impact.badges.length} earned
            </span>
          }
        >
          <div className="flex gap-5 flex-wrap pt-2 pb-1">
            {impact.badges.map((b) => (
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
      </div>
    </div>
  );
}

function HeroCarousel({ children }) {
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const timerRef = useRef(null);

  const goTo = useCallback((i) => {
    setIndex(((i % HERO_SLIDES.length) + HERO_SLIDES.length) % HERO_SLIDES.length);
  }, []);
  const next = useCallback(() => goTo(index + 1), [goTo, index]);
  const prev = useCallback(() => goTo(index - 1), [goTo, index]);

  useEffect(() => {
    if (paused) return undefined;
    timerRef.current = setInterval(() => {
      setIndex((i) => (i + 1) % HERO_SLIDES.length);
    }, 3000);
    return () => clearInterval(timerRef.current);
  }, [paused]);

  return (
    <div
      className="group relative overflow-hidden rounded-3xl bg-[#0B2F2C]"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
    >
      {/* Slides */}
      {HERO_SLIDES.map((slide, i) => (
        <img
          key={slide}
          src={slide}
          alt=""
          aria-hidden="true"
          className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-1000 ease-in-out ${
            i === index ? "opacity-100" : "opacity-0"
          }`}
        />
      ))}
      <div className="absolute inset-0 bg-gradient-to-r from-[#0B2F2C] via-[#0B2F2C]/85 to-[#0B2F2C]/20" />

      {/* Content */}
      <div className="relative grid md:grid-cols-[1.3fr_1fr] gap-6 p-6 sm:p-10 items-center min-h-[280px]">
        {children}
      </div>

      {/* Prev / next arrows */}
      <button
        type="button"
        onClick={prev}
        aria-label="Previous slide"
        className="absolute left-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/10 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity"
      >
        <ChevronLeft size={16} />
      </button>
      <button
        type="button"
        onClick={next}
        aria-label="Next slide"
        className="absolute right-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/10 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity"
      >
        <ChevronRight size={16} />
      </button>

      {/* Dot indicators */}
      <div className="absolute bottom-4 right-6 sm:right-10 flex items-center gap-1.5">
        {HERO_SLIDES.map((slide, i) => (
          <button
            key={slide}
            type="button"
            onClick={() => goTo(i)}
            aria-label={`Go to slide ${i + 1}`}
            className={`h-1.5 rounded-full transition-all duration-300 ${
              i === index ? "w-6 bg-white" : "w-1.5 bg-white/40 hover:bg-white/60"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

function AnimatedStat({
  label,
  value,
  decimals = 0,
  suffix = "",
  icon: Icon,
  color = "text-primary",
  sub,
}) {
  return (
    <div className="bg-white rounded-card shadow-soft hover-lift p-5 flex items-start gap-4 rise-in">
      {Icon && <Icon className={`${color} mt-0.5`} size={28} strokeWidth={1.5} />}
      <div>
        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold mt-0.5">
          <CountUp value={value} decimals={decimals} suffix={suffix} />
        </p>
        {sub && <p className="text-gray-400 text-xs mt-1">{sub}</p>}
      </div>
    </div>
  );
}

function QuickAction({ icon: Icon, label, color, onClick }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="bg-white rounded-card shadow-soft hover-lift p-4 text-left transition flex items-center gap-3"
    >
      <Icon className={color} size={22} />
      <span className="font-medium text-sm">{label}</span>
    </button>
  );
}
