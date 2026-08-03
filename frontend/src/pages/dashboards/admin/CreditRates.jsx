import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Coins, Save } from "lucide-react";
import { getAdminCreditFactors, updateAdminCreditFactor } from "../../../lib/api";
import { Section } from "./shared";

export default function CreditRates() {
  const [factors, setFactors] = useState([]);
  const [rates, setRates] = useState({});
  const [co2Rates, setCo2Rates] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const rows = await getAdminCreditFactors();
      setFactors(rows);
      setRates(Object.fromEntries(rows.map((row) => [row.category, row.credit_rate])));
      setCo2Rates(Object.fromEntries(rows.map((row) => [row.category, row.co2_factor])));
    } catch (err) {
      setError(err.response?.data?.error?.message || "Unable to load credit rates.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async (category) => {
    const creditRate = Number(rates[category]);
    if (!Number.isFinite(creditRate) || creditRate < 0) {
      setError("Enter a valid non-negative number of points per kg.");
      return;
    }
    const co2Rate = Number(co2Rates[category]);
    if (!Number.isFinite(co2Rate) || co2Rate < 0) {
      setError("Enter a valid non-negative CO₂ factor per kg.");
      return;
    }
    setSaving(category);
    setError("");
    setMessage("");
    try {
      const updated = await updateAdminCreditFactor(category, creditRate, co2Rate);
      setFactors((items) => items.map((item) => (item.category === category ? updated : item)));
      setRates((items) => ({ ...items, [category]: updated.credit_rate }));
      setCo2Rates((items) => ({ ...items, [category]: updated.co2_factor }));
      setMessage(`${updated.category_label} reward rate updated.`);
    } catch (err) {
      setError(err.response?.data?.error?.message || "Unable to update the reward rate.");
    } finally {
      setSaving("");
    }
  };

  return (
    <Section eyebrow="Rewards configuration" title="Collection credit rates">
      <p className="-mt-2 mb-5 max-w-2xl text-sm text-gray-500">
        Set the points a citizen earns per kilogram for each waste category. The current rate is
        applied when a recycler marks a batch as processed; previously issued credits do not change.
      </p>
      {error && (
        <p className="mb-4 rounded-input bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}
      {message && (
        <p className="mb-4 flex items-center gap-2 rounded-input bg-green-50 px-3 py-2 text-sm text-green-800">
          <CheckCircle2 size={16} /> {message}
        </p>
      )}
      {loading ? (
        <p className="text-sm text-gray-500">Loading credit rates…</p>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          {factors.map((factor) => (
            <div
              key={factor.category}
              className="rounded-card border border-gray-200 bg-white p-4 shadow-sm"
            >
              <div className="mb-4 flex items-center gap-2">
                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-amber-100 text-amber-700">
                  <Coins size={17} />
                </span>
                <div>
                  <h2 className="font-semibold text-gray-800">{factor.category_label}</h2>
                  <p className="text-xs text-gray-400">{factor.category}</p>
                </div>
              </div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500">
                Points per kg
              </label>
              <input
                type="number"
                min="0"
                step="0.01"
                value={rates[factor.category] ?? ""}
                onChange={(event) =>
                  setRates((items) => ({ ...items, [factor.category]: event.target.value }))
                }
                className="mt-1.5 w-full rounded-input border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0B4F4A]/30"
              />
              <label className="mt-3 block text-xs font-semibold uppercase tracking-wide text-gray-500">
                CO₂ factor per kg
              </label>
              <input
                type="number"
                min="0"
                step="0.001"
                value={co2Rates[factor.category] ?? ""}
                onChange={(event) =>
                  setCo2Rates((items) => ({ ...items, [factor.category]: event.target.value }))
                }
                className="mt-1.5 w-full rounded-input border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0B4F4A]/30"
              />
              <button
                type="button"
                onClick={() => save(factor.category)}
                disabled={saving === factor.category}
                className="mt-4 inline-flex items-center gap-1.5 rounded-input bg-[#0B4F4A] px-3 py-2 text-sm font-semibold text-white hover:bg-[#0B2F2C] disabled:opacity-50"
              >
                <Save size={15} /> {saving === factor.category ? "Saving…" : "Save rate"}
              </button>
            </div>
          ))}
        </div>
      )}
    </Section>
  );
}
