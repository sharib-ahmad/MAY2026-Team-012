import { Link } from "react-router-dom";
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  Landmark,
  Leaf,
  ClipboardList,
  MapPin,
  PhoneCall,
  Recycle,
  ShieldCheck,
  Smartphone,
  Truck,
} from "lucide-react";
import PublicLayout from "../components/PublicLayout";

const HERO_IMAGE =
  "https://images.unsplash.com/photo-1574974671999-24b7dfbb0d53?auto=format&fit=crop&w=2000&q=80";
const ROLES_IMAGE =
  "https://images.unsplash.com/photo-1611284446314-60a58ac0deb9?auto=format&fit=crop&w=2000&q=80";

const highlights = [
  {
    title: "Smart scheduling",
    description:
      "Residents book pickups in seconds and track every step from request to recycling.",
    icon: Smartphone,
  },
  {
    title: "QR traceability",
    description: "Each pickup gets a verifiable chain of custody so waste movement is transparent.",
    icon: ShieldCheck,
  },
  {
    title: "Eco impact",
    description:
      "Credits, CO₂ insights, and community dashboards turn participation into visible impact.",
    icon: BarChart3,
  },
];

const roles = [
  {
    name: "Residents",
    text: "Schedule pickups, donate reusable items, and earn credits for responsible disposal.",
    icon: Leaf,
  },
  {
    name: "Collectors",
    text: "Follow optimized routes, complete pickups, and keep every handoff accountable.",
    icon: MapPin,
  },
  {
    name: "Managers",
    text: "Oversee queues, verify credits, and manage teams with full visibility into the loop.",
    icon: ClipboardList,
  },
  {
    name: "Recyclers",
    text: "Receive, process, and certify batches.",
    icon: Recycle,
  },
];

const steps = [
  {
    label: "Request",
    detail: "A resident schedules a pickup and receives a manifest ID.",
    icon: Smartphone,
  },
  {
    label: "Collect",
    detail: "A verified collector scans and confirms the handoff on-site.",
    icon: Truck,
  },
  {
    label: "Certify",
    detail: "The batch is logged, weighed, and traced through to the recycler.",
    icon: BadgeCheck,
  },
];

export default function Landing() {
  return (
    <PublicLayout>
      {/* Fonts for this page only */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');
        .font-display { font-family: 'Fraunces', serif; }
        .font-mono-civic { font-family: 'IBM Plex Mono', monospace; }
      `}</style>

      {/* Official strip */}
      <div className="bg-amber-600 text-white text-xs sm:text-sm">
        <div className="max-w-7xl mx-auto px-4 py-2 flex flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-2">
            <Landmark size={14} />
            An official civic sanitation initiative by government of Uttar Pradesh, India
          </span>
          <span className="inline-flex items-center gap-2 text-white/80">
            <PhoneCall size={14} />
            24/7 municipal helpline
          </span>
        </div>
      </div>

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${HERO_IMAGE})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#0B2F2C]/95 via-[#0B4F4A]/85 to-[#0B4F4A]/50" />
        <div className="absolute inset-0 bg-gradient-to-t from-[#08221F]/80 via-transparent to-transparent" />

        <div className="relative max-w-7xl mx-auto px-4 py-20 sm:py-28">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-300/40 bg-amber-400/10 px-3 py-1 text-sm font-medium text-amber-200">
              <BadgeCheck size={14} /> Uttar Pradesh Municipal Waste Platform
            </div>
            <h1 className="font-display mt-5 text-4xl sm:text-5xl lg:text-6xl font-semibold text-white leading-[1.1]">
              End-to-end waste management, delivered by the state.
            </h1>
            <p className="mt-5 text-lg text-white/85 max-w-xl">
              Verdeza connects residents, collectors, managers, and recyclers under one accountable,
              publicly verifiable workflow &mdash; from pickup request to final recycling.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/register"
                className="inline-flex items-center gap-2 rounded-input bg-amber-400 px-5 py-3 font-semibold text-[#0B2F2C] hover:bg-amber-300 transition"
              >
                Create account <ArrowRight size={18} />
              </Link>
              <Link
                to="/flows"
                className="inline-flex items-center rounded-input border border-white/40 px-5 py-3 font-semibold text-white hover:border-white hover:bg-white/10 transition"
              >
                See how it works
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="bg-[#0B4F4A]">
        <div className="max-w-7xl mx-auto px-4 py-8 grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-white/15">
          {[
            ["24/7", "pickup visibility"],
            ["100%", "traceable handoffs"],
            ["AI-assisted", "classification & insights"],
          ].map(([stat, label]) => (
            <div key={label} className="py-4 sm:py-0 sm:px-6 text-center">
              <p className="font-display text-3xl font-semibold text-white">{stat}</p>
              <p className="mt-1 text-sm text-white/70">{label}</p>
            </div>
          ))}
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4">
        {/* HIGHLIGHTS */}
        <section className="mt-16 grid gap-6 md:grid-cols-3">
          {highlights.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.title}
                className="rounded-2xl border border-gray-200 bg-white p-6 shadow-soft"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-[#0B4F4A]/15 bg-[#0B4F4A]/5 text-[#0B4F4A]">
                  <Icon size={22} />
                </div>
                <h3 className="font-display mt-4 text-lg font-semibold text-gray-900">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm text-gray-600">{item.description}</p>
              </div>
            );
          })}
        </section>

        {/* PROCESS */}
        <section className="mt-16 rounded-3xl border border-gray-200 bg-white p-8 shadow-soft">
          <p className="text-sm font-semibold uppercase tracking-wide text-[#0B4F4A]">
            The manifest, step by step
          </p>
          <h2 className="font-display mt-2 text-3xl font-semibold text-gray-900">
            Every pickup follows the same verified path.
          </h2>
          <div className="mt-8 grid gap-6 sm:grid-cols-3">
            {steps.map((step, i) => {
              const Icon = step.icon;
              return (
                <div key={step.label} className="relative rounded-2xl bg-gray-50 p-5">
                  <span className="font-mono-civic text-xs text-gray-400">0{i + 1}</span>
                  <div className="mt-2 flex h-10 w-10 items-center justify-center rounded-xl bg-[#0B4F4A] text-white">
                    <Icon size={18} />
                  </div>
                  <h3 className="mt-4 font-semibold text-gray-900">{step.label}</h3>
                  <p className="mt-2 text-sm text-gray-600">{step.detail}</p>
                </div>
              );
            })}
          </div>
        </section>
      </div>

      {/* WHO IT SERVES — image background */}
      <section className="relative mt-16 overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center"
          style={{ backgroundImage: `url(${ROLES_IMAGE})` }}
        />
        <div className="absolute inset-0 bg-[#08221F]/85" />
        <div className="relative max-w-7xl mx-auto px-4 py-16">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-amber-300">
              Who it serves
            </p>
          </div>
          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            {roles.map((role) => {
              const Icon = role.icon;
              return (
                <div
                  key={role.name}
                  className="rounded-2xl bg-white/10 backdrop-blur border border-white/15 p-5"
                >
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/90 text-[#0B4F4A] shadow-sm">
                    <Icon size={20} />
                  </div>
                  <h3 className="mt-4 font-semibold text-white">{role.name}</h3>
                  <p className="mt-2 text-sm text-white/75">{role.text}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>
    </PublicLayout>
  );
}
