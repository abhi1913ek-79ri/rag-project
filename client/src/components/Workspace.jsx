"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { BookOpen, FileText, Home, LayoutDashboard, MessageSquare, Moon, PanelLeftClose, Plus, RefreshCw, Send, Sparkles, Sun, Trash2, Upload, X } from "lucide-react";
import Logo, { LogoMark } from "./Logo";
import { documentsApi } from "@/lib/api/client";

const verdictStyles = {
  SUPPORTED: "bg-emerald-500/10 text-emerald-600",
  CONTRADICTED: "bg-rose-500/10 text-rose-600",
  NOT_SUPPORTED: "bg-amber-500/10 text-amber-600",
  UNCERTAIN: "bg-zinc-500/10 text-zinc-500"
};

function Citation({ citation, onSelect }) {
  return (
    <button onClick={() => onSelect(citation)} className="group flex w-full items-center gap-3 rounded-xl border border-[var(--line)] bg-[var(--surface-muted)] p-3 text-left transition hover:border-[var(--accent)]">
      <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-[var(--accent-soft)] text-xs font-bold text-[var(--accent)]">{citation.key}</span>
      <span className="min-w-0 flex-1"><strong className="block truncate text-xs">{citation.filename}</strong><small className="text-[var(--muted)]">Page {citation.page} · {citation.chunk_id}</small></span>
      <span className="text-[10px] text-[var(--muted)]">{citation.similarity != null ? Number(citation.similarity).toFixed(2) : "—"}</span>
    </button>
  );
}

function getVerdictCounts(result) {
  const claims = result?.claim_audit || [];
  const counts = {
    SUPPORTED: 0,
    CONTRADICTED: 0,
    NOT_SUPPORTED: 0,
    UNCERTAIN: 0
  };

  claims.forEach((claim) => {
    const verdict = String(claim.overall_verdict || "UNCERTAIN").toUpperCase();
    if (Object.prototype.hasOwnProperty.call(counts, verdict)) counts[verdict] += 1;
    else counts.UNCERTAIN += 1;
  });

  if (claims.length > 0) return counts;

  const summary = result?.audit_summary || {};
  return {
    SUPPORTED: Number(summary.SUPPORTED ?? summary.supported ?? 0),
    CONTRADICTED: Number(summary.CONTRADICTED ?? summary.contradicted ?? summary.conflicting ?? 0),
    NOT_SUPPORTED: Number(summary.NOT_SUPPORTED ?? summary.not_supported ?? 0),
    UNCERTAIN: Number(summary.UNCERTAIN ?? summary.uncertain ?? 0)
  };
}

function AuditPanel({ result }) {
  const claims = result?.claim_audit || [];
  const counts = getVerdictCounts(result);
  return (
    <aside className="hidden w-[310px] shrink-0 border-l border-[var(--line)] p-6 xl:block">
      <p className="text-[10px] font-bold uppercase tracking-[.18em] text-[var(--accent)]">Claim audit</p>
      <h2 className="mt-1 text-lg font-semibold">Trust, not guesswork</h2>
      {result ? <><div className="mt-5 grid grid-cols-2 gap-2">{["SUPPORTED", "CONTRADICTED", "NOT_SUPPORTED", "UNCERTAIN"].map((item) => <div key={item} className="rounded-xl bg-[var(--surface-muted)] p-3"><strong className="block text-xl">{counts[item] || 0}</strong><span className={`text-[9px] font-bold ${verdictStyles[item]?.split(" ")[1]}`}>{item.replace("_", " ")}</span></div>)}</div><div className="mt-5 space-y-2">{claims.length ? claims.map((claim, index) => <details key={`${claim.claim}-${index}`} className="rounded-xl border border-[var(--line)] p-3"><summary className="cursor-pointer text-xs font-medium leading-5"><span className={`mr-2 inline-flex rounded-full px-2 py-0.5 text-[9px] font-bold ${verdictStyles[claim.overall_verdict] || verdictStyles.UNCERTAIN}`}>{claim.overall_verdict}</span>{claim.claim}</summary><div className="mt-3 border-t border-[var(--line)] pt-3 text-xs text-[var(--muted)]">{(claim.verification || []).map((item, itemIndex) => <p key={itemIndex} className="mb-2"><strong>{item.citation || "No citation"}</strong> — {item.reason}</p>)}</div></details>) : <p className="text-sm text-[var(--muted)]">No claims were extracted from this answer.</p>}</div></> : <div className="mt-6 rounded-2xl bg-[var(--surface-muted)] p-4 text-sm leading-6 text-[var(--muted)]">Ask a question to inspect retrieved sources, citation coverage, and claim-level support.</div>}
    </aside>
  );
}

