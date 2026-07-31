import { useEffect, useState } from "react";
import { Card } from "../../../components/UI";
import { getUserPickupOptions, scheduleUserPickup } from "../../../lib/api";
import { CheckCircle2 } from "lucide-react";

// Local YYYY-MM-DD for a given date, so the date picker's min (and our own
// validation) respects the resident's own clock rather than UTC.
function localISODate(date) {
  const offsetMs = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - offsetMs).toISOString().slice(0, 10);
}

// AC2 (Story 1.3): a bulk/institutional pickup needs at least a 24-hour
// lead time — that rules out "today" as well as any past date, since a
// request placed at any point today could be less than 24h before a
// same-day window. The earliest selectable date is therefore tomorrow.
const MIN_LEAD_HOURS = 24;
function minLeadDate() {
  return localISODate(new Date(Date.now() + MIN_LEAD_HOURS * 60 * 60 * 1000));
}

export default function SchedulePickup({ onNavigate }) {
  const minDateStr = minLeadDate();
  const [form, setForm] = useState({
    category: "",
    estimated_weight: "",
    scheduled_date: "",
    time_slot: "Morning (8-11)",
    notes: "",
  });
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);
  const [reference, setReference] = useState("");
  const [categories, setCategories] = useState([]);

  const slots = ["Morning (8-11)", "Midday (11-2)", "Evening (4-7)"];
  useEffect(() => {
    getUserPickupOptions()
      .then(({ categories: availableCategories }) => {
        setCategories(availableCategories);
        setForm((current) => ({
          ...current,
          category: current.category || availableCategories[0]?.code || "",
        }));
      })
      .catch(() => setErr("Unable to load pickup categories."));
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    if (!form.estimated_weight || Number(form.estimated_weight) <= 0) {
      setErr("Please enter an estimated weight greater than zero.");
      return;
    }
    if (!form.scheduled_date) {
      setErr("Please choose a date.");
      return;
    }
    if (form.scheduled_date < minDateStr) {
      setErr(
        `Pickup requests need at least ${MIN_LEAD_HOURS} hours' notice — please choose ${minDateStr} or later.`
      );
      return;
    }
    const scheduled = new Date(`${form.scheduled_date}T09:00:00`).toISOString();

    try {
      const pickup = await scheduleUserPickup({
        category: form.category,
        estimated_weight: parseFloat(form.estimated_weight),
        scheduled_date: scheduled,
        time_slot: form.time_slot,
        notes: form.notes || null,
      });
      setReference(pickup.ref_code);
      window.dispatchEvent(new Event("resident-notifications-updated"));
      setDone(true);
      setTimeout(() => onNavigate("pickups"), 2500);
    } catch (ex) {
      setErr(
        ex.response?.data?.error?.message ||
          ex.response?.data?.detail ||
          ex.message ||
          "Unable to schedule pickup."
      );
    }
  };

  if (done) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <CheckCircle2 className="mx-auto text-success mb-3" size={40} />
        <p className="font-medium">Pickup scheduled!</p>
        <p className="text-sm text-gray-500 mt-1">
          Your tracking reference is{" "}
          <span className="font-semibold text-gray-700">{reference}</span>.
        </p>
        <p className="text-sm text-gray-400 mt-1">Taking you to My Pickups…</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto fade-in">
      <h1 className="text-xl font-bold mb-6">Schedule a Pickup</h1>
      <Card>
        <form onSubmit={submit} className="space-y-4">
          {err && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{err}</div>}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Category</label>
            <select
              className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
            >
              {categories.map((category) => (
                <option key={category.code} value={category.code}>
                  {category.label}
                </option>
              ))}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">
                Est. Weight (kg) *
              </label>
              <input
                type="number"
                step="0.1"
                min="0.1"
                required
                className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
                value={form.estimated_weight}
                onChange={(e) => setForm({ ...form, estimated_weight: e.target.value })}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Date *</label>
              <input
                type="date"
                required
                min={minDateStr}
                className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
                value={form.scheduled_date}
                onChange={(e) => setForm({ ...form, scheduled_date: e.target.value })}
              />
              <p className="text-[11px] text-gray-400 mt-1">
                Requires at least {MIN_LEAD_HOURS}h notice.
              </p>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Time Slot *</label>
            <div className="flex gap-2 flex-wrap">
              {slots.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setForm({ ...form, time_slot: s })}
                  className={`px-3 py-2 rounded-input text-xs font-medium border ${
                    form.time_slot === s
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-gray-200"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Notes</label>
            <textarea
              className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
              rows={2}
              value={form.notes}
              onChange={(e) => setForm({ ...form, notes: e.target.value })}
            />
          </div>
          <button
            type="submit"
            className="w-full bg-primary text-white py-2.5 rounded-input font-medium hover:bg-primary/90"
          >
            Schedule Pickup
          </button>
        </form>
      </Card>
    </div>
  );
}
