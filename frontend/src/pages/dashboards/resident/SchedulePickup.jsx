import { useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card } from "../../../components/UI";
import AddressField from "../../../components/AddressField";
import { createPickup } from "../../../lib/mockResidentData";
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
  const { user } = useAuth();
  const minDateStr = minLeadDate();
  const [form, setForm] = useState({
    category: "Paper",
    estimated_weight: "",
    scheduled_date: "",
    time_slot: "Morning (8-11)",
    notes: "",
  });
  const [address, setAddress] = useState(user?.address || "");
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);

  const categories = ["Daily Waste", "Paper", "Plastic", "Metal", "Mixed Dry", "E-waste", "Glass"];
  const slots = ["Morning (8-11)", "Midday (11-2)", "Evening (4-7)"];
  const isDailyWaste = form.category === "Daily Waste";

  const submit = (e) => {
    e.preventDefault();
    setErr("");
    if (!address.trim()) {
      setErr("Please add a pickup address.");
      return;
    }
    if (!isDailyWaste && !form.scheduled_date) {
      setErr("Please choose a date.");
      return;
    }
    if (!isDailyWaste && form.scheduled_date < minDateStr) {
      setErr(
        `Pickup requests need at least ${MIN_LEAD_HOURS} hours' notice — please choose ${minDateStr} or later.`
      );
      return;
    }
    const scheduled = form.scheduled_date
      ? new Date(`${form.scheduled_date}T09:00:00`).toISOString()
      : new Date().toISOString();

    createPickup(user, {
      category: form.category,
      estimated_weight: isDailyWaste
        ? 5
        : form.estimated_weight
          ? parseFloat(form.estimated_weight)
          : null,
      scheduled_date: isDailyWaste ? new Date().toISOString() : scheduled,
      time_slot: isDailyWaste ? "Morning (8-11)" : form.time_slot,
      notes: form.notes || null,
      pickup_address: address,
    });
    setDone(true);
    setTimeout(() => onNavigate("pickups"), 900);
  };

  if (done) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <CheckCircle2 className="mx-auto text-success mb-3" size={40} />
        <p className="font-medium">Pickup scheduled!</p>
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
              {categories.map((c) => (
                <option key={c}>{c}</option>
              ))}
            </select>
          </div>
          {!isDailyWaste && (
            <>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Est. Weight (kg)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    className="w-full border border-gray-200 rounded-input px-3 py-2.5 text-sm"
                    value={form.estimated_weight}
                    onChange={(e) => setForm({ ...form, estimated_weight: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Date</label>
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
                <label className="block text-xs font-medium text-gray-600 mb-1">Time Slot</label>
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
            </>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Pickup Address *</label>
            <AddressField address={address} onChange={({ address: a }) => setAddress(a)} />
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
