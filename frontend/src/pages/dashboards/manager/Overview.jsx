import { ClusteredBarChartCard } from "../../../components/UI";
import DATA from "../../../data/municipal_officer_data.json";
import { Section, SeverityPill } from "./shared";
import { formatDate } from "./format";

// Chart tones from the Municipal Officer palette: goldenrod + olive.
const GOLD = "#B8860B";
const OLIVE = "#3F5426";

const openByWard = DATA.wards.map((w) => ({
  ward: w.code,
  open: DATA.complaints.filter((c) => c.ward_code === w.code && c.status !== "RESOLVED").length,
}));

// Escalated first, then high-severity open tickets — the queue an
// officer should look at before anything else.
const needsAttention = DATA.complaints
  .filter((c) => c.status === "ESCALATED" || (c.status !== "RESOLVED" && c.severity === "HIGH"))
  .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  .slice(0, 5);

export default function Overview() {
  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-2">
        <ClusteredBarChartCard
          title="Complaints this week — filed vs resolved"
          data={DATA.complaints_trend}
          nameKey="day"
          bars={[
            { key: "filed", name: "Filed", color: GOLD },
            { key: "resolved", name: "Resolved", color: OLIVE },
          ]}
        />
        <ClusteredBarChartCard
          title="Open complaints by ward"
          data={openByWard}
          nameKey="ward"
          bars={[{ key: "open", name: "Open complaints", color: GOLD }]}
        />
      </div>

      <Section eyebrow="Priority queue" title="Needs attention">
        <ul className="divide-y divide-gray-100">
          {needsAttention.map((c) => (
            <li key={c.id} className="py-3 flex flex-wrap items-center gap-x-4 gap-y-1">
              <span className="font-mono-civic text-xs text-gray-400">{c.ref_code}</span>
              <span className="text-xs font-semibold text-[#3F5426]">{c.ward_code}</span>
              <span className="flex-1 min-w-[200px] text-sm text-gray-700">{c.description}</span>
              <SeverityPill severity={c.severity} />
              <span className="text-xs text-gray-400">{formatDate(c.created_at)}</span>
            </li>
          ))}
        </ul>
      </Section>

      <Section eyebrow="Ward supervision" title="Today's ward coverage">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500 uppercase">
                <th className="px-4 py-2 font-medium">Ward</th>
                <th className="px-4 py-2 font-medium">Area</th>
                <th className="px-4 py-2 font-medium">Households</th>
                <th className="px-4 py-2 font-medium">Routes today</th>
                <th className="px-4 py-2 font-medium">Active workers</th>
                <th className="px-4 py-2 font-medium w-48">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {DATA.wards.map((w) => (
                <tr key={w.id} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="px-4 py-2.5 font-mono-civic text-xs">{w.code}</td>
                  <td className="px-4 py-2.5">{w.name}</td>
                  <td className="px-4 py-2.5">{w.households.toLocaleString("en-IN")}</td>
                  <td className="px-4 py-2.5">{w.routes_today}</td>
                  <td className="px-4 py-2.5">{w.active_workers}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-[#B8860B]"
                          style={{ width: `${w.coverage_pct}%` }}
                        />
                      </div>
                      <span className="font-mono-civic text-xs text-gray-500 w-9 text-right">
                        {w.coverage_pct}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}
