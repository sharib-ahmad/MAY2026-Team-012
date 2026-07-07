import { LogOut } from "lucide-react";
import { useAuth } from "../../context/AuthContext";

/** Placeholder home for roles that don't have a real dashboard built
 *  yet. Just enough here to avoid a redirect loop after login. */
export default function ComingSoon({ roleLabel }) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-[#FBF7EE] flex flex-col">
      <header className="bg-[#0B2F2C] px-4 sm:px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-white">
          <span className="text-2xl">♻</span>
          <span className="font-semibold">Verdeza</span>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-white/75 hover:text-amber-300 text-sm"
        >
          <LogOut size={15} /> Sign out
        </button>
      </header>

      <main className="flex-1 flex items-center justify-center px-4 text-center">
        <div>
          <h1 className="text-5xl sm:text-6xl font-bold text-gray-300 tracking-tight">
            # Coming soon
          </h1>
          <p className="text-gray-500 mt-4">
            {roleLabel} dashboard for {user?.name || "you"} isn't built yet — check back later.
          </p>
        </div>
      </main>
    </div>
  );
}
