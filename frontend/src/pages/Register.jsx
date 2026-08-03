import { useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import PublicLayout from "../components/PublicLayout";
import { useAuth } from "../context/AuthContext";
import { UserPlus, CheckCircle2, Landmark, Eye, EyeOff } from "lucide-react";
import API from "../lib/api";

import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

function LocationPicker({ onChange }) {
  useMapEvents({
    click(e) {
      onChange(e.latlng);
    },
  });
  return null;
}

function RecenterMap({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, 15, { animate: true, duration: 1.5 });
    }
  }, [center, map]);
  return null;
}

const ROLES = [
  { value: "CITIZEN", label: "Citizen", desc: "Schedule pickups and track your impact" },
  {
    value: "COLLECTION_WORKER",
    label: "Collection Worker",
    desc: "Collect and weigh dry waste on routes",
  },
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

const isValidUUID = (id) => {
  if (!id) return false;
  const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  return regex.test(id);
};

// className helper: swaps border color to red when a field has an error
function inputClass(hasError) {
  return `w-full border rounded-input px-3 py-3 sm:py-2.5 text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 ${
    hasError ? "border-red-300 focus:border-red-400" : "border-gray-200 focus:border-primary/40"
  }`;
}

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
    role: "CITIZEN",
    address: "",
    latitude: null,
    longitude: null,
  });
  const [err, setErr] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [done, setDone] = useState(false);
  const [mapCenter, setMapCenter] = useState([26.8467, 80.9462]);
  const lastSearchedAddressRef = useRef("");

  useEffect(() => {
    API.get("/v1/zones")
      .then((r) => {
        if (Array.isArray(r.data) && r.data.length > 0) {
          setZones(r.data);
        }
      })
      .catch(() => {
        //  FALLBACK_ZONES
      });
  }, []);

  useEffect(() => {
    const trimmed = form.address.trim();
    if (!trimmed || trimmed === lastSearchedAddressRef.current) return;

    // A word is considered completed if the input ends with a space
    const endsWithSpace = form.address.endsWith(" ");

    const performSearch = () => {
      lastSearchedAddressRef.current = trimmed;
      let query = trimmed;
      const lowerQuery = query.toLowerCase();
      if (!lowerQuery.includes("lucknow") && !lowerQuery.includes("uttar pradesh")) {
        query += ", Lucknow, Uttar Pradesh";
      }

      const fetchGeocode = (q) => {
        return fetch(
          `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(
            q
          )}`
        )
          .then((res) => res.json())
          .then((data) => {
            if (data && data.length > 0) {
              const lat = parseFloat(data[0].lat);
              const lon = parseFloat(data[0].lon);
              if (!isNaN(lat) && !isNaN(lon)) {
                setMapCenter([lat, lon]);
                setForm((f) => ({
                  ...f,
                  latitude: lat,
                  longitude: lon,
                }));
                setFieldErrors((prev) => {
                  const next = { ...prev };
                  delete next.location;
                  return next;
                });
                return true;
              }
            }
            return false;
          })
          .catch((error) => {
            console.error("Geocoding fetch failed for query:", q, error);
            return false;
          });
      };

      const fallbackLastWords = (originalQuery) => {
        const parts = originalQuery.split(/\s+/).filter(Boolean);
        if (parts.length > 3) {
          const lastWordsQuery = parts.slice(-4).join(" ");
          fetchGeocode(lastWordsQuery);
        }
      };

      // Try Stage 1: full query
      fetchGeocode(query).then((success) => {
        if (success) return;

        // Stage 2: clean house/room numbers, plot/flat designations
        let cleaned = query
          .replace(
            /^(room|house|flat|plot|shop|h\.?\s*no\.?|f\.?\s*no\.?|p\.?\s*no\.?|block|sect(?:or)?)\s*(?:no\.?|number)?\s*\w+([\/\-]?\w+)?/gi,
            ""
          )
          .trim();
        cleaned = cleaned.replace(/^[.,\s]+/, "").trim();
        cleaned = cleaned.replace(/^\d+([\/\-]?\w+)?/gi, "").trim();
        cleaned = cleaned.replace(/^[.,\/\-\s]+/, "").trim();

        if (cleaned && cleaned !== query && cleaned.length > 3) {
          fetchGeocode(cleaned).then((success2) => {
            if (success2) return;
            fallbackLastWords(query);
          });
        } else {
          fallbackLastWords(query);
        }
      });
    };

    if (endsWithSpace) {
      // Trigger search immediately as a word is completed
      performSearch();
      return;
    }

    // Otherwise wait for a 2-second pause (2000ms debounce)
    const delayDebounceFn = setTimeout(() => {
      performSearch();
    }, 1000);

    return () => clearTimeout(delayDebounceFn);
  }, [form.address]);

  const needsZone = form.role === "CITIZEN" || form.role === "COLLECTION_WORKER";
  const showAddress = form.role === "CITIZEN";

  // Clears just one field's error as the user edits it, so the message
  // doesn't stay stuck on screen after they've started fixing it.
  const updateField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    if (fieldErrors[key]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }
  };

  const handleMapClick = (latlng) => {
    setForm((f) => ({
      ...f,
      latitude: latlng.lat,
      longitude: latlng.lng,
    }));
    setFieldErrors((prev) => {
      const next = { ...prev };
      delete next.location;
      return next;
    });
  };

  const validate = () => {
    const errors = {};

    if (!form.name.trim() || form.name.trim().length < 2) {
      errors.name = "Please enter your full name (at least 2 characters).";
    }
    if (!isValidEmail(form.email)) {
      errors.email = "Please enter a valid email address.";
    }
    if (form.password.length < 8) {
      errors.password = "Password must be at least 8 characters.";
    }
    if (!form.confirm) {
      errors.confirm = "Please confirm your password.";
    } else if (form.password !== form.confirm) {
      errors.confirm = "Passwords do not match.";
    }
    if (needsZone && !form.zone_id) {
      errors.zone_id = "Please select your zone.";
    }
    if (!form.phone || !form.phone.trim() || form.phone.trim().length < 5) {
      errors.phone = "Please enter your phone number (at least 5 characters).";
    }
    if (form.role === "CITIZEN" && (!form.latitude || !form.longitude)) {
      errors.location = "Please select your location on the map.";
    }
    if (showAddress && !form.address.trim()) {
      errors.address = "Please enter your home address.";
    }

    return errors;
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr("");

    const errors = validate();
    setFieldErrors(errors);
    if (Object.keys(errors).length > 0) {
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
        zone_id: form.zone_id && isValidUUID(form.zone_id) ? form.zone_id : undefined,
        role: form.role,
        latitude: form.latitude !== null ? form.latitude : undefined,
        longitude: form.longitude !== null ? form.longitude : undefined,
      });
      setDone(true);
      setTimeout(() => navigate(data.homePath, { replace: true }), 1200);
    } catch ({ response }) {
      const errorMsg = response?.data?.error?.message;
      const details = response?.data?.error?.details;
      if (details && Array.isArray(details)) {
        const fieldErrorsStr = details
          .map((d) => `${d.loc.slice(1).join(".")}: ${d.type}`)
          .join(", ");
        setErr(`${errorMsg} (${fieldErrorsStr})`);
      } else {
        setErr(
          errorMsg ||
            (typeof response?.data?.detail === "string"
              ? response.data.detail
              : "Registration failed")
        );
      }
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
              Create an account as a citizen, collector, or recycler and become part of a publicly
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
                      className={inputClass(false)}
                      value={form.role}
                      onChange={(e) => updateField("role", e.target.value)}
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
                      aria-invalid={Boolean(fieldErrors.name)}
                      className={inputClass(fieldErrors.name)}
                      value={form.name}
                      onChange={(e) => updateField("name", e.target.value)}
                    />
                    {fieldErrors.name && (
                      <p className="text-red-600 text-xs mt-1">{fieldErrors.name}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Email *</label>
                    <input
                      type="email"
                      required
                      autoComplete="email"
                      inputMode="email"
                      aria-invalid={Boolean(fieldErrors.email)}
                      className={inputClass(fieldErrors.email)}
                      value={form.email}
                      onChange={(e) => updateField("email", e.target.value)}
                    />
                    {fieldErrors.email && (
                      <p className="text-red-600 text-xs mt-1">{fieldErrors.email}</p>
                    )}
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
                          aria-invalid={Boolean(fieldErrors.password)}
                          className={`${inputClass(fieldErrors.password)} pr-9`}
                          value={form.password}
                          onChange={(e) => updateField("password", e.target.value)}
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
                      {fieldErrors.password && (
                        <p className="text-red-600 text-xs mt-1">{fieldErrors.password}</p>
                      )}
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
                          aria-invalid={Boolean(fieldErrors.confirm)}
                          className={`${inputClass(fieldErrors.confirm)} pr-9`}
                          value={form.confirm}
                          onChange={(e) => updateField("confirm", e.target.value)}
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
                      {fieldErrors.confirm && (
                        <p className="text-red-600 text-xs mt-1">{fieldErrors.confirm}</p>
                      )}
                    </div>
                  </div>
                  {needsZone && (
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Zone *</label>
                      <select
                        required
                        aria-invalid={Boolean(fieldErrors.zone_id)}
                        className={inputClass(fieldErrors.zone_id)}
                        value={form.zone_id}
                        onChange={(e) => updateField("zone_id", e.target.value)}
                      >
                        <option value="">Select zone *</option>
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
                  )}
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Phone *</label>
                    <input
                      type="tel"
                      required
                      autoComplete="tel"
                      inputMode="tel"
                      placeholder="e.g. +919876543210"
                      aria-invalid={Boolean(fieldErrors.phone)}
                      className={inputClass(fieldErrors.phone)}
                      value={form.phone}
                      onChange={(e) => updateField("phone", e.target.value)}
                    />
                    {fieldErrors.phone && (
                      <p className="text-red-600 text-xs mt-1">{fieldErrors.phone}</p>
                    )}
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
                        aria-invalid={Boolean(fieldErrors.address)}
                        className={inputClass(fieldErrors.address)}
                        value={form.address}
                        onChange={(e) => updateField("address", e.target.value)}
                      />
                      {fieldErrors.address && (
                        <p className="text-red-600 text-xs mt-1">{fieldErrors.address}</p>
                      )}
                    </div>
                  )}
                  {needsZone && (
                    <div className="space-y-1 mt-2">
                      <label className="block text-xs font-medium text-gray-600">
                        Select Your Location on the Map *
                      </label>
                      <div
                        style={{
                          height: "240px",
                          width: "100%",
                          borderRadius: "8px",
                          overflow: "hidden",
                        }}
                        className="border border-gray-200 shadow-sm"
                      >
                        <MapContainer
                          center={mapCenter}
                          zoom={12}
                          scrollWheelZoom={false}
                          style={{ height: "100%", width: "100%" }}
                        >
                          <TileLayer
                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                          />
                          <LocationPicker onChange={handleMapClick} />
                          <RecenterMap center={mapCenter} />
                          {form.latitude && form.longitude && (
                            <Marker position={[form.latitude, form.longitude]} />
                          )}
                        </MapContainer>
                      </div>
                      {form.latitude && form.longitude ? (
                        <p className="text-xs text-green-600 font-medium">
                          Selected coordinates: {form.latitude.toFixed(6)},{" "}
                          {form.longitude.toFixed(6)}
                        </p>
                      ) : (
                        <p className="text-xs text-gray-500 italic">
                          Click on the map to set your location coordinates.
                        </p>
                      )}
                      {fieldErrors.location && (
                        <p className="text-red-600 text-xs mt-1">{fieldErrors.location}</p>
                      )}
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
