"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { ArrowUpIcon, DocumentMagnifyingGlassIcon, SparklesIcon } from "@heroicons/react/24/outline";
import { AppShell } from "@/components/AppShell";
import { api } from "@/lib/api";
import type { ChatMessage, Citation } from "@/lib/types";

const welcome: ChatMessage = { id: "welcome", role: "assistant", content: "Hi! I’m Tintin, your HR assistant. Ask about company policies, your leave balance, or how a policy applies to you. I’ll cite the source whenever I use policy documents." };

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([welcome]);
  const [question, setQuestion] = useState("");
  const [conversationId, setConversationId] = useState<string>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setQuestion(new URLSearchParams(window.location.search).get("q") || "");
  }, []);
  useEffect(() => bottom.current?.scrollIntoView({ behavior: "smooth" }), [messages, loading]);
  async function send(event: FormEvent) {
    event.preventDefault(); const text = question.trim(); if (!text || loading) return;
    setQuestion(""); setError(""); setLoading(true);
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };
    setMessages((current) => [...current, userMessage]);
    try {
      const response = await api<{ conversation_id: string; message_id: string; answer: string; citations: Citation[] }>("/chat", { method: "POST", body: JSON.stringify({ message: text, conversation_id: conversationId }) });
      setConversationId(response.conversation_id);
      setMessages((current) => [...current, { id: response.message_id, role: "assistant", content: response.answer, citations: response.citations }]);
    } catch (err) { setError(err instanceof Error ? err.message : "The assistant is unavailable"); }
    finally { setLoading(false); }
  }
  return <AppShell><div className="mx-auto flex h-[calc(100vh-4rem)] max-w-4xl flex-col">
    <header className="mb-5"><p className="text-sm font-bold uppercase tracking-[0.18em] text-emerald-700">Grounded HR intelligence</p><h1 className="mt-1 text-3xl font-black">Ask Tintin</h1></header>
    <section className="card flex-1 overflow-y-auto p-6">
      <div className="space-y-6">{messages.map((message) => <MessageBubble key={message.id} message={message} />)}
      {loading && <div className="flex items-center gap-3 text-sm text-slate-500"><div className="grid h-8 w-8 place-items-center rounded-full bg-lime"><SparklesIcon className="h-4 w-4 text-ink" /></div><span className="animate-pulse">Searching authorized sources and checking the answer…</span></div>}
      {error && <div className="rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</div>}<div ref={bottom} /></div>
    </section>
    <form onSubmit={send} className="mt-4 flex gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-lg"><textarea rows={1} value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); e.currentTarget.form?.requestSubmit(); } }} placeholder="Ask about leave, benefits, WFH or your HR data…" className="max-h-32 flex-1 resize-none px-3 py-2 focus:outline-none" /><button disabled={!question.trim() || loading} aria-label="Send question" className="focus-ring grid h-11 w-11 place-items-center rounded-xl bg-ink text-white disabled:opacity-40"><ArrowUpIcon className="h-5 w-5" /></button></form>
    <p className="mt-2 text-center text-xs text-slate-400">TintinHR can make mistakes. Verify sensitive decisions with HR and the cited policy.</p>
  </div></AppShell>;
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const assistant = message.role === "assistant";
  return <div className={`flex ${assistant ? "justify-start" : "justify-end"}`}><div className={`max-w-[85%] ${assistant ? "" : "rounded-2xl rounded-br-sm bg-ink px-5 py-3 text-white"}`}>
    {assistant && <div className="mb-2 flex items-center gap-2 text-xs font-black uppercase tracking-widest text-emerald-700"><SparklesIcon className="h-4 w-4" />Tintin</div>}
    <div className={`prose prose-sm max-w-none leading-7 ${assistant ? "text-slate-700" : "text-white"}`}><ReactMarkdown>{message.content}</ReactMarkdown></div>
    {!!message.citations?.length && <div className="mt-4 space-y-2 border-t border-slate-100 pt-3"><p className="text-xs font-black uppercase tracking-widest text-slate-400">Sources</p>{message.citations.map((source) => <details key={source.chunk_id} className="rounded-lg bg-slate-50 p-3 text-sm"><summary className="cursor-pointer list-none font-bold text-ink"><span className="mr-2 inline-grid h-5 w-5 place-items-center rounded bg-lime text-[11px]">{source.index}</span>{source.title} · Page {source.page_number || "N/A"}</summary><p className="mt-2 border-l-2 border-lime pl-3 text-xs leading-5 text-slate-500">{source.quote}…</p></details>)}</div>}
  </div></div>;
}
