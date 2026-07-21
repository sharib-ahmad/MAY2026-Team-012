import { useMemo, useState } from "react";
import {
  Users,
  MapPin,
  AlertTriangle,
  LogOut,
  Landmark,
  UserPlus,
  ScrollText,
  BookOpen,
  Menu,
  Bell,
  ChevronDown,
  User,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import DATA from "../../data/admin_portal_data.json";
import Accounts from "./admin/Accounts";
import Wards from "./admin/Wards";
import Logs from "./admin/Logs";
import CreateAccount from "./admin/CreateAccount";
import SortingGuideEditor from "./admin/SortingGuideEditor";

// Shell mirrors the recycler portal's app frame — sticky top bar +
// collapsible left nav rail (off-canvas drawer on mobile, width-collapse
// on desktop) with bell/account dropdowns and a footer — recolored to a
// white theme per request. INK is the admin portal's original dark teal,
// kept only as the "ink" color for the amber badge's letter and active
// accents, not as a shell background anymore.
const TABS = [
  { key: "accounts", label: "Accounts", icon: Users, component: Accounts },
  { key: "wards", label: "Wards", icon: MapPin, component: Wards },
  { key: "logs", label: "Logs", icon: ScrollText, component: Logs },
  { key: "create", label: "Create Account", icon: UserPlus, component: CreateAccount },
  { key: "sorting-guide", label: "Sorting Guide", icon: BookOpen, component: SortingGuideEditor },
];

const RAIL = "#FFFFFF"; // white theme — top bar & sidebar
const INK = "#0B2F2C"; // admin portal's original dark teal — used only as accent ink now

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState(TABS[0].key);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);

  const { stats } = DATA;
  const ActivePanel = TABS.find((t) => t.key === activeTab)?.component ?? TABS[0].component;

  const goToTab = (tab) => {
    setActiveTab(tab);
    setSidebarOpen(false);
    setShowNotifications(false);
  };

  // No separate activity feed in this dataset — the bell surfaces the
  // same stats the title band already shows, each deep-linking to the
  // tab that explains it.
  const notifications = useMemo(
    () =>
      [
        stats.pending_users > 0 && {
          title: `${stats.pending_users} account${stats.pending_users === 1 ? "" : "s"} pending approval`,
          tab: "accounts",
          icon: UserPlus,
        },
        stats.errors_last_24h > 0 && {
          title: `${stats.errors_last_24h} error${stats.errors_last_24h === 1 ? "" : "s"} in the last 24h`,
          tab: "logs",
          icon: AlertTriangle,
          tone: "danger",
        },
        {
          title: `${stats.total_zones} wards configured, ${stats.active_users} active users`,
          tab: "wards",
          icon: MapPin,
        },
      ].filter(Boolean),
    [stats]
  );

  return (
    <div className="min-h-screen bg-[#F7F5F0]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
        .font-mono-civic { font-family: 'IBM Plex Mono', monospace; }
      `}</style>

      {/* Top bar — full width, sits above the sidebar/content split */}
      <header
        className="sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6 h-16 border-b border-gray-200"
        style={{ backgroundColor: RAIL }}
      >
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setSidebarOpen((v) => !v)}
            className="text-gray-500 hover:text-gray-900"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>
          <span
            className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold shrink-0"
            style={{ color: INK }}
          >
            V
          </span>
          <div className="leading-tight">
            <div className="font-display font-semibold text-gray-800">Verdeza</div>
            <div className="text-[10px] text-gray-400 tracking-wide hidden sm:block">
              Admin Portal
            </div>
          </div>
        </div>

        <div className="flex items-center gap-4 relative z-30">
          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setShowNotifications((v) => !v);
                setShowAccountMenu(false);
              }}
              className="relative text-gray-500 hover:text-amber-600 transition"
              aria-label="Notifications"
            >
              <Bell size={18} />
              {notifications.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-amber-500" />
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-3 w-72 bg-white rounded-2xl shadow-lg border border-black/5 py-2 z-40 text-left">
                <div className="px-3.5 py-1.5 text-[10px] font-semibold tracking-wide text-gray-400 uppercase">
                  Platform Status
                </div>
                {notifications.length === 0 ? (
                  <div className="px-3.5 py-3 text-sm text-gray-400">
                    Nothing to flag right now.
                  </div>
                ) : (
                  notifications.map((n, i) => {
                    const Icon = n.icon;
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => goToTab(n.tab)}
                        className="w-full flex items-start gap-2.5 px-3.5 py-2 text-left hover:bg-black/[0.03] transition"
                      >
                        <span
                          className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
                          style={{
                            backgroundColor: n.tone === "danger" ? "#FEE2E2" : "#FDF3D8",
                            color: n.tone === "danger" ? "#DC2626" : "#8A6A10",
                          }}
                        >
                          <Icon size={13} />
                        </span>
                        <span className="text-sm font-medium text-gray-800 leading-snug">
                          {n.title}
                        </span>
                      </button>
                    );
                  })
                )}
              </div>
            )}
          </div>

          <div className="relative">
            <button
              type="button"
              onClick={() => {
                setShowAccountMenu((v) => !v);
                setShowNotifications(false);
              }}
              className="flex items-center gap-2"
              aria-label="Account menu"
            >
              <span
                className="w-7 h-7 rounded-full bg-amber-400 flex items-center justify-center text-xs font-bold shrink-0"
                style={{ color: INK }}
              >
                {user?.name ? user.name[0].toUpperCase() : <User size={14} />}
              </span>
              <ChevronDown
                size={14}
                className={`text-gray-400 hidden sm:block transition-transform ${
                  showAccountMenu ? "rotate-180" : ""
                }`}
              />
            </button>

            {showAccountMenu && (
              <div className="absolute right-0 mt-3 w-56 bg-white rounded-2xl shadow-lg border border-black/5 py-2 z-40 text-left">
                <div className="px-3.5 py-2 border-b border-black/5 mb-1">
                  <div className="text-sm font-semibold text-gray-800 truncate">
                    {user?.name || "System Admin"}
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

        {(showNotifications || showAccountMenu) && (
          <div
            className="fixed inset-0 z-20"
            onClick={() => {
              setShowNotifications(false);
              setShowAccountMenu(false);
            }}
          />
        )}
      </header>

      {/* Official strip — full width, sits with the top bar rather than
          inside the content column */}
      <div className="bg-amber-600 text-white text-xs">
        <div className="px-4 sm:px-6 py-1.5 flex items-center gap-2">
          <Landmark size={13} />
          Restricted administrative panel &middot; Role-Based Access Control enforced
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`fixed lg:sticky top-16 left-0 z-20 h-[calc(100vh-4rem)] shrink-0 flex flex-col justify-between overflow-y-auto overflow-x-hidden border-r border-gray-200 transition-all duration-200 ${
            sidebarOpen
              ? "w-64 translate-x-0"
              : "w-64 -translate-x-full lg:w-0 lg:translate-x-0 lg:border-r-0"
          }`}
          style={{ backgroundColor: RAIL }}
        >
          <nav className="w-64 px-3 py-4 space-y-1">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = tab.key === activeTab;
              return (
                <button
                  key={tab.key}
                  type="button"
                  onClick={() => goToTab(tab.key)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition ${
                    isActive
                      ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200"
                      : "text-gray-500 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  <Icon size={17} /> {tab.label}
                </button>
              );
            })}
          </nav>

          <div className="w-64 p-3 border-t border-gray-200 shrink-0">
            <div className="flex items-center gap-2.5 px-2 py-2">
              <span
                className="w-8 h-8 rounded-full bg-amber-400 flex items-center justify-center text-sm font-bold shrink-0"
                style={{ color: INK }}
              >
                {user?.name ? user.name[0].toUpperCase() : <User size={15} />}
              </span>
              <div className="min-w-0 leading-tight">
                <div className="text-sm font-semibold text-gray-800 truncate">
                  {user?.name || "System Admin"}
                </div>
                <div className="text-xs text-gray-400 truncate">{user?.email}</div>
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              className="w-full flex items-center gap-2 px-2 py-2 mt-1 text-sm text-gray-500 hover:text-amber-700 rounded-xl hover:bg-amber-50 transition"
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
          <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 sm:py-8">
            <ActivePanel />
          </div>
        </main>
      </div>
    </div>
  );
}
