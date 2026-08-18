export type UserRole = "student" | "supervisor" | "administrator";

export interface AuthenticatedUser {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  status: "active" | "suspended" | "deactivated";
}

export interface AuthResponse {
  access: string;
  refresh: string;
  user: AuthenticatedUser;
}

export interface AuthSession extends AuthResponse {}
