import { createContext, useContext, useState } from "react";
import { homePathForRole } from "./roles";
import * as auth from "../lib/mockAuth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("gc_token");
    if (!raw) return null;
    try {
      const { access_token } = JSON.parse(raw);
      const sessionUser = auth.getSessionUser(access_token);
      if (!sessionUser) {
        localStorage.removeItem("gc_token");
        return null;
      }
      return sessionUser;
    } catch {
      localStorage.removeItem("gc_token");
      return null;
    }
  });
  const [loading] = useState(false);

  const login = async (email, password) => {
    const data = await auth.login(email, password);
    localStorage.setItem("gc_token", JSON.stringify(data));
    setUser(data.user);
    return { ...data, homePath: homePathForRole(data.user.role) };
  };

  const register = async (payload) => {
    const data = await auth.register(payload);
    localStorage.setItem("gc_token", JSON.stringify(data));
    setUser(data.user);
    return { ...data, homePath: homePathForRole(data.user.role) };
  };

  const logout = () => {
    localStorage.removeItem("gc_token");
    setUser(null);
  };

  const homePath = user ? homePathForRole(user.role) : "/login";

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading, homePath }}>
      {children}
    </AuthContext.Provider>
  );
}
// eslint-disable-next-line react-refresh/only-export-components -- hook lives next to its Provider on purpose
export const useAuth = () => useContext(AuthContext);
export default AuthContext;
