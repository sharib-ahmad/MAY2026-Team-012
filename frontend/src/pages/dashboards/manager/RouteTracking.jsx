import { useMemo, useState } from "react";
import { Modal, StatusPill } from "../../../components/UI";
import DATA from "../../../data/municipal_officer_data.json";
import { Section, PaginatedTable, FilterSelect, SeverityPill } from "./shared";
import { formatDate, formatTime } from "./format";

const WARD_OPTIONS = [
  { value: "ALL", label: "All wards" },
  ...DATA.wards.map((w) => ({ value: w.code, label: `${w.code} · ${w.name}` })),
];

const ROUTE_STATUS_OPTIONS = [
  { value: "ALL", label: "All statuses" },
  { value: "ASSIGNED", label: "Assigned" },
  { value: "IN_PROGRESS", label: "In progress" },
  { value: "DELAYED", label: "Delayed" },
  { value: "COMPLETED", label: "Completed" },
];

const DELAY_REASON_LABELS = {
  VEHICLE_BREAKDOWN: "Vehicle breakdown",
  HEAVY_TRAFFIC: "Heavy traffic",
  ACCESS_BLOCKED: "Access blocked",
  WASTE_NOT_READY: "Waste not ready",
  ROUTE_OVERLOAD: "Route overload",
};

const workerName = (id) => DATA.workers.find((w) => w.id === id)?.name || "Unassigned";

function ProgressBar({ collected, total }) {
  const pct = total ? Math.round((collected / total) * 100) : 0;
  return (
    <div className="flex items-center gap-2 min-w-[130px]">
      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className="h-full rounded-full bg-[#B8860B]" style={{ width: `${pct}%` }} />
      </div>
      <span className="font-mono-civic text-xs text-gray-500">
        {collected}/{total}
      </span>
    </div>
  );
}

export default function RouteTracking() {
  const [wardFilter, setWardFilter] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selected, setSelected] = useState(null);

  // Worker updates arrive as per-point statuses; roll them up once into
  // the numbers the summary table shows.
  const routes = useMemo(
    () =>
      DATA.routes.map((r) => ({
        ...r,
        worker_name: workerName(r.worker_id),
        points_total: r.points.length,
        points_collected: r.points.filter((p) => p.status === "COLLECTED").length,
      })),
    []
  );

  const rows = routes.filter(
    (r) =>
      (wardFilter === "ALL" || r.ward_code === wardFilter) &&
      (statusFilter === "ALL" || r.status === statusFilter)
  );

  return (
    <div className="space-y-6">
      <Section
        eyebrow="Same-day supervision"
        title="Route tracking"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <FilterSelect value={wardFilter} onChange={setWardFilter} options={WARD_OPTIONS} />
            <FilterSelect
              value={statusFilter}
              onChange={setStatusFilter}
              options={ROUTE_STATUS_OPTIONS}
            />
          </div>
        }
      >
        <PaginatedTable
          onRowClick={setSelected}
          columns={[
            {
              key: "code",
              label: "Route",
              render: (v) => <span className="font-mono-civic text-xs">{v}</span>,
            },
            {
              key: "ward_code",
              label: "Ward",
              render: (v) => <span className="text-xs font-semibold text-[#3F5426]">{v}</span>,
            },
            { key: "worker_name", label: "Worker" },
            { key: "vehicle", label: "Vehicle" },
            {
              key: "shift",
              label: "Shift",
              render: (v) => (
                <span className="text-xs">{v === "MORNING" ? "Morning" : "Evening"}</span>
              ),
            },
            {
              key: "points_collected",
              label: "Progress",
              render: (_, row) => (
                <ProgressBar collected={row.points_collected} total={row.points_total} />
              ),
            },
            { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
            { key: "last_update_at", label: "Last update", render: (v) => formatDate(v) },
          ]}
          rows={rows}
        />
      </Section>

      <div className="grid gap-6 lg:grid-cols-2">
        <Section eyebrow="Worker reports" title="Delay logs">
          <ul className="divide-y divide-gray-100">
            {DATA.delay_logs.map((d) => (
              <li key={d.id} className="py-3">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="pill bg-amber-100 text-amber-800">
                    {DELAY_REASON_LABELS[d.reason] || d.reason}
                  </span>
                  <span className="font-mono-civic text-xs text-gray-400">{d.route_code}</span>
                  <span className="text-xs font-semibold text-[#3F5426]">{d.ward_code}</span>
                  <span className="ml-auto text-xs text-gray-400">{formatDate(d.logged_at)}</span>
                </div>
                <p className="text-sm text-gray-700 mt-1.5">{d.note}</p>
                <p className="text-xs text-gray-400 mt-0.5">Logged by {d.worker_name}</p>
              </li>
            ))}
          </ul>
        </Section>

        <Section eyebrow="Segregation issues" title="Mixed-waste flags">
          <ul className="divide-y divide-gray-100">
            {DATA.mixed_waste_flags.map((m) => (
              <li key={m.id} className="py-3">
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                  <SeverityPill severity={m.severity} />
                  <span className="text-sm font-medium text-gray-800">{m.point_label}</span>
                  <span className="text-xs font-semibold text-[#3F5426]">{m.ward_code}</span>
                  <span className="ml-auto text-xs text-gray-400">{formatDate(m.flagged_at)}</span>
                </div>
                <p className="text-sm text-gray-700 mt-1.5">{m.note}</p>
              </li>
            ))}
          </ul>
        </Section>
      </div>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Route ${selected.code} — ${selected.ward_code}` : ""}
      >
        {selected && (
          <div className="space-y-4 text-sm">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <p>
                <span className="text-gray-400">Worker</span>
                <br />
                {selected.worker_name}
              </p>
              <p>
                <span className="text-gray-400">Vehicle</span>
                <br />
                {selected.vehicle}
              </p>
              <p>
                <span className="text-gray-400">Started</span>
                <br />
                {formatDate(selected.started_at)}
              </p>
              <p>
                <span className="text-gray-400">Status</span>
                <br />
                <StatusPill status={selected.status} />
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2">
                Route points ({selected.points_collected}/{selected.points_total} collected)
              </p>
              <ul className="divide-y divide-gray-100 rounded-input border border-gray-100">
                {selected.points.map((p) => (
                  <li key={p.seq} className="flex items-center gap-3 px-3 py-2">
                    <span className="font-mono-civic text-xs text-gray-400 w-5">{p.seq}</span>
                    <span className="flex-1">{p.label}</span>
                    <span className="text-xs text-gray-400">{formatTime(p.updated_at)}</span>
                    <StatusPill status={p.status} />
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
