import { Trash2, Recycle, Award, CalendarClock, LogOut, MapPin } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { Card, StatCard, StatusPill, Table } from "../../components/UI";

const DEMO_PICKUPS = [];

export default function CitizenDashboard() {
  const { user, logout } = useAuth();

  const totalKg = DEMO_PICKUPS.reduce((sum, p) => sum + p.weight_kg, 0);

  return (
    <div className="min-h-screen bg-[#FBF7EE]">
      <header className="bg-[#0B2F2C] px-4 sm:px-6 py-3 flex items-center justify-between sticky top-0 z-10">
        <div className="flex items-center gap-2 text-white">
          <span className="text-2xl">♻</span>
          <div className="leading-tight">
            <div className="font-semibold">Verdeza</div>
            <div className="text-[11px] text-white/60">Citizen Dashboard</div>
          </div>
        </div>
        <button
          onClick={logout}
          className="flex items-center gap-1.5 text-white/75 hover:text-amber-300 text-sm"
        >
          <LogOut size={15} /> Sign out
        </button>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">
            Welcome back, {user?.name?.split(" ")[0] || "there"}{" "}
          </h1>
          <p className="text-gray-500 text-sm mt-1 flex items-center gap-1.5">
            <MapPin size={14} /> {user?.address || "No address on file"}
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard label="Total pickups" value={DEMO_PICKUPS.length} icon={Trash2} />
          <StatCard
            label="Waste recycled"
            value={`${totalKg.toFixed(1)} kg`}
            icon={Recycle}
            color="text-accent"
          />
          <StatCard
            label="Reward points"
            value="0"
            icon={Award}
            color="text-manager"
            sub="≈ ₹0 credit"
          />
          <StatCard label="Next pickup" value="NA" icon={CalendarClock} color="text-recycler" />
        </div>

        <Card title="Recent pickups">
          <Table
            columns={[
              { key: "id", label: "Pickup ID" },
              { key: "date", label: "Date" },
              { key: "category", label: "Category" },
              { key: "weight_kg", label: "Weight", render: (v) => `${v} kg` },
              { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
            ]}
            rows={DEMO_PICKUPS}
          />
        </Card>

        <div className="grid sm:grid-cols-3 gap-4">
          <button
            type="button"
            className="bg-white rounded-card shadow-soft p-4 text-left hover:shadow-elevated transition"
          >
            <Trash2 className="text-primary mb-2" size={22} />
            <p className="font-medium text-sm">Schedule a pickup</p>
            <p className="text-xs text-gray-400 mt-0.5">Coming soon</p>
          </button>
          <button
            type="button"
            className="bg-white rounded-card shadow-soft p-4 text-left hover:shadow-elevated transition"
          >
            <Award className="text-manager mb-2" size={22} />
            <p className="font-medium text-sm">Redeem rewards</p>
            <p className="text-xs text-gray-400 mt-0.5">Coming soon</p>
          </button>
        </div>
      </main>
    </div>
  );
}
