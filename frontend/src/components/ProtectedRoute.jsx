import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

/** Wrap a dashboard route with this to require a signed-in user of a
 *  specific role. Anyone else gets bounced somewhere sensible instead
 *  of seeing a broken page. */
export default function ProtectedRoute({ role, children }) {
  const { user, loading, homePath } = useAuth();

  if (loading) return null; // still checking localStorage for a session

  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={homePath} replace />;

  return children;
}
