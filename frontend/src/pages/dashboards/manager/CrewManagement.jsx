import { useMemo, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { Modal } from "../../../components/UI";
import { deleteManagerWorker, updateManagerWorker } from "../../../lib/api";
import { PaginatedTable, SearchInput, Section } from "./shared";

const statusClass = {
  ACTIVE: "bg-green-100 text-green-800",
  INACTIVE: "bg-gray-200 text-gray-700",
};

export default function CrewManagement({ data }) {
  const [workers, setWorkers] = useState(data.workers || []);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ name: "", phone: "", status: "ACTIVE" });
  const [error, setError] = useState("");

  const rows = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return workers.filter(
      (worker) =>
        !needle ||
        [worker.name, worker.phone, worker.status].some((value) =>
          String(value || "")
            .toLowerCase()
            .includes(needle)
        )
    );
  }, [query, workers]);

  const openEdit = (worker) => {
    setSelected(worker);
    setForm({ name: worker.name, phone: worker.phone, status: worker.status });
    setError("");
  };

  const save = async () => {
    if (!form.name.trim() || !form.phone.trim()) {
      setError("Name and phone number are required.");
      return;
    }
    try {
      const updated = await updateManagerWorker(selected.id, form);
      setWorkers((items) =>
        items.map((worker) => (worker.id === selected.id ? { ...worker, ...updated } : worker))
      );
      setSelected(null);
    } catch (err) {
      setError(err.response?.data?.error?.message || "Unable to update crew member.");
    }
  };

  const remove = async (worker) => {
    if (
      !window.confirm(
        `Delete ${worker.name}? This removes the crew member from the manager roster.`
      )
    )
      return;
    try {
      await deleteManagerWorker(worker.id);
      setWorkers((items) => items.filter((item) => item.id !== worker.id));
    } catch (err) {
      setError(err.response?.data?.error?.message || "Unable to delete crew member.");
    }
  };

  return (
    <>
      <Section
        eyebrow="Crew management"
        title="Crew members"
        actions={
          <SearchInput value={query} onChange={setQuery} placeholder="Search name, phone…" />
        }
      >
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        <PaginatedTable
          emptyMessage="No crew members match your search."
          columns={[
            { key: "name", label: "Name" },
            { key: "phone", label: "Phone number" },
            {
              key: "role",
              label: "Role",
              render: (value) => (
                <span className="text-xs font-semibold text-[#3F5426]">
                  {value === "COLLECTOR" ? "Collector" : "Recycler"}
                </span>
              ),
            },
            {
              key: "status",
              label: "Status",
              render: (value) => (
                <span className={`pill ${statusClass[value] || statusClass.INACTIVE}`}>
                  {value}
                </span>
              ),
            },
            {
              key: "actions",
              label: "Actions",
              render: (_, worker) => (
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => openEdit(worker)}
                    className="inline-flex items-center gap-1 rounded-input border border-gray-200 px-2.5 py-1 text-xs font-semibold text-[#3F5426] hover:border-[#3F5426]"
                  >
                    <Pencil size={12} /> Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => remove(worker)}
                    className="inline-flex items-center gap-1 rounded-input border border-red-200 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-50"
                  >
                    <Trash2 size={12} /> Delete
                  </button>
                </div>
              ),
            },
          ]}
          rows={rows}
        />
      </Section>

      <Modal
        open={!!selected}
        onClose={() => setSelected(null)}
        title={selected ? `Edit ${selected.name}` : ""}
      >
        <div className="space-y-4 text-sm">
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Name</label>
            <input
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              className="w-full border border-gray-200 rounded-input px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Phone number</label>
            <input
              value={form.phone}
              onChange={(event) => setForm({ ...form, phone: event.target.value })}
              className="w-full border border-gray-200 rounded-input px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-500 mb-1">Status</label>
            <select
              value={form.status}
              onChange={(event) => setForm({ ...form, status: event.target.value })}
              className="w-full border border-gray-200 rounded-input bg-white px-3 py-2"
            >
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </select>
          </div>
          {error && <p className="text-xs text-red-600">{error}</p>}
          <button
            type="button"
            onClick={save}
            className="rounded-input bg-[#3F5426] px-4 py-2 text-sm font-semibold text-white"
          >
            Save changes
          </button>
        </div>
      </Modal>
    </>
  );
}
