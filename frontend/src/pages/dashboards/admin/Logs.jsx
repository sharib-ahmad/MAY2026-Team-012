import { ScrollText } from "lucide-react";
import DATA from "../../../data/admin_portal_data.json";
import { Section, PaginatedTable } from "./shared";
import { formatDate } from "./format";

const LEVEL_CLASS = {
  ERROR: "pill pill-danger",
  WARN: "pill pill-warn",
  INFO: "pill pill-info",
};

export default function Logs() {
  return (
    <div className="space-y-6">
      <Section eyebrow="Diagnostics" title="Server error log">
        <PaginatedTable
          columns={[
            {
              key: "level",
              label: "Level",
              render: (v) => <span className={LEVEL_CLASS[v] || "pill pill-slate"}>{v}</span>,
            },
            { key: "source", label: "Source" },
            { key: "message", label: "Message" },
            { key: "timestamp", label: "Time", render: (v) => formatDate(v) },
          ]}
          rows={DATA.error_logs}
        />
      </Section>

      <Section eyebrow="Accountability" title="Audit log">
        <ul className="space-y-4">
          {DATA.audit_log.map((entry, i) => (
            <li key={entry.id} className="flex items-start gap-4 text-sm">
              <span className="font-mono-civic text-[11px] text-gray-300 mt-0.5">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#0B4F4A] text-white">
                <ScrollText size={14} />
              </div>
              <div>
                <p className="text-[#14171F]">
                  <span className="font-semibold">{entry.actor}</span>{" "}
                  <span className="text-gray-500">
                    {entry.action.replace(/_/g, " ").toLowerCase()}
                  </span>{" "}
                  &mdash; {entry.target}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {entry.note} &middot;{" "}
                  <span className="font-mono-civic">{formatDate(entry.timestamp)}</span>
                </p>
              </div>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}
