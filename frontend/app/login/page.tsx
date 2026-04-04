"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { login, setToken } from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const t = await login(email, password);
      setToken(t.access_token);
      router.replace("/chat");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-8">
        <div className="text-center space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">
            Financial GPT
          </h1>
          <p className="text-sm text-muted">Sign in to continue</p>
        </div>
        <form onSubmit={onSubmit} className="space-y-4">
          {error && (
            <p className="text-sm text-red-400/90 text-center">{error}</p>
          )}
          <input
            type="email"
            autoComplete="email"
            required
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            disabled={loading}
            className="w-full rounded-xl bg-surface border border-borderline px-4 py-3 text-sm text-foreground placeholder:text-muted outline-none focus:border-accent/40 transition-colors disabled:opacity-50"
          />
          <input
            type="password"
            autoComplete="current-password"
            required
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={loading}
            className="w-full rounded-xl bg-surface border border-borderline px-4 py-3 text-sm text-foreground placeholder:text-muted outline-none focus:border-accent/40 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-accent/15 text-accent border border-accent/25 py-3 text-sm font-medium hover:bg-accent/20 disabled:opacity-50 transition-colors flex items-center justify-center gap-2 min-h-[48px]"
          >
            {loading ? (
              <>
                <LoadingSpinner className="h-5 w-5" />
                <span>Signing in…</span>
              </>
            ) : (
              "Sign in"
            )}
          </button>
        </form>
        <p className="text-center text-sm text-muted">
          No account?{" "}
          <Link href="/register" className="text-accent hover:underline">
            Register
          </Link>
        </p>
      </div>
    </div>
  );
}
