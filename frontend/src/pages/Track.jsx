import { useState } from "react";
import { Link } from "react-router-dom";
import PublicLayout from "../components/PublicLayout";
import { Card, StatusPill } from "../components/UI";
import { Search, ShieldCheck, ShieldAlert, MapPin, Package, Clock, Ticket } from "lucide-react";
import { getTrackResult } from "../lib/mockResidentData";

export default function Track() {
  const [code, setCode] = useState("");
  const [result, setResult] = useState(null);
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const search = (e) => {
    e.preventDefault();
    if (!code.trim()) return;
    setErr("");
    setResult(null);
    setLoading(true);
    // Local, backend-free lookup — searches this browser's pickups and
    // tickets for an exact ref-code match and returns exactly one
    // result (or none), never a full listing.
    const data = getTrackResult(code);
    if (data) {
      setResult(data);
    } else {
      setErr("Id not found");
    }
    setLoading(false);
  };

  const isTicket = result?.entity_type === "TICKET";

  return (
    <PublicLayout>
      <div className="min-h-screen bg-[#FBF7EE]">
        <div className="max-w-3xl mx-auto px-4 py-12 fade-in">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-800">Track Your Waste</h1>
            <p className="text-gray-500 mt-2">
              Enter a pickup ID, ticket ID, or QR code to view status and history.
            </p>
          </div>
          <form onSubmit={search} className="flex gap-2 mb-6">
            <div className="flex-1 relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={18}
              />
              <input
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-input text-sm shadow-soft focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="e.g. P-201, T-001, PK-ABC123DEF4"
                value={code}
                onChange={(e) => setCode(e.target.value)}
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="bg-primary text-white px-6 py-3 rounded-input font-medium hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? "…" : "Track"}
            </button>
          </form>

          {err && <div className="bg-red-50 text-red-700 p-4 rounded-card mb-6 text-sm">{err}</div>}

          {result && isTicket && (
            <div className="space-y-4">
              <Card>
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Ticket size={16} />
                    <div>
                      <h2 className="font-bold text-lg">{result.code}</h2>
                      <p className="text-xs text-gray-400">TICKET</p>
                    </div>
                  </div>
                  <StatusPill status={result.status} />
                </div>
                <div className="space-y-3 text-sm">
                  <div>
                    <span className="text-gray-400">Issue:</span>{" "}
                    {result.issue_type?.replace(/_/g, " ")}
                  </div>
                  <div className="bg-gray-50 rounded-input p-3">{result.description}</div>
                  {result.resolution_notes && (
                    <div>
                      <p className="text-xs font-medium text-gray-600 mb-1">Manager Resolution</p>
                      <div className="bg-green-50 text-green-800 rounded-input p-3">
                        {result.resolution_notes}
                        {result.resolver_name && (
                          <p className="text-xs mt-1">— {result.resolver_name}</p>
                        )}
                      </div>
                    </div>
                  )}
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
                    <div>Created: {new Date(result.created_at).toLocaleString()}</div>
                    <div>Last updated: {new Date(result.last_updated).toLocaleString()}</div>
                  </div>
                </div>
              </Card>
            </div>
          )}

          {result && !isTicket && (
            <div className="space-y-4">
              <Card>
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2">
                      {result.entity_type === "PICKUP" ? (
                        <Package size={16} />
                      ) : (
                        <MapPin size={16} />
                      )}
                      <h2 className="font-bold text-lg">{result.ref_code || result.code}</h2>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {result.entity_type} · {result.code}
                    </p>
                  </div>
                  <StatusPill status={result.status} />
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-center">
                  {result.resident_name && (
                    <div>
                      <p className="text-xs text-gray-400">Resident</p>
                      <p className="font-semibold">{result.resident_name}</p>
                    </div>
                  )}
                  {result.collector_name && (
                    <div>
                      <p className="text-xs text-gray-400">Collector</p>
                      <p className="font-semibold">{result.collector_name}</p>
                    </div>
                  )}
                  {result.scheduled_date && (
                    <div>
                      <p className="text-xs text-gray-400">Scheduled</p>
                      <p className="font-semibold">
                        {new Date(result.scheduled_date).toLocaleDateString()}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-400">Category</p>
                    <p className="font-semibold">{result.category || "—"}</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">Weight</p>
                    <p className="font-semibold">{result.weight?.toFixed(1) || "—"} kg</p>
                  </div>
                  <div>
                    <p className="text-xs text-gray-400">CO₂ Saved</p>
                    <p className="font-semibold text-green-600">
                      {result.co2_saved?.toFixed(1) || "—"} kg
                    </p>
                  </div>
                  {result.credits != null && (
                    <div>
                      <p className="text-xs text-gray-400">Credits</p>
                      <p className="font-semibold text-manager">{result.credits?.toFixed(1)}</p>
                    </div>
                  )}
                </div>
                {result.notes && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs text-gray-400 mb-1">Resident Notes</p>
                    <p className="text-sm bg-gray-50 rounded-input p-3">{result.notes}</p>
                  </div>
                )}
              </Card>

              <Card title="Chain of Custody">
                <div
                  className={`flex items-center gap-2 p-3 rounded-input mb-4 ${result.verified ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"}`}
                >
                  {result.verified ? <ShieldCheck size={18} /> : <ShieldAlert size={18} />}
                  <span className="text-sm font-medium">
                    {result.verified
                      ? "Hash chain verified — integrity intact"
                      : "Hash chain BROKEN — possible tampering"}
                  </span>
                </div>
                <div className="space-y-3">
                  {(result.timeline ?? []).map((evt, i, arr) => (
                    <div key={evt.id} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div
                          className={`w-3 h-3 rounded-full ${i === arr.length - 1 ? "bg-primary" : "bg-gray-300"}`}
                        />
                        {i < arr.length - 1 && <div className="w-0.5 flex-1 bg-gray-200" />}
                      </div>
                      <div className="pb-3 flex-1">
                        <div className="flex items-center justify-between">
                          <span className="font-medium text-sm">
                            {evt.event_type.replace(/_/g, " ")}
                          </span>
                          <span className="text-xs text-gray-400">
                            {new Date(evt.created_at).toLocaleString()}
                          </span>
                        </div>
                        {evt.note && <p className="text-xs text-gray-500 mt-0.5">{evt.note}</p>}
                        <code className="text-xs text-gray-400 block mt-0.5">
                          {evt.hash?.slice(0, 16)}…
                        </code>
                      </div>
                    </div>
                  ))}
                  {(result.timeline ?? []).length === 0 && (
                    <p className="text-gray-400 text-sm">No events recorded yet</p>
                  )}
                </div>
              </Card>
            </div>
          )}

          {!result && !err && (
            <div className="text-center py-12 text-gray-400">
              <Clock size={48} className="mx-auto mb-3 opacity-50" />
              <p className="text-sm">
                Enter a pickup ref, ticket ref, or QR code above to trace its journey.
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
