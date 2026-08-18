import type { PropsWithChildren } from "react";

import { useAuth } from "./AuthContext";
import { LOGIN_PATH, roleHome } from "./routes";
import { Redirect } from "./Redirect";
import type { UserRole } from "../types/auth";

interface ProtectedRouteProps extends PropsWithChildren {
  role: UserRole;
}

export function ProtectedRoute({ role, children }: ProtectedRouteProps) {
  const { session } = useAuth();
  if (!session) {
    return <Redirect to={LOGIN_PATH} />;
  }
  if (session.user.role !== role) {
    return <Redirect to={roleHome[session.user.role]} />;
  }
  return <>{children}</>;
}
