import { useState } from "react";
import PublicLayout from "../components/PublicLayout";
import {
  Users,
  Truck,
  ClipboardList,
  Recycle,
  Search,
  BellRing,
  CalendarPlus,
  FileText,
  BookOpen,
  BarChart3,
  ListChecks,
  Timer,
  AlertTriangle,
  Inbox,
  CheckCircle2,
  RefreshCcw,
  PackageSearch,
  Gauge,
  Lock,
  Info,
} from "lucide-react";

const roles = [
  {
    key: "citizen",
    label: "Citizen",
    tag: "RESIDENT",
    color: { bg: "bg-[#1F7A4D]", text: "text-[#1F7A4D]", ring: "border-[#1F7A4D]" },
    icon: Users,
    blurb: "Households, shopkeepers, and school administrators generating waste across the ward.",
    preview: ["Ward schedule look-up", "Delay alerts", "Complaint tracking"],
    steps: [
      {
        icon: Search,
        title: "Look up your ward's schedule",
        detail:
          "Search by ward code to see morning/evening collection windows for wet, dry, and recyclable waste.",
      },
      {
        icon: BellRing,
        title: "Get delay notifications",
        detail:
          "If today's collection is delayed or skipped, an in-app alert tells you before you assume it was missed.",
      },
      {
        icon: CalendarPlus,
        title: "Request a bulk pickup",
        detail:
          "Schools, shops, or households with excess waste can request a dated pickup at least 24 hours ahead.",
      },
      {
        icon: FileText,
        title: "File a complaint",
        detail:
          "Report a missed pickup or overflow and get a ticket ID you can track through to resolution.",
      },
      {
        icon: BookOpen,
        title: "Use the sorting guide",
        detail: "A plain-language Wet / Dry / Recyclable reference, no login required.",
      },
      {
        icon: BarChart3,
        title: "See your recycling impact",
        detail:
          'A monthly summary of what was collected from your zone, labeled "as reported by municipal records."',
      },
    ],
  },
  {
    key: "worker",
    label: "Collection Worker",
    tag: "FIELD OPERATOR",
    color: { bg: "bg-[#2947A3]", text: "text-[#2947A3]", ring: "border-[#2947A3]" },
    icon: Truck,
    blurb: "Drivers and helpers covering assigned routes on the ground.",
    preview: ["Daily route checklist", "Delay logging", "Hazard flagging"],
    steps: [
      {
        icon: ListChecks,
        title: "Open today's checklist",
        detail: "Only the route points assigned to you for the day are shown — nothing else.",
      },
      {
        icon: CheckCircle2,
        title: "Mark each point collected",
        detail:
          "Timestamped and tied to your worker ID, with same-day undo if you tap the wrong point.",
      },
      {
        icon: Timer,
        title: "Log a delay reason",
        detail:
          "Pick from a dropdown (traffic, breakdown…) or add your own note, so you're protected from unfair complaints.",
      },
      {
        icon: AlertTriangle,
        title: "Flag mixed or unsafe waste",
        detail:
          "Tag a point Routine or Hazardous so supervisors can prioritize and act on recurring segregation problems.",
      },
    ],
  },
  {
    key: "officer",
    label: "Municipal Officer",
    tag: "OPERATIONS",
    color: { bg: "bg-[#14171F]", text: "text-[#14171F]", ring: "border-[#14171F]" },
    icon: ClipboardList,
    blurb: "Operations supervisors monitoring complaints, routes, and crew performance.",
    preview: ["Complaint dashboard", "Ticket resolution", "Route oversight"],
    steps: [
      {
        icon: Inbox,
        title: "Review the complaint grid",
        detail:
          "Sortable by ward, date, and status — complaints aging past 3 days are flagged automatically.",
      },
      {
        icon: CheckCircle2,
        title: "Resolve tickets",
        detail:
          "Closing a complaint requires a resolution note; citizens can reopen it within 48 hours if unsatisfied.",
      },
      {
        icon: CalendarPlus,
        title: "Approve or reject bulk requests",
        detail:
          "Same-ward, same-day requests are shown together so scheduling conflicts can be managed manually.",
      },
      {
        icon: Gauge,
        title: "Oversee ward-level activity",
        detail:
          "See which route points are completed, delayed, or flagged for mixed waste across all crews.",
      },
    ],
  },
  {
    key: "recycler",
    label: "Recycler",
    tag: "MATERIALS VENDOR",
    color: { bg: "bg-[#C4611A]", text: "text-[#C4611A]", ring: "border-[#C4611A]" },
    icon: Recycle,
    blurb: "External material vendors and scrap aggregators sourcing sorted recyclables.",
    preview: ["Batch ledger", "Quality tags", "Claim & collect"],
    steps: [
      {
        icon: PackageSearch,
        title: "Browse the material ledger",
        detail: "Filter available batches by material type, source ward, and pickup readiness.",
      },
      {
        icon: Gauge,
        title: "Check quality before committing",
        detail:
          "Each batch is tagged Clean, Moisture-Affected, Mixed, or Unsafe, with contamination notes.",
      },
      {
        icon: Lock,
        title: "Claim a batch",
        detail:
          "Claiming locks it instantly — two recyclers can't end up competing for the same load.",
      },
      {
        icon: RefreshCcw,
        title: "Update pickup status",
        detail: "Mark a batch Collected; unclaimed batches auto-release after 48–72 hours.",
      },
    ],
  },
];

