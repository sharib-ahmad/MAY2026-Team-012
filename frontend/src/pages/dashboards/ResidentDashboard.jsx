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
  ChevronDown,
  Bot,
  CalendarSearch,
  BookOpen,
  Recycle,
  User,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { ensureResidentSeed, listNotifications } from "../../lib/mockResidentData";
import heroBg from "../../assets/eco-banner-bg.webp";
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

// Shell mechanics brought in line with the recycler portal's app frame:
// one <aside> handling both the off-canvas mobile drawer and the
// desktop width-collapse (instead of a fully duplicated mobile-drawer
// block), a single 3-line toggle in the top bar driving both, and
// outside-click-to-close on the notification/account dropdowns. The
// resident portal's own identity — dark teal + hero photo on the
// sidebar, amber active-state accents — is unchanged.
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
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => {
    ensureResidentSeed(user);
  }, [user]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [activeTab]);

  const ActiveTab = useMemo(
    () => TABS.find((t) => t.key === activeTab)?.component || Home,
    [activeTab]
  );
  const notifications = useMemo(() => listNotifications(user.id), [user.id]);
  const notificationCount = notifications.length;

  const goTo = (key) => {
    setActiveTab(key);
    setSidebarOpen(false);
    setNotificationsOpen(false);
  };

  return (
    <div className="min-h-screen bg-[#FBF7EE]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
      `}</style>

      {/* Top bar — full width, sits above the sidebar/content split */}
      <header className="sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6 h-16 bg-[#0b362f] text-white border-b border-[#145047]">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setSidebarOpen((v) => !v)}
            className="text-white/80 hover:text-white"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold text-[#0B2F2C] shrink-0">
            V
          </span>
          <div className="leading-tight">
            <div className="font-display font-semibold text-white">Verdeza</div>
            <div className="text-[10px] text-white/50 uppercase tracking-wide hidden sm:block">
              Resident Portal
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 relative z-30">
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setNotificationsOpen((o) => !o);
                setProfileOpen(false);
              }}
              className="relative text-white/75 hover:text-white transition"
              aria-label="Notifications"
            >
              <Bell size={19} />
              {notificationCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-amber-500 text-white text-[9px] flex items-center justify-center">
                  {notificationCount}
                </span>
              )}
            </button>

            {notificationsOpen && (
              <div className="absolute right-0 mt-3 w-80 overflow-hidden rounded-3xl border border-white/10 bg-white text-slate-900 shadow-elevated z-40 text-left">
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
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setProfileOpen((o) => !o);
                setNotificationsOpen(false);
              }}
              className="flex items-center gap-2"
              aria-label="Account menu"
            >
              <span className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-semibold shrink-0">
                {user?.name ? user.name[0].toUpperCase() : <User size={14} />}
              </span>
              <ChevronDown
                size={14}
                className={`hidden sm:block text-white/50 transition-transform ${
                  profileOpen ? "rotate-180" : ""
                }`}
              />
            </button>

            {profileOpen && (
              <div className="absolute right-0 mt-3 w-56 bg-white rounded-2xl shadow-lg border border-black/5 py-2 z-40 text-left">
                <div className="px-3.5 py-2 border-b border-black/5 mb-1">
                  <div className="text-sm font-semibold text-gray-800 truncate">
                    {user?.name || "Resident"}
                  </div>
                  <div className="text-xs text-gray-400 truncate">{user?.email}</div>
                </div>
                <button
                  type="button"
                  onClick={logout}
                  className="w-full flex items-center gap-2 px-3.5 py-2 text-sm text-gray-600 hover:bg-black/[0.03] transition"
                >
                  <LogOut size={15} /> Sign out
                </button>
              </div>
            )}
          </div>
        </div>

        {(notificationsOpen || profileOpen) && (
          <div
            className="fixed inset-0 z-20"
            onClick={() => {
              setNotificationsOpen(false);
              setProfileOpen(false);
            }}
          />
        )}
      </header>

      <div className="flex">
        {/* Sidebar — one element handles both the off-canvas mobile
            drawer and the desktop width-collapse, instead of a
            duplicated mobile-only block */}
        <aside
          className={`fixed lg:sticky top-16 left-0 z-20 h-[calc(100vh-4rem)] shrink-0 flex flex-col justify-between overflow-y-auto overflow-x-hidden transition-all duration-200 bg-cover bg-center ${
            sidebarOpen ? "w-64 translate-x-0" : "w-64 -translate-x-full lg:w-0 lg:translate-x-0"
          }`}
          style={{
            backgroundImage: `linear-gradient(rgba(11,47,44,0.85), rgba(11,47,44,0.85)), url(${heroBg})`,
          }}
        >
          <nav className="w-64 px-3 py-4 space-y-1">
            {TABS.filter((t) => !t.hidden).map((tab) => {
              const Icon = tab.icon;
              const isActive = tab.key === activeTab;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => goTo(tab.key)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition ${
                    isActive
                      ? "bg-amber-500/15 text-amber-300"
                      : "text-white/70 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  <Icon size={17} className="shrink-0" /> {tab.label}
                </button>
              );
            })}
          </nav>

          <div className="w-64 p-3 border-t border-white/10 shrink-0">
            <div className="flex items-center gap-2.5 px-2 py-2">
              <span className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-sm font-semibold shrink-0">
                {user?.name ? user.name[0].toUpperCase() : <User size={15} />}
              </span>
              <div className="min-w-0 leading-tight">
                <div className="text-sm font-medium text-white truncate">
                  {user?.name || "Resident"}
                </div>
                <div className="text-xs text-white/50 truncate">{user?.email}</div>
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              className="w-full flex items-center gap-2 px-2 py-2 mt-1 text-sm text-white/60 hover:text-amber-300 rounded-xl hover:bg-white/5 transition"
            >
              <LogOut size={15} /> Sign out
            </button>
          </div>
        </aside>

        {/* Mobile scrim */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 top-16 bg-black/30 z-10 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 min-w-0">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
            <ActiveTab onNavigate={goTo} />
          </div>

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
        </main>
      </div>
    </div>
  );
}
