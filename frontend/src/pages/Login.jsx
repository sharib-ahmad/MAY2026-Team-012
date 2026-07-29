import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldCheck, Landmark, Eye, EyeOff } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import PublicLayout from "../components/PublicLayout";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({ email: "", password: "" });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // handle login form submit
  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setLoading(true);

    try {
      const data = await login(form.email, form.password);
      navigate(data.homePath, { replace: true });
    } catch (error) {
      const resp = error?.response;
      setErr(resp?.data?.error?.message || resp?.data?.detail || "Login failed");
    }

    setLoading(false);
  };

  return (
    <PublicLayout>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
      `}</style>

      <div className="min-h-[calc(100vh-4rem)] grid lg:grid-cols-2 bg-[#FBF7EE]">
        {/* Login form - left side */}
        <div className="flex items-center justify-center px-4 sm:px-6 py-10 sm:py-16 order-1">
          <div className="w-full max-w-md">
            {/* logo shown only on small screens */}
            <div className="text-center mb-6 sm:mb-8 lg:hidden">
              <span className="text-5xl">♻</span>
              <h1 className="font-display text-2xl font-semibold mt-2 text-primary">Verdeza</h1>
              <p className="text-gray-500 text-sm mt-1">AI-Powered Dry-Waste Platform</p>
            </div>

            <div className="bg-white rounded-card shadow-elevated w-full p-6 sm:p-8 fade-in border border-gray-100">
              <div className="mb-6">
                <h2 className="font-display text-2xl font-semibold text-gray-900">Sign in</h2>
                <p className="text-sm text-gray-500 mt-1">
                  Enter your details to access your dashboard.
                </p>
              </div>

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
                  <label className="block text-xs font-medium text-gray-600 mb-1">Email</label>
                  <input
                    type="email"
                    required
                    autoComplete="email"
                    inputMode="email"
                    className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                    value={form.email}
                    onChange={(e) => setForm({ ...form, email: e.target.value })}
                    placeholder="you@example.com"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Password</label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      autoComplete="current-password"
                      className="w-full border border-gray-200 rounded-input px-3 py-3 sm:py-2.5 pr-10 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/40"
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      placeholder="••••••••"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      tabIndex={-1}
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full min-h-[44px] bg-primary text-white py-2.5 rounded-input font-medium hover:bg-primary/90 disabled:opacity-50 transition inline-flex items-center justify-center gap-2"
                >
                  {loading ? "Signing in…" : "Sign In"}
                </button>
              </form>

              <p className="text-center text-sm text-gray-500 mt-6">
                New resident?{" "}
                <Link to="/register" className="text-primary font-medium hover:underline">
                  Create an account
                </Link>
              </p>
            </div>
          </div>
        </div>

        {/* Right side panel  */}
        <div className="relative hidden lg:flex flex-col justify-between bg-[#0B4F4A] p-10 xl:p-14 order-2">
          <div className="inline-flex items-center gap-2 text-white/90 font-semibold">
            <span className="text-2xl">♻</span>
            <span className="font-display text-xl">Verdeza</span>
          </div>

          <div className="max-w-md">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-xs font-medium text-white mb-4 backdrop-blur">
              <Landmark size={12} /> Government of Uttar Pradesh
            </div>
            <h2 className="font-display text-3xl xl:text-4xl font-semibold text-white leading-tight">
              Welcome back to a cleaner, more accountable loop.
            </h2>
            <p className="mt-4 text-white/85 text-sm">
              Sign in to schedule pickups, track chain-of-custody, and see your impact in real time.
            </p>

            <div className="mt-8 flex items-center gap-3 rounded-2xl bg-white/10 backdrop-blur border border-white/20 p-4">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/90 text-primary">
                <ShieldCheck size={18} />
              </div>
              <p className="text-sm text-white/90">
                Every session is tied to a verified account — residents, collectors, and recyclers
                each see only what's theirs.
              </p>
            </div>
          </div>

          <p className="text-xs text-white/60">
            © {new Date().getFullYear()} Verdeza. All rights reserved.
          </p>
        </div>
      </div>
    </PublicLayout>
  );
}