const notices = [
  "Verdeza is committed to promoting scientific waste management and sustainable recycling practices.",
  "Citizens are encouraged to segregate wet and dry waste at the source to support efficient waste collection.",
  "Together, let us contribute towards a cleaner, healthier, and greener Uttar Pradesh through responsible waste disposal.",
  "This platform aligns with the vision of Swachh Bharat Mission (Urban) and sustainable municipal waste management initiatives.",
];

export default function Flows() {
  const [active, setActive] = useState(roles[0].key);
  const role = roles.find((r) => r.key === active);
  const RoleIcon = role.icon;

  return (
    <PublicLayout>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700;9..144,800&family=IBM+Plex+Mono:wght@500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
        .font-mono-civic { font-family: 'IBM Plex Mono', monospace; }
        @keyframes ticker-scroll { 0% { transform: translateX(0); } 100% { transform: translateX(-50%); } }
        .ticker-track { animation: ticker-scroll 32s linear infinite; }
      `}</style>

      {/* NOTICE TICKER */}
      <div className="bg-[#14171F] overflow-hidden">
        <div className="flex items-stretch">
          <div className="shrink-0 bg-[#C4611A] text-white text-xs font-bold uppercase tracking-wide px-4 py-3 flex items-center gap-2 z-10">
            <AlertTriangle size={14} /> Public Notices
          </div>
          <div className="relative flex-1 overflow-hidden py-3">
            <div className="flex whitespace-nowrap ticker-track">
              {[...notices, ...notices].map((n, i) => (
                <span key={i} className="text-white/80 text-sm px-8 inline-flex items-center gap-2">
                  <span className="h-1 w-1 rounded-full bg-[#C4611A]" />
                  {n}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* HERO */}
      <div className="bg-[#F7F5F0]">
        <div className="max-w-6xl mx-auto px-4 pt-14 pb-10">
          <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#C4611A]">
            <span className="inline-block h-px w-8 bg-[#C4611A]" />
            Verdeza Civic Waste Platform
          </div>
          <h1 className="font-display mt-4 text-4xl sm:text-5xl font-extrabold text-[#14171F] leading-[1.08] max-w-3xl">
            One platform. Many roles.
            <br />
            <span className="text-[#1F7A4D]">One accountable loop.</span>
          </h1>
        </div>
      </div>

      {/* ROLE BLOCKS — four-bin-rule style */}
      <div className="max-w-6xl mx-auto px-4 py-14">
        <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-[#C4611A]"></div>
        <h2 className="font-display mt-2 text-2xl sm:text-3xl font-bold text-[#14171F]">
          Every role sees a different slice of the loop.
        </h2>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {roles.map((r) => {
            const Icon = r.icon;
            const isActive = r.key === active;
            return (
              <button
                key={r.key}
                onClick={() => setActive(r.key)}
                className={`text-left rounded-2xl p-5 text-white transition ${r.color.bg} ${
                  isActive
                    ? "ring-4 ring-offset-2 ring-[#14171F]/20 scale-[1.02]"
                    : "opacity-90 hover:opacity-100"
                }`}
              >
                <div className="flex items-center justify-between">
                  <Icon size={22} />
                  <span className="text-[10px] font-bold uppercase tracking-wide bg-white/15 rounded-full px-2 py-1">
                    {r.tag}
                  </span>
                </div>
                <h3 className="font-display mt-4 text-lg font-semibold">{r.label}</h3>
                <ul className="mt-3 space-y-1.5">
                  {r.preview.map((p) => (
                    <li key={p} className="text-xs text-white/85 flex items-center gap-1.5">
                      <span className="h-1 w-1 rounded-full bg-white/70" /> {p}
                    </li>
                  ))}
                </ul>
              </button>
            );
          })}
        </div>
      </div>

      {/* SELECTED ROLE — services grid style */}
      <div className="bg-white border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-14">
          <div className="flex items-start gap-4">
            <div
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl text-white ${role.color.bg}`}
            >
              <RoleIcon size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="font-display text-2xl font-bold text-[#14171F]">{role.label}</h2>
                <span
                  className={`text-[11px] font-bold uppercase tracking-wide rounded-full px-2.5 py-1 border ${role.color.ring} ${role.color.text}`}
                >
                  {role.tier}
                </span>
              </div>
              <p className="mt-1 text-sm text-gray-600 max-w-xl">{role.blurb}</p>
            </div>
          </div>

          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {role.steps.map((step, i) => {
              const StepIcon = step.icon;
              return (
                <div
                  key={step.title}
                  className="rounded-2xl border border-gray-200 p-5 hover:border-gray-300 hover:shadow-soft transition"
                >
                  <div className="flex items-center justify-between">
                    <div
                      className={`flex h-10 w-10 items-center justify-center rounded-lg bg-gray-50 ${role.color.text}`}
                    >
                      <StepIcon size={18} />
                    </div>
                    <span className="font-mono-civic text-[11px] text-gray-300">
                      STEP {String(i + 1).padStart(2, "0")}
                    </span>
                  </div>
                  <h3 className="mt-4 font-semibold text-[#14171F]">{step.title}</h3>
                  <p className="mt-2 text-sm text-gray-600 leading-relaxed">{step.detail}</p>
                  {step.note && (
                    <p className="mt-3 inline-flex items-start gap-1.5 text-[11px] text-[#C4611A] bg-[#C4611A]/8 border border-[#C4611A]/20 rounded-lg px-2.5 py-1.5">
                      <Info size={12} className="mt-0.5 shrink-0" /> {step.note}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
