import { useState } from "react";
import { Card, Empty } from "../../../components/UI";
import { Search, Sun, Moon, MapPin, AlertCircle } from "lucide-react";
import { getWardSchedule, listWardCodes } from "../../../lib/mockSchedules";

export default function ScheduleLookup() {
  const wards = listWardCodes();
  const [code, setCode] = useState("");
  // AC3: no result renders until a ward code has actually been searched.
  const [result, setResult] = useState(null);
  const [searched, setSearched] = useState(false);

  const runSearch = (e) => {
    e?.preventDefault();
    if (!code.trim()) {
      setSearched(false);
      setResult(null);
      return;
    }
    setResult(getWardSchedule(code));
    setSearched(true);
  };

  return (
    <div className="space-y-6 fade-in max-w-2xl mx-auto">
      <div>
        <h1 className="text-xl font-bold">Schedule Look-up</h1>
        <p className="text-sm text-gray-500 mt-1">
          Search your ward code to see the morning/evening arrival windows for wet, dry, and
          recyclable waste.
        </p>
      </div>

      <Card>
        <form onSubmit={runSearch} className="flex gap-2">
          <div className="relative flex-1">
            <MapPin size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              list="ward-codes"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter ward code, e.g. WARD-01"
              className="w-full border border-gray-200 rounded-input pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
            <datalist id="ward-codes">
              {wards.map((w) => (
                <option key={w.code} value={w.code}>
                  {w.name}
                </option>
              ))}
            </datalist>
          </div>
          <button
            type="submit"
            className="bg-primary text-white px-4 py-2.5 rounded-input text-sm font-medium hover:bg-primary/90 flex items-center gap-2"
          >
            <Search size={15} /> Search
          </button>
        </form>
      </Card>

      {/* AC3: prompt to provide a ward code before any results render */}
      {!searched && (
        <Card>
          <Empty
            icon={MapPin}
            title="Enter your ward code to get started"
            description="You'll find it on your municipal ID or property tax slip."
          />
        </Card>
      )}

      {/* AC2: ward code doesn't exist */}
      {searched && result && !result.found && (
        <Card>
          <Empty
            icon={AlertCircle}
            title="Ward code not found"
            description={`No ward matches "${code.trim()}". Double-check the code and try again.`}
          />
        </Card>
      )}

      {/* AC4: ward exists, but no schedule has been published yet */}
      {searched && result?.found && !result.published && (
        <Card>
          <Empty
            icon={AlertCircle}
            title="No schedule published yet for this ward"
            description={`${result.ward.name} (${result.ward.code}) hasn't had a collection schedule configured yet. Check back soon.`}
          />
        </Card>
      )}

      {/* AC1: happy path — morning/evening windows labeled by waste type */}
      {searched && result?.found && result.published && (
        <Card title={`${result.ward.name} (${result.ward.code})`}>
          <div className="space-y-3">
            {result.windows.map((w) => (
              <div key={w.waste_type} className="border border-gray-100 rounded-input p-3">
                <p className="font-medium text-sm mb-2">{w.waste_type}</p>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="flex items-center gap-2">
                    <Sun size={15} className="text-amber-500 shrink-0" />
                    <span className={w.morning ? "text-gray-700" : "text-gray-400"}>
                      {w.morning || "Not scheduled"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Moon size={15} className="text-indigo-500 shrink-0" />
                    <span className={w.evening ? "text-gray-700" : "text-gray-400"}>
                      {w.evening || "Not scheduled"}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
