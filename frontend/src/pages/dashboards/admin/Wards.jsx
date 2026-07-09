import { StatusPill } from "../../../components/UI";
import DATA from "../../../data/admin_portal_data.json";
import { Section, PaginatedTable } from "./shared";

const officerName = (id) => DATA.users.find((u) => u.id === id)?.name || "Unassigned";

export default function Wards() {
  return (
    <Section eyebrow="Ward configuration" title="Zones">
      <PaginatedTable
        columns={[
          { key: "code", label: "Ward" },
          { key: "name", label: "Name" },
          { key: "officer_id", label: "Officer", render: (v) => officerName(v) },
          { key: "active_workers", label: "Workers" },
          { key: "status", label: "Status", render: (v) => <StatusPill status={v} /> },
        ]}
        rows={DATA.zones}
      />
    </Section>
  );
}
