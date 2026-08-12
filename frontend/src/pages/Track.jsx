import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Clock,
  Package,
  Search,
  Ticket,
  FileText,
  Calendar,
  Truck,
  Box,
  Building2,
  Cog,
  CheckCircle2,
  Sparkles,
} from "lucide-react";

import PublicLayout from "../components/PublicLayout";
import { Card, StatusPill } from "../components/UI";
import { getPublicTracking } from "../lib/api";

function WasteFlowAnimation({ result }) {
  const isTicket = result.entity_type === "TICKET";

  const PICKUP_STAGES = [
    { key: "PENDING", label: "Request", desc: "Submitted", icon: FileText },
    { key: "SCHEDULED", label: "Schedule", desc: "Planned Date", icon: Calendar },
    { key: "COLLECTED", label: "Collect", desc: "Picked Up", icon: Truck },
    { key: "BATCHED", label: "Batch", desc: "Sorted/Packed", icon: Box },
    { key: "ASSIGNED", label: "Transfer", desc: "To Recycler", icon: Building2 },
    { key: "PROCESSING", label: "Process", desc: "Recycling", icon: Cog },
    { key: "PROCESSED", label: "Done", desc: "Completed", icon: CheckCircle2 },
  ];

  const TICKET_STAGES = [
    { key: "OPEN", label: "Submitted", desc: "Complaint filed", icon: FileText },
    { key: "RESOLVED", label: "Resolved", desc: "Action completed", icon: CheckCircle2 },
  ];

  const STAGES = isTicket ? TICKET_STAGES : PICKUP_STAGES;
  const timelineStages = result.timeline.map((e) => e.stage);

  // Find highest stage index completed
  let activeStageIndex = -1;
  STAGES.forEach((stage, idx) => {
    if (timelineStages.includes(stage.key)) {
      activeStageIndex = idx;
    }
  });

  // If status is closed/cancelled or resolved, force active index
  if (result.status === "RESOLVED") {
    activeStageIndex = STAGES.length - 1;
  }

  return (
    <Card className="overflow-hidden border border-gray-100 shadow-elevated">
      <style>{`
        @keyframes pulse-ring {
          0% { transform: scale(0.95); opacity: 0.8; }
          50% { transform: scale(1.35); opacity: 0.4; }
          100% { transform: scale(1.75); opacity: 0; }
        }
        .animate-pulse-ring {
          animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes line-flow {
          0% { background-position: 0% 50%; }
          100% { background-position: -200% 50%; }
        }
        .animate-line-flow {
          background-size: 200% auto;
          animation: line-flow 1.5s linear infinite;
        }
        .scrollbar-none::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-none {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
            <Sparkles className="text-emerald-500 animate-pulse" size={20} />
            {isTicket ? "Complaint Status Journey" : "Live Waste Journey"}
          </h3>
          <p className="text-xs text-gray-400">
            {isTicket
              ? "Track your complaint progress through to resolution"
              : "Track your waste from collection to successful processing"}
          </p>
        </div>
        <div className="text-xs font-mono bg-emerald-50 text-emerald-700 px-2.5 py-1 rounded-full border border-emerald-100 font-semibold">
          {STAGES[activeStageIndex]?.label || result.status.replace(/_/g, " ")}
        </div>
      </div>

      {/* Stepper Container */}
      <div className="relative py-4 overflow-x-auto scrollbar-none">
        <div
          className={`relative min-w-[720px] md:min-w-0 ${isTicket ? "max-w-md mx-auto min-w-[320px] md:min-w-[320px]" : ""}`}
        >
          {/* Horizontal connection line */}
          <div className="absolute top-[24px] left-[7%] right-[7%] h-1 bg-gray-200 rounded">
            {/* Progress fill */}
            <div
              className={`h-full bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-500 rounded transition-all duration-1000 ${
                activeStageIndex < STAGES.length - 1 ? "animate-line-flow" : ""
              }`}
              style={{
                width: `${(activeStageIndex / (STAGES.length - 1)) * 100}%`,
              }}
            />
          </div>

          {/* Nodes */}
          <div className={`grid relative z-10 ${isTicket ? "grid-cols-2" : "grid-cols-7"}`}>
            {STAGES.map((stage, idx) => {
              const IconComponent = stage.icon;
              const isCompleted = idx < activeStageIndex;
              const isActive = idx === activeStageIndex;

              // Find the event for this stage
              const event = result.timeline.find((e) => e.stage === stage.key);

              // Handle formatting
              const eventTime = event
                ? new Date(event.at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
                : "";
              const eventDate = event
                ? new Date(event.at).toLocaleDateString([], { month: "short", day: "numeric" })
                : "";

              return (
                <div key={stage.key} className="flex flex-col items-center text-center group">
                  {/* Node Icon Circle */}
                  <div className="relative shrink-0 mb-2">
                    {isActive && (
                      <div className="absolute inset-0 rounded-full bg-emerald-400/40 animate-pulse-ring" />
                    )}
                    <div
                      className={`w-12 h-12 rounded-full flex items-center justify-center border-2 transition-all duration-500 relative z-10 ${
                        isCompleted || (idx === STAGES.length - 1 && result.status === "RESOLVED")
                          ? "bg-emerald-500 border-emerald-500 text-white shadow-md shadow-emerald-200"
                          : isActive
                            ? "bg-white border-emerald-500 text-emerald-600 shadow-lg shadow-emerald-100 scale-115"
                            : "bg-gray-50 border-gray-200 text-gray-400"
                      }`}
                    >
                      <IconComponent size={20} className={isActive ? "animate-bounce" : ""} />
                    </div>
                  </div>

                  {/* Node Labels */}
                  <div>
                    <p
                      className={`text-sm font-bold transition-colors duration-300 ${
                        isActive
                          ? "text-emerald-600"
                          : isCompleted
                            ? "text-gray-700"
                            : "text-gray-400"
                      }`}
                    >
                      {stage.label}
                    </p>
                    <p className="text-[10px] text-gray-400 leading-tight">{stage.desc}</p>
                    {event && (
                      <p className="text-[9px] text-emerald-600 font-medium mt-1 bg-emerald-50 inline-block px-1.5 py-0.5 rounded">
                        {eventDate}, {eventTime}
                      </p>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
}

export default function Track() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const search = async (event) => {
    event.preventDefault();
    if (!code.trim()) return;

    setErr("");
    setResult(null);
    setLoading(true);
    try {
      const res = await getPublicTracking(code);
      setResult(res);
    } catch (requestError) {
      setErr(
        requestError.response?.status === 404
          ? "Reference not found. Check the ticket or pickup reference and try again."
          : "Unable to retrieve tracking progress. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const getFallback = (value) => {
    if (value) return value;
    const finishedStatuses = ["COMPLETED", "PROCESSED", "CANCELLED", "REJECTED", "RESOLVED"];
    const isFinished = finishedStatuses.includes(result?.status);
    return isFinished ? "Not Applicable" : "Awaiting Assignment";
  };

  const isTicket = result?.entity_type === "TICKET";

  return (
    <PublicLayout>
      <div className="min-h-screen bg-[#FBF7EE]">
        <div className="max-w-3xl mx-auto px-4 py-12 fade-in">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800">Track your request</h1>
            <p className="text-gray-500 mt-2">
              Enter a complaint ticket or pickup reference to view its current progress.
            </p>
          </div>

          <form onSubmit={search} className="flex gap-2 max-w-xl mx-auto mb-10">
            <div className="flex-1 relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={18}
              />
              <input
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-input text-sm shadow-soft focus:outline-none focus:ring-2 focus:ring-primary/30 bg-white"
                placeholder="e.g. PK-123456 or TK-123456"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-primary text-white px-6 py-3 rounded-input font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? "Loading…" : "Track"}
            </button>
          </form>

          {err && (
            <div className="max-w-xl mx-auto p-4 bg-red-50 text-red-600 rounded-lg text-sm border border-red-100 mb-6">
              {err}
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <WasteFlowAnimation result={result} />
              <Card>
                <div className="flex items-start justify-between mb-5">
                  <div className="flex items-center gap-2">
                    {isTicket ? <Ticket size={18} /> : <Package size={18} />}
                    <div>
                      <h2 className="font-bold text-lg">{result.ref_code}</h2>
                      <p className="text-xs text-gray-400">
                        {isTicket ? "COMPLAINT TICKET" : "PICKUP"}
                      </p>
                    </div>
                  </div>
                  <StatusPill status={result.status} />
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm border-t border-gray-100 pt-4">
                  <div>
                    <p className="text-xs text-gray-400">{isTicket ? "Issue type" : "Category"}</p>
                    <p className="font-medium">
                      {(result.issue_type || result.category || "—").replace(/_/g, " ")}
                    </p>
                  </div>
                  {result.scheduled_date && (
                    <div>
                      <p className="text-xs text-gray-400">Scheduled</p>
                      <p className="font-medium">
                        {new Date(result.scheduled_date).toLocaleString()}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-400">Last updated</p>
                    <p className="font-medium">{new Date(result.last_updated).toLocaleString()}</p>
                  </div>
                  {result.citizen_name && (
                    <div>
                      <p className="text-xs text-gray-400">Citizen</p>
                      <p className="font-medium">{result.citizen_name}</p>
                    </div>
                  )}
                  {result.zone_name && (
                    <div>
                      <p className="text-xs text-gray-400">Zone</p>
                      <p className="font-medium">{result.zone_name}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-400">Manager</p>
                    <p className="font-medium">{getFallback(result.manager_name)}</p>
                  </div>
                  {!isTicket && (
                    <div>
                      <p className="text-xs text-gray-400">Collector</p>
                      <p className="font-medium">{getFallback(result.collector_name)}</p>
                    </div>
                  )}
                  {!isTicket && (
                    <div>
                      <p className="text-xs text-gray-400">Recycler</p>
                      <p className="font-medium">{getFallback(result.recycler_name)}</p>
                    </div>
                  )}
                </div>
              </Card>
            </div>
          )}

          {!result && !err && (
            <div className="text-center py-12 text-gray-400">
              <Clock size={48} className="mx-auto mb-3 opacity-50" />
              <p className="text-sm">
                Track any complaint ticket or pickup using its reference number.
              </p>
              <Link to="/flows" className="text-primary text-sm mt-2 inline-block hover:underline">
                See how the full workflow works →
              </Link>
            </div>
          )}
        </div>
      </div>
    </PublicLayout>
  );
}
