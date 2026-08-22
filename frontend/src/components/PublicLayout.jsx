import { Link } from "react-router-dom";
import Footer from "./Footer";

/** Shared shell for login, register, track, and other public pages. */
export default function PublicLayout({ children, showAuthLinks = true }) {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-primary/5 to-accent/5">
      <header className="bg-[#0B2F2C] shadow-soft sticky top-0 z-40">
        <div className="w-full px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between h-16">
          <Link
            to="/"
            className="flex items-center gap-3 rounded-full bg-white/8 px-3 py-2 text-white transition hover:bg-white/12"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-md bg-amber-400 font-display text-lg font-bold text-[#0B2F2C]">
              V
            </span>
            <div className="leading-tight">
              <div className="text-lg font-display font-semibold tracking-wide text-white">
                Verdeza
              </div>
              <div className="text-[11px] text-white/60">Government of Uttar Pradesh</div>
            </div>
          </Link>

          {showAuthLinks && (
            <div className="flex items-center gap-4 text-sm">
              <Link to="/track" className="text-white/75 hover:text-amber-300">
                Track
              </Link>
              <Link to="/flows" className="text-white/75 hover:text-amber-300 hidden sm:inline">
                How It Works
              </Link>
              <Link to="/login" className="text-white/75 hover:text-amber-300">
                Sign In
              </Link>
              <Link
                to="/register"
                className="bg-amber-400 text-[#0B2F2C] px-3 py-1.5 rounded-input font-medium hover:bg-amber-300 transition"
              >
                Register
              </Link>
            </div>
          )}
        </div>
      </header>

      <main className="flex-1">{children}</main>
      <Footer />
    </div>
  );
}
