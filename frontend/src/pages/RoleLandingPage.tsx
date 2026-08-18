import { LogOut } from "lucide-react";

import { useAuth } from "../auth/AuthContext";
import { LOGIN_PATH, navigate } from "../auth/routes";
import { AppShell } from "../layouts/AppShell";
import type { UserRole } from "../types/auth";

const labels: Record<UserRole, string> = { student: "Student", supervisor: "Supervisor", administrator: "Administrator" };

export function RoleLandingPage({ role }: { role: UserRole }) {
  const { session, logout } = useAuth();

  async function handleLogout() {
    await logout();
    navigate(LOGIN_PATH);
  }

  return (
    <AppShell>
      <section className="max-w-2xl space-y-6">
        <div>
          <p className="text-sm font-medium text-primary">Authenticated access</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight">{labels[role]} area</h1>
          <p className="mt-3 text-muted-foreground">Signed in as {session?.user.name}. This role-specific workspace will be implemented in its approved later phase.</p>
        </div>
        {role === "student" && <div className="flex gap-3"><button className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground" onClick={() => navigate("/student/goals/")}>Manage academic goals</button><button className="rounded-lg border border-border px-4 py-2 text-sm font-semibold" onClick={() => navigate("/student/plans/")}>View study plans</button><button className="rounded-lg border border-border px-4 py-2 text-sm font-semibold" onClick={() => navigate("/student/reviews/")}>Feedback and notifications</button></div>}
        {role === "supervisor" && <button className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground" onClick={() => navigate("/supervisor/plans/")}>View assigned study plans</button>}
        <button className="inline-flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm font-medium" onClick={handleLogout}>
          <LogOut className="size-4" aria-hidden="true" /> Sign out
        </button>
      </section>
    </AppShell>
  );
}
