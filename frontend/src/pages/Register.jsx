import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import PublicLayout from "../components/PublicLayout";
import { useAuth } from "../context/AuthContext";
import { UserPlus, CheckCircle2, Landmark, Eye, EyeOff } from "lucide-react";
import API from "../lib/api";

const ROLES = [
  { value: "RESIDENT", label: "Resident", desc: "Schedule pickups and track your impact" },
  { value: "COLLECTOR", label: "Collector", desc: "Collect and weigh dry waste on routes" },
  { value: "RECYCLER", label: "Recycler", desc: "Process incoming batches at your facility" },
];

// Hardcoded fallback zones, used until the backend /zones endpoint is wired up
const FALLBACK_ZONES = [
  { id: "zone-1", name: "Zone 1 - Gomti Nagar" },
  { id: "zone-2", name: "Zone 2 - Hazratganj" },
  { id: "zone-3", name: "Zone 3 - Alambagh" },
  { id: "zone-4", name: "Zone 4 - Indira Nagar" },
  { id: "zone-5", name: "Zone 5 - Chowk" },
];

const isValidEmail = (email) => {
  const value = email.trim();
  const at = value.indexOf("@");
  const dot = value.lastIndexOf(".");
  // must contain '@' and '.', in the right relative order, with something on either side
  return at > 0 && dot > at + 1 && dot < value.length - 1;
};

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [zones, setZones] = useState(FALLBACK_ZONES);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
    phone: "",
    zone_id: "",
    role: "RESIDENT",
    address: "",
  });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [done, setDone] = useState(false);

  useEffect(() => {
    API.get("/zones")
      .then((r) => {
        if (Array.isArray(r.data) && r.data.length > 0) {
          setZones(r.data);
        }
      })
      .catch(() => {
        //  FALLBACK_ZONES
      });
  }, []);

  const needsZone = form.role === "RESIDENT" || form.role === "COLLECTOR";
  const showAddress = form.role === "RESIDENT";

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    if (!isValidEmail(form.email)) {
      setErr("Please enter a valid email address.");
      return;
    }
    if (form.password.length < 8) {
      setErr("Password must be at least 8 characters.");
      return;
    }
    if (form.password !== form.confirm) {
      setErr("Passwords do not match.");
      return;
    }
    if (needsZone && !form.zone_id) {
      setErr("Please select your zone.");
      return;
    }
    if (showAddress && !form.address.trim()) {
      setErr("Please enter your home address.");
      return;
    }
    setLoading(true);
    try {
      const data = await register({
        name: form.name,
        email: form.email,
        password: form.password,
        phone: form.phone || undefined,
        address: form.address || undefined,
        zone_id: form.zone_id || undefined,
        role: form.role,
      });
      setDone(true);
      setTimeout(() => navigate(data.homePath, { replace: true }), 1200);
    } catch ({ response }) {
      setErr(
        typeof response?.data?.detail === "string" ? response.data.detail : "Registration failed"
      );
    }
    setLoading(false);
  };

  const roleInfo = ROLES.find((r) => r.value === form.role);

  return (
    <PublicLayout>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
      `}</style>

      <div className="min-h-[calc(100vh-4rem)] grid lg:grid-cols-2 bg-[#FBF7EE]">
        {/* Branded panel  */}
        <div className="relative hidden lg:flex flex-col justify-between bg-[#0B4F4A] p-10 xl:p-14">
          <div className="inline-flex items-center gap-2 text-white/90 font-semibold">
            <span className="text-2xl">♻</span>
            <span className="font-display text-xl">Verdeza</span>
          </div>

          <div className="max-w-md">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-xs font-medium text-white mb-4 backdrop-blur">
              <Landmark size={12} /> Government of Uttar Pradesh
            </div>
            <h2 className="font-display text-3xl xl:text-4xl font-semibold text-white leading-tight">
              Join the state's waste network.
            </h2>
            <p className="mt-4 text-white/85 text-sm">
              Create an account as a resident, collector, or recycler and become part of a publicly
              verifiable, accountable waste-management loop.
            </p>

            <div className="mt-8 flex items-center gap-3 rounded-2xl bg-white/10 backdrop-blur border border-white/20 p-4">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/90 text-primary">
                <UserPlus size={18} />
              </div>
              <p className="text-sm text-white/90">
                Takes less than two minutes &mdash; you'll be routed straight to your dashboard.
              </p>
            </div>
          </div>

          <p className="text-xs text-white/60">
            © {new Date().getFullYear()} Verdeza. All rights reserved.
          </p>
        </div>

        {/* Form side */}
        <div className="flex items-center justify-center px-4 sm:px-6 py-10 sm:py-16">
          <div className="w-full max-w-md">
            <div className="text-center mb-6 sm:mb-8 lg:hidden">
              <span className="text-5xl">♻</span>
              <h1 className="font-display text-2xl font-semibold mt-2 text-primary">Verdeza</h1>
              <p className="text-gray-500 text-sm mt-1">AI-Powered Dry-Waste Platform</p>
            </div>

            <div className="bg-white rounded-card shadow-elevated w-full p-6 sm:p-8 fade-in border border-gray-100">
              <div className="mb-6">
                <h2 className="font-display text-2xl font-semibold text-gray-900">
                  Create account
                </h2>
                <p className="text-sm text-gray-500 mt-1">Join Verdeza in under two minutes.</p>
              </div>

              {done ? (
                <div className="text-center py-8 text-green-700">
                  <CheckCircle2 size={48} className="mx-auto mb-3" />
                  <p className="font-medium">Account created! Redirecting…</p>
                </div>
              ) : (
                <form onSubmit={submit} className="space-y-4" noValidate>
                  {err && (
                    <div
                      className="bg-red-50 text-red-700 text-sm p-3 rounded-input border border-red-100"
                      role="alert"
                    >
                      {err}
                    </div>
                  )}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Role *</label>
                    <select
                      required
                      className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                      value={form.role}
                      onChange={(e) => setForm({ ...form, role: e.target.value })}
                    >
                      {ROLES.map((r) => (
                        <option key={r.value} value={r.value}>
                          {r.label}
                        </option>
                      ))}
                    </select>
                    {roleInfo && <p className="text-xs text-gray-400 mt-1">{roleInfo.desc}</p>}
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      Full Name *
                    </label>
                    <input
                      type="text"
                      required
                      minLength={2}
                      autoComplete="name"
                      className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Email *</label>
                    <input
                      type="email"
                      required
                      autoComplete="email"
                      inputMode="email"
                      className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Password *
                      </label>
                      <div className="relative">
                        <input
                          type={showPassword ? "text" : "password"}
                          required
                          minLength={8}
                          autoComplete="new-password"
                          placeholder="••••••••"
                          className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 pr-9 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                          value={form.password}
                          onChange={(e) => setForm({ ...form, password: e.target.value })}
                        />
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          tabIndex={-1}
                        >
                          {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Confirm *
                      </label>
                      <div className="relative">
                        <input
                          type={showConfirm ? "text" : "password"}
                          required
                          minLength={8}
                          autoComplete="new-password"
                          placeholder="••••••••"
                          className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 pr-9 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                          value={form.confirm}
                          onChange={(e) => setForm({ ...form, confirm: e.target.value })}
                        />
                        <button
                          type="button"
                          onClick={() => setShowConfirm(!showConfirm)}
                          className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          tabIndex={-1}
                        >
                          {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
                        </button>
                      </div>
                    </div>
                  </div>
                  {needsZone && (
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Zone *</label>
                      <select
                        required
                        className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                        value={form.zone_id}
                        onChange={(e) => setForm({ ...form, zone_id: e.target.value })}
                      >
                        <option value="">Select zone *</option>
                        {zones.map((z) => (
                          <option key={z.id} value={z.id}>
                            {z.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Phone</label>
                    <input
                      type="tel"
                      autoComplete="tel"
                      inputMode="tel"
                      placeholder="Optional"
                      className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                    />
                  </div>
                  {showAddress && (
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">
                        Home Address *
                      </label>
                      <input
                        type="text"
                        required
                        autoComplete="street-address"
                        placeholder="House no., street, locality, city"
                        className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                        value={form.address}
                        onChange={(e) => setForm({ ...form, address: e.target.value })}
                      />
                    </div>
                  )}
                  <button
                    type="submit"
                    disabled={loading}
                    className="w-full min-h-[44px] bg-primary text-white py-2.5 rounded-input font-medium hover:bg-primary/90 disabled:opacity-50 transition inline-flex items-center justify-center gap-2"
                  >
                    {loading ? "Creating…" : "Create Account"}
                  </button>
                </form>
              )}

              {!done && (
                <p className="text-center text-sm text-gray-500 mt-6">
                  Already have an account?{" "}
                  <Link to="/login" className="text-primary font-medium hover:underline">
                    Sign in
                  </Link>
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </PublicLayout>
  );
}
