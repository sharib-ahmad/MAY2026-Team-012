import { useState, useEffect } from "react";
import { UserPlus, CheckCircle2, Eye, EyeOff } from "lucide-react";
import { createAccount, getZones } from "../../../lib/api";
import { Section } from "./shared";

const EMPTY_FORM = {
  name: "",
  email: "",
  phone: "",
  role: "MANAGER",
  zone_id: "",
  password: "",
  confirm: "",
};

const isValidEmail = (email) => {
  const value = email.trim();
  const at = value.indexOf("@");
  const dot = value.lastIndexOf(".");
  return at > 0 && dot > at + 1 && dot < value.length - 1;
};

function inputClass(hasError) {
  return `w-full border rounded-input px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0B4F4A]/30 ${
    hasError ? "border-red-300 focus:border-red-400" : "border-gray-200 focus:border-[#0B4F4A]/40"
  }`;
}

export default function CreateAccount() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [err, setErr] = useState("");
  const [created, setCreated] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [zones, setZones] = useState([]);
  const [zonesLoading, setZonesLoading] = useState(true);

  // Fetch zones on component mount
  useEffect(() => {
    const fetchZones = async () => {
      try {
        const data = await getZones();
        setZones(data);
      } catch {
        setZonesLoading(false);
      } finally {
        setZonesLoading(false);
      }
    };

    fetchZones();
  }, []);

  const updateField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) => ({ ...e, [key]: undefined }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    setCreated(null);

    const errors = {};
    if (!form.name.trim()) errors.name = "Name is required.";
    if (!isValidEmail(form.email)) errors.email = "Enter a valid email address.";
    if (form.role === "MANAGER" && !form.zone_id) errors.zone_id = "Assign the officer a zone.";
    if (form.password.length < 8) errors.password = "Password must be at least 8 characters.";
    if (form.confirm !== form.password) errors.confirm = "Passwords do not match.";
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    setLoading(true);
    try {
      const { user } = await createAccount({
        name: form.name,
        email: form.email,
        password: form.password,
        phone: form.phone || null,
        zone_id: form.role === "MANAGER" ? form.zone_id : null,
        role: form.role,
      });
      setCreated(user);
      setForm(EMPTY_FORM);
    } catch (ex) {
      setErr(
        ex?.response?.data?.error?.message ||
          ex?.response?.data?.detail ||
          "Could not create the account. Try again."
      );
    }
    setLoading(false);
  };

  return (
    <Section eyebrow="Identity provisioning" title="Create Officer / Admin account">
      <p className="text-sm text-gray-500 -mt-2 mb-5 max-w-xl">
        Municipal Officer and System Admin accounts cannot be created through public registration.
        Provision them here — the new account can sign in immediately with the credentials you set.
      </p>

      {created && (
        <div className="mb-5 flex items-start gap-2 rounded-input border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
          <span>
            Account created successfully. <span className="font-semibold">{created.name}</span> can
            now sign in as a {created.role === "ADMIN" ? "System Admin" : "Municipal Officer"} using{" "}
            <span className="font-mono-civic">{created.email}</span>.
          </span>
        </div>
      )}
      {err && (
        <div className="mb-5 rounded-input border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {err}
        </div>
      )}

      <form onSubmit={submit} className="grid gap-4 sm:grid-cols-2 max-w-2xl">
        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
            Full name
          </label>
          <input
            className={inputClass(fieldErrors.name)}
            value={form.name}
            onChange={(e) => updateField("name", e.target.value)}
            placeholder="e.g. Officer Anita Rao"
          />
          {fieldErrors.name && <p className="text-red-600 text-xs mt-1">{fieldErrors.name}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
            Email
          </label>
          <input
            className={inputClass(fieldErrors.email)}
            value={form.email}
            onChange={(e) => updateField("email", e.target.value)}
            placeholder="name@verdeza.test"
          />
          {fieldErrors.email && <p className="text-red-600 text-xs mt-1">{fieldErrors.email}</p>}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
            Role
          </label>
          <select
            className={inputClass(false)}
            value={form.role}
            onChange={(e) => updateField("role", e.target.value)}
          >
            <option value="MANAGER">Municipal Officer</option>
            <option value="ADMIN">System Admin</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
            Assigned zone {form.role === "ADMIN" && "(not required)"}
          </label>
          <select
            className={inputClass(fieldErrors.zone_id)}
            value={form.zone_id}
            onChange={(e) => updateField("zone_id", e.target.value)}
            disabled={form.role === "ADMIN" || zonesLoading}
          >
            <option value="">Select a zone…</option>
            {zones.map((z) => (
              <option key={z.id} value={z.id}>
                {z.name}
              </option>
            ))}
          </select>
          {fieldErrors.zone_id && (
            <p className="text-red-600 text-xs mt-1">{fieldErrors.zone_id}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
            Phone (optional)
          </label>
          <input
            className={inputClass(false)}
            value={form.phone}
            onChange={(e) => updateField("phone", e.target.value)}
            placeholder="+91 …"
          />
        </div>

        <div className="hidden sm:block" />

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
            Password
          </label>
          <div className="relative">
            <input
              type={showPassword ? "text" : "password"}
              className={`${inputClass(fieldErrors.password)} pr-10`}
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              placeholder="Min. 8 characters"
            />
            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {fieldErrors.password && (
            <p className="text-red-600 text-xs mt-1">{fieldErrors.password}</p>
          )}
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
            Confirm password
          </label>
          <div className="relative">
            <input
              type={showConfirm ? "text" : "password"}
              className={`${inputClass(fieldErrors.confirm)} pr-10`}
              value={form.confirm}
              onChange={(e) => updateField("confirm", e.target.value)}
              placeholder="Repeat password"
            />
            <button
              type="button"
              onClick={() => setShowConfirm((s) => !s)}
              aria-label={showConfirm ? "Hide password" : "Show password"}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showConfirm ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
          {fieldErrors.confirm && (
            <p className="text-red-600 text-xs mt-1">{fieldErrors.confirm}</p>
          )}
        </div>

        <div className="sm:col-span-2">
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-input bg-[#0B4F4A] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#0B2F2C] transition disabled:opacity-60"
          >
            <UserPlus size={16} /> {loading ? "Creating…" : "Create account"}
          </button>
        </div>
      </form>
    </Section>
  );
}
