export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <div className="grid h-10 w-10 place-items-center rounded-xl bg-lime font-black text-ink shadow-sm">T</div>
      {!compact && <div><div className="text-lg font-black tracking-tight">TintinHR</div><div className="text-[10px] uppercase tracking-[0.22em] text-slate-500">People intelligence</div></div>}
    </div>
  );
}

