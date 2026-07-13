import { MapPin } from "lucide-react";

/** Lightweight replacement for the old map-based location picker. The
 *  resident portal now runs fully client-side with no map/geocoding
 *  service, so location is just a free-text address. latitude/longitude
 *  are kept in the returned object (set to null) purely so any code that
 *  destructures { latitude, longitude, address } keeps working. */
export default function AddressField({ address, onChange, placeholder = "Enter pickup address" }) {
  return (
    <div>
      <div className="relative">
        <MapPin size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          required
          placeholder={placeholder}
          className="w-full border border-gray-200 rounded-input pl-9 pr-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          value={address || ""}
          onChange={(e) => onChange({ latitude: 0, longitude: 0, address: e.target.value })}
        />
      </div>
    </div>
  );
}
