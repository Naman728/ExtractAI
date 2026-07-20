"use client";

import { useEffect, useState, type ReactNode } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

/** Local product photos in /public/demo-products (Unsplash, free license). */
const PRODUCTS = [
  {
    id: "1",
    name: "Cedar Trail Runner",
    price: 150,
    was: 300,
    image: "/demo-products/shoe.jpg",
    tag: "Footwear",
  },
  {
    id: "2",
    name: "Atlas Shell Jacket",
    price: 150,
    was: 300,
    image: "/demo-products/jacket.jpg",
    tag: "Outerwear",
  },
  {
    id: "3",
    name: "Harbor Soft Tee",
    price: 150,
    was: 300,
    image: "/demo-products/tee.jpg",
    tag: "Basics",
  },
  {
    id: "4",
    name: "Night Hike Boot",
    price: 150,
    was: 300,
    image: "/demo-products/boot.jpg",
    tag: "Footwear",
  },
] as const;

const HERO_SHOE = "/demo-products/shoe-hero.jpg";

const TABS = ["Details", "Payment", "Delivery", "Review", "Confirm"] as const;

function ProductPhoto({
  src,
  alt,
  className = "",
}: {
  src: string;
  alt: string;
  className?: string;
}) {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      loading="lazy"
      decoding="async"
      className={`object-cover ${className}`}
      draggable={false}
    />
  );
}

function CursorDot({ x, y }: { x: string; y: string }) {
  return (
    <motion.div
      className="pointer-events-none absolute z-20 h-5 w-5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-slate-900 shadow-lg"
      style={{ left: x, top: y }}
      animate={{ scale: [1, 0.85, 1] }}
      transition={{ duration: 1.2, repeat: Infinity }}
    />
  );
}