function SummarySection({ summary, loading, error, onRegenerate }) {
  if (loading) {
    return <section className="mt-5 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-sm md:p-6">
      <div className="flex items-center gap-3"><BookOpen size={18} className="text-[var(--accent)]" /><div><p className="text-[10px] font-bold uppercase tracking-[.18em] text-[var(--accent)]">Document summary</p><h2 className="mt-1 text-lg font-semibold">Reading your source…</h2></div></div>
      <div className="mt-5 animate-pulse space-y-3"><div className="h-3 w-5/6 rounded bg-[var(--surface-muted)]" /><div className="h-3 w-full rounded bg-[var(--surface-muted)]" /><div className="h-3 w-2/3 rounded bg-[var(--surface-muted)]" /></div>
    </section>;
  }
  if (error) {
    return <section className="mt-5 rounded-2xl border border-rose-500/20 bg-[var(--surface)] p-5 shadow-sm md:p-6"><p className="text-[10px] font-bold uppercase tracking-[.18em] text-rose-600">Document summary</p><p className="mt-2 text-sm text-[var(--muted)]">{error}</p><button onClick={onRegenerate} className="mt-4 flex items-center gap-2 rounded-xl bg-[var(--accent)] px-3 py-2 text-xs font-bold text-white"><RefreshCw size={14} /> Try again</button></section>;
  }
  if (!summary) return null;
  return <section className="mt-5 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-sm md:p-6">
    <div className="flex items-start justify-between gap-4"><div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]"><BookOpen size={18} /></span><div><p className="text-[10px] font-bold uppercase tracking-[.18em] text-[var(--accent)]">Document summary</p><h2 className="mt-1 text-lg font-semibold">Understand your source</h2></div></div><button onClick={onRegenerate} title="Regenerate summary" className="rounded-xl border border-[var(--line)] p-2 text-[var(--muted)] hover:bg-[var(--surface-muted)]"><RefreshCw size={15} /></button></div>
    <div className="mt-5 rounded-xl bg-[var(--surface-muted)] p-4"><p className="text-[10px] font-bold uppercase tracking-[.16em] text-[var(--accent)]">Overview</p><p className="mt-2 text-sm leading-7">{summary.overview}</p></div>
    <div className="mt-4 grid gap-4 md:grid-cols-2"><div><p className="text-[10px] font-bold uppercase tracking-[.16em] text-[var(--accent)]">Short summary</p><p className="mt-2 text-sm leading-6 text-[var(--muted)]">{summary.short_summary}</p></div><div><p className="text-[10px] font-bold uppercase tracking-[.16em] text-[var(--accent)]">Key points</p><ul className="mt-2 space-y-2 text-sm leading-6 text-[var(--muted)]">{(summary.key_points || []).map((item, index) => <li key={index} className="flex gap-2"><span className="text-[var(--accent)]">•</span><span>{item.point}<SourceRefs refs={item.source_refs} /></span></li>)}</ul></div></div>
    <details className="mt-5 rounded-xl border border-[var(--line)] p-4"><summary className="cursor-pointer text-sm font-semibold">Detailed and section-wise summary</summary><div className="mt-4 space-y-4">{(summary.detailed_summary || []).map((item, index) => <div key={index}><h3 className="text-sm font-semibold">{item.heading}</h3><p className="mt-1 text-sm leading-6 text-[var(--muted)]">{item.summary}</p><SourceRefs refs={item.source_refs} /></div>)}</div></details>
    <details className="mt-3 rounded-xl border border-[var(--line)] p-4"><summary className="cursor-pointer text-sm font-semibold">Important entities and terms</summary><div className="mt-4 grid gap-2 sm:grid-cols-2">{(summary.entities || []).map((item, index) => <div key={index} className="rounded-lg bg-[var(--surface-muted)] p-3"><strong className="block text-sm">{item.name}</strong><span className="text-[10px] font-bold uppercase text-[var(--accent)]">{item.type}</span><p className="mt-1 text-xs leading-5 text-[var(--muted)]">{item.context}</p><SourceRefs refs={item.source_refs} /></div>)}</div></details>
    <div className="mt-4 border-t border-[var(--line)] pt-4"><p className="text-[10px] font-bold uppercase tracking-[.16em] text-[var(--accent)]">Source references</p><div className="mt-2 flex flex-wrap gap-2">{(summary.source_references || []).map((source, index) => <span key={`${source.chunk_id}-${index}`} className="rounded-full bg-[var(--surface-muted)] px-2.5 py-1 text-[10px] text-[var(--muted)]">{source.filename} · Page {source.page} · {source.chunk_id}</span>)}</div></div>
  </section>;
}

