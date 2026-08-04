import { useEffect, useState, useCallback } from "react";
import { Modal, StatusPill } from "../../../components/UI";
import ImageLightbox from "../../../components/ImageLightBox";
import {
  getManagerPendingDonations,
  getManagerPendingClaims,
  getManagerAllDonations,
  reviewManagerDonation,
  reviewManagerClaim,
} from "../../../lib/api";
import { Section, PaginatedTable } from "./shared";

export default function Donations() {
  const [activeSubTab, setActiveSubTab] = useState("items"); // 'items', 'claims', or 'all'
  const [pendingDonations, setPendingDonations] = useState([]);
  const [pendingClaims, setPendingClaims] = useState([]);
  const [allDonations, setAllDonations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [successMsg, setSuccessMsg] = useState("");

  // Modals / Detail Views
  const [selectedDonation, setSelectedDonation] = useState(null);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [viewingImages, setViewingImages] = useState(null);

  // Reject States
  const [rejectionNote, setRejectionNote] = useState("");
  const [rejecting, setRejecting] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [donations, claims, all] = await Promise.all([
        getManagerPendingDonations(),
        getManagerPendingClaims(),
        getManagerAllDonations(),
      ]);
      setPendingDonations(donations);
      setPendingClaims(claims);
      setAllDonations(all);
    } catch {
      setError("Failed to load reuse data from server.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleApproveDonation = async (listingId) => {
    if (!window.confirm("Approve this item to go live on the Community Shelf?")) return;
    setError("");
    setSuccessMsg("");
    try {
      await reviewManagerDonation(listingId, { status: "AVAILABLE" });
      setSuccessMsg("Donation listing approved successfully!");
      setSelectedDonation(null);
      loadData();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to approve listing.");
    }
  };

  const handleRejectDonation = async (listingId) => {
    const reason = rejectionNote.trim();
    if (!reason) {
      alert("A rejection reason is required.");
      return;
    }
    setError("");
    setSuccessMsg("");
    try {
      await reviewManagerDonation(listingId, { status: "REJECTED", rejection_reason: reason });
      setSuccessMsg("Donation listing rejected.");
      setRejectionNote("");
      setRejecting(false);
      setSelectedDonation(null);
      loadData();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to reject listing.");
    }
  };

  const handleApproveClaim = async (claimId) => {
    if (!window.confirm("Approve this claim? This will mark the item as completed.")) return;
    setError("");
    setSuccessMsg("");
    try {
      await reviewManagerClaim(claimId, { status: "APPROVED" });
      setSuccessMsg("Claim request approved!");
      setSelectedClaim(null);
      loadData();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to approve claim.");
    }
  };

  const handleRejectClaim = async (claimId) => {
    const reason = rejectionNote.trim();
    if (!reason) {
      alert("A rejection note is required.");
      return;
    }
    setError("");
    setSuccessMsg("");
    try {
      await reviewManagerClaim(claimId, { status: "REJECTED", note: reason });
      setSuccessMsg("Claim request rejected.");
      setRejectionNote("");
      setRejecting(false);
      setSelectedClaim(null);
      loadData();
    } catch (e) {
      setError(e.response?.data?.detail || "Failed to reject claim.");
    }
  };

  // Define table structures
  const donationColumns = [
    { key: "title", label: "Item Title" },
    { key: "category", label: "Category" },
    { key: "condition", label: "Condition" },
    { key: "donor_name", label: "Donor" },
    { key: "created_at", label: "Submitted At", render: (val) => new Date(val).toLocaleString() },
  ];

  const claimColumns = [
    { key: "title", label: "Item Title" },
    { key: "claimant_name", label: "Claimant" },
    {
      key: "created_at",
      label: "Claim Requested At",
      render: (val) => new Date(val).toLocaleString(),
    },
  ];

  const allDonationColumns = [
    { key: "title", label: "Item Title" },
    { key: "category", label: "Category" },
    { key: "condition", label: "Condition" },
    { key: "donor_name", label: "Donor" },
    { key: "status", label: "Status", render: (val) => <StatusPill status={val} /> },
    { key: "created_at", label: "Submitted At", render: (val) => new Date(val).toLocaleString() },
  ];

  return (
    <div className="space-y-6 fade-in">
      <div className="flex justify-between items-center flex-wrap gap-2">
        <h1 className="text-xl font-bold">Community Shelf Moderation</h1>
        <div className="flex gap-2 bg-gray-100 p-0.5 rounded-input">
          <button
            type="button"
            onClick={() => {
              setActiveSubTab("items");
              setError("");
              setSuccessMsg("");
            }}
            className={`px-4 py-1.5 rounded-input text-xs font-semibold ${
              activeSubTab === "items" ? "bg-white shadow-soft text-[#3F5426]" : "text-gray-500"
            }`}
          >
            Pending Items ({pendingDonations.length})
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveSubTab("claims");
              setError("");
              setSuccessMsg("");
            }}
            className={`px-4 py-1.5 rounded-input text-xs font-semibold ${
              activeSubTab === "claims" ? "bg-white shadow-soft text-[#3F5426]" : "text-gray-500"
            }`}
          >
            Pending Claims ({pendingClaims.length})
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveSubTab("all");
              setError("");
              setSuccessMsg("");
            }}
            className={`px-4 py-1.5 rounded-input text-xs font-semibold ${
              activeSubTab === "all" ? "bg-white shadow-soft text-[#3F5426]" : "text-gray-500"
            }`}
          >
            All Donations ({allDonations.length})
          </button>
        </div>
      </div>

      {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{error}</div>}
      {successMsg && (
        <div className="bg-green-50 text-green-700 text-sm p-3 rounded-input">{successMsg}</div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-500 text-sm">Loading requests…</div>
      ) : activeSubTab === "items" ? (
        <Section title="Donations Awaiting Review" eyebrow="Civic Exchange">
          <PaginatedTable
            columns={donationColumns}
            rows={pendingDonations}
            onRowClick={(row) => {
              setSelectedDonation(row);
              setRejecting(false);
              setRejectionNote("");
            }}
            emptyMessage="No pending donations in your supervised wards."
          />
        </Section>
      ) : activeSubTab === "claims" ? (
        <Section title="Claims Awaiting Review" eyebrow="Civic Exchange">
          <PaginatedTable
            columns={claimColumns}
            rows={pendingClaims}
            onRowClick={(row) => {
              setSelectedClaim(row);
              setRejecting(false);
              setRejectionNote("");
            }}
            emptyMessage="No pending claims in your supervised wards."
          />
        </Section>
      ) : (
        <Section title="All Donation Records" eyebrow="Civic Exchange">
          <PaginatedTable
            columns={allDonationColumns}
            rows={allDonations}
            onRowClick={(row) => {
              setSelectedDonation(row);
              setRejecting(false);
              setRejectionNote("");
            }}
            emptyMessage="No donation records found in your supervised wards."
          />
        </Section>
      )}

      {/* Donation Detail Modal (Pending Review / History) */}
      {selectedDonation && (
        <Modal
          open={!!selectedDonation}
          onClose={() => setSelectedDonation(null)}
          title={
            selectedDonation.status === "PENDING_APPROVAL"
              ? "Review Donation Listing"
              : "Donation Details"
          }
        >
          <div className="space-y-4">
            <div className="flex justify-between items-center border-b pb-2">
              <h3 className="font-semibold text-[#1C2312]">{selectedDonation.title}</h3>
              <StatusPill status={selectedDonation.status} />
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-gray-500">Category:</span>
                <p className="font-semibold text-sm">{selectedDonation.category}</p>
              </div>
              <div>
                <span className="text-gray-500">Condition:</span>
                <p className="font-semibold text-sm">
                  {selectedDonation.condition?.replace(/_/g, " ")}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Donor Name:</span>
                <p className="font-semibold text-sm">{selectedDonation.donor_name}</p>
              </div>
              <div>
                <span className="text-gray-500">Submitted:</span>
                <p className="font-semibold">
                  {new Date(selectedDonation.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <span className="text-gray-500">Donor Phone:</span>
                <p className="font-semibold">{selectedDonation.donor_phone || "Not specified"}</p>
              </div>
              <div>
                <span className="text-gray-500">Donor Email:</span>
                <p className="font-semibold">{selectedDonation.donor_email || "Not specified"}</p>
              </div>
            </div>

            {selectedDonation.description && (
              <div>
                <span className="text-xs text-gray-500">Description:</span>
                <p className="text-sm bg-gray-50 p-2.5 rounded border border-gray-100 whitespace-pre-wrap">
                  {selectedDonation.description}
                </p>
              </div>
            )}

            {selectedDonation.address && (
              <div>
                <span className="text-xs text-gray-500">Address / Pickup Location:</span>
                <p className="text-xs text-gray-700 font-medium">{selectedDonation.address}</p>
              </div>
            )}

            {/* Claimant details if item is claimed/completed */}
            {selectedDonation.claimant_id && (
              <div className="bg-amber-50/50 border border-amber-100 rounded-input p-3 space-y-2">
                <span className="text-xs font-semibold text-[#A16207]">Claimant Information</span>
                <div className="grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-gray-500">Claimant Name:</span>
                    <p className="font-semibold">{selectedDonation.claimant_name}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Claimant Email:</span>
                    <p className="font-semibold">{selectedDonation.claimant_email || "N/A"}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Claimant Phone:</span>
                    <p className="font-semibold">{selectedDonation.claimant_phone || "N/A"}</p>
                  </div>
                </div>
              </div>
            )}

            <div>
              <span className="text-xs text-gray-500 block mb-1">Item Photos:</span>
              <div className="flex gap-2 overflow-x-auto py-1">
                {selectedDonation.images?.length > 0 ? (
                  selectedDonation.images.map((img, i) => (
                    <img
                      key={i}
                      src={img}
                      alt=""
                      onClick={() => setViewingImages(selectedDonation.images)}
                      className="w-20 h-20 object-cover rounded cursor-pointer border border-gray-200 hover:border-primary"
                    />
                  ))
                ) : (
                  <p className="text-xs text-gray-400">No images uploaded.</p>
                )}
              </div>
            </div>

            {selectedDonation.rejection_reason && (
              <div className="bg-red-50 border border-red-100 rounded-input p-3 text-xs text-red-800">
                <span className="font-semibold block mb-0.5">Rejection Reason:</span>
                <p>{selectedDonation.rejection_reason}</p>
              </div>
            )}

            {selectedDonation.status === "PENDING_APPROVAL" && (
              <>
                {rejecting ? (
                  <div className="space-y-2 border-t pt-3">
                    <label className="block text-xs font-semibold text-red-700">
                      Rejection Reason *
                    </label>
                    <textarea
                      value={rejectionNote}
                      onChange={(e) => setRejectionNote(e.target.value)}
                      placeholder="Explain why this listing is rejected (e.g. poor photo quality, inappropriate item)…"
                      rows={3}
                      className="w-full text-xs border rounded p-2 focus:ring-1 focus:ring-red-500 focus:outline-none"
                    />
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => setRejecting(false)}
                        className="border px-3 py-1.5 rounded-input text-xs font-medium"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => handleRejectDonation(selectedDonation.id)}
                        className="bg-red-600 text-white px-3 py-1.5 rounded-input text-xs font-medium hover:bg-red-700"
                      >
                        Confirm Rejection
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex gap-2 justify-end border-t pt-3">
                    <button
                      type="button"
                      onClick={() => setRejecting(true)}
                      className="border border-red-200 text-red-600 px-4 py-2 rounded-input text-xs font-semibold hover:bg-red-50"
                    >
                      Reject Listing
                    </button>
                    <button
                      type="button"
                      onClick={() => handleApproveDonation(selectedDonation.id)}
                      className="bg-primary text-white px-4 py-2 rounded-input text-xs font-semibold"
                    >
                      Approve & Go Live
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        </Modal>
      )}

      {/* Claim Detail Modal */}
      {selectedClaim && (
        <Modal
          open={!!selectedClaim}
          onClose={() => setSelectedClaim(null)}
          title="Review Claim Request"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span className="text-gray-500">Item Title:</span>
                <p className="font-semibold text-sm">{selectedClaim.title}</p>
              </div>
              <div>
                <span className="text-gray-500">Claimant Name:</span>
                <p className="font-semibold text-sm">{selectedClaim.claimant_name}</p>
              </div>
              <div>
                <span className="text-gray-500">Requested:</span>
                <p className="font-semibold">
                  {new Date(selectedClaim.created_at).toLocaleString()}
                </p>
              </div>
            </div>

            {rejecting ? (
              <div className="space-y-2 border-t pt-3">
                <label className="block text-xs font-semibold text-red-700">Rejection Note *</label>
                <textarea
                  value={rejectionNote}
                  onChange={(e) => setRejectionNote(e.target.value)}
                  placeholder="Explain why this claim request is rejected…"
                  rows={3}
                  className="w-full text-xs border rounded p-2 focus:ring-1 focus:ring-red-500 focus:outline-none"
                />
                <div className="flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => setRejecting(false)}
                    className="border px-3 py-1.5 rounded-input text-xs font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRejectClaim(selectedClaim.id)}
                    className="bg-red-600 text-white px-3 py-1.5 rounded-input text-xs font-medium hover:bg-red-700"
                  >
                    Confirm Rejection
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex gap-2 justify-end border-t pt-3">
                <button
                  type="button"
                  onClick={() => setRejecting(true)}
                  className="border border-red-200 text-red-600 px-4 py-2 rounded-input text-xs font-semibold hover:bg-red-50"
                >
                  Reject Claim
                </button>
                <button
                  type="button"
                  onClick={() => handleApproveClaim(selectedClaim.id)}
                  className="bg-primary text-white px-4 py-2 rounded-input text-xs font-semibold"
                >
                  Approve Claim
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