function ProductCard({
  product,
  compact,
}: {
  product: (typeof PRODUCTS)[number];
  compact?: boolean;
}) {
  return (
    <motion.div
      layout
      whileHover={{ y: -3, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      className={`overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900 ${
        compact ? "" : ""
      }`}
    >
      <div className={`relative overflow-hidden bg-slate-100 ${compact ? "aspect-square" : "aspect-[4/3]"}`}>
        <ProductPhoto
          src={product.image}
          alt={product.name}
          className="h-full w-full transition duration-500 hover:scale-105"
        />
        <div className="absolute left-1.5 top-1.5 flex gap-1 text-[10px] font-bold">
          <span className="rounded bg-black/55 px-1.5 py-0.5 text-white/80 line-through">
            ${product.was}
          </span>
          <span className="rounded bg-teal-600 px-1.5 py-0.5 text-white">${product.price}</span>
        </div>
      </div>
      <div className={compact ? "p-2" : "p-3"}>
        <p className={`font-semibold text-slate-900 dark:text-white ${compact ? "text-[10px]" : "text-xs"}`}>
          {product.name}
        </p>
        {!compact ? (
          <p className="text-[10px] font-medium text-slate-600 dark:text-slate-400">{product.tag}</p>
        ) : null}
      </div>
    </motion.div>
  );
}

/** Demo 1 — Point & click on a product page */
function DemoPointClick() {
  const [tab, setTab] = useState(0);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) return;
    const t = setInterval(() => setTab((i) => (i + 1) % TABS.length), 1800);
    return () => clearInterval(t);
  }, [reduce]);

  const tabPositions = ["12%", "32%", "52%", "72%", "88%"];

  return (
    <div className="relative mx-auto w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-700 dark:bg-slate-900">
      <div className="flex gap-4">
        <motion.div
          className="relative h-28 w-28 shrink-0 overflow-hidden rounded-xl bg-slate-100"
          animate={{ y: [0, -4, 0] }}
          transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
        >
          <ProductPhoto src={HERO_SHOE} alt="Cedar Trail Runner" className="h-full w-full" />
        </motion.div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-bold text-slate-900 dark:text-white">Cedar Trail Runner</p>
          <p className="mt-1 text-sm font-semibold text-teal-700">
            $150 <span className="text-xs font-normal text-slate-400 line-through">$300</span>
          </p>
          <p className="mt-1 text-[11px] text-amber-500">★★★★★ 4.9</p>
          <div className="mt-2 flex gap-1.5">
            <span className="h-4 w-4 rounded-full bg-teal-700 ring-2 ring-teal-300" />
            <span className="h-4 w-4 rounded-full bg-slate-800" />
            <span className="h-4 w-4 rounded-full bg-sky-600" />
          </div>
          <button
            type="button"
            className="mt-3 w-full rounded-lg bg-teal-600 py-1.5 text-[11px] font-bold uppercase tracking-wide text-white"
          >
            Add to cart
          </button>
        </div>
      </div>

      <div className="relative mt-4 flex flex-wrap gap-1.5 border-t border-slate-100 pt-3 dark:border-slate-800">
        {TABS.map((label, i) => (
          <button
            key={label}
            type="button"
            onClick={() => setTab(i)}
            className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide transition ${
              tab === i
                ? "bg-teal-600 text-white"
                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            {label}
          </button>
        ))}
        {!reduce ? <CursorDot x={tabPositions[tab]} y="70%" /> : null}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={tab}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="mt-3 space-y-1.5"
        >
          {[1, 2, 3].map((n) => (
            <div
              key={n}
              className="h-2 rounded bg-slate-100 dark:bg-slate-800"
              style={{ width: `${90 - n * 12}%` }}
            />
          ))}
          <p className="pt-1 text-[10px] font-medium text-teal-700 dark:text-teal-400">
            Selected: {TABS[tab]} · field mapped
          </p>
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/** Demo 2 — Dynamic multi-level navigation */
function DemoDynamic() {
  const cats = [
    { id: "shoes", label: "Shoes", kids: ["Women", "Men"] },
    { id: "tees", label: "T-Shirts", kids: ["Basics", "Graphic"] },
    { id: "jackets", label: "Jackets", kids: ["Shell", "Fleece"] },
  ] as const;
  const [open, setOpen] = useState<string>("shoes");
  const [sub, setSub] = useState("Women");
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) return;
    const seq = [
      { o: "shoes", s: "Women" },
      { o: "shoes", s: "Men" },
      { o: "tees", s: "Basics" },
      { o: "jackets", s: "Shell" },
    ];
    let i = 0;
    const t = setInterval(() => {
      i = (i + 1) % seq.length;
      setOpen(seq[i].o);
      setSub(seq[i].s);
    }, 2200);
    return () => clearInterval(t);
  }, [reduce]);

  const filtered =
    open === "jackets"
      ? [PRODUCTS[1], PRODUCTS[3], PRODUCTS[0], PRODUCTS[2]]
      : open === "tees"
        ? [PRODUCTS[2], PRODUCTS[0], PRODUCTS[1], PRODUCTS[3]]
        : PRODUCTS;

  return (
    <div className="relative flex w-full max-w-lg gap-3 rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-700 dark:bg-slate-900">
      <div className="w-28 shrink-0 space-y-1.5">
        {cats.map((c) => (
          <div key={c.id}>
            <button
              type="button"
              onClick={() => setOpen(c.id)}
              className={`flex w-full items-center justify-between rounded-full border px-2.5 py-1.5 text-[11px] font-semibold transition ${
                open === c.id
                  ? "border-teal-500 bg-teal-50 text-teal-800 dark:bg-teal-950 dark:text-teal-200"
                  : "border-slate-200 bg-white text-slate-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-300"
              }`}
            >
              {c.label}
              <span className="text-[9px] opacity-60">▾</span>
            </button>
            <AnimatePresence>
              {open === c.id ? (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: "auto", opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden pl-2"
                >
                  {c.kids.map((k) => (
                    <button
                      key={k}
                      type="button"
                      onClick={() => setSub(k)}
                      className={`mt-1 block w-full rounded-md px-2 py-1 text-left text-[10px] font-medium ${
                        sub === k
                          ? "bg-slate-900 text-white dark:bg-teal-600"
                          : "text-slate-600 hover:bg-slate-100 dark:text-slate-400"
                      }`}
                    >
                      {k}
                    </button>
                  ))}
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
        ))}
      </div>
      <div className="relative min-w-0 flex-1">
        <p className="mb-2 text-[10px] font-bold uppercase tracking-wide text-slate-500">
          {cats.find((c) => c.id === open)?.label} → {sub}
        </p>
        <motion.div
          key={`${open}-${sub}`}
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          className="grid grid-cols-2 gap-2"
        >
          {filtered.map((p) => (
            <ProductCard key={p.id} product={p} compact />
          ))}
        </motion.div>
        {!reduce ? <CursorDot x="8%" y="18%" /> : null}
      </div>
    </div>
  );
}

/** Demo 3 — JavaScript / Ajax wait */
function DemoJsRender() {
  const [phase, setPhase] = useState<"wait" | "load" | "done">("wait");
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) {
      setPhase("done");
      return;
    }
    let cancelled = false;
    const loop = async () => {
      while (!cancelled) {
        setPhase("wait");
        await new Promise((r) => setTimeout(r, 1400));
        if (cancelled) break;
        setPhase("load");
        await new Promise((r) => setTimeout(r, 1000));
        if (cancelled) break;
        setPhase("done");
        await new Promise((r) => setTimeout(r, 2200));
      }
    };
    void loop();
    return () => {
      cancelled = true;
    };
  }, [reduce]);

  return (
    <div className="relative w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-3 flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${
            phase === "done" ? "bg-teal-500" : "animate-pulse bg-amber-400"
          }`}
        />
        <p className="font-mono text-[10px] font-semibold text-slate-600 dark:text-slate-300">
          {phase === "wait" && "Waiting for Ajax…"}
          {phase === "load" && "Executing page JavaScript…"}
          {phase === "done" && "DOM ready · 4 products hydrated"}
        </p>
      </div>
      <div className="mb-3 flex gap-2">
        {["Shoes", "T-Shirts", "Jackets"].map((d, i) => (
          <div
            key={d}
            className="flex flex-1 items-center justify-between rounded-lg border border-slate-200 px-2 py-1.5 text-[10px] font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-300"
          >
            {d}
            <motion.span
              animate={phase === "load" ? { rotate: 180 } : { rotate: 0 }}
              className="text-slate-400"
            >
              ▾
            </motion.span>
            {i === 0 && phase !== "wait" ? (
              <span className="sr-only">open</span>
            ) : null}
          </div>
        ))}
      </div>
      <AnimatePresence mode="wait">
        {phase === "wait" || phase === "load" ? (
          <motion.div
            key="skel"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-2 gap-2"
          >
            {[1, 2, 3, 4].map((n) => (
              <div
                key={n}
                className="h-24 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800"
              />
            ))}
          </motion.div>
        ) : (
          <motion.div
            key="grid"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid grid-cols-2 gap-2"
          >
            {PRODUCTS.map((p, i) => (
              <motion.div
                key={p.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
              >
                <ProductCard product={p} compact />
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/** Demo 4 — Selector / sitemap mapping */
function DemoSelectors() {
  const fields = [
    { id: "title", label: "Text selector", target: "Cedar Trail Runner" },
    { id: "price", label: "Price selector", target: "$150.00 USD" },
    { id: "rating", label: "Rating selector", target: "4.9 ★" },
  ];
  const [active, setActive] = useState(0);
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) return;
    const t = setInterval(() => setActive((i) => (i + 1) % fields.length), 2000);
    return () => clearInterval(t);
  }, [reduce, fields.length]);

  const f = fields[active];

  return (
    <div className="relative w-full max-w-md rounded-2xl border border-slate-200 bg-white p-5 shadow-card dark:border-slate-700 dark:bg-slate-900">
      <div className="flex gap-4">
        <motion.div
          className="relative h-24 w-24 shrink-0 overflow-hidden rounded-xl bg-slate-100"
          animate={{ scale: [1, 1.04, 1] }}
          transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
        >
          <ProductPhoto src={HERO_SHOE} alt="Cedar Trail Runner" className="h-full w-full" />
        </motion.div>
        <div className="relative flex-1 space-y-2">
          <p
            className={`inline-block rounded px-1 text-sm font-bold transition ${
              active === 0 ? "bg-teal-100 text-teal-900 ring-2 ring-teal-400" : "text-slate-900 dark:text-white"
            }`}
          >
            Cedar Trail Runner
          </p>
          <p
            className={`inline-block rounded px-1 text-sm font-semibold transition ${
              active === 1 ? "bg-teal-100 text-teal-900 ring-2 ring-teal-400" : "text-slate-700 dark:text-slate-300"
            }`}
          >
            $150.00 USD
          </p>
          <p
            className={`inline-block rounded px-1 text-xs transition ${
              active === 2 ? "bg-teal-100 text-teal-900 ring-2 ring-teal-400" : "text-amber-500"
            }`}
          >
            ★★★★★ 4.9
          </p>
          <div className="flex gap-1 pt-1">
            <span className="h-3 w-3 rounded-full bg-teal-700" />
            <span className="h-3 w-3 rounded-full bg-slate-800" />
          </div>
          <button
            type="button"
            className="rounded-md bg-teal-600 px-3 py-1 text-[10px] font-bold uppercase text-white"
          >
            Add to cart
          </button>

          <AnimatePresence mode="wait">
            <motion.div
              key={f.id}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0 }}
              className="absolute -right-2 top-0 rounded-lg bg-slate-900 px-2.5 py-1.5 text-[10px] font-bold text-white shadow-lg"
            >
              {f.label}
              <span className="absolute -left-1 top-2 h-2 w-2 rotate-45 bg-slate-900" />
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
      <div className="mt-4 rounded-lg border border-dashed border-teal-300 bg-teal-50/50 p-3 font-mono text-[10px] text-slate-700 dark:border-teal-800 dark:bg-teal-950/30 dark:text-slate-300">
        <p className="font-bold text-teal-800 dark:text-teal-300">sitemap · product</p>
        <p className="mt-1">
          {f.id}: &quot;{f.target}&quot;
        </p>
      </div>
    </div>
  );
}

/** Demo 5 — Export preview */
function DemoExport() {
  const [fmt, setFmt] = useState<"JSON" | "CSV" | "XLSX">("JSON");
  const reduce = useReducedMotion();

  useEffect(() => {
    if (reduce) return;
    const order: Array<"JSON" | "CSV" | "XLSX"> = ["JSON", "CSV", "XLSX"];
    let i = 0;
    const t = setInterval(() => {
      i = (i + 1) % order.length;
      setFmt(order[i]);
    }, 2200);
    return () => clearInterval(t);
  }, [reduce]);

  const rows = PRODUCTS.slice(0, 3);

  return (
    <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-4 shadow-card dark:border-slate-700 dark:bg-slate-900">
      <div className="mb-3 flex gap-2">
        {(["JSON", "CSV", "XLSX"] as const).map((f) => (
          <button
            key={f}
            type="button"
            onClick={() => setFmt(f)}
            className={`rounded-lg px-3 py-1.5 text-xs font-bold transition ${
              fmt === f
                ? "bg-teal-600 text-white"
                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
            }`}
          >
            {f}
          </button>
        ))}
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={fmt}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="overflow-hidden rounded-xl border border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-950"
        >
          {fmt === "JSON" ? (
            <pre className="max-h-48 overflow-auto p-3 font-mono text-[10px] leading-relaxed text-slate-800 dark:text-slate-200">
              {JSON.stringify(
                {
                  entities: {
                    products: rows.map((p) => ({
                      name: p.name,
                      price: p.price,
                      currency: "USD",
                    })),
                  },
                },
                null,
                2,
              )}
            </pre>
          ) : (
            <table className="w-full text-left text-[10px]">
              <thead className="bg-slate-200/80 font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
                <tr>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Price</th>
                  <th className="px-3 py-2">Tag</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((p) => (
                  <tr key={p.id} className="border-t border-slate-200 dark:border-slate-800">
                    <td className="px-3 py-2 font-medium text-slate-800 dark:text-slate-200">
                      {p.name}
                    </td>
                    <td className="px-3 py-2 text-slate-600">${p.price}</td>
                    <td className="px-3 py-2 text-slate-600">{p.tag}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </motion.div>
      </AnimatePresence>
      <p className="mt-2 text-[10px] font-medium text-slate-500">
        Ready-made {fmt} — copy straight into your project
      </p>
    </div>
  );
}

const SHOWCASE = [
  {
    id: "point",
    title: "Point-and-click interface",
    body: "Configure extraction by pointing at elements. No coding required — ExtractAI maps fields as you click.",
    Demo: DemoPointClick,
    flip: false,
  },
  {
    id: "dynamic",
    title: "Extract data from dynamic websites",
    body: "Follow multi-level navigation, category trees, and listing pages — then scrape every branch.",
    Demo: DemoDynamic,
    flip: true,
  },
  {
    id: "js",
    title: "Handle JavaScript sites",
    body: "Full JS execution with waits for Ajax and SPA hydration before plugins run.",
    Demo: DemoJsRender,
    flip: false,
  },
  {
    id: "sitemap",
    title: "Use selectors to customize data",
    body: "Bind title, price, ratings, and more to a reusable sitemap tailored to each site structure.",
    Demo: DemoSelectors,
    flip: true,
  },
  {
    id: "export",
    title: "Export CSV, XLSX, and JSON",
    body: "Preview structured tables or ready-made entity JSON — then export to your stack.",
    Demo: DemoExport,
    flip: false,
  },
] as const;

function ShowcaseRow({
  title,
  body,
  Demo,
  flip,
}: {
  title: string;
  body: string;
  Demo: () => ReactNode;
  flip: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.35 }}
      transition={{ duration: 0.5 }}
      className={`grid items-center gap-10 lg:grid-cols-2 lg:gap-16 ${
        flip ? "" : ""
      }`}
    >
      <div className={flip ? "lg:order-2" : ""}>
        <h3 className="font-display text-2xl font-semibold uppercase tracking-tight text-slate-950 dark:text-white md:text-3xl">
          {title}
        </h3>
        <p className="mt-3 max-w-md text-base text-slate-600 dark:text-slate-400">{body}</p>
      </div>
      <div className={`flex justify-center ${flip ? "lg:order-1" : ""}`}>
        <Demo />
      </div>
    </motion.div>
  );
}

export function ProductShowcase() {
  return (
    <section
      id="product-demos"
      className="scroll-mt-24 border-b border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950"
    >
      <div className="mx-auto max-w-6xl space-y-24 px-4 py-20 sm:px-6 md:space-y-32 md:py-28">
        <div className="mx-auto max-w-2xl text-center">
          <p className="font-mono text-[11px] font-bold uppercase tracking-[0.18em] text-teal-700 dark:text-teal-400">
            See it move
          </p>
          <h2 className="mt-3 font-display text-3xl text-slate-950 dark:text-white md:text-4xl">
            Interactive demos of what ExtractAI does
          </h2>
          <p className="mt-3 text-slate-600 dark:text-slate-400">
            Scroll through live explainers — selectors, dynamic nav, JavaScript waits, and exports —
            built as original ExtractAI mockups.
          </p>
        </div>

        {SHOWCASE.map((row) => (
          <ShowcaseRow key={row.id} {...row} />
        ))}
      </div>
    </section>
  );
}
