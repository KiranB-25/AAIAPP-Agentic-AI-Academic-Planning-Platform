import { get, post } from "./api-client";
import type { AuthResponse, AuthenticatedUser } from "../types/auth";

export function login(email: string, password: string): Promise<AuthResponse> {
  return post<AuthResponse>("/api/auth/login/", { email, password });
}

export function logout(refresh: string, accessToken: string): Promise<void> {
  return post<void>("/api/auth/logout/", { refresh }, { authenticated: true, accessToken, retryOnUnauthorized: false });
}

export function getCurrentUser(): Promise<AuthenticatedUser> {
  return get<AuthenticatedUser>("/api/auth/me/", { authenticated: true });
}
