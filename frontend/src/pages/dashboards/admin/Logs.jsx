import { useState } from "react";
import { ScrollText } from "lucide-react";
import DATA from "../../../data/admin_portal_data.json";
import { Section, PaginatedTable, SearchInput, FilterSelect } from "./shared";
import { formatDate } from "./format";

const LEVEL_CLASS = {
  ERROR: "pill pill-danger",
  WARN: "pill pill-warn",
  INFO: "pill pill-info",
};

const LEVEL_OPTIONS = [
  { value: "ALL", label: "All levels" },
  { value: "ERROR", label: "Error" },
  { value: "WARN", label: "Warning" },
  { value: "INFO", label: "Info" },
];

export default function Logs() {
  const [errorQuery, setErrorQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState("ALL");
  const [auditQuery, setAuditQuery] = useState("");

  const eq = errorQuery.trim().toLowerCase();
  const errors = DATA.error_logs.filter(
    (log) =>
      (levelFilter === "ALL" || log.level === levelFilter) &&
      (!eq || log.source.toLowerCase().includes(eq) || log.message.toLowerCase().includes(eq))
  );

  const aq = auditQuery.trim().toLowerCase();
  const audits = DATA.audit_log.filter(
    (entry) =>
      !aq ||
      entry.actor.toLowerCase().includes(aq) ||
      entry.action.replace(/_/g, " ").toLowerCase().includes(aq) ||
      entry.target.toLowerCase().includes(aq) ||
      entry.note.toLowerCase().includes(aq)
  );

  return (
    <div className="space-y-6">
      <Section
        eyebrow="Diagnostics"
        title="Server error log"
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <SearchInput
              value={errorQuery}
              onChange={setErrorQuery}
              placeholder="Search source, message…"
            />
            <FilterSelect value={levelFilter} onChange={setLevelFilter} options={LEVEL_OPTIONS} />
          </div>
        }
      >
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
          rows={errors}
        />
      </Section>

      <Section
        eyebrow="Accountability"
        title="Audit log"
        actions={
          <SearchInput
            value={auditQuery}
            onChange={setAuditQuery}
            placeholder="Search actor, action…"
          />
        }
      >
        {audits.length === 0 && (
          <p className="text-center text-sm text-gray-400 py-8">No records found.</p>
        )}
        <ul className="space-y-4">
          {audits.map((entry, i) => (
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
