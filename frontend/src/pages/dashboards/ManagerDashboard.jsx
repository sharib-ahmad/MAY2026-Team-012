import { useState } from "react";
import {
  AlertCircle,
  BadgeCheck,
  LayoutDashboard,
  Landmark,
  LogOut,
  MapPinned,
  Users,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import DATA from "../../data/municipal_officer_data.json";
import Overview from "./manager/Overview";
import Complaints from "./manager/Complaints";

// Officer workspace tabs: ward overview and the citizen grievance grid;
// Route Tracking and Crew Assignments panels land here as they are built.
const TABS = [
  { key: "overview", label: "Overview", icon: LayoutDashboard, component: Overview },
  { key: "complaints", label: "Complaints", icon: AlertCircle, component: Complaints },
];

export default function ManagerDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState(TABS[0].key);

  const { stats } = DATA;
  const ActivePanel = TABS.find((t) => t.key === activeTab).component;

  return (
    <div className="min-h-screen bg-[#F6F3EA]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
        .font-mono-civic { font-family: 'IBM Plex Mono', monospace; }
      `}</style>

      {/* Header — deep olive, goldenrod badge (Municipal Officer palette) */}
      <header className="bg-[#26321B] px-4 sm:px-6 py-3 sticky top-0 z-10">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-white">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-[#D9A521] font-display text-lg font-bold text-[#26321B]">
              V
            </span>
            <div className="leading-tight">
              <div className="font-semibold">Verdeza</div>
              <div className="text-[11px] text-white/60">Municipal Operations</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="flex items-center gap-1.5 text-white/75 hover:text-[#E9C55F] text-sm"
          >
            <LogOut size={15} /> Sign out
          </button>
        </div>
      </header>

      {/* Official strip */}
      <div className="bg-[#8C6D1F] text-white text-xs">
        <div className="max-w-6xl mx-auto px-4 py-1.5 flex items-center gap-2">
          <Landmark size={13} />
          Municipal supervision dashboard &middot; Multi-ward pilot, Uttar Pradesh
        </div>
      </div>

      {/* Title band */}
      <div className="bg-[#3F5426]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 pt-10 pb-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-[#E9C55F]/40 bg-[#E9C55F]/10 px-3 py-1 text-xs font-medium text-[#F0D488]">
            <BadgeCheck size={13} /> {user?.name || "Municipal Officer"}
          </div>
          <h1 className="font-display mt-4 text-3xl sm:text-4xl font-semibold text-white leading-[1.1]">
            Wards, routes &amp; citizen grievances.
          </h1>
        </div>

        {/* Stat band */}
        <div className="max-w-6xl mx-auto px-4 sm:px-6 pb-10 grid grid-cols-2 sm:grid-cols-4 divide-x divide-white/15">
          {[
            [
              AlertCircle,
              stats.open_complaints,
              "open complaints",
              `${stats.escalated_complaints} escalated`,
            ],
            [
              MapPinned,
              `${stats.routes_completed_today}/${stats.routes_today}`,
              "routes completed",
              `${stats.route_points_collected}/${stats.route_points_total} points collected`,
            ],
            [
              Users,
              stats.active_workers,
              "workers on duty",
              `${stats.wards_supervised} wards supervised`,
            ],
            [
              BadgeCheck,
              stats.resolved_this_week,
              "resolved this week",
              `avg ${stats.avg_resolution_hours} hrs to close`,
            ],
          ].map(([Icon, value, label, sub]) => (
            <div key={label} className="px-4 sm:px-6 py-2">
              <Icon size={16} className="text-[#F0D488]" />
              <p className="font-display mt-2 text-2xl sm:text-3xl font-semibold text-white">
                {value}
              </p>
              <p className="text-xs uppercase tracking-wide text-white/70 mt-0.5">{label}</p>
              <p className="font-mono-civic text-[11px] text-white/45 mt-1">{sub}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tab navigation */}
      <div className="bg-white border-b border-gray-200 sticky top-[57px] z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 flex gap-1 overflow-x-auto">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = tab.key === activeTab;
            return (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`inline-flex items-center gap-2 whitespace-nowrap px-4 py-3 text-sm font-semibold border-b-2 transition ${
                  isActive
                    ? "border-[#B8860B] text-[#1C2312]"
                    : "border-transparent text-gray-500 hover:text-[#1C2312]"
                }`}
              >
                <Icon size={15} /> {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <ActivePanel />
      </main>
    </div>
  );
}
