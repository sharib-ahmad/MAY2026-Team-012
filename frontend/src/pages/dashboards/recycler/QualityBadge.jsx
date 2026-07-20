import { CheckCircle2, Droplets, Blend, AlertTriangle } from "lucide-react";

const QUALITY_META = {
  CLEAN: { label: "Clean", icon: CheckCircle2, className: "bg-green-100 text-green-800" },
  MOISTURE_AFFECTED: {
    label: "Moisture-Affected",
    icon: Droplets,
    className: "bg-blue-100 text-blue-800",
  },
  MIXED: { label: "Mixed", icon: Blend, className: "bg-amber-100 text-amber-800" },
  // Story 4.2-AC2: Unsafe must be visually distinguished from lower-severity tags.
  UNSAFE: {
    label: "Unsafe",
    icon: AlertTriangle,
    className: "bg-red-100 text-red-800 ring-1 ring-red-400",
  },
};

export default function QualityBadge({ status }) {
  const meta = QUALITY_META[status] || {
    label: status || "Unknown",
    icon: CheckCircle2,
    className: "bg-gray-100 text-gray-700",
  };
  const Icon = meta.icon;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${meta.className}`}
    >
      <Icon size={12} /> {meta.label}
    </span>
  );
}
