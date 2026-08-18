import { createContext, useCallback, useContext, useEffect, useState, type PropsWithChildren } from "react";

import { getCurrentUser, logout as logoutRequest } from "../services/auth-service";
import type { AuthSession } from "../types/auth";
import { clearSession, readSession, sessionChangedEvent, storeSession } from "./session-store";

interface AuthContextValue {
  session: AuthSession | null;
  isInitializing: boolean;
  setSession: (session: AuthSession) => void;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
  const [session, updateSession] = useState<AuthSession | null>(readSession);
  const [isInitializing, setIsInitializing] = useState(() => readSession() !== null);

  useEffect(() => {
    const syncSession = (event: Event) => updateSession((event as CustomEvent<AuthSession | null>).detail);
    window.addEventListener(sessionChangedEvent, syncSession);
    return () => window.removeEventListener(sessionChangedEvent, syncSession);
  }, []);

  useEffect(() => {
    const restoredSession = readSession();
    if (!restoredSession) {
      setIsInitializing(false);
      return;
    }
    let cancelled = false;
    getCurrentUser()
      .then((user) => {
        if (cancelled) return;
        if (user.status !== "active") {
          clearSession();
          return;
        }
        storeSession({ ...readSession() ?? restoredSession, user });
      })
      .catch(() => {
        if (!cancelled) clearSession();
      })
      .finally(() => {
        if (!cancelled) setIsInitializing(false);
      });
    return () => { cancelled = true; };
  }, []);

  const setSession = useCallback((nextSession: AuthSession) => {
    storeSession(nextSession);
  }, []);

  const logout = useCallback(async () => {
    const currentSession = session;
    clearSession();
    if (currentSession) {
      try {
        await logoutRequest(currentSession.refresh, currentSession.access);
      } catch {
        // Clearing the local session remains safe if the access token is expired or unavailable.
      }
    }
  }, [session]);

  return <AuthContext.Provider value={{ session, isInitializing, setSession, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider.");
  return context;
}
