import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import CollectorRoutes from "./collector/Routes";
import CollectorImage from "../../assets/collector-image.webp";

export default function CollectorDashboard() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="min-h-screen bg-[#F4F6FB] overflow-x-hidden">
      <header className="bg-[#16214D] text-white shadow-sm">
        <div className="w-full px-4 sm:px-8 py-5 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold text-[#16214D]">
              V
            </span>
            <div className="leading-tight">
              <div className="text-lg font-semibold tracking-wide text-white">◈Verdeza◈</div>
              <div className="text-[11px] text-white/60">Government of Uttar Pradesh</div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="rounded-input border border-white/20 bg-white/10 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/15"
          >
            Log out
          </button>
        </div>
      </header>

      <img
        src={CollectorImage}
        alt="Collector"
        className="w-full max-h-[340px] object-cover shadow-soft"
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <CollectorRoutes />
      </main>
    </div>
  );
}
