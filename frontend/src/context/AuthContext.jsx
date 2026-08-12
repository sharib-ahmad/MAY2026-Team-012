import { createContext, useContext, useState } from "react";
import { homePathForRole } from "./roles";
import API from "../lib/api";
import { usePolling } from "../hooks/usePolling";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("gc_token");
    if (!raw) return null;
    try {
      const { user } = JSON.parse(raw);
      return user || null;
    } catch {
      localStorage.removeItem("gc_token");
      return null;
    }
  });
  const [loading] = useState(false);

  const login = async (email, password) => {
    const res = await API.post("/v1/auth/login", { email, password });
    const data = res.data;
    localStorage.setItem("gc_token", JSON.stringify(data));
    setUser(data.user);
    return { ...data, homePath: homePathForRole(data.user.role) };
  };

  const register = async (payload) => {
    const res = await API.post("/v1/auth/register", payload);
    const data = res.data;
    localStorage.setItem("gc_token", JSON.stringify(data));
    setUser(data.user);
    return { ...data, homePath: homePathForRole(data.user.role) };
  };

  const logout = () => {
    localStorage.removeItem("gc_token");
    setUser(null);
  };

  // Story 5.1-AC2: re-checks the session every few seconds so suspending
  // an account takes effect right away for anyone already logged in,
  // rather than only on their next login.
  usePolling(async () => {
    if (!user) return;
    const raw = localStorage.getItem("gc_token");
    if (!raw) return;
    try {
      const res = await API.get("/v1/auth/me");
      setUser(res.data);
      const stored = JSON.parse(raw);
      localStorage.setItem("gc_token", JSON.stringify({ ...stored, user: res.data }));
    } catch {
      logout();
    }
  }, 45000);

  const homePath = user ? homePathForRole(user.role) : "/login";

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, homePath }}>
      {children}
    </AuthContext.Provider>
  );
}
export const useAuth = () => useContext(AuthContext);
export default AuthContext;
