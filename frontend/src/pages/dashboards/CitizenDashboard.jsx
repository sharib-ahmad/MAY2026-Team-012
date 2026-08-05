import { useCallback, useEffect, useMemo, useState } from "react";
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
  BookOpen,
  Recycle,
  User,
  Trash2,
} from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { ensureCitizenSeed } from "../../lib/mockCitizenData";
import {
  listUserNotifications,
  markUserNotificationRead,
  markAllUserNotificationsRead,
  deleteUserAccount,
} from "../../lib/api";
import { Modal } from "../../components/UI";
import heroBg from "../../assets/eco-banner-bg.webp";
import Footer from "../../components/Footer";
import EcoBotWidget from "../../components/EcoBotWidget";

import Home from "./citizen/Home";
import SchedulePickup from "./citizen/SchedulePickup";
import MyPickups from "./citizen/MyPickups";
import CollectionFlow from "./citizen/CollectionFlow";
import Tickets from "./citizen/Tickets";
import CommunityShelf from "./citizen/CommunityShelf";
import Impact from "./citizen/Impact";
import SortingGuide from "./citizen/SortingGuide";
import RecyclingTransparency from "./citizen/RecyclingTransparency";

// Shell mechanics brought in line with the recycler portal's app frame:
// one <aside> handling both the off-canvas mobile drawer and the
// desktop width-collapse (instead of a fully duplicated mobile-drawer
// block), a single 3-line toggle in the top bar driving both, and
// outside-click-to-close on the notification/account dropdowns. The
// citizen portal's own identity — dark teal + hero photo on the
// sidebar, amber active-state accents — is unchanged.
const TABS = [
  { key: "home", label: "Home", icon: HomeIcon, component: Home },
  { key: "schedule", label: "Schedule Pickup", icon: PackagePlus, component: SchedulePickup },
  { key: "pickups", label: "My Pickups", icon: Package, component: MyPickups },
  { key: "flow", label: "Today's Collection", icon: Route, component: CollectionFlow },
  { key: "tickets", label: "Tickets", icon: AlertCircle, component: Tickets },
  { key: "sorting", label: "Sorting Guide", icon: BookOpen, component: SortingGuide },
  { key: "communityshelf", label: "Community Shelf", icon: Gift, component: CommunityShelf },
  { key: "impact", label: "My Impact", icon: Leaf, component: Impact },
  {
    key: "recycling",
    label: "Recycling Transparency ",
    icon: Recycle,
    component: RecyclingTransparency,
  },
];

export default function CitizenDashboard() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("home");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [profileOpen, setProfileOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [deleteReason, setDeleteReason] = useState("");
  const [deleting, setDeleting] = useState(false);

  const handleDeleteAccount = async (e) => {
    e.preventDefault();
    if (deleting) return;
    setDeleting(true);
    try {
      await deleteUserAccount(deleteReason);
      setDeleteModalOpen(false);
      logout();
    } catch (err) {
      console.error("Failed to delete account:", err);
      alert("Failed to delete account. Please try again later.");
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    ensureCitizenSeed(user);
  }, [user]);

  const loadNotifications = useCallback(() => {
    listUserNotifications()
      .then(setNotifications)
      .catch(() => setNotifications([]));
  }, []);

  useEffect(() => {
    loadNotifications();
    window.addEventListener("citizen-notifications-updated", loadNotifications);
    return () => window.removeEventListener("citizen-notifications-updated", loadNotifications);
  }, [loadNotifications]);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [activeTab]);

  const ActiveTab = useMemo(
    () => TABS.find((t) => t.key === activeTab)?.component || Home,
    [activeTab]
  );
  const notificationCount = notifications.filter((notification) => !notification.is_read).length;

  const markAsRead = async (notificationId) => {
    try {
      await markUserNotificationRead(notificationId);
      setNotifications((current) =>
        current.map((notification) =>
          notification.id === notificationId ? { ...notification, is_read: true } : notification
        )
      );
    } catch {
      // Keep the notification unread when the server update fails.
    }
  };

  const markAllAsRead = async () => {
    try {
      await markAllUserNotificationsRead();
      setNotifications((current) =>
        current.map((notification) => ({ ...notification, is_read: true }))
      );
    } catch {
      // ignore
    }
  };

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
          <div
            className="flex items-center gap-2.5 cursor-pointer select-none"
            onClick={() => {
              window.location.href = "/";
            }}
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold text-[#0B2F2C] shrink-0">
              V
            </span>
            <div className="leading-tight">
              <div className="font-display font-semibold text-white">Verdeza</div>
              <div className="text-[10px] text-white/50 tracking-wide hidden sm:block">
                Citizen Portal
              </div>
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
                <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold">Notifications</p>
                    <p className="text-xs text-slate-500">{notificationCount} new</p>
                  </div>
                  {notificationCount > 0 && (
                    <button
                      type="button"
                      onClick={markAllAsRead}
                      className="text-xs text-primary font-medium hover:underline"
                    >
                      Mark all as read
                    </button>
                  )}
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
                        {!n.is_read && (
                          <button
                            type="button"
                            onClick={() => markAsRead(n.id)}
                            className="mt-2 text-xs font-medium text-primary hover:underline"
                          >
                            Mark as read
                          </button>
                        )}
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
                    {user?.name || "Citizen"}
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
                  {user?.name || "Citizen"}
                </div>
                <div className="text-xs text-white/50 truncate">{user?.email}</div>
              </div>
            </div>
            <div className="flex gap-2 mt-1">
              <button
                type="button"
                onClick={logout}
                className="flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-xs text-white/60 hover:text-amber-300 rounded-xl hover:bg-white/5 transition border border-white/10"
              >
                <LogOut size={13} /> Sign out
              </button>
              <button
                type="button"
                onClick={() => setDeleteModalOpen(true)}
                className="flex-1 flex items-center justify-center gap-1.5 px-2 py-2 text-xs text-red-400 hover:text-red-300 rounded-xl hover:bg-white/5 transition border border-red-500/30"
              >
                <Trash2 size={13} /> Delete
              </button>
            </div>
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

          <EcoBotWidget />
        </main>
      </div>

      <Modal
        open={deleteModalOpen}
        onClose={() => {
          if (!deleting) setDeleteModalOpen(false);
        }}
        title="Delete Your Account"
      >
        <form onSubmit={handleDeleteAccount} className="space-y-4">
          <p className="text-sm text-gray-600 leading-relaxed">
            Are you sure you want to delete your account? This action is permanent and cannot be
            undone. All of your personal identifiers will be disabled, but your historical waste
            pickups and credits will remain in the database for municipal reporting.
          </p>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-gray-500 mb-1.5">
              Reason for Deleting (Optional)
            </label>
            <textarea
              className="w-full border border-gray-200 rounded-2xl px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-red-500/20 focus:border-red-500 min-h-[80px]"
              placeholder="Please let us know why you are deleting your account..."
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              disabled={deleting}
            />
          </div>

          <div className="flex gap-3 justify-end pt-3 border-t border-gray-100">
            <button
              type="button"
              onClick={() => setDeleteModalOpen(false)}
              disabled={deleting}
              className="px-4 py-2 rounded-xl text-sm font-semibold text-gray-500 hover:bg-gray-50 border border-gray-200 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={deleting}
              className="px-4 py-2 rounded-xl text-sm font-semibold text-white bg-red-600 hover:bg-red-700 transition disabled:opacity-50"
            >
              {deleting ? "Deleting..." : "Confirm Delete"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
