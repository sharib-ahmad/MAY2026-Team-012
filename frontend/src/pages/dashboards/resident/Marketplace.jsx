import { useMemo, useState } from "react";
import { useAuth } from "../../../context/AuthContext";
import { Card, Empty } from "../../../components/UI";
import DonationImages from "../../../components/DonationImages";
import ImageLightbox from "../../../components/ImageLightBox";
import { Gift } from "lucide-react";
import { listMarketplace, claimDonation } from "../../../lib/mockResidentData";

const CATEGORIES = [
  "BOOKS",
  "FURNITURE",
  "ELECTRONICS",
  "CLOTHES",
  "TOYS",
  "KITCHEN",
  "BICYCLE",
  "BAGS",
  "OTHER",
];

export default function Marketplace({ onNavigate }) {
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [version, setVersion] = useState(0);
  const [msg, setMsg] = useState("");
  const [viewing, setViewing] = useState(null); // donation whose photos are open in the lightbox

  const items = useMemo(
    () => listMarketplace(user.id, { search, category, version }),
    [user.id, search, category, version]
  );

  const claim = (id) => {
    if (!window.confirm("Request to claim this item?")) return;
    claimDonation(id, user);
    setMsg("Claim requested — check My Claims for updates.");
    setVersion((v) => v + 1);
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex justify-between items-center flex-wrap gap-2">
        <h1 className="text-xl font-bold">Donation Marketplace</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => onNavigate("claims")}
            className="border border-gray-200 px-4 py-2 rounded-input text-sm"
          >
            My Claims
          </button>
          <button
            type="button"
            onClick={() => onNavigate("donate")}
            className="bg-primary text-white px-4 py-2 rounded-input text-sm"
          >
            Donate Item
          </button>
        </div>
      </div>
      {msg && <div className="bg-green-50 text-green-700 text-sm p-3 rounded-input">{msg}</div>}
      <div className="flex gap-2 flex-wrap">
        <input
          placeholder="Search…"
          className="border border-gray-200 rounded-input px-3 py-2 text-sm flex-1 min-w-[140px]"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          className="border border-gray-200 rounded-input px-3 py-2 text-sm"
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
      {items.length === 0 ? (
        <Empty icon={Gift} title="No items" description="Check back later for donated products" />
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {items.map((d) => (
            <Card key={d.id} className="!p-0 overflow-hidden">
              <DonationImages
                images={d.images}
                alt={d.title}
                thumbClass="w-full h-40 object-cover"
                onClick={() => setViewing(d)}
              />
              <div className="p-4 space-y-2">
                <h3 className="font-medium">{d.title}</h3>
                <p className="text-xs text-gray-500">
                  {d.category} · {d.condition?.replace(/_/g, " ")}
                </p>
                <p className="text-sm text-gray-600 line-clamp-2">{d.description}</p>
                <p className="text-xs text-gray-400">{d.address || "Location on file"}</p>
                <button
                  type="button"
                  onClick={() => claim(d.id)}
                  className="w-full bg-primary text-white py-2 rounded-input text-sm"
                >
                  Claim
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <ImageLightbox
        open={!!viewing}
        onClose={() => setViewing(null)}
        images={viewing?.images || []}
        title={viewing?.title}
      />
    </div>
  );
}
