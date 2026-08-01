import { useState } from "react";
import { Link } from "react-router-dom";
import { Clock, Package, Search, Ticket } from "lucide-react";

import PublicLayout from "../components/PublicLayout";
import { Card, StatusPill } from "../components/UI";
import { getPublicTracking } from "../lib/api";

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
      setResult(await getPublicTracking(code));
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

          <form onSubmit={search} className="flex gap-2 mb-6">
            <div className="flex-1 relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400"
                size={18}
              />
              <input
                className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-input text-sm shadow-soft focus:outline-none focus:ring-2 focus:ring-primary/30"
                placeholder="e.g. TK-ABC12345 or BPR-ABC12345"
                value={code}
                onChange={(event) => setCode(event.target.value)}
                aria-label="Ticket or pickup reference"
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

          {err && <div className="bg-red-50 text-red-700 p-4 rounded-card mb-6 text-sm">{err}</div>}

          {result && (
            <div className="space-y-4">
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
                </div>
              </Card>

              <Card title="Progress">
                <div className="space-y-3">
                  {result.timeline.map((event, index) => (
                    <div key={`${event.stage}-${event.at}`} className="flex gap-3">
                      <div className="flex flex-col items-center">
                        <div
                          className={`w-3 h-3 rounded-full ${index === result.timeline.length - 1 ? "bg-primary" : "bg-gray-300"}`}
                        />
                        {index < result.timeline.length - 1 && (
                          <div className="w-0.5 flex-1 bg-gray-200" />
                        )}
                      </div>
                      <div className="pb-3 flex-1">
                        <div className="flex items-center justify-between gap-3">
                          <span className="font-medium text-sm">{event.label}</span>
                          <span className="text-xs text-gray-400 whitespace-nowrap">
                            {new Date(event.at).toLocaleString()}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {event.stage.replace(/_/g, " ")}
                        </p>
                      </div>
                    </div>
                  ))}
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
