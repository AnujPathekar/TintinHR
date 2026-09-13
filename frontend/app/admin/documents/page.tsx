"use client";

import { FormEvent, useEffect, useState } from "react";
import { ArrowPathIcon, ArrowUpTrayIcon, CloudArrowUpIcon, DocumentTextIcon, TrashIcon } from "@heroicons/react/24/outline";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { HRDocument } from "@/lib/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<HRDocument[]>([]); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const load = () => api<HRDocument[]>("/documents").then(setDocuments).catch((e) => setError(e.message));
  useEffect(() => { void load(); }, []);
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoading(true); setError("");
    const form = event.currentTarget; const data = new FormData(form);
    try { await api("/documents", { method: "POST", body: data }); form.reset(); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Upload failed"); }
    finally { setLoading(false); }
  }
  async function archive(id: string) { if (!confirm("Archive this document? It will stop appearing in retrieval.")) return; await api(`/documents/${id}`, { method: "DELETE" }); await load(); }
  async function replace(id: string, file?: File) {
    if (!file) return; setError("");
    const data = new FormData(); data.append("file", file);
    try { await api(`/documents/${id}/content`, { method: "PUT", body: data }); await load(); }
    catch (e) { setError(e instanceof Error ? e.message : "Replacement failed"); }
  }
  return <AppShell>
    <header><p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-700">HR administration</p><h1 className="mt-2 text-4xl font-black">Knowledge base</h1><p className="mt-2 text-slate-500">Upload approved policy sources and control who can retrieve them.</p></header>
    <section className="mt-8 grid gap-6 lg:grid-cols-[0.8fr_1.4fr]">
      <form onSubmit={upload} className="card h-fit p-6"><CloudArrowUpIcon className="h-8 w-8 text-emerald-700" /><h2 className="mt-4 text-xl font-black">Add a source</h2><p className="mt-2 text-sm leading-6 text-slate-500">PDF, DOCX, TXT or CSV up to 20 MB. Processing happens in the background.</p>
        <label className="mt-6 block text-sm font-bold">Title<input name="title" required className="focus-ring mt-2 w-full rounded-xl border border-slate-300 px-4 py-3" placeholder="2026 Leave Policy" /></label>
        <label className="mt-5 block text-sm font-bold">Audience<select name="visibility" className="focus-ring mt-2 w-full rounded-xl border border-slate-300 bg-white px-4 py-3"><option value="employee">All employees</option><option value="manager">Managers and above</option><option value="hr">HR and admins</option><option value="admin">Admins only</option><option value="public">Public</option></select></label>
        <label className="mt-5 block text-sm font-bold">File<input name="file" required type="file" accept=".pdf,.docx,.txt,.csv" className="mt-2 block w-full rounded-xl border border-dashed border-slate-300 p-4 text-sm" /></label>
        <button disabled={loading} className="focus-ring mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-ink px-5 py-3 font-bold text-white disabled:opacity-50">{loading ? <ArrowPathIcon className="h-5 w-5 animate-spin" /> : <CloudArrowUpIcon className="h-5 w-5" />}{loading ? "Uploading…" : "Upload & index"}</button>{error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
      </form>
      <div className="card overflow-hidden"><div className="flex items-center justify-between border-b border-slate-100 p-6"><div><h2 className="text-xl font-black">Approved sources</h2><p className="mt-1 text-sm text-slate-500">{documents.length} documents</p></div><button onClick={load} className="focus-ring rounded-lg border border-slate-200 p-2" aria-label="Refresh"><ArrowPathIcon className="h-5 w-5" /></button></div>
        <div className="divide-y divide-slate-100">{documents.map((document) => <div key={document.id} className="flex items-center gap-4 p-5"><div className="grid h-11 w-11 place-items-center rounded-xl bg-emerald-50 text-emerald-700"><DocumentTextIcon className="h-6 w-6" /></div><div className="min-w-0 flex-1"><p className="truncate font-bold">{document.title}</p><p className="mt-1 truncate text-xs text-slate-500">{document.filename} · v{document.current_version} · <span className="capitalize">{document.visibility}</span></p></div><span className={`rounded-full px-3 py-1 text-xs font-bold capitalize ${document.status === "active" ? "bg-emerald-50 text-emerald-700" : document.status === "failed" ? "bg-red-50 text-red-700" : "bg-amber-50 text-amber-700"}`}>{document.status}</span><label className="focus-ring cursor-pointer rounded-lg p-2 text-slate-400 hover:bg-emerald-50 hover:text-emerald-700" title="Upload a new version"><ArrowUpTrayIcon className="h-5 w-5" /><input type="file" accept=".pdf,.docx,.txt,.csv" className="hidden" onChange={(event) => { void replace(document.id, event.target.files?.[0]); event.target.value = ""; }} /></label><button onClick={() => archive(document.id)} className="focus-ring rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600" aria-label={`Archive ${document.title}`}><TrashIcon className="h-5 w-5" /></button></div>)}{!documents.length && <div className="p-10 text-center text-sm text-slate-500">No documents available for your role.</div>}</div>
      </div>
    </section>
  </AppShell>;
}
