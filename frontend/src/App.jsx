import { Routes as AppRoutes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Landing from "./pages/Landing";
import Track from "./pages/Track";
import Flows from "./pages/Flows";
import SortingGuidePublic from "./pages/SortingGuidePublic";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ResidentDashboard from "./pages/dashboards/ResidentDashboard";
import AdminDashboard from "./pages/dashboards/AdminDashboard";
import ManagerDashboard from "./pages/dashboards/ManagerDashboard";
import CollectorDashboard from "./pages/dashboards/CollectorDashboard";
import RecyclerDashboard from "./pages/dashboards/RecyclerDashoard";

export default function App() {
  const { user, homePath, loading } = useAuth();

  // Wait for AuthProvider to finish checking localStorage for a session
  // before deciding where to route — otherwise a logged-in user briefly
  // flashes the login page on refresh.
  if (loading) {
    return <div className="min-h-screen bg-[#FBF7EE]" />;
  }

  return (
    <AppRoutes>
      <Route path="/track" element={<Track />} />
      <Route path="/flows" element={<Flows />} />
      <Route path="/sorting-guide" element={<SortingGuidePublic />} />
      <Route path="/login" element={user ? <Navigate to={homePath} replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to={homePath} replace /> : <Register />} />

      <Route
        path="/resident/dashboard"
        element={
          <ProtectedRoute role="CITIZEN">
            <ResidentDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/collector/dashboard"
        element={
          <ProtectedRoute role="COLLECTION_WORKER">
            <CollectorDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recycler/dashboard"
        element={
          <ProtectedRoute role="RECYCLER">
            <RecyclerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager/dashboard"
        element={
          <ProtectedRoute role="MUNICIPAL_OFFICER">
            <ManagerDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute role="SYSTEM_ADMIN">
            <AdminDashboard />
          </ProtectedRoute>
        }
      />

      <Route path="/" element={user ? <Navigate to={homePath} replace /> : <Landing />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </AppRoutes>
  );
}
