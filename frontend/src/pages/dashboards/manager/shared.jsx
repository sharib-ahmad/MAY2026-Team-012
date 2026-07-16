/* Shared pieces for the Municipal Officer tabs: themed Section wrapper,
   search/filter controls, severity pill, and a Table with built-in
   10-row pagination — all carrying the portal palette (deep olive +
   goldenrod accent). */
import { useState } from "react";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { Table } from "../../../components/UI";

export function SearchInput({ value, onChange, placeholder = "Search…" }) {
  return (
    <div className="relative">
      <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full sm:w-52 border border-gray-200 rounded-input bg-white pl-8 pr-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[#3F5426]/30"
      />
    </div>
  );
}

export function FilterSelect({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-gray-200 rounded-input bg-white px-2.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-[#3F5426]/30"
    >
      {options.map((o) => (
        <option key={o.value} value={o.value}>
          {o.label}
        </option>
      ))}
    </select>
  );
}

/** Themed section card matching the civic style of the other portals. */
export function Section({ eyebrow, title, actions, children }) {
  return (
    <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-soft">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          {eyebrow && (
            <p className="text-xs font-semibold uppercase tracking-wider text-[#A16207]">
              {eyebrow}
            </p>
          )}
          <h2 className="font-display mt-1 text-xl font-semibold text-[#1C2312]">{title}</h2>
        </div>
        {actions}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

const SEVERITY_TONES = {
  HIGH: "bg-red-100 text-red-800",
  MEDIUM: "bg-amber-100 text-amber-800",
  LOW: "bg-gray-100 text-gray-700",
};

export function SeverityPill({ severity }) {
  return (
    <span className={`pill ${SEVERITY_TONES[severity] || SEVERITY_TONES.LOW}`}>{severity}</span>
  );
}

const PAGE_SIZE = 10;

/** Table showing at most 10 rows at a time with Prev / Next controls. */
export function PaginatedTable({ columns, rows, onRowClick, emptyMessage = "No records found." }) {
  const [page, setPage] = useState(0);

  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  // Clamp instead of resetting so a shrinking filter result can't leave
  // the pager pointing past the last page.
  const current = Math.min(page, pages - 1);
  const start = current * PAGE_SIZE;
  const slice = rows.slice(start, start + PAGE_SIZE);

  return (
    <div>
      <Table columns={columns} rows={slice} onRowClick={onRowClick} />
      {rows.length === 0 && (
        <p className="text-center text-sm text-gray-400 py-8">{emptyMessage}</p>
      )}
      {rows.length > PAGE_SIZE && (
        <div className="flex items-center justify-between mt-4 text-sm">
          <p className="font-mono-civic text-xs text-gray-400">
            Showing {start + 1}–{Math.min(start + PAGE_SIZE, rows.length)} of {rows.length}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setPage(current - 1)}
              disabled={current === 0}
              className="inline-flex items-center gap-1 rounded-input border border-gray-200 px-3 py-1.5 text-xs font-semibold text-[#1C2312] hover:border-[#3F5426] disabled:opacity-40 disabled:hover:border-gray-200"
            >
              <ChevronLeft size={14} /> Prev
            </button>
            <span className="font-mono-civic text-xs text-gray-500">
              {current + 1} / {pages}
            </span>
            <button
              type="button"
              onClick={() => setPage(current + 1)}
              disabled={current >= pages - 1}
              className="inline-flex items-center gap-1 rounded-input border border-gray-200 px-3 py-1.5 text-xs font-semibold text-[#1C2312] hover:border-[#3F5426] disabled:opacity-40 disabled:hover:border-gray-200"
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
