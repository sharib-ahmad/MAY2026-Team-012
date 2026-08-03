import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  LayoutDashboard,
  Landmark,
  LogOut,
  MapPinned,
  Recycle,
  Users,
  Menu,
  Bell,
  ChevronDown,
  User,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import Footer from "../../components/Footer";
import Overview from "./manager/Overview";
import Complaints from "./manager/Complaints";
import BulkCollections from "./manager/BulkCollections";
import CrewManagement from "./manager/CrewManagement";
import BatchManagement from "./manager/BatchManagement";
import { getManagerDashboard, markManagerNotificationsRead } from "../../lib/api";

// Shell mirrors the recycler portal's app frame — sticky top bar +
// collapsible left nav rail (off-canvas drawer on mobile, width-collapse
// on desktop) with bell/account dropdowns and a footer — restyled onto
// a single theme color (#14171F) for the chrome, per request. The
// official strip and stat band keep their existing olive/goldenrod
// identity (same treatment as the admin portal: unique page content
// isn't forced onto the shell's single color) and now live inside the
// content column as a contained card next to the sidebar, rather than
// a full-bleed band sitting above it.
const TABS = [
  { key: "overview", label: "Overview", icon: LayoutDashboard, component: Overview },
  {
    key: "bulk-collections",
    label: "Bulk collections",
    icon: MapPinned,
    component: BulkCollections,
  },
  { key: "complaints", label: "Complaints", icon: AlertCircle, component: Complaints },
  { key: "crew-management", label: "Crew management", icon: Users, component: CrewManagement },
  {
    key: "batch-management",
    label: "Batch management",
    icon: Recycle,
    component: BatchManagement,
  },
];

const RAIL = "#14171F"; // single theme color — top bar & sidebar
// Active/contrast states use white/black opacity overlays on top of
// RAIL rather than a second hex, matching the recycler shell.

