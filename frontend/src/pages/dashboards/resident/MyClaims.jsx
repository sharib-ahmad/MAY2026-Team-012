import { useMemo, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card, StatusPill, Empty } from "../../../components/UI";
import DonationImages from "../../../components/DonationImages";
import { Gift, Search } from "lucide-react";
import { listMyClaims } from "../../../lib/mockResidentData";

const FILTERS = [
  { value: "", label: "All" },
  { value: "CLAIM_REQUESTED", label: "Pending" },
  { value: "COMPLETED", label: "Approved" },
];

export default function MyClaims() {
  const { user } = useAuth();
  const [filter, setFilter] = useState("");
  const [search, setSearch] = useState("");

  const items = useMemo(() => listMyClaims(user.id, filter), [user.id, filter]);

  const stats = useMemo(
    () => ({
      total: items.length,
      pending: items.filter((i) => i.status === "CLAIM_REQUESTED").length,
      approved: items.filter((i) => i.status === "COMPLETED").length,
      completed: items.filter((i) => i.status === "COMPLETED").length,
    }),
    [items]
  );

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((d) =>
      [d.title, d.donor_name, d.status, d.address]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [items, search]);

  const statusLabel = (d) => {
    if (d.status === "CLAIM_REQUESTED") return "Pending";
    if (d.status === "COMPLETED") return "Approved";
    return d.status?.replace(/_/g, " ");
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-bold">My Claims</h1>
        <div className="relative max-w-sm w-full sm:w-72">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search claims…"
            className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-4 py-2 text-sm text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Card className="!p-3 text-center">
          <p className="text-xl font-bold">{stats.total}</p>
          <p className="text-xs text-gray-500">Total Claimed</p>
        </Card>
        <Card className="!p-3 text-center">
          <p className="text-xl font-bold text-warn">{stats.pending}</p>
          <p className="text-xs text-gray-500">Pending</p>
        </Card>
        <Card className="!p-3 text-center">
          <p className="text-xl font-bold text-success">{stats.approved}</p>
          <p className="text-xs text-gray-500">Approved</p>
        </Card>
        <Card className="!p-3 text-center">
          <p className="text-xl font-bold">{stats.completed}</p>
          <p className="text-xs text-gray-500">Completed</p>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2">
        {FILTERS.map((f) => (
          <button
            key={f.value}
            type="button"
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1.5 rounded-input text-xs font-medium ${
              filter === f.value ? "bg-primary text-white" : "bg-gray-100"
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {filteredItems.length === 0 ? (
        <Empty
          icon={Gift}
          title={search ? "No claims found" : "No claims yet"}
          description={
            search
              ? "Try another search term."
              : "Browse the Community Shelf to claim donated products"
          }
        />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((d) => (
            <Card key={d.id} className="!p-0 overflow-hidden">
              <DonationImages
                images={d.images}
                alt={d.title}
                thumbClass="w-full h-40 object-cover"
              />
              <div className="p-4 space-y-2">
                <div className="flex justify-between items-start gap-2">
                  <h3 className="font-medium">{d.title}</h3>
                  <StatusPill status={d.status} />
                </div>
                <p className="text-xs text-gray-500">Donor: {d.donor_name}</p>
                <p className="text-xs text-gray-400">
                  Claimed: {new Date(d.updated_at).toLocaleDateString()}
                </p>
                <p className="text-xs">
                  <span className="text-gray-500">Status:</span> {statusLabel(d)}
                </p>
                {d.status === "COMPLETED" && (
                  <div className="bg-green-50 text-green-800 text-xs rounded-input p-2">
                    Pickup: contact donor at{" "}
                    {d.donor_phone || d.donor_email || "via community shelf"}
                    <br />
                    Address: {d.address || "See donor details"}
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
