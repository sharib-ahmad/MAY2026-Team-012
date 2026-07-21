import { useState } from "react";
import { CheckCircle2 } from "lucide-react";
import { getSortingGuideItems, updateSortingGuideItems } from "../../../lib/mockSortingGuide";
import { Section } from "./shared";

// Story 3.1-AC2: gives an admin an actual editable path for the sorting
// guide's static content, instead of it being hardcoded with no update
// mechanism. One textarea per stream — one item per line.
const STREAMS = [
  { key: "wet", label: "Wet Waste" },
  { key: "dry", label: "Dry Waste" },
  { key: "recyclable", label: "Recyclable" },
];

export default function SortingGuideEditor() {
  const [items, setItems] = useState(getSortingGuideItems());
  const [saved, setSaved] = useState(false);

  const updateStream = (key, text) => {
    setSaved(false);
    setItems((prev) => ({ ...prev, [key]: text.split("\n") }));
  };

  const save = () => {
    STREAMS.forEach((s) => {
      const cleaned = (items[s.key] || []).map((i) => i.trim()).filter(Boolean);
      updateSortingGuideItems(s.key, cleaned);
    });
    setItems(getSortingGuideItems());
    setSaved(true);
  };

  return (
    <Section
      eyebrow="Content management"
      title="Sorting Guide content"
      actions={
        <button
          type="button"
          onClick={save}
          className="rounded-input bg-[#0B4F4A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0B2F2C]"
        >
          Save changes
        </button>
      }
    >
      <p className="text-sm text-gray-500 -mt-2 mb-5 max-w-xl">
        One item per line. Changes apply immediately to the public Sorting Guide page and the
        resident dashboard tab.
      </p>

      {saved && (
        <div className="mb-5 flex items-center gap-2 rounded-input border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 size={16} /> Sorting guide content updated.
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        {STREAMS.map((s) => (
          <div key={s.key}>
            <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
              {s.label}
            </label>
            <textarea
              rows={7}
              className="w-full border border-gray-200 rounded-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[#0B4F4A]/30"
              value={(items[s.key] || []).join("\n")}
              onChange={(e) => updateStream(s.key, e.target.value)}
            />
          </div>
        ))}
      </div>
    </Section>
  );
}