export default function ManagerDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState(TABS[0].key);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [dashboardError, setDashboardError] = useState("");
  const [markingNotificationsRead, setMarkingNotificationsRead] = useState(false);

  const ActivePanel = TABS.find((t) => t.key === activeTab)?.component ?? TABS[0].component;

  useEffect(() => {
    let active = true;
    getManagerDashboard()
      .then((data) => active && setDashboardData(data))
      .catch(() => active && setDashboardError("Live dashboard data could not be loaded."));
    return () => {
      active = false;
    };
  }, []);

  const goToTab = (tab) => {
    setActiveTab(tab);
    setSidebarOpen(false);
    setShowNotifications(false);
  };

  const notifications = useMemo(
    () =>
      (dashboardData?.notifications || []).map((notification) => {
        const title = notification.title.toLowerCase();
        const isBatch = title.includes("batch");
        const isComplaint = title.includes("complaint");
        return {
          ...notification,
          tab: isBatch ? "batch-management" : isComplaint ? "complaints" : "overview",
          icon: isBatch ? Recycle : isComplaint ? AlertCircle : MapPinned,
        };
      }),
    [dashboardData]
  );

  const markAllNotificationsRead = async () => {
    if (!notifications.length || markingNotificationsRead) return;
    setMarkingNotificationsRead(true);
    try {
      await markManagerNotificationsRead();
      setDashboardData((current) => (current ? { ...current, notifications: [] } : current));
      setShowNotifications(false);
    } catch {
      setDashboardError("Unable to mark notifications as read.");
    } finally {
      setMarkingNotificationsRead(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6F3EA]">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=IBM+Plex+Mono:wght@500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
        .font-mono-civic { font-family: 'IBM Plex Mono', monospace; }
      `}</style>

      {/* Top bar — full width, sits above the sidebar/content split */}
      <header
        className="sticky top-0 z-30 flex items-center justify-between px-4 sm:px-6 h-16 border-b border-black/10"
        style={{ backgroundColor: RAIL }}
      >
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setSidebarOpen((v) => !v)}
            className="text-white/80 hover:text-white"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>
          <span
            className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold shrink-0"
            style={{ color: RAIL }}
          >
            V
          </span>
          <div className="leading-tight">
            <div className="font-semibold text-white">Verdeza</div>
            <div className="text-[11px] text-white/60">Municipal Operations</div>
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
              className="relative text-white/70 hover:text-white transition"
              aria-label="Notifications"
            >
              <Bell size={18} />
              {notifications.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-white" />
              )}
            </button>

            {showNotifications && (
              <div className="absolute right-0 mt-3 w-72 bg-white rounded-2xl shadow-lg border border-black/5 py-2 z-40 text-left">
                <div className="flex items-center justify-between gap-3 px-3.5 py-1.5">
                  <span className="text-[10px] font-semibold tracking-wide text-gray-400 uppercase">
                    Ward Status
                  </span>
                  <button
                    type="button"
                    onClick={markAllNotificationsRead}
                    disabled={markingNotificationsRead || notifications.length === 0}
                    className="text-[11px] font-semibold text-[#3F5426] hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {markingNotificationsRead ? "Marking…" : "Mark all as read"}
                  </button>
                </div>
                {notifications.map((n, i) => {
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
                          backgroundColor: n.tone === "danger" ? "#FEE2E2" : "#EDEDF2",
                          color: n.tone === "danger" ? "#DC2626" : RAIL,
                        }}
                      >
                        <Icon size={13} />
                      </span>
                      <span className="text-sm font-medium text-gray-800 leading-snug">
                        {n.title}
                      </span>
                    </button>
                  );
                })}
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
                className="w-7 h-7 rounded-full bg-white flex items-center justify-center text-xs font-semibold shrink-0"
                style={{ color: RAIL }}
              >
                {user?.name ? user.name[0].toUpperCase() : <User size={14} />}
              </span>
              <ChevronDown
                size={14}
                className={`text-white/50 hidden sm:block transition-transform ${
                  showAccountMenu ? "rotate-180" : ""
                }`}
              />
            </button>

            {showAccountMenu && (
              <div className="absolute right-0 mt-3 w-56 bg-white rounded-2xl shadow-lg border border-black/5 py-2 z-40 text-left">
                <div className="px-3.5 py-2 border-b border-black/5 mb-1">
                  <div className="text-sm font-semibold text-gray-800 truncate">
                    {user?.name || "Municipal Officer"}
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

      {/* Official strip — full width, sits with the top bar */}
      <div className="bg-[#8C6D1F] text-white text-xs">
        <div className="px-4 sm:px-6 py-1.5 flex items-center gap-2">
          <Landmark size={13} />
          Municipal supervision dashboard &middot; Multi-ward pilot, Uttar Pradesh
        </div>
      </div>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`fixed lg:sticky top-16 left-0 z-20 h-[calc(100vh-4rem)] shrink-0 flex flex-col justify-between overflow-y-auto overflow-x-hidden transition-all duration-200 ${
            sidebarOpen ? "w-64 translate-x-0" : "w-64 -translate-x-full lg:w-0 lg:translate-x-0"
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
                      ? "bg-white/10 text-white ring-1 ring-white/30"
                      : "text-white/60 hover:text-white/90 hover:bg-white/5"
                  }`}
                >
                  <Icon size={17} /> {tab.label}
                </button>
              );
            })}
          </nav>

          <div className="w-64 p-3 border-t border-white/10 shrink-0">
            <div className="flex items-center gap-2.5 px-2 py-2">
              <span
                className="w-8 h-8 rounded-full bg-white flex items-center justify-center text-sm font-semibold shrink-0"
                style={{ color: RAIL }}
              >
                {user?.name ? user.name[0].toUpperCase() : <User size={15} />}
              </span>
              <div className="min-w-0 leading-tight">
                <div className="text-sm font-semibold text-white truncate">
                  {user?.name || "Municipal Officer"}
                </div>
                <div className="text-xs text-white/40 truncate">{user?.email}</div>
              </div>
            </div>
            <button
              type="button"
              onClick={logout}
              className="w-full flex items-center gap-2 px-2 py-2 mt-1 text-sm text-white/60 hover:text-white rounded-xl hover:bg-white/5 transition"
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
            {dashboardError ? (
              <div className="rounded-2xl border border-red-200 bg-red-50 p-5 text-sm text-red-800">
                {dashboardError}
              </div>
            ) : !dashboardData ? (
              <div className="rounded-2xl border border-gray-200 bg-white p-8 text-sm text-gray-500">
                Loading live ward operations data…
              </div>
            ) : (
              <ActivePanel data={dashboardData} />
            )}
          </div>
          <Footer />
        </main>
      </div>
    </div>
  );
}
