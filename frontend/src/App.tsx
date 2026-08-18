import { useEffect, useState } from "react";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import { ProtectedRoute } from "./auth/ProtectedRoute";
import { Redirect } from "./auth/Redirect";
import { LOGIN_PATH, roleForPath, roleHome } from "./auth/routes";
import { LoginPage } from "./pages/LoginPage";
import { RoleLandingPage } from "./pages/RoleLandingPage";
import { StudentGoalsPage } from "./pages/StudentGoalsPage";
import { StudentPlansPage } from "./pages/StudentPlansPage";
import { SupervisorPlansPage } from "./pages/SupervisorPlansPage";
import { StudentReviewsPage } from "./pages/StudentReviewsPage";

export default function App() {
  return <AuthProvider><ApplicationRoutes /></AuthProvider>;
}

function ApplicationRoutes() {
  const { session, isInitializing } = useAuth();
  const [pathname, setPathname] = useState(window.location.pathname);

  useEffect(() => {
    const updatePathname = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", updatePathname);
    return () => window.removeEventListener("popstate", updatePathname);
  }, []);

  if (isInitializing) {
    return <main className="grid min-h-screen place-items-center">Restoring session…</main>;
  }

  if (pathname === "/") return <Redirect to={session ? roleHome[session.user.role] : LOGIN_PATH} />;

  if (pathname === LOGIN_PATH) {
    if (session) {
      return <Redirect to={roleHome[session.user.role]} />;
    }
    return <LoginPage />;
  }

  const role = roleForPath(pathname);
  if (role) {
    const page = pathname === "/student/goals/" ? <StudentGoalsPage /> : pathname === "/student/plans/" ? <StudentPlansPage /> : pathname === "/student/reviews/" ? <StudentReviewsPage /> : pathname === "/supervisor/plans/" ? <SupervisorPlansPage /> : <RoleLandingPage role={role} />;
    return <ProtectedRoute role={role}>{page}</ProtectedRoute>;
  }

  return <Redirect to={session ? roleHome[session.user.role] : LOGIN_PATH} />;
}
