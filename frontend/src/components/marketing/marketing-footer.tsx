import Link from "next/link";

const COLS = [
  {
    title: "Product",
    links: [
      { href: "#features", label: "Features" },
      { href: "#pricing", label: "Pricing" },
      { href: "#how", label: "Docs" },
      { href: "/intelligence", label: "API" },
    ],
  },
  {
    title: "Company",
    links: [
      { href: "#", label: "Blog" },
      { href: "#", label: "GitHub" },
      { href: "mailto:hello@extractai.local", label: "Contact" },
    ],
  },
  {
    title: "Legal",
    links: [
      { href: "#", label: "Privacy" },
      { href: "#", label: "Terms" },
    ],
  },
];

export function MarketingFooter() {
  return (
    <footer className="border-t border-slate-200 px-5 py-16 md:px-6">
      <div className="mx-auto grid max-w-6xl gap-10 md:grid-cols-[1.4fr_1fr_1fr_1fr]">
        <div>
          <Link href="/" className="font-display text-2xl text-slate-900">
            Extract<span className="text-accent">AI</span>
          </Link>
          <p className="mt-3 max-w-xs text-sm text-slate-700">
            Understand any website. Not just scrape it.
          </p>
        </div>
        {COLS.map((col) => (
          <div key={col.title}>
            <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-slate-700">{col.title}</p>
            <ul className="mt-4 space-y-2 text-sm text-slate-600">
              {col.links.map((l) => (
                <li key={l.label}>
                  <a href={l.href} className="transition hover:text-slate-950">
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="mx-auto mt-12 flex max-w-6xl flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-8 text-xs text-slate-600">
        <p>© {new Date().getFullYear()} ExtractAI</p>
        <div className="flex gap-4">
          <span>X</span>
          <span>LinkedIn</span>
          <span>GitHub</span>
        </div>
      </div>
    </footer>
  );
}
