import { useCallback, useEffect, useMemo, useState } from "react";
import {
  LayoutDashboard,
  FileBarChart,
  LogOut,
  User,
  Bell,
  Menu,
  ChevronDown,
  Inbox,
  Cog,
  CheckCircle2,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import {
  listRecyclerNotifications,
  markAllRecyclerNotificationsRead,
  markRecyclerNotificationRead,
} from "../../lib/api";
import { usePolling } from "../../hooks/usePolling";
import Footer from "../../components/Footer";
import Reports from "./recycler/Reports";
import AssignedBatches from "./recycler/AssignedBatches";
import BatchProcessing from "./recycler/BatchProcessing";
import Dashboard from "./recycler/Dashboard";
import ProcessedBatches from "./recycler/ProcessedBatches";

const TABS = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard, component: Dashboard },
  { key: "assigned-batches", label: "Assigned Batches", icon: Inbox, component: AssignedBatches },
  { key: "batch-processing", label: "Batch Processing", icon: Cog, component: BatchProcessing },
  {
    key: "processed-batches",
    label: "Processed Batches",
    icon: CheckCircle2,
    component: ProcessedBatches,
  },
  { key: "reports", label: "Reports", icon: FileBarChart, component: Reports },
];

const RAIL = "#C4611A";

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

function backendNotificationRoute(title) {
  const lower = title.toLowerCase();
  if (lower.includes("assigned")) return { tab: "assigned-batches", icon: Inbox };
  if (lower.includes("batch")) return { tab: "assigned-batches", icon: Inbox };
  return { tab: "assigned-batches", icon: Bell };
}

export default function RecyclerDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState(TABS[0].key);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showNotifications, setShowNotifications] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [focusBatch, setFocusBatch] = useState(null);
  const [backendNotifications, setBackendNotifications] = useState([]);
  const [markingNotificationsRead, setMarkingNotificationsRead] = useState(false);

  const loadBackendNotifications = useCallback(async () => {
    if (!user) return;
    try {
      setBackendNotifications(await listRecyclerNotifications());
    } catch {
      // Shelf/claims tabs remain usable if notifications are temporarily unavailable.
    }
  }, [user]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadBackendNotifications();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadBackendNotifications]);
  usePolling(loadBackendNotifications, 30000);

  const goToBatch = (tab, batchId) => {
    setFocusBatch(batchId ? { tab, batchId } : null);
    setActiveTab(tab);
    setSidebarOpen(false);
    setShowNotifications(false);
  };

  const notifications = useMemo(() => {
    const live = backendNotifications.map((notification) => {
      const route = backendNotificationRoute(notification.title);
      return {
        id: notification.id,
        title: notification.title,
        time: notification.created_at,
        icon: route.icon,
        tab: route.tab,
        batchId: null,
        isRead: notification.is_read,
        source: "backend",
      };
    });
    return live.slice(0, 8);
  }, [backendNotifications]);

  const hasUnreadBackend = backendNotifications.some((notification) => !notification.is_read);

  const openNotification = async (notification) => {
    if (notification.source === "backend" && notification.id && !notification.isRead) {
      try {
        await markRecyclerNotificationRead(notification.id);
        setBackendNotifications((items) =>
          items.map((item) => (item.id === notification.id ? { ...item, is_read: true } : item))
        );
      } catch {
        // Keep the notification visible; it will be retried on the next refresh.
      }
    }
    goToBatch(notification.tab, notification.batchId);
  };

  const markAllNotificationsRead = async () => {
    if (!hasUnreadBackend || markingNotificationsRead) return;
    setMarkingNotificationsRead(true);
    try {
      await markAllRecyclerNotificationsRead();
      setBackendNotifications((items) => items.map((item) => ({ ...item, is_read: true })));
    } catch {
      // The next poll will retain the current state if this request fails.
    } finally {
      setMarkingNotificationsRead(false);
    }
  };

  const ActivePanel = TABS.find((t) => t.key === activeTab)?.component ?? TABS[0].component;

  return (
    <div className="min-h-screen bg-[#FBF7F0]">
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
          <div
            className="flex items-center gap-2.5 cursor-pointer select-none"
            onClick={() => {
              window.location.href = "/";
            }}
          >
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
                    Recent Activity
                  </span>
                  {hasUnreadBackend && (
                    <button
                      type="button"
                      onClick={markAllNotificationsRead}
                      disabled={markingNotificationsRead}
                      className="text-[11px] font-semibold text-[#C4611A] hover:underline disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {markingNotificationsRead ? "Marking…" : "Mark all as read"}
                    </button>
                  )}
                </div>
                {notifications.length === 0 ? (
                  <div className="px-3.5 py-3 text-sm text-gray-400">No recent activity yet.</div>
                ) : (
                  notifications.map((n, i) => {
                    const Icon = n.icon;
                    return (
                      <button
                        key={n.id || `mock-${i}`}
                        type="button"
                        onClick={() => openNotification(n)}
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

        {sidebarOpen && (
          <div
            className="fixed inset-0 top-16 bg-black/30 z-10 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

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
