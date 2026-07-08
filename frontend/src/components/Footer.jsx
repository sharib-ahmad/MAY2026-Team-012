import { Link } from "react-router-dom";
import { Github, Mail, MapPin, Recycle } from "lucide-react";

export default function Footer({ variant = "default" }) {
  const isDark = variant === "dark";

  return (
    <footer
      className={`mt-auto border-t ${
        isDark
          ? "bg-gray-900 border-gray-800 text-gray-300"
          : "bg-white border-gray-200 text-gray-600"
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 py-10 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        <div>
          <div
            className={`flex items-center gap-2 font-bold text-lg ${isDark ? "text-white" : "text-primary"}`}
          >
            <Recycle size={22} />
            Verdeza
          </div>
          <p className="text-xs mt-2 leading-relaxed opacity-80">
            An initiative of the Government of Uttar Pradesh for the systematic collection,
            tracking, and recycling across communities.
          </p>
        </div>

        <div>
          <h4
            className={`text-xs font-semibold uppercase tracking-wide mb-3 ${isDark ? "text-white" : "text-gray-800"}`}
          >
            Platform
          </h4>
          <ul className="space-y-2 text-sm">
            <li>
              <Link to="/track" className="hover:text-primary transition">
                Track Waste
              </Link>
            </li>
            <li>
              <Link to="/login" className="hover:text-primary transition">
                Sign In
              </Link>
            </li>
            <li>
              <Link to="/register" className="hover:text-primary transition">
                Register as Resident
              </Link>
            </li>
            <li>
              <Link to="/flows" className="hover:text-primary transition">
                How It Works
              </Link>
            </li>
          </ul>
        </div>

        <div>
          <h4
            className={`text-xs font-semibold uppercase tracking-wide mb-3 ${isDark ? "text-white" : "text-gray-800"}`}
          >
            Roles
          </h4>
          <ul className="space-y-2 text-sm opacity-90">
            <li>Resident — schedule pickups & earn credits</li>
            <li>Collector — routes & weigh-in</li>
            <li>Manager — zone queue & tickets</li>
            <li>Recycler — batch intake & processing</li>
          </ul>
        </div>

        <div>
          <h4
            className={`text-xs font-semibold uppercase tracking-wide mb-3 ${isDark ? "text-white" : "text-gray-800"}`}
          >
            Contact
          </h4>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <Mail size={14} /> support@verdeza.com
            </li>
            <li className="flex items-center gap-2">
              <MapPin size={14} /> Uttar Pradesh{" "}
            </li>
            <li className="flex items-center gap-2">
              <Github size={14} /> Verdeza v2.0
            </li>
          </ul>
        </div>
      </div>

      <div
        className={`text-center text-xs py-4 border-t ${isDark ? "border-gray-800 text-gray-500" : "border-gray-100 text-gray-400"}`}
      >
        © {new Date().getFullYear()} Verdeza. Built for sustainable waste management.
      </div>
    </footer>
  );
}
