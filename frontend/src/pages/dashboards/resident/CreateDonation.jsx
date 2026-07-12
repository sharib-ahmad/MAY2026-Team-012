import { useState } from 'react';
import { useAuth } from '../../../context/AuthContext';
import { Card } from '../../../components/UI';
import AddressField from '../../../components/AddressField';
import { createDonation } from '../../../lib/mockResidentData';
import { CheckCircle2 } from 'lucide-react';

const CATEGORIES = ['BOOKS', 'FURNITURE', 'ELECTRONICS', 'CLOTHES', 'TOYS', 'KITCHEN', 'BICYCLE', 'BAGS', 'OTHER'];
const CONDITIONS = ['NEW', 'LIKE_NEW', 'GOOD', 'FAIR', 'NEEDS_REPAIR'];
const TITLE_MAX = 80;
const DESCRIPTION_MIN = 10;
const DESCRIPTION_MAX = 500;
const MAX_PHOTOS = 5;
const MAX_PHOTO_MB = 5;
const ALLOWED_TYPES = ['image/jpeg', 'image/png'];

function filesToDataUrls(files) {
  return Promise.all(
    files.map(
      (f) =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = () => resolve(reader.result);
          reader.onerror = reject;
          reader.readAsDataURL(f);
        })
    )
  );
}

export default function CreateDonation({ onNavigate }) {
  const { user } = useAuth();
  const [form, setForm] = useState({ title: '', category: 'BOOKS', description: '', condition: 'GOOD' });
  const [address, setAddress] = useState(user?.address || '');
  const [files, setFiles] = useState([]);
  // Field-specific errors (AC4) rather than one generic banner.
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  // AC2/AC3 (Photo validation): reject anything that isn't JPEG/PNG, and
  // anything over 5MB, with a message naming which file and why.
  const handleFiles = (fileList) => {
    const incoming = [...fileList].slice(0, MAX_PHOTOS);
    for (const f of incoming) {
      if (!ALLOWED_TYPES.includes(f.type)) {
        setFieldErrors((prev) => ({ ...prev, photos: 'Only JPEG and PNG images are accepted.' }));
        return;
      }
      if (f.size > MAX_PHOTO_MB * 1024 * 1024) {
        setFieldErrors((prev) => ({ ...prev, photos: `Each photo must be ${MAX_PHOTO_MB}MB or smaller.` }));
        return;
      }
    }
    setFieldErrors((prev) => ({ ...prev, photos: undefined }));
    setFiles(incoming);
  };

  const submit = async (e) => {
    e.preventDefault();
    const errors = {};
    if (!form.title.trim()) errors.title = 'Title is required.';
    else if (form.title.trim().length > TITLE_MAX) errors.title = `Title must be ${TITLE_MAX} characters or fewer.`;
    if (!form.category) errors.category = 'Category is required.';
    if (!form.condition) errors.condition = 'Condition is required.';
    const descLen = form.description.trim().length;
    if (descLen < DESCRIPTION_MIN) errors.description = `Description must be at least ${DESCRIPTION_MIN} characters.`;
    else if (descLen > DESCRIPTION_MAX) errors.description = `Description must be ${DESCRIPTION_MAX} characters or fewer.`;
    // AC1: a valid photo is required, not optional.
    if (files.length === 0) errors.photos = 'Please add at least one photo (JPEG or PNG).';

    setFieldErrors(errors);
    if (Object.keys(errors).filter((k) => errors[k]).length > 0) return;

    setLoading(true);
    try {
      const images = await filesToDataUrls(files);
      createDonation(user, { ...form, address, images });
      setDone(true);
      setTimeout(() => onNavigate('donations'), 1200);
    } catch {
      setFieldErrors({ submit: 'Failed to submit — please try again.' });
    }
    setLoading(false);
  };

  if (done) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center">
        <CheckCircle2 className="mx-auto text-success mb-3" size={40} />
        <p className="font-medium">Listing submitted for approval!</p>
        <p className="text-sm text-gray-400 mt-1">
          A municipal officer will review it before it appears in the Marketplace. Taking you to My Donations…
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto fade-in">
      <h1 className="text-xl font-bold mb-6">Donate a Product</h1>
      <Card>
        <form onSubmit={submit} className="space-y-4" noValidate>
          {fieldErrors.submit && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-input">{fieldErrors.submit}</div>}
          <div>
            <div className="flex items-center justify-between mb-1">
              <span />
              <span className="text-[11px] text-gray-400">{form.title.length}/{TITLE_MAX}</span>
            </div>
            <input
              placeholder="Title *"
              maxLength={TITLE_MAX}
              className={`w-full border rounded-input px-3 py-2.5 text-sm ${fieldErrors.title ? 'border-red-300' : 'border-gray-200'}`}
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
            />
            {fieldErrors.title && <p className="text-xs text-red-600 mt-1">{fieldErrors.title}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <select
                className={`w-full border rounded-input px-3 py-2.5 text-sm ${fieldErrors.category ? 'border-red-300' : 'border-gray-200'}`}
                value={form.category}
                onChange={(e) => setForm({ ...form, category: e.target.value })}
              >
                {CATEGORIES.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
              {fieldErrors.category && <p className="text-xs text-red-600 mt-1">{fieldErrors.category}</p>}
            </div>
            <div>
              <select
                className={`w-full border rounded-input px-3 py-2.5 text-sm ${fieldErrors.condition ? 'border-red-300' : 'border-gray-200'}`}
                value={form.condition}
                onChange={(e) => setForm({ ...form, condition: e.target.value })}
              >
                {CONDITIONS.map((c) => (
                  <option key={c}>{c.replace(/_/g, ' ')}</option>
                ))}
              </select>
              {fieldErrors.condition && <p className="text-xs text-red-600 mt-1">{fieldErrors.condition}</p>}
            </div>
          </div>
          <div>
            <div className="flex items-center justify-between mb-1">
              <span />
              <span className="text-[11px] text-gray-400">{form.description.length}/{DESCRIPTION_MAX}</span>
            </div>
            <textarea
              maxLength={DESCRIPTION_MAX}
              rows={4}
              placeholder="Description *"
              className={`w-full border rounded-input px-3 py-2.5 text-sm ${fieldErrors.description ? 'border-red-300' : 'border-gray-200'}`}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
            />
            {fieldErrors.description && <p className="text-xs text-red-600 mt-1">{fieldErrors.description}</p>}
          </div>
          <AddressField
            address={address}
            onChange={({ address: a }) => setAddress(a)}
            placeholder="Pickup / meetup location"
          />
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">
              Photo * (JPEG or PNG, up to {MAX_PHOTO_MB}MB each, max {MAX_PHOTOS})
            </label>
            <input
              type="file"
              accept="image/jpeg,image/png"
              multiple
              onChange={(e) => handleFiles(e.target.files)}
              className="text-sm"
            />
            {fieldErrors.photos && <p className="text-xs text-red-600 mt-1">{fieldErrors.photos}</p>}
            {files.length > 0 && (
              <div className="flex gap-2 mt-2 flex-wrap">
                {files.map((f, i) => (
                  <img key={i} src={URL.createObjectURL(f)} alt="" className="w-16 h-16 object-cover rounded" />
                ))}
              </div>
            )}
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary text-white py-2.5 rounded-input font-medium disabled:opacity-50"
          >
            {loading ? 'Submitting…' : 'Submit for Approval'}
          </button>
        </form>
      </Card>
    </div>
  );
}
