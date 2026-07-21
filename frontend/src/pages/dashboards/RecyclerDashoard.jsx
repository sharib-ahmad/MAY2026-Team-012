import { useMemo, useState } from "react";
import {
  LayoutDashboard,
  Store,
  Truck,
  FileBarChart,
  LogOut,
  User,
  Bell,
  Menu,
  ChevronDown,
  ShieldAlert,
  PackageCheck,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { listBatches } from "../../lib/mockRecyclerData";
import Footer from "../../components/Footer";
import Home from "./recycler/Home";
import CommunityShelf from "./recycler/CommunityShelf";
import MyClaims from "./recycler/MyClaims";
import Reports from "./recycler/Reports";

// Recycler facility workspace covering Epic 4 (B2G Material Inventory
// Ledger): browse/claim the shared batch community shelf (Story 4.1),
// review quality/contamination info (Story 4.2), and confirm pickups
// (Story 4.3). Entirely backend-free — see lib/mockRecyclerData.js.
//
// Shell mirrors the resident portal's app frame — sticky top bar +
// left nav rail with the active-item highlight and account card —
// but stays entirely on the recycler's terracotta/clay palette
// already established in Home.jsx (no green carried over).
const TABS = [
  { key: "home", label: "Home", icon: LayoutDashboard, component: Home },
  { key: "communityshelf", label: "Community Shelf", icon: Store, component: CommunityShelf },
  { key: "claims", label: "My Claims", icon: Truck, component: MyClaims },
  { key: "reports", label: "Reports", icon: FileBarChart, component: Reports },
];

const RAIL = "#C4611A"; // single brand color — top bar & sidebar
// Active/contrast states are done with white/black opacity overlays on
// top of RAIL rather than a second hex, per request to stay on one color.

function formatTime(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const startOfDay = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate());
  const diffDays = Math.round((startOfDay(new Date()) - startOfDay(d)) / 86_400_000);
  if (diffDays <= 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

export default function RecyclerDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState(TABS[0].key);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  // Lets "Recent Activity" on Home deep-link straight to a specific batch:
  // it sets { tab, batchId } and switches tabs; the target panel picks up
  // focusBatchId on mount, opens that batch's own detail modal, then clears it.
  const [focusBatch, setFocusBatch] = useState(null);

  const goToBatch = (tab, batchId) => {
    setFocusBatch({ tab, batchId });
    setActiveTab(tab);
    setSidebarOpen(false);
    setShowNotifications(false);
  };

  const notifications = useMemo(() => {
    if (!user) return [];
    // Same backend-free source as Home's activity feed — just trimmed to
    // one entry per event type so the bell stays a quick glance, not a log.
    const byDateDesc = (key) => (a, b) => new Date(b[key] || 0) - new Date(a[key] || 0);
    const available = listBatches({ status: "AVAILABLE" }).sort(byDateDesc("drop_date"));
    const unsafe = available.filter((b) => b.quality_status === "UNSAFE");
    const claimed = listBatches({ status: "CLAIMED", mine: true, recyclerUser: user }).sort(
      byDateDesc("claim_expires_at")
    );
    const collected = listBatches({ status: "COLLECTED", mine: true, recyclerUser: user }).sort(
      byDateDesc("collected_at")
    );

    const items = [];
    if (unsafe[0]) {
      items.push({
        title: `Batch #${unsafe[0].ref_code} flagged unsafe`,
        time: unsafe[0].drop_date,
        icon: ShieldAlert,
        tone: "danger",
        tab: "communityshelf",
        batchId: unsafe[0].id,
      });
    }
    if (claimed[0]) {
      items.push({
        title: `Batch #${claimed[0].ref_code} awaiting pickup`,
        time: claimed[0].claim_expires_at,
        icon: Truck,
        tab: "claims",
        batchId: claimed[0].id,
      });
    }
    if (available[0]) {
      items.push({
        title: `Batch #${available[0].ref_code} listed in community shelf`,
        time: available[0].drop_date,
        icon: Store,
        tab: "communityshelf",
        batchId: available[0].id,
      });
    }
    if (collected[0]) {
      items.push({
        title: `Batch #${collected[0].ref_code} collected`,
        time: collected[0].collected_at,
        icon: PackageCheck,
        tab: "reports",
        batchId: collected[0].id,
      });
    }
    return items;
  }, [user]);

  const ActivePanel = TABS.find((t) => t.key === activeTab)?.component ?? TABS[0].component;

  return (
    <div className="min-h-screen bg-[#FBF7F0]">
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
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 text-lg font-bold text-[#0B2F2C] shrink-0">
            V
          </span>
          <div className="leading-tight">
            <div className="text-base sm:text-lg font-serif font-bold tracking-wide text-white">
              Verdeza
            </div>
            <div className="text-[10px] sm:text-xs font-semibold tracking-wider text-white/60">
              Recycler Portal
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
                <div className="px-3.5 py-1.5 text-[10px] font-semibold tracking-wide text-gray-400 uppercase">
                  Recent Activity
                </div>
                {notifications.length === 0 ? (
                  <div className="px-3.5 py-3 text-sm text-gray-400">No recent activity yet.</div>
                ) : (
                  notifications.map((n, i) => {
                    const Icon = n.icon;
                    return (
                      <button
                        key={i}
                        type="button"
                        onClick={() => goToBatch(n.tab, n.batchId)}
                        className="w-full flex items-start gap-2.5 px-3.5 py-2 text-left hover:bg-black/[0.03] transition"
                      >
                        <span
                          className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
                          style={{
                            backgroundColor: n.tone === "danger" ? "#FEE2E2" : "#FBEAE0",
                            color: n.tone === "danger" ? "#DC2626" : RAIL,
                          }}
                        >
                          <Icon size={13} />
                        </span>
                        <span className="min-w-0">
                          <span className="block text-sm font-medium text-gray-800 leading-tight truncate">
                            {n.title}
                          </span>
                          <span className="block text-xs text-gray-400 mt-0.5">
                            {formatTime(n.time)}
                          </span>
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
                    {user?.name || "Recycler"}
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
                  onClick={() => {
                    setActiveTab(tab.key);
                    setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition ${
                    isActive
                      ? "bg-white/20 text-white ring-1 ring-white/30"
                      : "text-white/60 hover:text-white/90 hover:bg-white/10"
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
                  {user?.name || "Recycler"}
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
          <ActivePanel
            onOpenBatch={goToBatch}
            focusBatchId={focusBatch?.tab === activeTab ? focusBatch.batchId : null}
            onFocusConsumed={() => setFocusBatch(null)}
          />
          <Footer />
        </main>
      </div>
    </div>
  );
}
