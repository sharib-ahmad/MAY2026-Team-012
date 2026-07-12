import { useEffect, useMemo, useState } from "react";
import {
  Home as HomeIcon,
  PackagePlus,
  Package,
  Route,
  AlertCircle,
  Gift,
  Leaf,
  LogOut,
  Bell,
  Menu,
  X,
  ChevronDown,
  Bot,
  CalendarSearch,
  BookOpen,
  Recycle,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { ensureResidentSeed, listNotifications } from "../../lib/mockResidentData";
import heroBg from "../../assets/eco-banner-bg.jpg";
import Footer from "../../components/Footer";

import Home from "./resident/Home";
import SchedulePickup from "./resident/SchedulePickup";
import MyPickups from "./resident/MyPickups";
import CollectionFlow from "./resident/CollectionFlow";
import Tickets from "./resident/Tickets";
import Marketplace from "./resident/Marketplace";
import MyDonations from "./resident/MyDonations";
import CreateDonation from "./resident/CreateDonation";
import MyClaims from "./resident/MyClaims";
import Impact from "./resident/Impact";
import EcoBotChat from "./resident/EcoBotChat";
import ScheduleLookup from "./resident/ScheduleLookup";
import SortingGuide from "./resident/SortingGuide";
import RecyclingTransparency from "./resident/RecyclingTransparency";

const TABS = [
  { key: "home", label: "Home", icon: HomeIcon, component: Home },
  { key: "lookup", label: "Schedule Look-up", icon: CalendarSearch, component: ScheduleLookup },
  { key: "schedule", label: "Schedule Pickup", icon: PackagePlus, component: SchedulePickup },
  { key: "pickups", label: "My Pickups", icon: Package, component: MyPickups },
  { key: "flow", label: "Today's Collection", icon: Route, component: CollectionFlow },
  { key: "tickets", label: "Tickets", icon: AlertCircle, component: Tickets },
  { key: "sorting", label: "Sorting Guide", icon: BookOpen, component: SortingGuide },
  { key: "marketplace", label: "Marketplace", icon: Gift, component: Marketplace },
  { key: "donations", label: "My Donations", icon: Package, component: MyDonations },
  { key: "donate", label: "Donate Item", icon: Gift, component: CreateDonation, hidden: true },
  { key: "claims", label: "My Claims", icon: Gift, component: MyClaims },
  { key: "impact", label: "My Impact", icon: Leaf, component: Impact },
  { key: "ecobot", label: "EcoBot Chat", icon: Bot, component: EcoBotChat },
  {
    key: "recycling",
    label: "Recycling Transparency ",
    icon: Recycle,
    component: RecyclingTransparency,
  },
];

export default function ResidentDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("home");
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => {
    ensureResidentSeed(user);
  }, [user]);

  const ActiveTab = useMemo(
    () => TABS.find((t) => t.key === activeTab)?.component || Home,
    [activeTab]
  );
  const activeLabel = TABS.find((t) => t.key === activeTab)?.label || "Home";
  const notifications = useMemo(() => listNotifications(user.id), [user.id]);
  const notificationCount = notifications.length;

  const goTo = (key) => {
    setActiveTab(key);
    setMobileNavOpen(false);
    setNotificationsOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#FBF7EE] lg:flex">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
      `}</style>

      {/* ── Sidebar (desktop) ───────────────────────────────────── */}
      <aside
        className={`hidden lg:flex lg:flex-col ${
          sidebarCollapsed ? "w-20" : "w-64"
        } shrink-0 bg-[#0B2F2C] text-white p-5 sticky top-0 h-screen transition-[width] duration-200 ease-out bg-cover bg-center`}
        style={{
          backgroundImage: `linear-gradient(rgba(11,47,44,0.85), rgba(11,47,44,0.85)), url(${heroBg})`,
        }}
      >
        <div
          className={`flex items-center mb-8 px-1 ${sidebarCollapsed ? "justify-center" : "justify-end"}`}
        >
          <button
            type="button"
            onClick={() => setSidebarCollapsed((c) => !c)}
            title={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
            className="shrink-0 p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/5 transition"
          >
            <Menu size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto">
          {TABS.filter((t) => !t.hidden).map((tab) => {
            const Icon = tab.icon;
            const isActive = tab.key === activeTab;
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => goTo(tab.key)}
                title={sidebarCollapsed ? tab.label : undefined}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                  sidebarCollapsed ? "justify-center px-0" : ""
                } ${
                  isActive
                    ? "bg-amber-500/15 text-amber-300"
                    : "text-white/70 hover:bg-white/5 hover:text-white"
                }`}
              >
                <Icon size={17} className="shrink-0" />
                {!sidebarCollapsed && tab.label}
              </button>
            );
          })}
        </nav>

        <div className="pt-4 mt-4 border-t border-white/10">
          <div
            className={`flex items-center gap-3 px-1 ${sidebarCollapsed ? "justify-center" : ""}`}
          >
            <div className="w-9 h-9 rounded-full bg-primary flex items-center justify-center font-semibold text-sm shrink-0">
              {user?.name?.[0]?.toUpperCase() || "R"}
            </div>
            {!sidebarCollapsed && (
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium truncate">{user?.name || "Resident"}</p>
                <p className="text-[11px] text-white/50 truncate">{user?.email}</p>
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={logout}
            title={sidebarCollapsed ? "Sign out" : undefined}
            className={`w-full mt-3 flex items-center gap-2 text-white/60 hover:text-amber-300 text-sm px-1 ${
              sidebarCollapsed ? "justify-center" : ""
            }`}
          >
            <LogOut size={15} className="shrink-0" />
            {!sidebarCollapsed && "Sign out"}
          </button>
        </div>
      </aside>

      {/* ── Mobile nav drawer ───────────────────────────────────── */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setMobileNavOpen(false)} />
          <aside
            className="absolute left-0 top-0 h-full w-72 bg-[#0B2F2C] text-white p-5 flex flex-col bg-cover bg-center"
            style={{
              backgroundImage: `linear-gradient(rgba(11,47,44,0.85), rgba(11,47,44,0.85)), url(${heroBg})`,
            }}
          >
            <div className="flex items-center justify-between mb-8">
              <div className="flex items-center gap-2">
                <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold text-[#0B2F2C]">
                  V
                </span>
                <span className="font-display font-semibold">Verdeza</span>
              </div>
              <button type="button" onClick={() => setMobileNavOpen(false)}>
                <X size={20} />
              </button>
            </div>
            <nav className="flex-1 space-y-1 overflow-y-auto">
              {TABS.filter((t) => !t.hidden).map((tab) => {
                const Icon = tab.icon;
                const isActive = tab.key === activeTab;
                return (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => goTo(tab.key)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                      isActive ? "bg-amber-500/15 text-amber-300" : "text-white/70"
                    }`}
                  >
                    <Icon size={17} />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
            <button
              type="button"
              onClick={logout}
              className="flex items-center gap-2 text-white/60 hover:text-amber-300 text-sm px-1 pt-4 border-t border-white/10 mt-4"
            >
              <LogOut size={15} /> Sign out
            </button>
          </aside>
        </div>
      )}

      {/* ── Main column ─────────────────────────────────────────── */}
      <div className="flex-1 min-w-0">
        <header className="bg-[#0b362f] text-white border-b border-[#145047] px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-3 flex-1">
            <button
              type="button"
              className="lg:hidden text-white/75 hover:text-white"
              onClick={() => setMobileNavOpen(true)}
            >
              <Menu size={22} />
            </button>
            <div className="flex items-center gap-2">
              <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold text-[#0B2F2C]">
                V
              </span>
              <div className="leading-tight">
                <div className="font-display font-semibold text-white">Verdeza</div>
                <div className="text-[10px] text-white/50 uppercase tracking-wide hidden sm:block">
                  Resident Portal
                </div>
              </div>
            </div>
            <div className="hidden sm:block max-w-sm w-full" />
            <p className="sm:hidden font-display font-semibold text-white">{activeLabel}</p>
          </div>
          <div className="flex items-center gap-4 relative">
            <button
              type="button"
              className="relative text-white/75 hover:text-white"
              onClick={() => setNotificationsOpen((o) => !o)}
            >
              <Bell size={19} />
              {notificationCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-white text-[9px] flex items-center justify-center">
                  {notificationCount}
                </span>
              )}
            </button>
            {notificationsOpen && (
              <div className="absolute right-0 top-full mt-3 w-80 overflow-hidden rounded-3xl border border-white/10 bg-white text-slate-900 shadow-elevated">
                <div className="px-4 py-3 border-b border-slate-100">
                  <p className="text-sm font-semibold">Notifications</p>
                  <p className="text-xs text-slate-500">{notificationCount} new</p>
                </div>
                <div className="max-h-72 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <div className="p-4 text-sm text-slate-500">No new notifications.</div>
                  ) : (
                    notifications.map((n) => (
                      <div key={n.id} className="border-b border-slate-100 p-4 last:border-b-0">
                        <p className="font-medium text-sm text-slate-900">{n.title}</p>
                        <p className="text-xs text-slate-500 mt-1">{n.body}</p>
                        <p className="text-[10px] text-slate-400 mt-2">
                          {new Date(n.created_at).toLocaleString()}
                        </p>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
            <button
              type="button"
              onClick={() => setProfileOpen((o) => !o)}
              className="flex items-center gap-2"
            >
              <div className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-semibold">
                {user?.name?.[0]?.toUpperCase() || "R"}
              </div>
              <ChevronDown size={14} className="hidden sm:block text-gray-400" />
            </button>
            {profileOpen && (
              <div className="absolute right-4 sm:right-6 top-14 bg-white rounded-card shadow-elevated border border-gray-100 w-44 py-1 z-30">
                <div className="px-3 py-2 border-b border-gray-50">
                  <p className="text-sm font-medium truncate">{user?.name}</p>
                  <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 flex items-center gap-2"
                >
                  <LogOut size={14} /> Sign out
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <ActiveTab onNavigate={goTo} />
        </main>

        <Footer />

        {activeTab !== "ecobot" && (
          <button
            type="button"
            onClick={() => goTo("ecobot")}
            className="fixed bottom-6 right-6 z-30 w-14 h-14 rounded-full bg-primary text-white shadow-elevated flex items-center justify-center hover:bg-primary/90 hover-lift"
            title="Ask EcoBot"
          >
            <Bot size={22} />
          </button>
        )}
      </div>
    </div>
  );
}
