import { Routes as AppRoutes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ComingSoon from "./pages/dashboards/ComingSoon";

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
      <Route path="/track" element={<ComingSoon roleLabel="Track" />} />
      <Route path="/flows" element={<ComingSoon roleLabel="Flows" />} />
      <Route path="/login" element={user ? <Navigate to={homePath} replace /> : <Login />} />
      <Route path="/register" element={user ? <Navigate to={homePath} replace /> : <Register />} />

      <Route
        path="/resident/dashboard"
        element={
          <ProtectedRoute role="RESIDENT">
            <ComingSoon roleLabel="Resident" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/collector/dashboard"
        element={
          <ProtectedRoute role="COLLECTOR">
            <ComingSoon roleLabel="Collector" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/recycler/dashboard"
        element={
          <ProtectedRoute role="RECYCLER">
            <ComingSoon roleLabel="Recycler" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/manager/dashboard"
        element={
          <ProtectedRoute role="MANAGER">
            <ComingSoon roleLabel="Manager" />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin/dashboard"
        element={
          <ProtectedRoute role="ADMIN">
            <ComingSoon roleLabel="Admin" />
          </ProtectedRoute>
        }
      />

      <Route path="/" element={user ? <Navigate to={homePath} replace /> : <Landing />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </AppRoutes>
  );
}
