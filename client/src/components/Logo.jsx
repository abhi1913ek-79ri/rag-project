import { ScanSearch } from "lucide-react";

export default function Logo({ light = false }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="grid h-9 w-9 place-items-center rounded-xl bg-[var(--accent)] text-white shadow-lg shadow-violet-500/20">
        <ScanSearch size={19} strokeWidth={2.2} />
      </span>
      <span className={`text-lg font-bold tracking-tight ${light ? "text-white" : ""}`}>RAG<span className="text-[var(--accent)]">Lens</span></span>
    </div>
  );
}

export function LogoMark() {
  return (
    <span className="grid h-9 w-9 place-items-center rounded-xl bg-[var(--accent)] text-white shadow-lg shadow-violet-500/20">
      <ScanSearch size={19} strokeWidth={2.2} />
    </span>
  );
}
