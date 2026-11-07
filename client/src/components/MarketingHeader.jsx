import Link from "next/link";
import Logo from "./Logo";

export default function MarketingHeader() {
  return (
    <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
      <Link href="/"><Logo /></Link>
      <div className="flex items-center gap-5 text-sm text-[var(--muted)]">
        <Link href="/about" className="hidden hover:text-[var(--foreground)] sm:block">About</Link>
        <Link href="/contact" className="hidden hover:text-[var(--foreground)] sm:block">Contact</Link>
        <Link href="/dashboard" className="rounded-xl bg-[var(--foreground)] px-4 py-2.5 font-semibold text-[var(--background)]">Open workspace</Link>
      </div>
    </nav>
  );
}
