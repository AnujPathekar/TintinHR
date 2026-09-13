"use client";

import { ChatBubbleLeftRightIcon, DocumentTextIcon, HomeIcon, ArrowRightStartOnRectangleIcon } from "@heroicons/react/24/outline";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { logout, parseSession } from "@/lib/auth";
import type { Session } from "@/lib/types";
import { Logo } from "./Logo";

const links = [
  { href: "/", label: "Overview", icon: HomeIcon, roles: ["employee", "manager", "hr", "admin"] },
  { href: "/chat", label: "AI Assistant", icon: ChatBubbleLeftRightIcon, roles: ["employee", "manager", "hr", "admin"] },
  { href: "/admin/documents", label: "Knowledge Base", icon: DocumentTextIcon, roles: ["hr", "admin"] },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [session, setSession] = useState<Session | null>(null);
  useEffect(() => {
    const parsed = parseSession(localStorage.getItem("access_token"));
    if (!parsed) router.replace("/login"); else setSession(parsed);
  }, [router]);
  if (!session) return <div className="grid min-h-screen place-items-center text-slate-500">Loading secure workspace…</div>;
  return (
    <div className="min-h-screen bg-mist text-ink">
      <aside className="fixed inset-y-0 left-0 z-20 w-64 border-r border-slate-200 bg-white p-5">
        <Logo />
        <nav className="mt-10 space-y-2">
          {links.filter((link) => link.roles.includes(session.role)).map((link) => {
            const active = pathname === link.href;
            return <Link key={link.href} href={link.href} className={`flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${active ? "bg-ink text-white" : "text-slate-600 hover:bg-slate-100"}`}><link.icon className="h-5 w-5" />{link.label}</Link>;
          })}
        </nav>
        <button onClick={logout} className="absolute bottom-6 left-5 flex items-center gap-3 text-sm font-semibold text-slate-500 hover:text-red-600"><ArrowRightStartOnRectangleIcon className="h-5 w-5" />Sign out</button>
      </aside>
      <main className="min-h-screen pl-64"><div className="mx-auto max-w-7xl p-8">{children}</div></main>
    </div>
  );
}