function SourceRefs({ refs }) {
  if (!refs?.length) return <span className="ml-2 text-[10px] text-[var(--muted)]">Source reference unavailable</span>;
  return <span className="ml-2 text-[10px] text-[var(--muted)]">Page {refs.map((ref) => ref.page).join(", ")}</span>;
}

function AnswerContent({ answer }) {
  const lines = String(answer || "No answer returned.")
    .split(/\r?\n/)
    .map((line) => line.replace(/^\s*(?:[-*+]|\d+[.)])\s+/, "").replace(/\*\*/g, "").trim())
    .filter(Boolean);

  return (
    <ul className="mt-4 list-disc space-y-3 pl-5 text-sm leading-7 marker:text-[var(--accent)]">
      {lines.map((line, index) => <li key={`${line}-${index}`}>{line}</li>)}
    </ul>
  );
}

export default function Workspace() {
  const [documents, setDocuments] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [source, setSource] = useState(null);
  const [loading, setLoading] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dark, setDark] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [summary, setSummary] = useState(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [summaryError, setSummaryError] = useState("");
  const inputRef = useRef(null);

  useEffect(() => {
    const stored = localStorage.getItem("raglens-theme");
    setDark(stored === "dark");
    documentsApi.list().then((data) => { setDocuments(data.documents || []); if (data.documents?.[0]) setSelectedId(data.documents[0].document_id); }).catch((e) => setError(e.message));
  }, []);
  useEffect(() => { document.documentElement.dataset.theme = dark ? "dark" : "light"; localStorage.setItem("raglens-theme", dark ? "dark" : "light"); }, [dark]);
  useEffect(() => {
    if (!selectedId) return;
    setSummary(null);
    setSummaryError("");
    setSummaryLoading(true);
    documentsApi.summarize(selectedId).then(setSummary).catch((e) => setSummaryError(e.message)).finally(() => setSummaryLoading(false));
  }, [selectedId]);

  async function upload(file) {
    if (!file || file.type !== "application/pdf" || file.size > 10 * 1024 * 1024) { setError("Choose a PDF file no larger than 10 MB."); return; }
    setBusy(true); setError("");
    try { const data = await documentsApi.upload(file); const next = await documentsApi.list(); setDocuments(next.documents || []); setSelectedId(data.document_id); } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function ask(event) {
    event.preventDefault();
    if (!query.trim() || !selectedId || loading) return;
    setLoading(true); setError(""); setResult(null);
    try { setResult(await documentsApi.audit(query.trim(), selectedId)); } catch (e) { setError(e.message); } finally { setLoading(false); }
  }
  async function remove(id) {
    const doc = documents.find((item) => item.document_id === id);
    if (!doc || !window.confirm(`Delete "${doc.filename}"?`)) return;
    try { await documentsApi.remove(id); const next = documents.filter((item) => item.document_id !== id); setDocuments(next); if (selectedId === id) { setSelectedId(next[0]?.document_id || ""); setResult(null); setSummary(null); } } catch (e) { setError(e.message); }
  }
  async function regenerateSummary() {
    if (!selectedId || summaryLoading) return;
    setSummaryLoading(true); setSummaryError("");
    try { setSummary(await documentsApi.summarize(selectedId, true)); } catch (e) { setSummaryError(e.message); } finally { setSummaryLoading(false); }
  }
  const selected = documents.find((item) => item.document_id === selectedId);
  const citations = Object.entries(result?.citations || {}).map(([key, value]) => ({ key, ...value }));

  return <div className="flex min-h-screen bg-[var(--background)] text-[var(--foreground)]">
    <aside className={`${collapsed ? "w-[76px]" : "w-[248px]"} hidden shrink-0 flex-col border-r border-[var(--line)] bg-[var(--surface)] p-4 transition-all md:flex`}>
      <div className={`flex items-center ${collapsed ? "justify-center" : "justify-between"}`}>
        {collapsed ? <button onClick={() => setCollapsed(false)} aria-label="Expand sidebar" title="Expand sidebar" className="rounded-xl p-1 transition hover:bg-[var(--surface-muted)]"><LogoMark /></button> : <><Logo /><button onClick={() => setCollapsed(true)} aria-label="Collapse sidebar" title="Collapse sidebar" className="rounded-lg p-2 text-[var(--muted)] hover:bg-[var(--surface-muted)]"><PanelLeftClose size={17} /></button></>}
      </div>
      {!collapsed && <><button onClick={() => { setResult(null); setQuery(""); inputRef.current?.focus(); }} className="mt-8 flex items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-3 py-2.5 text-sm font-semibold text-white shadow-lg shadow-violet-500/20"><Plus size={16} /> New chat</button><nav className="mt-8 space-y-1"><Link href="/dashboard" className="flex items-center gap-3 rounded-xl bg-[var(--accent-soft)] px-3 py-2.5 text-sm font-semibold text-[var(--accent)]"><LayoutDashboard size={17} /> Workspace</Link><Link href="#documents" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-[var(--muted)] hover:bg-[var(--surface-muted)]"><FileText size={17} /> Documents</Link><Link href="#chat" className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-[var(--muted)] hover:bg-[var(--surface-muted)]"><MessageSquare size={17} /> Chat</Link></nav><div className="mt-auto rounded-2xl bg-[var(--surface-muted)] p-4"><Sparkles size={16} className="text-[var(--accent)]" /><p className="mt-3 text-xs font-semibold">Grounded by design</p><p className="mt-1 text-[11px] leading-5 text-[var(--muted)]">Answers stay connected to retrieved evidence.</p></div></>}
    </aside>
    <main className="flex min-w-0 flex-1 flex-col">
      <header className="flex items-center justify-between border-b border-[var(--line)] px-5 py-4 md:px-10"><div><p className="text-[10px] font-bold uppercase tracking-[.2em] text-[var(--accent)]">Knowledge workspace</p><h1 className="mt-1 text-xl font-bold tracking-tight md:text-2xl">Ask your documents</h1></div><div className="flex items-center gap-2">{error && <button onClick={() => setError("")} className="mr-2 flex max-w-[260px] items-center gap-1 truncate rounded-lg bg-rose-500/10 px-2 py-1 text-xs text-rose-600"><X size={13} /> {error}</button>}<Link href="/" className="flex items-center gap-2 rounded-xl border border-[var(--line)] px-3 py-2.5 text-xs font-semibold text-[var(--muted)] hover:bg-[var(--surface-muted)]" title="Go to home"><Home size={16} /> <span className="hidden sm:inline">Home</span></Link><button onClick={() => setDark(!dark)} className="rounded-xl border border-[var(--line)] p-2.5 text-[var(--muted)] hover:bg-[var(--surface-muted)]">{dark ? <Sun size={17} /> : <Moon size={17} />}</button></div></header>
      <div className="flex min-h-0 flex-1"><div className="min-w-0 flex-1 px-5 py-6 md:px-10"><div className="mx-auto max-w-3xl">
        <section id="documents" className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-sm md:p-6"><div className="flex items-start justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.18em] text-[var(--accent)]">Document library</p><h2 className="mt-1 text-lg font-semibold">Bring your sources</h2></div><span className="rounded-full bg-[var(--surface-muted)] px-2.5 py-1 text-xs text-[var(--muted)]">{documents.length} {documents.length === 1 ? "document" : "documents"}</span></div><label className="mt-5 flex cursor-pointer flex-col items-center justify-center rounded-2xl border border-dashed border-[var(--line)] bg-[var(--surface-muted)] px-4 py-6 text-center transition hover:border-[var(--accent)]"><input type="file" accept="application/pdf" className="hidden" onChange={(e) => upload(e.target.files?.[0])} /><span className="grid h-10 w-10 place-items-center rounded-full bg-[var(--accent-soft)] text-[var(--accent)]"><Upload size={18} /></span><strong className="mt-3 text-sm">{busy ? "Uploading…" : "Drop a PDF here or browse"}</strong><span className="mt-1 text-xs text-[var(--muted)]">PDF only · maximum 10 MB</span></label>{documents.length > 0 && <div className="mt-4 space-y-1">{documents.map((doc) => <div key={doc.document_id} className={`flex items-center gap-2 rounded-xl border px-3 py-2 ${doc.document_id === selectedId ? "border-[var(--accent)] bg-[var(--accent-soft)]" : "border-transparent hover:bg-[var(--surface-muted)]"}`}><button onClick={() => { setSelectedId(doc.document_id); setResult(null); }} className="flex min-w-0 flex-1 items-center gap-3 text-left"><span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-rose-500/10 text-[10px] font-bold text-rose-500">PDF</span><span className="truncate text-sm">{doc.filename}</span></button><button onClick={() => remove(doc.document_id)} className="rounded-lg p-2 text-[var(--muted)] hover:bg-rose-500/10 hover:text-rose-600"><Trash2 size={15} /></button></div>)}</div>}</section>
        <SummarySection summary={summary} loading={summaryLoading} error={summaryError} onRegenerate={regenerateSummary} />
        <section id="chat" className="mt-5 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-5 shadow-sm md:p-6"><div className="flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.18em] text-[var(--accent)]">RAG assistant</p><h2 className="mt-1 text-lg font-semibold">Explore a source</h2></div>{selected && <span className="max-w-[190px] truncate rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-xs text-[var(--accent)]">{selected.filename}</span>}</div><form onSubmit={ask} className="mt-5"><textarea ref={inputRef} value={query} onChange={(e) => setQuery(e.target.value)} disabled={!selected || loading} rows={3} placeholder={selected ? "Ask a question grounded in this document…" : "Select a document before asking a question…"} className="w-full resize-y rounded-xl border border-[var(--line)] bg-[var(--surface-muted)] p-3 text-sm outline-none transition focus:border-[var(--accent)]" /><div className="mt-3 flex items-center justify-between gap-3"><span className="text-[11px] text-[var(--muted)]">Answers include citations and claim verification.</span><button disabled={!selected || !query.trim() || loading} className="flex items-center gap-2 rounded-xl bg-[var(--accent)] px-4 py-2.5 text-xs font-bold text-white disabled:cursor-not-allowed disabled:opacity-40">{loading ? "Analyzing…" : "Ask document"}<Send size={14} /></button></div></form>{loading && <div className="mt-6 animate-pulse rounded-xl bg-[var(--surface-muted)] p-5 text-sm text-[var(--muted)]">Retrieving relevant passages and verifying claims…</div>}{result && <div className="mt-6 border-t border-[var(--line)] pt-5"><div className="flex items-center gap-2 text-xs text-[var(--muted)]"><span className="h-2 w-2 rounded-full bg-emerald-500" /> Generated answer</div><AnswerContent answer={result.answer} />{citations.length > 0 && <div className="mt-5 space-y-2">{citations.map((citation) => <Citation key={citation.key} citation={citation} onSelect={setSource} />)}</div>}{source && <div className="mt-3 rounded-xl border-l-4 border-[var(--accent)] bg-[var(--accent-soft)] p-4"><div className="flex items-start justify-between gap-3"><div><strong className="text-xs">{source.key} · {source.filename}</strong><p className="mt-1 text-[11px] text-[var(--muted)]">Page {source.page} · {source.chunk_id}</p></div><button onClick={() => setSource(null)}><X size={14} /></button></div><p className="mt-3 max-h-40 overflow-auto whitespace-pre-wrap text-xs leading-5">{source.text || "Source text was not returned by the service."}</p></div>}</div>}</section>
      </div></div><AuditPanel result={result} /></div>
    </main>
  </div>;
}
