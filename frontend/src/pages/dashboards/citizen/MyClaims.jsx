import { useMemo, useState, useEffect, useCallback } from "react";
import { Card, StatusPill, Empty, Modal } from "../../../components/UI";
import DonationImages from "../../../components/DonationImages";
import ImageLightbox from "../../../components/ImageLightBox";
import { Gift, Search } from "lucide-react";
import { listMyClaims } from "../../../lib/api";

const FILTERS = [
  { value: "", label: "All" },
  { value: "CLAIM_REQUESTED", label: "Pending" },
  { value: "COMPLETED", label: "Approved" },
];
export default function MyClaims() {
  const [filter, setFilter] = useState("");
  const [search, setSearch] = useState("");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Detail Modal States
  const [selected, setSelected] = useState(null);
  const [viewingImages, setViewingImages] = useState(null);

  const fetchClaims = useCallback(async () => {
    try {
      const data = await listMyClaims(filter);
      setItems(data);
    } catch {
      setError("Failed to load claims.");
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchClaims();
  }, [fetchClaims]);

  const stats = useMemo(
    () => ({
      total: items.length,
      pending: items.filter((i) => i.status === "PENDING").length,
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
    if (d.status === "PENDING") return "Pending Approval";
    if (d.status === "APPROVED") return "Approved";
    return d.status?.replace(/_/g, " ");
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-bold text-[#1C2312]">My Claims</h1>
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

      <div className="grid grid-cols-2 gap-3 max-w-sm">
        <Card className="!p-3 text-center">
          <p className="text-xl font-bold">{stats.total}</p>
          <p className="text-xs text-gray-500">Total Claimed</p>
        </Card>
        <Card className="!p-3 text-center">
          <p className="text-xl font-bold text-[#A16207]">{stats.pending}</p>
          <p className="text-xs text-gray-500">Pending</p>
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

      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{error}</div>}

      {loading ? (
        <div className="text-center py-10 text-gray-500 text-sm">Loading claims…</div>
      ) : filteredItems.length === 0 ? (
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
            <div
              key={d.id}
              className="bg-white rounded-card shadow-soft overflow-hidden cursor-pointer hover:shadow-md transition-all hover:-translate-y-0.5 border border-gray-250 flex flex-col"
              onClick={() => setSelected(d)}
            >
              <DonationImages
                images={d.images}
                alt={d.title}
                thumbClass="w-full h-40 object-cover"
              />
              <div className="p-4 space-y-2 flex-1">
                <div className="flex justify-between items-start gap-2">
                  <h3 className="font-medium text-sm text-[#1C2312] line-clamp-1">{d.title}</h3>
                  <StatusPill status={d.status} />
                </div>
                <p className="text-xs text-gray-500">Donor: {d.donor_name}</p>
                <p className="text-xs text-gray-400">
                  Claimed: {new Date(d.updated_at).toLocaleDateString()}
                </p>
                <p className="text-xs">
                  <span className="text-gray-500">Status:</span> {statusLabel(d)}
                </p>
                {d.status === "APPROVED" && (
                  <div className="bg-green-50 text-green-855 text-[11px] rounded-input p-2 font-medium">
                    Pickup: Contact donor at {d.donor_phone || d.donor_email}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Claims Detail Modal */}
      {selected && (
        <Modal open={!!selected} onClose={() => setSelected(null)} title="Claim Details">
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="font-semibold text-sm text-[#1C2312]">{selected.title}</h3>
              <StatusPill status={selected.status} />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-gray-500">Donor Name:</span>
                <p className="font-semibold text-sm">{selected.donor_name}</p>
              </div>
              <div>
                <span className="text-gray-500">Claim Requested:</span>
                <p className="font-semibold">{new Date(selected.created_at).toLocaleString()}</p>
              </div>
              <div>
                <span className="text-gray-500">Last Updated:</span>
                <p className="font-semibold">{new Date(selected.updated_at).toLocaleString()}</p>
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

            {/* If claim is approved/completed, show contact & pickup address details */}
            {selected.status === "COMPLETED" && (
              <div className="bg-green-50/50 border border-green-100 rounded-input p-3 space-y-2">
                <span className="text-xs font-semibold text-green-700">
                  Donor Pickup Instructions
                </span>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-gray-500">Donor Phone:</span>
                    <p className="font-semibold">{selected.donor_phone || "Not specified"}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Donor Email:</span>
                    <p className="font-semibold">{selected.donor_email || "Not specified"}</p>
                  </div>
                  {selected.address && (
                    <div className="col-span-2">
                      <span className="text-gray-500">Pickup Address:</span>
                      <p className="font-semibold text-[#1C2312]">{selected.address}</p>
                    </div>
                  )}
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

            {selected.note && selected.status === "REJECTED" && (
              <div className="bg-red-50 border border-red-100 rounded-input p-3 text-xs text-red-800">
                <span className="font-semibold block mb-0.5">Manager Rejection Note:</span>
                <p>{selected.note}</p>
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
