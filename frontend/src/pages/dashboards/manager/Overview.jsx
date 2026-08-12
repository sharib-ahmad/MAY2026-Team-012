import { AlertCircle, AlertTriangle, BadgeCheck, MapPinned, Users } from "lucide-react";
import { useAuth } from "../../../context/AuthContext";
import { ClusteredBarChartCard } from "../../../components/UI";
import { listMixedWasteFlags } from "../../../lib/mockCollectorData";
import { Section, SeverityPill } from "./shared";
import { formatDate } from "./format";

// Chart tones from the Municipal Officer palette: goldenrod + olive.
const GOLD = "#B8860B";
const OLIVE = "#3F5426";
const THEME = "#14171F"; // hero card — matches the dashboard shell's single theme color

// Story 3.2-AC3: Hazardous mixed-waste flags need to appear prominently
// and take priority over Routine ones for officer review.
function getPriorityMixedWasteFlags() {
  return listMixedWasteFlags()
    .slice()
    .sort((a, b) => {
      if (a.severity !== b.severity) return a.severity === "HAZARDOUS" ? -1 : 1;
      return new Date(b.flagged_at) - new Date(a.flagged_at);
    })
    .slice(0, 5);
}
void getPriorityMixedWasteFlags;

// Title/stat hero — moved here from the dashboard shell so it lives with
// the page it summarizes rather than as a band sitting above the sidebar.
// Recolored onto the shell's single theme color (#14171F) instead of the
// olive it used to carry.
function WardOverviewHero({ name, stats }) {
  return (
    <div className="rounded-2xl overflow-hidden mb-6" style={{ backgroundColor: THEME }}>
      <div className="px-5 sm:px-8 pt-7 pb-5">
        <div className="inline-flex items-center gap-2 rounded-full border border-[#E9C55F]/40 bg-[#E9C55F]/10 px-3 py-1 text-xs font-medium text-[#F0D488]">
          <BadgeCheck size={13} /> {name || "Municipal Officer"}
        </div>
        <h1 className="font-display mt-3 text-2xl sm:text-3xl font-semibold text-white leading-[1.1]">
          Wards, routes &amp; citizen grievances.
        </h1>
      </div>
      <div className="px-5 sm:px-8 pb-7 grid grid-cols-2 sm:grid-cols-4 divide-x divide-white/15">
        {[
          [
            AlertCircle,
            stats.open_complaints,
            "open complaints",
            `${stats.escalated_complaints} escalated`,
          ],
          [
            MapPinned,
            `${stats.routes_completed_today}/${stats.routes_today}`,
            "routes completed",
            `${stats.route_points_collected}/${stats.route_points_total} points collected`,
          ],
          [
            Users,
            stats.collectors_assigned,
            "collectors assigned",
            `${stats.wards_supervised} wards supervised`,
          ],
          [
            BadgeCheck,
            stats.resolved_this_week,
            "resolved this week",
            `avg ${stats.avg_resolution_hours} hrs to close`,
          ],
        ].map(([Icon, value, label, sub]) => (
          <div key={label} className="px-3 sm:px-5 py-1">
            <Icon size={15} className="text-[#F0D488]" />
            <p className="font-display mt-1.5 text-xl sm:text-2xl font-semibold text-white">
              {value}
            </p>
            <p className="text-[11px] uppercase tracking-wide text-white/70 mt-0.5">{label}</p>
            <p className="font-mono-civic text-[10px] text-white/45 mt-1">{sub}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function Overview({ data }) {
  const { user } = useAuth();
  const wardCoverage = data.ward_coverage || data.wards;
  const openByWardLive = data.all_ward_open_complaints || [];
  const needsAttentionLive = data.complaints
    .filter((c) => c.status !== "RESOLVED" && c.severity === "HIGH")
    .slice(0, 5);
  const hazardFlags = data.mixed_waste_flags
    .slice()
    .sort((a, b) => {
      if (a.severity !== b.severity) return a.severity === "HAZARDOUS" ? -1 : 1;
      return new Date(b.flagged_at) - new Date(a.flagged_at);
    })
    .slice(0, 5);

  return (
    <div className="space-y-6">
      <WardOverviewHero name={user?.name} stats={data.stats} />

      <div className="grid gap-6 lg:grid-cols-2">
        <ClusteredBarChartCard
          title="Complaints this week — filed vs resolved"
          data={data.complaints_trend}
          nameKey="day"
          bars={[
            { key: "filed", name: "Filed", color: GOLD },
            { key: "resolved", name: "Resolved", color: OLIVE },
          ]}
        />
        <ClusteredBarChartCard
          title="Complaints by ward — open vs resolved"
          data={openByWardLive}
          nameKey="ward"
          bars={[
            { key: "open", name: "Open", color: GOLD },
            { key: "resolved", name: "Resolved", color: OLIVE },
          ]}
          isStacked={true}
        />
      </div>

      <Section eyebrow="Priority queue" title="Needs attention">
        <ul className="divide-y divide-gray-100">
          {needsAttentionLive.map((c) => (
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

      <Section eyebrow="Field reports" title="Mixed waste flags">
        {hazardFlags.length === 0 ? (
          <p className="text-sm text-gray-400 py-2">No mixed-waste issues flagged yet.</p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {hazardFlags.map((f) => (
              <li key={f.id} className="py-3 flex flex-wrap items-center gap-x-4 gap-y-1">
                <span className="font-mono-civic text-xs text-gray-400">{f.route_code}</span>
                <span className="text-xs font-semibold text-[#3F5426]">{f.ward_code}</span>
                <span className="flex-1 min-w-[200px] text-sm text-gray-700">
                  {f.point_label} — {f.note}
                </span>
                {f.severity === "HAZARDOUS" ? (
                  <span className="pill bg-red-100 text-red-800 inline-flex items-center gap-1">
                    <AlertTriangle size={11} /> Hazardous
                  </span>
                ) : (
                  <span className="pill bg-gray-100 text-gray-700">Routine</span>
                )}
                <span className="text-xs text-gray-400">{formatDate(f.flagged_at)}</span>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section eyebrow="Ward supervision" title="Today's ward coverage">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 text-left text-xs text-gray-500 uppercase">
                <th className="px-4 py-2 font-medium">Ward</th>
                <th className="px-4 py-2 font-medium">Area</th>
                <th className="px-4 py-2 font-medium">Households</th>
                <th className="px-4 py-2 font-medium">Stops today</th>
                <th className="px-4 py-2 font-medium">Active workers</th>
                <th className="px-4 py-2 font-medium w-48">Coverage</th>
              </tr>
            </thead>
            <tbody>
              {wardCoverage.map((w) => (
                <tr
                  key={w.id}
                  className={`border-b border-gray-50 ${w.is_managed ? "bg-amber-50 hover:bg-amber-100/70" : "hover:bg-gray-50"}`}
                >
                  <td className="px-4 py-2.5 font-mono-civic text-xs">
                    <span className="inline-flex items-center gap-2">
                      {w.code}
                      {w.is_managed && (
                        <span className="rounded-full bg-[#3F5426] px-2 py-0.5 font-sans text-[10px] font-semibold text-white">
                          Your ward
                        </span>
                      )}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">{w.name}</td>
                  <td className="px-4 py-2.5">{w.households.toLocaleString("en-IN")}</td>
                  <td className="px-4 py-2.5">{w.stops_today}</td>
                  <td className="px-4 py-2.5">{w.active_workers}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
                        <div
                          className={`h-full rounded-full ${w.is_managed ? "bg-[#3F5426]" : "bg-[#B8860B]"}`}
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
