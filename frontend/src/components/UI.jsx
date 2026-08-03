/* Shared UI primitives: Card, Modal, StatusPill, Chart, ChatWidget, StatCard */
import { createPortal } from "react-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  CartesianGrid,
  Legend,
} from "recharts";
import { useState, useRef, useEffect } from "react";
import { Send, Bot } from "lucide-react";
import { ecoBotReply } from "../lib/ecobot";

// ── CountUp ─────────────────────────────────────────────────────────
/** Animates a number from 0 up to `value` on mount/whenever value changes.
 *  Pure CSS/requestAnimationFrame, no dependency needed. */
export function CountUp({ value, decimals = 0, suffix = "", duration = 800 }) {
  const [display, setDisplay] = useState(0);
  const raf = useRef(null);

  useEffect(() => {
    const start = performance.now();
    const from = 0;
    const to = Number(value) || 0;
    const tick = (now) => {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(from + (to - from) * eased);
      if (progress < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => raf.current && cancelAnimationFrame(raf.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <>
      {display.toFixed(decimals)}
      {suffix}
    </>
  );
}

// ── StatCard ─────────────────────────────────────────────────────────
export function StatCard({ label, value, sub, icon: Icon, color = "text-primary" }) {
  return (
    <div className="bg-white rounded-card shadow-soft p-5 flex items-start gap-4 fade-in">
      {Icon && <Icon className={`${color} mt-0.5`} size={28} strokeWidth={1.5} />}
      <div>
        <p className="text-gray-500 text-xs font-medium uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold mt-0.5">{value}</p>
        {sub && <p className="text-gray-400 text-xs mt-1">{sub}</p>}
      </div>
    </div>
  );
}

// ── Card ────────────────────────────────────────────────────────────
export function Card({ children, className = "", title, actions }) {
  return (
    <div className={`bg-white rounded-card shadow-soft ${className}`}>
      {(title || actions) && (
        <div className="flex items-center justify-between px-5 py-3 border-b border-gray-100">
          <h3 className="font-semibold text-sm">{title}</h3>
          {actions && <div>{actions}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

// ── StatusPill ─────────────────────────────────────────────────────────
const STATUS_MAP = {
  REQUESTED: "pill-info",
  SCHEDULED: "pill-purple",
  ASSIGNED: "pill-purple",
  RECYCLER_ASSIGNED: "pill-purple",
  IN_PROGRESS: "pill-warn",
  COLLECTED: "pill-success",
  VERIFIED: "pill-success",
  CREDITED: "pill-success",
  MISSED: "pill-danger",
  OPEN: "pill-info",
  IN_REVIEW: "pill-warn",
  RESOLVED: "pill-success",
  ESCALATED: "pill-danger",
  IN_TRANSIT: "pill-warn",
  PROCESSING: "pill-warn",
  ACCEPTED: "pill-success",
  APPROVED: "pill-success",
  REJECTED: "pill-danger",
  DISPUTED: "pill-danger",
  PROCESSED: "pill-success",
  ACTIVE: "pill-success",
  SUSPENDED: "pill-danger",
  PENDING: "pill-warn",
  INITIATED: "pill-info",
  DELIVERED: "pill-success",
  CONFIRMED: "pill-success",
  REVERSED: "pill-danger",
  PENDING_APPROVAL: "pill-warn",
  WITHDRAWN: "pill-slate",
  CLAIM_REQUESTED: "pill-warn",
  COMPLETED: "pill-success",
  DELAYED: "pill-danger",
  ON_ROUTE: "pill-info",
  AVAILABLE: "pill-success",
  ON_LEAVE: "pill-slate",
};

export function StatusPill({ status }) {
  const cls = STATUS_MAP[status] || "pill-slate";
  return <span className={`pill ${cls}`}>{status?.replace(/_/g, " ")}</span>;
}

// ── Modal ────────────────────────────────────────────────────────────
export function Modal({ open, onClose, title, children }) {
  if (!open) return null;
  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 fade-in p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="bg-white rounded-card shadow-elevated w-full max-w-lg max-h-[85vh] overflow-auto relative z-[10000]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-3 border-b sticky top-0 bg-white z-10">
          <h3 className="font-semibold">{title}</h3>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            &times;
          </button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>,
    document.body
  );
}

const COLORS = ["#1B5E20", "#0277BD", "#B8860B", "#6A1B9A", "#C62828", "#ED6C02"];

export function BarChartCard({ data, dataKey, nameKey, title }) {
  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey={nameKey} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Bar dataKey={dataKey} fill="#1B5E20" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

export function ClusteredBarChartCard({ data, bars, nameKey, title }) {
  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey={nameKey} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          {bars.map((bar, i) => (
            <Bar
              key={bar.key}
              dataKey={bar.key}
              name={bar.name}
              fill={bar.color || COLORS[i % COLORS.length]}
              radius={[4, 4, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );
}

export function PieChartCard({ data, title }) {
  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={280}>
        <PieChart margin={{ top: 24, right: 24, bottom: 8, left: 24 }}>
          <Pie
            data={data}
            dataKey="weight_kg"
            nameKey="category"
            cx="50%"
            cy="50%"
            outerRadius={80}
            label
          >
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );
}

export function LineChartCard({ data, lines, title }) {
  return (
    <Card title={title}>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="month" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip />
          <Legend />
          {lines.map((l, i) => (
            <Line
              key={l.key}
              type="monotone"
              dataKey={l.key}
              name={l.name}
              stroke={l.color || COLORS[i]}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </Card>
  );
}

// ── ChatWidget (EcoBot) ─────────────────────────────────────────────
export function ChatWidget() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Hi! I'm EcoBot. Ask me anything about dry-waste segregation, your pickups, or sustainability tips.",
    },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const bottom = useRef(null);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = () => {
    const msg = input.trim();
    if (!msg) return;
    setMessages((p) => [...p, { role: "user", text: msg }]);
    setInput("");
    setTyping(true);
    // No AI backend is connected yet — EcoBot answers from a small local
    // knowledge base of segregation tips so the widget stays useful and
    // interactive offline.
    setTimeout(() => {
      setMessages((p) => [...p, { role: "bot", text: ecoBotReply(msg) }]);
      setTyping(false);
    }, 500);
  };

  return (
    <Card
      title={
        <>
          <Bot size={16} className="inline mr-1" /> EcoBot
        </>
      }
    >
      <div className="h-64 overflow-y-auto space-y-2 mb-3">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] px-3 py-2 rounded-lg text-sm ${
                m.role === "user" ? "bg-primary text-white" : "bg-gray-100 text-gray-700"
              }`}
            >
              {m.text}
            </div>
          </div>
        ))}
        {typing && <div className="text-xs text-gray-400 animate-pulse">EcoBot is typing…</div>}
        <div ref={bottom} />
      </div>
      <div className="flex gap-2">
        <input
          className="flex-1 border border-gray-200 rounded-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
          placeholder="Ask about waste segregation…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
        />
        <button
          onClick={send}
          className="bg-primary text-white px-3 py-2 rounded-input hover:bg-primary/90"
        >
          <Send size={16} />
        </button>
      </div>
    </Card>
  );
}

// ── Loading spinner ─────────────────────────────────────────────────
export function Spinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

// ── Empty state ──────────────────────────────────────────────────────
export function Empty({ icon: Icon, title, description }) {
  return (
    <div className="text-center py-16 text-gray-400">
      {Icon && <Icon size={48} className="mx-auto mb-3 opacity-50" />}
      <p className="font-medium">{title}</p>
      {description && <p className="text-sm mt-1">{description}</p>}
    </div>
  );
}

// ── DataTable (simple) ───────────────────────────────────────────────
export function Table({ columns, rows, onRowClick }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-200 text-left text-xs text-gray-500 uppercase">
            {columns.map((c) => (
              <th key={c.key} className="px-4 py-2 font-medium">
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={row.id || i}
              className={`border-b border-gray-50 hover:bg-gray-50 transition-colors ${onRowClick ? "cursor-pointer" : ""}`}
              onClick={() => onRowClick?.(row)}
            >
              {columns.map((c) => (
                <td key={c.key} className="px-4 py-2.5">
                  {c.render ? c.render(row[c.key], row) : row[c.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
