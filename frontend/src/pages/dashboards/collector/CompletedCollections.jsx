import { useCallback, useEffect, useMemo, useState } from "react";
import { CheckCircle2, Flag, Recycle, Search } from "lucide-react";
import { Card, StatusPill } from "../../../components/UI";
import { getCompletedCollectorCollections } from "../../../lib/api";

const FILTERS = [
  ["newest", "New to old"],
  ["oldest", "Old to new"],
  ["flagged", "Flagged"],
  ["normal", "Normal"],
];

export default function CompletedCollections() {
  const [collections, setCollections] = useState([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("newest");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setCollections(await getCompletedCollectorCollections());
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Unable to load completed collections.");
    }
  }, []);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(timeoutId);
  }, [load]);

  const results = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const filtered = collections.filter((collection) => {
      const matchesFilter =
        filter === "newest" ||
        filter === "oldest" ||
        (filter === "flagged" && collection.is_flagged) ||
        (filter === "normal" && !collection.is_flagged);
      const searchable = [
        collection.ref_code,
        collection.resident_name,
        collection.category,
        collection.zone_name,
      ]
        .join(" ")
        .toLowerCase();
      return matchesFilter && (!needle || searchable.includes(needle));
    });
    return filtered.sort((a, b) => {
      const difference = new Date(b.completed_at || 0) - new Date(a.completed_at || 0);
      return filter === "oldest" ? -difference : difference;
    });
  }, [collections, filter, query]);

  return (
    <div className="min-h-[calc(100vh-8rem)] flex flex-col space-y-6 fade-in">
      <div>
        <p className="text-xs tracking-[0.2em] text-[#2947A3]/60 font-semibold uppercase">
          Collection Register
        </p>
        <h1 className="font-serif text-2xl sm:text-3xl font-bold text-[#1F3259] mt-1">
          Completed Collections
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Search and review your completed pickup history.
        </p>
      </div>

      <Card className="!p-4">
        <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
          <label className="relative flex-1 max-w-xl">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search resident, pickup code, category or zone"
              className="w-full rounded-input border border-gray-200 py-2 pl-9 pr-3 text-sm"
            />
          </label>
          <label className="flex items-center gap-2 text-sm font-medium text-gray-600">
            Filter
            <select
              value={filter}
              onChange={(event) => setFilter(event.target.value)}
              className="rounded-input border border-gray-200 bg-white px-3 py-2 text-sm font-normal text-gray-700"
            >
              {FILTERS.map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </Card>

      {error && <div className="rounded-input bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className="space-y-3">
        {results.map((collection) => (
          <Card key={collection.id} className="!p-4 border-l-4 border-l-emerald-500">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-start gap-3">
                <span className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-full bg-emerald-500 text-white">
                  <CheckCircle2 size={18} />
                </span>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-serif font-semibold text-[#0B3D38]">
                      {collection.resident_name}
                    </span>
                    <StatusPill status="COLLECTED" />
                    {collection.is_flagged ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-[11px] font-semibold text-red-700">
                        <Flag size={11} /> Flagged
                      </span>
                    ) : (
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700">
                        Green
                      </span>
                    )}
                  </div>
                  <p className="mt-1 text-sm text-gray-600">
                    {collection.category} · {collection.estimated_weight} kg
                  </p>
                  <p className="mt-0.5 text-xs text-gray-400">
                    {collection.ref_code} · {collection.zone_name}
                  </p>
                </div>
              </div>
              <time className="text-xs text-gray-400">
                {collection.completed_at ? new Date(collection.completed_at).toLocaleString() : "—"}
              </time>
            </div>
          </Card>
        ))}
        {!error && results.length === 0 && (
          <p className="py-12 text-center text-sm text-gray-400">
            No completed collections match this filter.
          </p>
        )}
      </div>

      <div className="!mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-[#2947A3]/15 pt-6">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#2947A3]">
            <Recycle size={13} className="text-white" />
          </div>
          <div>
            <p className="text-xs font-semibold text-[#1F3259]">Verdeza</p>
            <p className="text-[11px] text-gray-400">
              © 2026 Ministry of Housing &amp; Urban Affairs · Portal v2.4
            </p>
          </div>
        </div>
        <p className="text-[11px] text-gray-400">Helpline · 000-111-1969 · toll-free</p>
      </div>
    </div>
  );
}
