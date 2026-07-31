import { useEffect, useState } from "react";
import { ScrollText } from "lucide-react";
import { getLogs } from "../../../lib/api";
import { Section, SearchInput } from "./shared";
import { formatDate } from "./format";

const ACTION_CLASS = {
  WARD_CREATED: "pill pill-info",
  WARD_UPDATED: "pill pill-warn",
  WARD_DELETED: "pill pill-danger",
  USER_CREATED: "pill pill-info",
  LOGIN_SUCCESS: "pill pill-info",
  LOGIN_FAILED: "pill pill-danger",
};

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [auditQuery, setAuditQuery] = useState("");

  // Fetch logs on component mount
  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        const data = await getLogs();
        setLogs(data.logs || []);
      } catch (err) {
        setError(err.message || "Failed to load logs");
      } finally {
        setLoading(false);
      }
    };

    fetchLogs();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <Section eyebrow="Accountability" title="Audit log">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-gray-500">Loading logs...</div>
          </div>
        </Section>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <Section eyebrow="Accountability" title="Audit log">
          <div className="flex items-center justify-center min-h-[400px]">
            <div className="text-red-500">Error: {error}</div>
          </div>
        </Section>
      </div>
    );
  }

  const aq = auditQuery.trim().toLowerCase();
  const filteredLogs = logs.filter(
    (log) =>
      !aq ||
      (log.actor_name && log.actor_name.toLowerCase().includes(aq)) ||
      log.action.toLowerCase().includes(aq) ||
      (log.entity_id && log.entity_id.toLowerCase().includes(aq)) ||
      (log.description && log.description.toLowerCase().includes(aq))
  );

  return (
    <div className="space-y-6">
      <Section
        eyebrow="Accountability"
        title="Audit log"
        actions={
          <SearchInput
            value={auditQuery}
            onChange={setAuditQuery}
            placeholder="Search user, action, entity…"
          />
        }
      >
        {filteredLogs.length === 0 && (
          <p className="text-center text-sm text-gray-400 py-8">No records found.</p>
        )}
        <ul className="space-y-4">
          {filteredLogs.map((log, i) => (
            <li key={log.id} className="flex items-start gap-4 text-sm">
              <span className="font-mono-civic text-[11px] text-gray-300 mt-0.5">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#0B4F4A] text-white">
                <ScrollText size={14} />
              </div>
              <div className="flex-1">
                <p className="text-[#14171F]">
                  <span className="font-semibold">{log.actor_name || "System"}</span>{" "}
                  <span className="text-gray-500">
                    {log.action.replace(/_/g, " ").toLowerCase()}
                  </span>{" "}
                  &mdash; {log.entity_type}{" "}
                  {log.entity_id && (
                    <span className="font-mono-civic text-xs">({log.entity_id})</span>
                  )}
                </p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {log.description} &middot;{" "}
                  <span className="font-mono-civic">{formatDate(log.timestamp)}</span>
                  {log.ip_address && <span> &middot; IP: {log.ip_address}</span>}
                </p>
              </div>
              <div>
                <span className={ACTION_CLASS[log.action] || "pill pill-slate"}>
                  {log.action.replace(/_/g, " ")}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}
