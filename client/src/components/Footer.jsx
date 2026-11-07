import Link from "next/link";
import Logo from "./Logo";

export default function Footer() {
  return (
    <footer className="border-t border-[var(--line)] bg-[var(--surface)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-6 py-10 md:flex-row md:items-center md:justify-between">
        <div>
          <Logo />
          <p className="mt-3 max-w-xs text-sm leading-6 text-[var(--muted)]">Your documents. Your knowledge. One intelligent conversation.</p>
        </div>
        <nav className="flex gap-5 text-sm text-[var(--muted)]">
          <Link className="hover:text-[var(--foreground)]" href="/about">About</Link>
          <Link className="hover:text-[var(--foreground)]" href="/contact">Contact us</Link>
          <Link className="hover:text-[var(--foreground)]" href="/dashboard">Workspace</Link>
        </nav>
      </div>
      <div className="border-t border-[var(--line)] px-6 py-4 text-center text-xs text-[var(--muted)]">© {new Date().getFullYear()} RAGLens. Built for evidence-led work.</div>
    </footer>
  );
}
