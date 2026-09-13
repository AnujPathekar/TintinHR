"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/Logo";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("employee@tintinhr.demo");
  const [password, setPassword] = useState("TintinHR@123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault(); setLoading(true); setError("");
    try {
      const response = await fetch(`${API_URL}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password }) });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Unable to sign in");
      localStorage.setItem("access_token", body.access_token); localStorage.setItem("refresh_token", body.refresh_token);
      router.replace("/");
    } catch (err) { setError(err instanceof Error ? err.message : "Unable to sign in"); }
    finally { setLoading(false); }
  }
  return (
    <main className="grid min-h-screen lg:grid-cols-2">
      <section className="hidden bg-ink p-14 text-white lg:flex lg:flex-col lg:justify-between">
        <Logo />
        <div><div className="mb-5 inline-flex rounded-full border border-white/20 px-4 py-2 text-xs uppercase tracking-widest text-lime">Secure people intelligence</div><h1 className="max-w-xl text-5xl font-black leading-tight">Answers grounded in your company&apos;s truth.</h1><p className="mt-5 max-w-lg text-lg leading-8 text-slate-300">Policy knowledge and personal HR data, connected safely with role-aware retrieval and verifiable sources.</p></div>
        <p className="text-sm text-slate-400">Built for trustworthy employee support.</p>
      </section>
      <section className="grid place-items-center bg-white p-8">
        <form onSubmit={submit} className="w-full max-w-md">
          <div className="mb-10 lg:hidden"><Logo /></div>
          <p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-700">Welcome back</p><h2 className="mt-2 text-3xl font-black">Sign in to TintinHR</h2><p className="mt-3 text-slate-500">Use your employee account to continue.</p>
          <label className="mt-8 block text-sm font-bold">Work email<input className="focus-ring mt-2 w-full rounded-xl border border-slate-300 px-4 py-3" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
          <label className="mt-5 block text-sm font-bold">Password<input className="focus-ring mt-2 w-full rounded-xl border border-slate-300 px-4 py-3" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
          {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
          <button disabled={loading} className="focus-ring mt-7 w-full rounded-xl bg-ink px-5 py-3 font-bold text-white hover:bg-slate-800 disabled:opacity-50">{loading ? "Signing in…" : "Sign in"}</button>
          <p className="mt-5 text-xs leading-5 text-slate-400">Demo credentials are prefilled. Use HR or Admin demo accounts to manage the knowledge base.</p>
        </form>
      </section>
    </main>
  );
}

