import type { AuthSession } from "../types/auth";
import { LOGIN_PATH, navigate } from "./routes";

export const sessionKey = "aaiapp-auth-session";
export const sessionChangedEvent = "aaiapp-auth-session-changed";

export function readSession(): AuthSession | null {
  const stored = sessionStorage.getItem(sessionKey);
  if (!stored) return null;
  try {
    return JSON.parse(stored) as AuthSession;
  } catch {
    sessionStorage.removeItem(sessionKey);
    return null;
  }
}

export function storeSession(session: AuthSession) {
  sessionStorage.setItem(sessionKey, JSON.stringify(session));
  window.dispatchEvent(new CustomEvent(sessionChangedEvent, { detail: session }));
}

export function clearSession(redirectToLogin = false) {
  sessionStorage.removeItem(sessionKey);
  window.dispatchEvent(new CustomEvent(sessionChangedEvent, { detail: null }));
  if (redirectToLogin && window.location.pathname !== LOGIN_PATH) navigate(LOGIN_PATH);
}
