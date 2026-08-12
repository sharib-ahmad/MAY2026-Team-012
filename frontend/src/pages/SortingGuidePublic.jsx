import PublicLayout from "../components/PublicLayout";
import SortingGuide from "./dashboards/citizen/SortingGuide";

// Story 3.1-AC1: the sorting guide must render fully with no login
// required. The dashboard tab version (citizen/SortingGuide) is reused
// here so content stays in one place, just wrapped in the public site
// chrome instead of the citizen dashboard shell.
export default function SortingGuidePublic() {
  return (
    <PublicLayout>
      <div className="px-4 py-12">
        <SortingGuide />
      </div>
    </PublicLayout>
  );
}
