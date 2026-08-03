import { useMemo, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card, StatusPill, Empty } from "../../../components/UI";
import DonationImages from "../../../components/DonationImages";
import { Package, Search, X } from "lucide-react";
import { listMyDonations, withdrawDonation } from "../../../lib/mockCitizenData";

export default function MyDonations({ onNavigate }) {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [version, setVersion] = useState(0);
  const [withdrawingId, setWithdrawingId] = useState(null);
  const [error, setError] = useState("");
  // version is a deliberate cache-bust counter for listMyDonations after localStorage updates
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const items = useMemo(() => listMyDonations(user.id), [user.id, version]);

  const handleWithdraw = async (id) => {
    if (!window.confirm("Withdraw this listing before it is reviewed?")) return;
    setWithdrawingId(id);
    setError("");
    try {
      await withdrawDonation(id, user.id);
      setVersion((v) => v + 1);
    } catch (e) {
      setError(e?.message || "Could not withdraw this listing.");
    }
    setWithdrawingId(null);
  };

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return items;
    return items.filter((d) =>
      [d.title, d.category, d.status, d.condition]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(query)
    );
  }, [items, search]);

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-bold">My Donations</h1>
        <div className="flex w-full max-w-md gap-3 items-center">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search donations…"
              className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-4 py-2 text-sm text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
            />
          </div>
          <button
            type="button"
            onClick={() => onNavigate("donate")}
            className="bg-primary text-white px-4 py-2 rounded-input text-sm"
          >
            New Donation
          </button>
        </div>
      </div>
      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{error}</div>}
      {filteredItems.length === 0 ? (
        <Card>
          <Empty
            icon={Package}
            title={search ? "No donations found" : "No donations yet"}
            description={search ? "Try a different search term." : "Add a donation to get started"}
          />
        </Card>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredItems.map((d) => (
            <Card key={d.id} className="!p-0 overflow-hidden">
              <DonationImages
                images={d.images}
                alt={d.title}
                thumbClass="w-full h-36 object-cover"
              />
              <div className="p-4 space-y-2">
                <h3 className="font-medium">{d.title}</h3>
                <p className="text-xs text-gray-500">
                  {d.category} · {d.condition?.replace(/_/g, " ")}
                </p>
                <StatusPill status={d.status} />
                <p className="text-xs text-gray-400">
                  {new Date(d.created_at).toLocaleDateString()}
                </p>
                {d.rejection_reason && <p className="text-xs text-red-600">{d.rejection_reason}</p>}
                {d.status === "PENDING_APPROVAL" && (
                  <button
                    type="button"
                    onClick={() => handleWithdraw(d.id)}
                    disabled={withdrawingId === d.id}
                    className="w-full flex items-center justify-center gap-1.5 border border-red-200 text-red-600 rounded-input py-1.5 text-xs font-medium hover:bg-red-50 disabled:opacity-50"
                  >
                    <X size={13} /> {withdrawingId === d.id ? "Withdrawing…" : "Withdraw Listing"}
                  </button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
