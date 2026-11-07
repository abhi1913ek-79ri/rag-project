import Link from "next/link";
import MarketingHeader from "@/components/MarketingHeader";
import Footer from "@/components/Footer";

export default function AboutPage() {
  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <MarketingHeader />
      <section className="mx-auto max-w-3xl px-6 py-20 md:py-28">
        <p className="text-xs font-bold uppercase tracking-[.2em] text-[var(--accent)]">About RAGLens</p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight md:text-6xl">Make every answer easier to trust.</h1>
        <p className="mt-7 text-lg leading-8 text-[var(--muted)]">RAGLens turns the documents you already rely on into an intelligent, searchable workspace. Ask questions in natural language, trace answers back to source passages, and inspect how claims were verified.</p>
        <div className="mt-12 grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-6"><h2 className="font-semibold">Grounded by default</h2><p className="mt-2 text-sm leading-6 text-[var(--muted)]">Retrieval and citations stay at the center of every conversation.</p></div>
          <div className="rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-6"><h2 className="font-semibold">Built for inspection</h2><p className="mt-2 text-sm leading-6 text-[var(--muted)]">Claim-level audit results make it clear what the evidence supports.</p></div>
        </div>
        <Link href="/dashboard" className="mt-10 inline-flex rounded-xl bg-[var(--accent)] px-5 py-3 text-sm font-bold text-white">Explore the workspace</Link>
      </section>
      <Footer />
    </main>
  );
}
