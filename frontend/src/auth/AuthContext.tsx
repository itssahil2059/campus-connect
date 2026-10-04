import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { apiGet, apiPost } from "../api/client";
import type { User } from "../api/types";

interface AuthState {
  user: User | null;
  /** True while we check a saved token on first load. */
  loading: boolean;
  login: (token: string, user: User) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(() => !!localStorage.getItem("token"));

  // On page load, turn a saved token back into a user (or drop it if expired).
  useEffect(() => {
    if (!localStorage.getItem("token")) return;
    apiGet<User>("/api/auth/me/")
      .then(setUser)
      .catch(() => localStorage.removeItem("token"))
      .finally(() => setLoading(false));
  }, []);

  function login(token: string, newUser: User) {
    localStorage.setItem("token", token);
    setUser(newUser);
  }

  async function logout() {
    // Revoke the token on the server; log out locally even if that fails.
    await apiPost("/api/auth/logout/").catch(() => {});
    localStorage.removeItem("token");
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
