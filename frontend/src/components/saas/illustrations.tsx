type IconProps = {
  className?: string;
};

const base = "h-10 w-10";

export function IconScrape({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <rect x="4" y="8" width="32" height="24" rx="3" stroke="currentColor" strokeWidth="1.5" className="text-teal-600 dark:text-teal-400" />
      <path d="M12 16h16M12 21h10M12 26h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-slate-400" />
      <circle cx="30" cy="12" r="4" fill="#0D9488" opacity="0.2" />
      <path d="M28 12l1.5 1.5L32 11" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconDynamic({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <rect x="6" y="10" width="28" height="20" rx="2" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <path d="M14 20c2-4 4-4 6 0s4 4 6 0" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="20" cy="28" r="2" fill="#0D9488" />
      <path d="M20 24v2" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function IconJs({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <rect x="8" y="8" width="24" height="24" rx="4" fill="#0D9488" fillOpacity="0.12" />
      <path d="M16 26v-8h2.5c2 0 3.5 1 3.5 3s-1.5 3-3.5 3H16z" stroke="#0D9488" strokeWidth="1.5" strokeLinejoin="round" />
      <path d="M24 18c2.5 0 4 1.2 4 3.2 0 2.5-2 3.3-3.5 3.6V26" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function IconCaptcha({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <rect x="6" y="12" width="28" height="16" rx="2" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <path d="M10 20h6M24 20h6" stroke="#0D9488" strokeWidth="2" strokeLinecap="round" />
      <circle cx="20" cy="20" r="3" stroke="#0D9488" strokeWidth="1.5" />
      <path d="M12 8l4 4M28 8l-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-slate-500" />
    </svg>
  );
}

export function IconAi({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <circle cx="20" cy="20" r="12" stroke="#0D9488" strokeWidth="1.5" />
      <circle cx="20" cy="20" r="4" fill="#0D9488" fillOpacity="0.3" />
      <path d="M20 8v4M20 28v4M8 20h4M28 20h4" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M11.5 11.5l2.8 2.8M25.7 25.7l2.8 2.8M28.5 11.5l-2.8 2.8M14.3 25.7l-2.8 2.8" stroke="currentColor" strokeWidth="1" className="text-slate-400" />
    </svg>
  );
}

export function IconSchedule({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <circle cx="20" cy="22" r="10" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <path d="M20 16v6l4 2" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M14 8h12" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="14" cy="8" r="1.5" fill="#0D9488" />
      <circle cx="26" cy="8" r="1.5" fill="#0D9488" />
    </svg>
  );
}

export function IconCloud({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <path
        d="M12 28h18a6 6 0 000-12 8 8 0 00-15.2-2.4A5 5 0 0012 28z"
        stroke="#0D9488"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M18 24l2 2 4-4" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function IconProxy({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <rect x="4" y="14" width="10" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <rect x="26" y="14" width="10" height="12" rx="2" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <rect x="15" y="10" width="10" height="20" rx="2" fill="#0D9488" fillOpacity="0.15" stroke="#0D9488" strokeWidth="1.5" />
      <path d="M14 20h4M22 20h4" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export function IconApi({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <path d="M8 20h6l3-6 3 12 3-6h6" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="6" y="28" width="28" height="4" rx="1" fill="#0D9488" fillOpacity="0.15" />
      <path d="M10 30h20" stroke="#0D9488" strokeWidth="1" strokeLinecap="round" opacity="0.5" />
    </svg>
  );
}

export function IconExport({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <path d="M20 8v16" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M14 14l6-6 6 6" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="8" y="24" width="24" height="8" rx="2" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <path d="M14 28h12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-slate-400" />
    </svg>
  );
}

export function IconExtension({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <rect x="8" y="8" width="24" height="24" rx="4" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <path d="M16 20h8M20 16v8" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="28" cy="12" r="4" fill="#0D9488" />
    </svg>
  );
}

export function IconTeam({ className = base }: IconProps) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} aria-hidden>
      <circle cx="16" cy="16" r="5" stroke="#0D9488" strokeWidth="1.5" />
      <circle cx="26" cy="18" r="4" stroke="currentColor" strokeWidth="1.5" className="text-slate-400" />
      <path d="M8 30c0-4 3.5-7 8-7s8 3 8 7" stroke="#0D9488" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M26 26c2.5 0 5 1.5 5 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" className="text-slate-400" />
    </svg>
  );
}

export function BrowserChrome({
  children,
  url = "https://example.com/products",
  className = "",
}: {
  children: React.ReactNode;
  url?: string;
  className?: string;
}) {
  return (
    <div
      className={`overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card dark:border-slate-700 dark:bg-slate-900 ${className}`}
    >
      <div className="flex items-center gap-2 border-b border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-800/80">
        <div className="flex gap-1.5" aria-hidden>
          <span className="h-2.5 w-2.5 rounded-full bg-red-400/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-amber-400/80" />
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-400/80" />
        </div>
        <div className="ml-2 flex-1 truncate rounded-md border border-slate-200 bg-white px-3 py-1 font-mono text-[11px] text-slate-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-400">
          {url}
        </div>
      </div>
      {children}
    </div>
  );
}
