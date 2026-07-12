import { Card } from "../../../components/UI";
import { Droplets, Newspaper, Recycle } from "lucide-react";

// AC1: renders fully with no login required and no external data fetch —
// this is a static reference page, so it loads instantly.
// AC3 (Performance on low-end devices): pure text/table content, no
// images, so it stays lightweight on slow connections.
const STREAMS = [
  {
    key: "wet",
    label: "Wet Waste",
    icon: Droplets,
    color: "text-emerald-600 bg-emerald-50",
    items: [
      "Fruit & vegetable peels",
      "Cooked/uncooked food scraps",
      "Tea leaves & coffee grounds",
      "Eggshells",
      "Garden trimmings, flowers, leaves",
    ],
  },
  {
    key: "dry",
    label: "Dry Waste",
    icon: Newspaper,
    color: "text-amber-600 bg-amber-50",
    items: [
      "Paper, cardboard & cartons",
      "Plastic wrappers & packaging",
      "Cloth, rags & footwear",
      "Broken ceramics & glass",
      "Rubber & thermocol",
    ],
  },
  {
    key: "recyclable",
    label: "Recyclable",
    icon: Recycle,
    color: "text-sky-600 bg-sky-50",
    items: [
      "Clean plastic bottles & containers (PET/HDPE)",
      "Metal cans & foil",
      "Glass bottles & jars",
      "Newspaper, office paper, cardboard (dry & clean)",
      "E-waste — batteries, cables, small electronics (bag separately)",
    ],
  },
];

export default function SortingGuide() {
  return (
    <div className="space-y-6 fade-in max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold">Sorting Guide</h1>
        <p className="text-sm text-gray-500 mt-1">
          What belongs in each stream — no login required, share this page with anyone.
        </p>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        {STREAMS.map((s) => {
          const Icon = s.icon;
          return (
            <Card key={s.key} className="!p-0 overflow-hidden">
              <div className={`px-4 py-3 flex items-center gap-2 ${s.color}`}>
                <Icon size={18} />
                <h3 className="font-semibold text-sm">{s.label}</h3>
              </div>
              <ul className="p-4 space-y-2 text-sm text-gray-700 list-disc list-inside">
                {s.items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </Card>
          );
        })}
      </div>

      <Card>
        <p className="text-xs text-gray-500">
          Rules are set by your municipal ward office and may be updated periodically by an
          administrator. If something you have isn't listed here, ask EcoBot or raise a ticket for
          guidance.
        </p>
      </Card>
    </div>
  );
}
