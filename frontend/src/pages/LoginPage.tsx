import { useState, type FormEvent } from "react";
import { LockKeyhole } from "lucide-react";

import { useAuth } from "../auth/AuthContext";
import { navigate, roleHome } from "../auth/routes";
import { ApiError } from "../services/api-client";
import { login } from "../services/auth-service";

export function LoginPage() {
  const { setSession } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (!email || !password) {
      setError("Enter your email address and password.");
      return;
    }
    setIsSubmitting(true);
    try {
      const session = await login(email, password);
      setSession(session);
      navigate(roleHome[session.user.role]);
    } catch (caughtError) {
      setError(caughtError instanceof ApiError ? caughtError.message : "Unable to sign in. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-background px-5 py-10 text-foreground">
      <section className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-sm sm:p-8" aria-labelledby="login-title">
        <div className="mb-6 flex size-10 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <LockKeyhole className="size-5" aria-hidden="true" />
        </div>
        <h1 id="login-title" className="text-2xl font-semibold tracking-tight">Sign in to AAIAPP</h1>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">Use your registered academic planning account.</p>
        <form className="mt-6 space-y-4" onSubmit={onSubmit} noValidate>
          <label className="block text-sm font-medium" htmlFor="email">Email address
            <input id="email" className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2.5" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} disabled={isSubmitting} required />
          </label>
          <label className="block text-sm font-medium" htmlFor="password">Password
            <input id="password" className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2.5" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} disabled={isSubmitting} required />
          </label>
          {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-destructive" role="alert">{error}</p>}
          <button className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:opacity-60" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}
