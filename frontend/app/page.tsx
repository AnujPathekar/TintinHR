"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowUpRightIcon, ChatBubbleLeftRightIcon, ShieldCheckIcon, SparklesIcon } from "@heroicons/react/24/outline";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";

type Profile = { full_name: string; job_title: string; employee_code: string; location: string; role: string };
type Leave = { leave_type: string; allocated: number; used: number; pending: number; available: number };

export default function Dashboard() {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [leave, setLeave] = useState<Leave[]>([]);
  useEffect(() => { Promise.all([api<Profile>("/employees/me"), api<Leave[]>("/employees/me/leave")]).then(([p, l]) => { setProfile(p); setLeave(l); }).catch(() => undefined); }, []);
  return <AppShell>
    <header className="flex items-end justify-between"><div><p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-700">Employee workspace</p><h1 className="mt-2 text-4xl font-black">Good to see you{profile ? `, ${profile.full_name.split(" ")[0]}` : ""}.</h1><p className="mt-2 text-slate-500">Here&apos;s your people dashboard for today.</p></div><div className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-bold capitalize">{profile?.role || "Employee"}</div></header>
    <section className="mt-8 grid gap-5 md:grid-cols-3">
      {leave.map((item) => <article className="card p-6" key={item.leave_type}><p className="text-sm font-semibold text-slate-500">{item.leave_type}</p><p className="mt-3 text-4xl font-black">{item.available}</p><p className="mt-1 text-sm text-slate-500">days available of {item.allocated}</p><div className="mt-5 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-lime" style={{ width: `${Math.max(0, item.available / item.allocated * 100)}%` }} /></div></article>)}
      <article className="card flex flex-col justify-between bg-ink p-6 text-white"><SparklesIcon className="h-8 w-8 text-lime" /><div><h2 className="mt-8 text-xl font-black">Ask Tintin</h2><p className="mt-2 text-sm leading-6 text-slate-300">Get a cited answer from approved policies or check your HR data.</p><Link href="/chat" className="mt-5 inline-flex items-center gap-2 font-bold text-lime">Open assistant <ArrowUpRightIcon className="h-4 w-4" /></Link></div></article>
    </section>
    <section className="mt-8 grid gap-5 lg:grid-cols-[1.5fr_1fr]">
      <article className="card p-7"><div className="flex items-center gap-3"><ChatBubbleLeftRightIcon className="h-6 w-6 text-emerald-700" /><h2 className="text-xl font-black">Try asking</h2></div><div className="mt-5 grid gap-3 sm:grid-cols-2">{["How many casual leaves do I have left?", "Can I carry sick leave into next year?", "What is the WFH policy during probation?", "Compare my balance with policy eligibility."].map((question) => <Link href={`/chat?q=${encodeURIComponent(question)}`} key={question} className="rounded-xl border border-slate-200 p-4 text-sm font-semibold leading-6 hover:border-emerald-500 hover:bg-emerald-50">{question}</Link>)}</div></article>
      <article className="card p-7"><ShieldCheckIcon className="h-7 w-7 text-emerald-700" /><h2 className="mt-4 text-xl font-black">Access-aware by design</h2><p className="mt-3 text-sm leading-6 text-slate-500">Answers only use policies and employee data your authenticated role is allowed to access. Sources are included for policy claims.</p>{profile && <div className="mt-5 border-t border-slate-100 pt-5 text-sm"><p className="font-bold">{profile.job_title}</p><p className="mt-1 text-slate-500">{profile.employee_code} · {profile.location}</p></div>}</article>
    </section>
  </AppShell>;
}

