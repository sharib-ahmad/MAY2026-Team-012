import { useEffect, useState } from "react";
import { Plus, CheckCircle2, Pencil, Trash2 } from "lucide-react";
import { Modal } from "../../../components/UI";
import API, { createWard, getWards } from "../../../lib/api";
import { Section, PaginatedTable, SearchInput } from "./shared";

function inputClass(hasError) {
  return `w-full border rounded-input px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-[#0B4F4A]/30 ${
    hasError ? "border-red-300 focus:border-red-400" : "border-gray-200 focus:border-[#0B4F4A]/40"
  }`;
}

const EMPTY_FORM = { code: "", name: "", sectors: "", manager_id: "" };

// Generate next ward code based on existing wards
const generateWardCode = (existingWards) => {
  const maxNum = existingWards.reduce((max, ward) => {
    const match = ward.code.match(/(?:WARD-|W-)(\d+)/i);
    if (match) {
      const num = parseInt(match[1], 10);
      return num > max ? num : max;
    }
    return max;
  }, 0);
  return `WARD-${String(maxNum + 1).padStart(2, "0")}`;
};

export default function Wards() {
  const [wards, setWards] = useState([]);
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editingWardId, setEditingWardId] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [fieldErrors, setFieldErrors] = useState({});
  const [err, setErr] = useState("");
  const [created, setCreated] = useState(null);

  // Fetch wards and managers on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [wardsData, dashboardData] = await Promise.all([
          getWards(),
          API.get("/v1/admin/dashboard"),
        ]);
        setWards(wardsData.wards || []);
        // Filter only manager users from dashboard
        const managerUsers = dashboardData.data.users.filter((u) => u.role === "MUNICIPAL_OFFICER");
        setManagers(managerUsers);
      } catch (err) {
        setError(err.message || "Failed to load data");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Refresh wards after creation/update/delete
  const refreshWards = async () => {
    try {
      const data = await getWards();
      setWards(data.wards || []);
    } catch (err) {
      setError(err.message || "Failed to refresh wards");
    }
  };

  const openModal = () => {
    setForm({ ...EMPTY_FORM, code: generateWardCode(wards) });
    setEditMode(false);
    setEditingWardId(null);
    setFieldErrors({});
    setErr("");
    setOpen(true);
  };

  const openEditModal = (ward) => {
    setForm({
      code: ward.code,
      name: ward.name,
      sectors: ward.sectors || "",
      manager_id: ward.manager_id || "",
    });
    setEditMode(true);
    setEditingWardId(ward.id);
    setFieldErrors({});
    setErr("");
    setOpen(true);
  };

  const deleteWard = async (wardId) => {
    if (!confirm("Are you sure you want to delete this ward?")) return;

    try {
      await API.delete(`/v1/admin/ward/${wardId}`);
      refreshWards();
    } catch (err) {
      console.error("Failed to delete ward:", err);
      const errorDetail =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        err.message ||
        "Failed to delete ward";
      alert(errorDetail);
    }
  };

  const updateField = (key, value) => {
    setForm((f) => ({ ...f, [key]: value }));
    setFieldErrors((e) => ({ ...e, [key]: undefined }));
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr("");

    const errors = {};
    if (!form.code.trim()) errors.code = "Ward code is required.";
    if (!form.name.trim()) errors.name = "Ward name is required.";
    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors);
      return;
    }

    try {
      if (editMode) {
        // Update existing ward
        await API.patch(`/v1/admin/ward/${editingWardId}`, {
          name: form.name,
          sectors: form.sectors || null,
          manager_id: form.manager_id || null,
        });
      } else {
        // Create new ward
        await createWard({
          code: form.code,
          name: form.name,
          sectors: form.sectors || null,
        });
      }
      setCreated(editMode ? null : form);
      setOpen(false);
      refreshWards();
    } catch (ex) {
      setErr(
        ex.response?.data?.error?.message ||
          ex.response?.data?.detail ||
          ex.message ||
          "Failed to save ward"
      );
    }
  };

  const q = query.trim().toLowerCase();
  const filtered = wards.filter(
    (z) =>
      !q ||
      z.code.toLowerCase().includes(q) ||
      z.name.toLowerCase().includes(q) ||
      (z.manager_name && z.manager_name.toLowerCase().includes(q))
  );

  if (loading) {
    return (
      <Section eyebrow="Ward configuration" title="Zones">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-gray-500">Loading wards...</div>
        </div>
      </Section>
    );
  }

  if (error) {
    return (
      <Section eyebrow="Ward configuration" title="Zones">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-red-500">Error: {error}</div>
        </div>
      </Section>
    );
  }

  return (
    <Section
      eyebrow="Ward configuration"
      title="Zones"
      actions={
        <div className="flex flex-wrap items-center gap-2">
          <SearchInput value={query} onChange={setQuery} placeholder="Search ward, manager…" />
          <button
            type="button"
            onClick={openModal}
            className="inline-flex items-center gap-1.5 rounded-input bg-[#0B4F4A] px-4 py-2 text-xs font-semibold text-white hover:bg-[#0B2F2C] transition"
          >
            <Plus size={14} /> Add ward
          </button>
        </div>
      }
    >
      {created && (
        <div className="mb-5 flex items-start gap-2 rounded-input border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-800">
          <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
          <span>
            Ward created successfully. <span className="font-semibold">{created.name}</span> (
            <span className="font-mono-civic">{created.code}</span>) is now available for manager
            and citizen assignment.
          </span>
        </div>
      )}

      <PaginatedTable
        columns={[
          { key: "code", label: "Ward" },
          { key: "name", label: "Name" },
          { key: "sectors", label: "Sectors", render: (v) => v || "—" },
          { key: "manager_name", label: "Manager", render: (v) => v || "Unassigned" },
          { key: "workers_count", label: "Workers" },
          {
            key: "actions",
            label: "Actions",
            render: (_, row) => (
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => openEditModal(row)}
                  className="inline-flex items-center gap-1 rounded-input border border-gray-200 px-2 py-1 text-xs font-semibold text-gray-600 hover:border-gray-300 hover:bg-gray-50 transition"
                >
                  <Pencil size={12} /> Edit
                </button>
                <button
                  type="button"
                  onClick={() => deleteWard(row.id)}
                  className="inline-flex items-center gap-1 rounded-input border border-red-200 px-2 py-1 text-xs font-semibold text-red-600 hover:border-red-300 hover:bg-red-50 transition"
                >
                  <Trash2 size={12} /> Delete
                </button>
              </div>
            ),
          },
        ]}
        rows={filtered}
      />

      <Modal
        open={open}
        onClose={() => setOpen(false)}
        title={editMode ? "Edit ward" : "Add a new ward"}
      >
        {err && (
          <div className="mb-4 rounded-input border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {err}
          </div>
        )}
        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
                Ward code
              </label>
              <input
                className={inputClass(fieldErrors.code)}
                value={form.code}
                onChange={(e) => updateField("code", e.target.value)}
                placeholder="e.g. WARD-06"
                disabled={editMode}
              />
              {fieldErrors.code && <p className="text-red-600 text-xs mt-1">{fieldErrors.code}</p>}
            </div>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
                Assigned manager (optional)
              </label>
              <select
                className={inputClass(false)}
                value={form.manager_id}
                onChange={(e) => updateField("manager_id", e.target.value)}
              >
                <option value="">Unassigned</option>
                {managers.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
              Ward name
            </label>
            <input
              className={inputClass(fieldErrors.name)}
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="e.g. Zone 6 - Aliganj"
            />
            {fieldErrors.name && <p className="text-red-600 text-xs mt-1">{fieldErrors.name}</p>}
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wide text-gray-500 mb-1.5">
              Sectors (optional)
            </label>
            <input
              className={inputClass(false)}
              value={form.sectors}
              onChange={(e) => updateField("sectors", e.target.value)}
              placeholder="e.g. Sector 10, Sector 11"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="rounded-input border border-gray-200 px-4 py-2 text-sm font-semibold text-gray-600 hover:border-gray-300"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="inline-flex items-center gap-1.5 rounded-input bg-[#0B4F4A] px-4 py-2 text-sm font-semibold text-white hover:bg-[#0B2F2C] transition"
            >
              {editMode ? <Pencil size={14} /> : <Plus size={14} />}
              {editMode ? "Update ward" : "Create ward"}
            </button>
          </div>
        </form>
      </Modal>
    </Section>
  );
}
