import { useMemo, useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { Card, StatusPill, Empty, Table, Modal } from '../../../components/UI';
import { MapPin, Search, CheckCircle2, Clock, XCircle, AlertTriangle } from 'lucide-react';
import { listMyPickups, getPickupTracking, cancelPickup } from '../../../lib/mockResidentData';

const TRACKABLE = new Set(['ASSIGNED', 'IN_PROGRESS', 'SCHEDULED', 'REQUESTED']);
// Once a collector is on the way (or the job is done/already cancelled), it's too late to cancel.
const CANCELLABLE = new Set(['REQUESTED', 'SCHEDULED', 'ASSIGNED']);

export default function MyPickups() {
  const { user } = useAuth();
  const [selected, setSelected] = useState(null);
  const [showTracking, setShowTracking] = useState(false);
  const [confirmingCancel, setConfirmingCancel] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [cancelError, setCancelError] = useState(null);
  const [search, setSearch] = useState('');

  const initialPickups = useMemo(() => listMyPickups(user.id), [user.id]);
  const [pickups, setPickups] = useState(initialPickups);

  const tracking = useMemo(
    () => (selected && showTracking ? getPickupTracking(selected) : null),
    [selected, showTracking]
  );

  const filteredPickups = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return pickups;
    return pickups.filter((p) =>
      [p.ref_code, p.category, p.collector_name, p.status, p.notes]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
        .includes(query)
    );
  }, [pickups, search]);

  const cols = [
    { key: 'ref_code', label: 'Ref' },
    { key: 'category', label: 'Category' },
    { key: 'scheduled_date', label: 'Date', render: (v) => v && new Date(v).toLocaleDateString() },
    { key: 'collector_name', label: 'Collector', render: (v) => v || '—' },
    { key: 'status', label: 'Status', render: (v) => <StatusPill status={v} /> },
    {
      key: 'notes',
      label: 'Notes',
      render: (v) => (v ? (v.length > 30 ? `${v.slice(0, 30)}…` : v) : '—'),
    },
  ];

  const openPickup = (p) => {
    setSelected(p);
    setShowTracking(false);
    setConfirmingCancel(false);
    setCancelError(null);
  };

  const closeModal = () => {
    setSelected(null);
    setConfirmingCancel(false);
    setCancelError(null);
  };

  const handleConfirmCancel = async () => {
    if (!selected) return;
    setCancelling(true);
    setCancelError(null);
    try {
      const updated = await cancelPickup(selected.id);
      const nextStatus = updated?.status || 'CANCELLED';
      setPickups((prev) =>
        prev.map((p) => (p.id === selected.id ? { ...p, status: nextStatus } : p))
      );
      setSelected((prev) => (prev ? { ...prev, status: nextStatus } : prev));
      setConfirmingCancel(false);
    } catch (err) {
      setCancelError(err?.message || 'Could not cancel this pickup. Please try again.');
    } finally {
      setCancelling(false);
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-xl font-bold">My Pickups</h1>
        <div className="relative max-w-sm w-full sm:w-auto">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search pickups…"
            className="w-full rounded-full border border-gray-200 bg-white pl-10 pr-4 py-2 text-sm text-gray-700 shadow-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          />
        </div>
      </div>
      <Card>
        {filteredPickups.length === 0 ? (
          <Empty
            icon={Search}
            title={search ? 'No pickups found' : 'No pickups'}
            description={search ? 'Try a different search term.' : 'Schedule your first pickup'}
          />
        ) : (
          <Table columns={cols} rows={filteredPickups} onRowClick={openPickup} />
        )}
      </Card>

      <Modal open={!!selected} onClose={closeModal} title={`Pickup ${selected?.ref_code}`}>
        {selected && !showTracking && (
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-2">
              <div>
                <span className="text-gray-400">Category:</span> {selected.category}
              </div>
              <div>
                <span className="text-gray-400">Status:</span> <StatusPill status={selected.status} />
              </div>
              <div>
                <span className="text-gray-400">Zone:</span> {selected.zone_name || '—'}
              </div>
              <div>
                <span className="text-gray-400">Date:</span>{' '}
                {selected.scheduled_date && new Date(selected.scheduled_date).toLocaleDateString()}
              </div>
              <div>
                <span className="text-gray-400">Time Slot:</span> {selected.time_slot || '—'}
              </div>
              <div>
                <span className="text-gray-400">Est. Weight:</span>{' '}
                {selected.estimated_weight?.toFixed(1) || '—'} kg
              </div>
            </div>
            {selected.notes && (
              <div>
                <p className="text-xs font-medium text-gray-600 mb-1">Your Notes</p>
                <div className="bg-gray-50 rounded-input p-3">{selected.notes}</div>
              </div>
            )}
            {selected.collector_name ? (
              <div className="bg-primary/5 rounded-input p-3">
                <p className="text-xs font-medium text-gray-600 mb-1">Assigned Collector</p>
                <p className="font-medium">{selected.collector_name}</p>
                {selected.collector_phone && <p className="text-gray-500">{selected.collector_phone}</p>}
                <p className="text-xs text-gray-400 mt-1">
                  Assignment status: {selected.status.replace(/_/g, ' ')}
                </p>
              </div>
            ) : (
              <p className="text-gray-400 text-xs">No collector assigned yet.</p>
            )}

            {TRACKABLE.has(selected.status) && !confirmingCancel && (
              <button
                type="button"
                onClick={() => setShowTracking(true)}
                className="block w-full text-center bg-primary text-white rounded-input py-2.5 text-sm font-medium hover:bg-primary/90 flex items-center justify-center gap-2"
              >
                <MapPin size={16} /> Track Live Pickup
              </button>
            )}

            {selected.status === 'CANCELLED' && (
              <div className="flex items-center gap-2 text-gray-400 text-xs bg-gray-50 rounded-input p-3">
                <XCircle size={14} /> This pickup was cancelled.
              </div>
            )}

            {CANCELLABLE.has(selected.status) && !confirmingCancel && (
              <button
                type="button"
                onClick={() => setConfirmingCancel(true)}
                className="block w-full text-center border border-red-200 text-red-600 rounded-input py-2.5 text-sm font-medium hover:bg-red-50 flex items-center justify-center gap-2"
              >
                <XCircle size={16} /> Cancel Pickup
              </button>
            )}

            {confirmingCancel && (
              <div className="border border-red-200 bg-red-50 rounded-input p-3 space-y-3">
                <div className="flex gap-2 text-red-700">
                  <AlertTriangle size={16} className="shrink-0 mt-0.5" />
                  <p className="text-sm">
                    Cancel pickup <span className="font-medium">{selected.ref_code}</span>? This can't be
                    undone, and you'll need to schedule a new pickup if you change your mind.
                  </p>
                </div>
                {cancelError && <p className="text-xs text-red-600">{cancelError}</p>}
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleConfirmCancel}
                    disabled={cancelling}
                    className="flex-1 bg-red-600 hover:bg-red-700 disabled:opacity-60 text-white rounded-input py-2 text-sm font-medium"
                  >
                    {cancelling ? 'Cancelling…' : 'Yes, cancel it'}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setConfirmingCancel(false);
                      setCancelError(null);
                    }}
                    disabled={cancelling}
                    className="flex-1 bg-white border border-gray-200 hover:bg-gray-50 disabled:opacity-60 text-gray-700 rounded-input py-2 text-sm font-medium"
                  >
                    Keep pickup
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {selected && showTracking && tracking && (
          <div className="space-y-4 text-sm">
            <p className="text-xs text-gray-400">
              Live status for <span className="font-medium text-gray-600">{tracking.ref_code}</span> only.
            </p>
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center bg-gray-50 rounded-input p-3">
                <p className="text-xl font-bold">{tracking.stops_remaining}</p>
                <p className="text-xs text-gray-500">Stages Left</p>
              </div>
              <div className="text-center bg-gray-50 rounded-input p-3">
                <p className="text-lg font-bold">{tracking.estimated_arrival || 'Done'}</p>
                <p className="text-xs text-gray-500">Est. Arrival</p>
              </div>
              <div className="text-center bg-gray-50 rounded-input p-3">
                <StatusPill status={tracking.status} />
                <p className="text-xs text-gray-500 mt-1">Status</p>
              </div>
            </div>
            <div>
              <p className="text-xs font-medium text-gray-600 mb-2">Progress for this pickup</p>
              <div className="space-y-3">
                {tracking.timeline.map((evt, i) => (
                  <div key={evt.stage} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center ${
                          i === tracking.timeline.length - 1 ? 'bg-primary text-white' : 'bg-success text-white'
                        }`}
                      >
                        {i === tracking.timeline.length - 1 && tracking.status !== 'COLLECTED' ? (
                          <Clock size={12} />
                        ) : (
                          <CheckCircle2 size={12} />
                        )}
                      </div>
                      {i < tracking.timeline.length - 1 && <div className="w-0.5 flex-1 bg-gray-200 my-0.5" />}
                    </div>
                    <div className="pb-2">
                      <p className="font-medium text-sm">{evt.label}</p>
                      <p className="text-xs text-gray-400">{evt.at.toLocaleString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowTracking(false)}
              className="text-xs text-primary font-medium"
            >
              ← Back to details
            </button>
          </div>
        )}
      </Modal>
    </div>
  );
}