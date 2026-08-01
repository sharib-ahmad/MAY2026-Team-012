import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Menu,
  LogOut,
  User,
  LayoutDashboard,
  ChevronDown,
  Bell,
  ClipboardCheck,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import CollectorRoutes from "./collector/Routes";
import CompletedCollections from "./collector/CompletedCollections";
import {
  listCollectorNotifications,
  markAllCollectorNotificationsRead,
  markCollectorNotificationRead,
} from "../../lib/api";
import { usePolling } from "../../hooks/usePolling";

// Collector workspace shell — mirrors the Recycler Dashboard's app frame
// (top bar with account dropdown, left nav rail with an account card +
// sign out at the bottom, and a Footer at the end of the content area)
// while keeping the Collector's existing navy/amber Verdeza branding.
//
// Layout note: the whole shell is locked to the viewport height
// (h-screen + overflow-hidden) with only <main> scrolling internally.
// This avoids relying on `sticky`, which silently breaks whenever any
// ancestor has `overflow-x-hidden` (a common gotcha) — that was the
// cause of the sidebar appearing to "scroll away" / show as empty.
const RAIL = "#16214D"; // single brand color — top bar & sidebar, matches existing header

export default function CollectorDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [activePage, setActivePage] = useState("route");
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);

  const loadNotifications = useCallback(async () => {
    if (!user) return;
    try {
      setNotifications(await listCollectorNotifications());
    } catch {
      // Route data remains usable if the notification panel is temporarily unavailable.
    }
  }, [user]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void loadNotifications();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [loadNotifications]);
  usePolling(loadNotifications, 30000);

  const openNotification = async (notification) => {
    if (!notification.is_read) {
      try {
        await markCollectorNotificationRead(notification.id);
        setNotifications((items) =>
          items.map((item) => (item.id === notification.id ? { ...item, is_read: true } : item))
        );
      } catch {
        // Keep the notification visible; it will be retried on the next refresh.
      }
    }
  };

  const markAllNotificationsRead = async () => {
    if (!notifications.some((notification) => !notification.is_read)) return;
    try {
      await markAllCollectorNotificationsRead();
      setNotifications((items) => items.map((item) => ({ ...item, is_read: true })));
    } catch {
      // The next poll will retain the current state if this request fails.
    }
  };

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-[#F4F6FB]">
      {/* Top bar — fixed height, never scrolls */}
      <header
        className="shrink-0 z-30 flex items-center justify-between px-4 sm:px-6 h-16 border-b border-black/10"
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
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold text-[#16214D] shrink-0">
            V
          </span>
          <div className="leading-tight">
            <div className="text-base sm:text-lg font-semibold tracking-wide text-white">
              ◈Verdeza◈
            </div>
            <div className="text-[10px] sm:text-xs text-white/60">Collector Portal</div>
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
              className="relative text-white/70 hover:text-white"
              aria-label="Notifications"
            >
              <Bell size={18} />
              {notifications.some((item) => !item.is_read) && (
                <span className="absolute -top-1 -right-1 h-2 w-2 rounded-full bg-amber-400" />
              )}
            </button>
            {showNotifications && (
              <div className="absolute right-0 mt-3 w-72 bg-white rounded-2xl shadow-lg border border-black/5 py-2 z-40 text-left">
                <div className="flex items-center justify-between gap-3 px-3.5 py-1.5">
                  <p className="text-[10px] font-semibold tracking-wide text-gray-400 uppercase">
                    Assignments & updates
                  </p>
                  <button
                    type="button"
                    onClick={markAllNotificationsRead}
                    disabled={!notifications.some((item) => !item.is_read)}
                    className="text-[11px] font-semibold text-[#2947A3] hover:underline disabled:opacity-40"
                  >
                    Mark all as read
                  </button>
                </div>
                {notifications.length ? (
                  notifications.map((notification) => (
                    <button
                      key={notification.id}
                      type="button"
                      onClick={() => openNotification(notification)}
                      className={`w-full px-3.5 py-2 text-left hover:bg-black/[.03] ${notification.is_read ? "" : "bg-amber-50/50"}`}
                    >
                      <span className="block text-sm font-semibold text-gray-800">
                        {notification.title}
                      </span>
                      <span className="block mt-0.5 text-xs text-gray-500">
                        {notification.body}
                      </span>
                    </button>
                  ))
                ) : (
                  <p className="px-3.5 py-3 text-sm text-gray-400">No notifications yet.</p>
                )}
              </div>
            )}
          </div>
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowAccountMenu((v) => !v)}
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
                    {user?.name || "Collector"}
                  </div>
                  <div className="text-xs text-gray-400 truncate">{user?.email}</div>
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3.5 py-2 text-sm text-gray-600 hover:bg-black/[0.03] transition"
                >
                  <LogOut size={15} /> Sign out
                </button>
              </div>
            )}
          </div>
        </div>

        {(showAccountMenu || showNotifications) && (
          <div
            className="fixed inset-0 z-20"
            onClick={() => {
              setShowAccountMenu(false);
              setShowNotifications(false);
            }}
          />
        )}
      </header>

      {/* Body row fills the rest of the viewport; only <main> scrolls */}
      <div className="flex flex-1 min-h-0">
        {/* Sidebar — fixed height, part of normal flex flow, never
            floats over content and never relies on `sticky` */}
        <aside
          className={`shrink-0 h-full flex flex-col justify-between overflow-y-auto overflow-x-hidden transition-all duration-200 ${
            sidebarOpen ? "w-64" : "w-0"
          }`}
          style={{ backgroundColor: RAIL }}
        >
          <nav className="w-64 px-3 py-4 space-y-1">
            <button
              type="button"
              onClick={() => setActivePage("route")}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-white transition ${activePage === "route" ? "bg-white/20 ring-1 ring-white/30" : "hover:bg-white/10"}`}
            >
              <LayoutDashboard size={17} /> My pickups
            </button>
            <button
              type="button"
              onClick={() => setActivePage("completed")}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold text-white transition ${activePage === "completed" ? "bg-white/20 ring-1 ring-white/30" : "hover:bg-white/10"}`}
            >
              <ClipboardCheck size={17} /> Completed collections
            </button>
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
                  {user?.name || "Collector"}
                </div>
                <div className="text-xs text-white/40 truncate">{user?.email}</div>
              </div>
            </div>
            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-2 py-2 mt-1 text-sm text-white/60 hover:text-white rounded-xl hover:bg-white/5 transition"
            >
              <LogOut size={15} /> Sign out
            </button>
          </div>
        </aside>

        {/* Main content — the only scrollable region */}
        <main className="flex-1 min-w-0 overflow-y-auto">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
            {activePage === "route" ? <CollectorRoutes /> : <CompletedCollections />}
          </div>
        </main>
      </div>
    </div>
  );
}
