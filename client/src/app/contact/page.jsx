import Link from "next/link";
import MarketingHeader from "@/components/MarketingHeader";
import Footer from "@/components/Footer";

export default function ContactPage() {
  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
      <MarketingHeader />
      <section className="mx-auto max-w-3xl px-6 py-20 md:py-28">
        <p className="text-xs font-bold uppercase tracking-[.2em] text-[var(--accent)]">Contact us</p>
        <h1 className="mt-4 text-4xl font-bold tracking-tight md:text-6xl">Let’s talk about your knowledge base.</h1>
        <p className="mt-7 text-lg leading-8 text-[var(--muted)]">Have feedback, questions, or an idea for making document intelligence more useful? We’d love to hear from you.</p>
        <div className="mt-10 rounded-2xl border border-[var(--line)] bg-[var(--surface)] p-6">
          <p className="text-sm text-[var(--muted)]">For product questions and feedback, email</p>
          <a href="mailto:hello@raglens.ai" className="mt-2 inline-block text-lg font-semibold text-[var(--accent)] hover:underline">hello@raglens.ai</a>
        </div>
        <Link href="/dashboard" className="mt-8 inline-flex rounded-xl border border-[var(--line)] bg-[var(--surface)] px-5 py-3 text-sm font-bold">Open workspace</Link>
      </section>
      <Footer />
    </main>
  );
}
