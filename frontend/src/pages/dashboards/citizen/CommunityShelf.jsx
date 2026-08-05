import { useState } from "react";
import ShelfList from "./ShelfList";
import MyDonations from "./MyDonations";
import MyClaims from "./MyClaims";
import CreateDonation from "./CreateDonation";

export default function CommunityShelf() {
  const [subTab, setSubTab] = useState("shelf"); // "shelf", "donations", "claims", or "donate"

  return (
    <div className="space-y-6 fade-in">
      <div className="flex justify-between items-center flex-wrap gap-2">
        <h1 className="text-xl font-bold">Community Shelf</h1>
        <div className="flex gap-2 bg-gray-100 p-0.5 rounded-input">
          <button
            type="button"
            onClick={() => setSubTab("shelf")}
            className={`px-4 py-1.5 rounded-input text-xs font-semibold ${
              subTab === "shelf" ? "bg-white shadow-soft text-[#3F5426]" : "text-gray-500"
            }`}
          >
            Browse Shelf
          </button>
          <button
            type="button"
            onClick={() => setSubTab("donations")}
            className={`px-4 py-1.5 rounded-input text-xs font-semibold ${
              subTab === "donations" || subTab === "donate"
                ? "bg-white shadow-soft text-[#3F5426]"
                : "text-gray-500"
            }`}
          >
            My Donations
          </button>
          <button
            type="button"
            onClick={() => setSubTab("claims")}
            className={`px-4 py-1.5 rounded-input text-xs font-semibold ${
              subTab === "claims" ? "bg-white shadow-soft text-[#3F5426]" : "text-gray-500"
            }`}
          >
            My Claims
          </button>
        </div>
      </div>

      {subTab === "shelf" && <ShelfList onNavigate={(dest) => setSubTab(dest)} />}
      {subTab === "donations" && <MyDonations onNavigate={(dest) => setSubTab(dest)} />}
      {subTab === "donate" && <CreateDonation onNavigate={(dest) => setSubTab(dest)} />}
      {subTab === "claims" && <MyClaims />}
    </div>
  );
}
