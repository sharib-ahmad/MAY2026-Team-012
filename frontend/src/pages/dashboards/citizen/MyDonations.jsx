import { useMemo, useState, useEffect, useCallback } from "react";
import { Card, StatusPill, Empty, Modal } from "../../../components/UI";
import DonationImages from "../../../components/DonationImages";
import ImageLightbox from "../../../components/ImageLightBox";
import { Package, Search, X } from "lucide-react";
import { listMyDonations, withdrawDonation } from "../../../lib/api";

export default function MyDonations({ onNavigate }) {
  const [search, setSearch] = useState("");
  const [version, setVersion] = useState(0);
  const [withdrawingId, setWithdrawingId] = useState(null);
  const [error, setError] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  // Detail Modal States
  const [selected, setSelected] = useState(null);
  const [viewingImages, setViewingImages] = useState(null);

  const fetchDonations = useCallback(async () => {
    try {
      const data = await listMyDonations();
      setItems(data);
    } catch {
      setError("Failed to load your donations.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDonations();
  }, [fetchDonations, version]);

  const handleWithdraw = async (id, e) => {
    e?.stopPropagation(); // Prevent opening modal when clicking withdraw button on card
    if (!window.confirm("Withdraw this listing before it is reviewed?")) return;
    setWithdrawingId(id);
    setError("");
    try {
      await withdrawDonation(id);
      setVersion((v) => v + 1);
      setSelected(null); // Close modal if open
    } catch (e) {
      setError(e.response?.data?.detail || "Could not withdraw this listing.");
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
        <h1 className="text-xl font-bold text-[#1C2312]">My Donations</h1>
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
      {loading ? (
        <div className="text-center py-10 text-gray-500 text-sm">Loading your donations…</div>
      ) : filteredItems.length === 0 ? (
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
            <div
              key={d.id}
              className="bg-white rounded-card shadow-soft overflow-hidden cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5 border border-gray-250 flex flex-col"
              onClick={() => setSelected(d)}
            >
              <DonationImages
                images={d.images}
                alt={d.title}
                thumbClass="w-full h-36 object-cover"
              />
              <div className="p-4 space-y-2 flex-1">
                <div className="flex justify-between items-start gap-1">
                  <h3 className="font-medium text-sm text-[#1C2312] line-clamp-1">{d.title}</h3>
                  <StatusPill status={d.status} />
                </div>
                <p className="text-xs text-gray-500">
                  {d.category} · {d.condition?.replace(/_/g, " ")}
                </p>
                <p className="text-xs text-gray-400">
                  {new Date(d.created_at).toLocaleDateString()}
                </p>
                {d.rejection_reason && (
                  <p className="text-xs text-red-600 font-medium line-clamp-1">
                    Reason: {d.rejection_reason}
                  </p>
                )}
                {d.status === "PENDING_APPROVAL" && (
                  <button
                    type="button"
                    onClick={(e) => handleWithdraw(d.id, e)}
                    disabled={withdrawingId === d.id}
                    className="w-full flex items-center justify-center gap-1.5 border border-red-200 text-red-600 rounded-input py-1.5 text-xs font-medium hover:bg-red-50 disabled:opacity-50 mt-1"
                  >
                    <X size={13} /> {withdrawingId === d.id ? "Withdrawing…" : "Withdraw Listing"}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Donation Detail Modal */}
      {selected && (
        <Modal open={!!selected} onClose={() => setSelected(null)} title="Donation Details">
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="font-semibold text-sm text-[#1C2312]">{selected.title}</h3>
              <StatusPill status={selected.status} />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-gray-500">Category:</span>
                <p className="font-semibold text-sm">{selected.category}</p>
              </div>
              <div>
                <span className="text-gray-500">Condition:</span>
                <p className="font-semibold text-sm">{selected.condition?.replace(/_/g, " ")}</p>
              </div>
              <div>
                <span className="text-gray-500">Submitted:</span>
                <p className="font-semibold">{new Date(selected.created_at).toLocaleString()}</p>
              </div>
            </div>

            {selected.description && (
              <div>
                <span className="text-xs text-gray-500">Description:</span>
                <p className="text-sm bg-gray-50 p-2.5 rounded border border-gray-100 whitespace-pre-wrap">
                  {selected.description}
                </p>
              </div>
            )}

            {/* Display claimant details if approved/completed */}
            {selected.claimant_id && (
              <div className="bg-green-50/50 border border-green-100 rounded-input p-3 space-y-2">
                <span className="text-xs font-semibold text-green-700">Claimant Contact Info</span>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-gray-500">Name:</span>
                    <p className="font-semibold">{selected.claimant_name}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Email:</span>
                    <p className="font-semibold">{selected.claimant_email || "N/A"}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Phone:</span>
                    <p className="font-semibold">{selected.claimant_phone || "N/A"}</p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <span className="text-xs text-gray-500 block mb-1">Item Photos:</span>
              <div className="flex gap-2 overflow-x-auto py-1">
                {selected.images?.length > 0 ? (
                  selected.images.map((img, i) => (
                    <img
                      key={i}
                      src={img}
                      alt=""
                      onClick={() => setViewingImages(selected.images)}
                      className="w-20 h-20 object-cover rounded cursor-pointer border border-gray-200 hover:border-primary"
                    />
                  ))
                ) : (
                  <p className="text-xs text-gray-400">No images uploaded.</p>
                )}
              </div>
            </div>

            {selected.rejection_reason && (
              <div className="bg-red-50 border border-red-100 rounded-input p-3 text-xs text-red-800">
                <span className="font-semibold block mb-0.5">Rejection Reason:</span>
                <p>{selected.rejection_reason}</p>
              </div>
            )}

            {selected.status === "PENDING_APPROVAL" && (
              <div className="border-t pt-3 flex justify-end">
                <button
                  type="button"
                  onClick={(e) => handleWithdraw(selected.id, e)}
                  disabled={withdrawingId === selected.id}
                  className="bg-red-600 text-white px-4 py-2 rounded-input text-xs font-semibold hover:bg-red-700"
                >
                  Withdraw Listing
                </button>
              </div>
            )}
          </div>
        </Modal>
      )}

      {/* Photo Lightbox */}
      <ImageLightbox
        open={!!viewingImages}
        onClose={() => setViewingImages(null)}
        images={viewingImages || []}
        title="Donation Photos"
      />
    </div>
  );
}
