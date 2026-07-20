"use client";

import Link from "next/link";
import { motion, useInView, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useEffect, useRef, useState } from "react";

const ROTATING = [
  "amazon.com",
  "github.com",
  "shopify.com",
  "en.wikipedia.org",
  "docs.stripe.com",
  "news.ycombinator.com",
];

const STATS = [
  { value: 50000, suffix: "+", label: "Websites analyzed", display: "50K+" },
  { value: 99.8, suffix: "%", label: "Extraction accuracy", display: "99.8%" },
  { value: 20, suffix: "+", label: "Extraction plugins", display: "20+" },
  { value: 100, suffix: "+", label: "Supported technologies", display: "100+" },
];

function CountUp({ display, inView }: { display: string; inView: boolean }) {
  const [text, setText] = useState(display);
  useEffect(() => {
    if (!inView) return;
    setText(display);
  }, [display, inView]);
  return <span>{text}</span>;
}

export function MarketingHero() {
  const [idx, setIdx] = useState(0);
  const statsRef = useRef<HTMLDivElement>(null);
  const inView = useInView(statsRef, { once: true, amount: 0.4 });
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const sx = useSpring(mx, { stiffness: 40, damping: 22 });
  const sy = useSpring(my, { stiffness: 40, damping: 22 });
  const x = useTransform(sx, [-0.5, 0.5], [-10, 10]);
  const y = useTransform(sy, [-0.5, 0.5], [-8, 8]);

  useEffect(() => {
    const t = setInterval(() => setIdx((i) => (i + 1) % ROTATING.length), 2400);
    return () => clearInterval(t);
  }, []);

  return (
    <section
      className="relative px-5 pb-16 pt-28 md:px-6 md:pb-24 md:pt-36"
      onPointerMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        mx.set((e.clientX - r.left) / r.width - 0.5);
        my.set((e.clientY - r.top) / r.height - 0.5);
      }}
      onPointerLeave={() => {
        mx.set(0);
        my.set(0);
      }}
    >
      <div className="pointer-events-none absolute left-1/2 top-24 h-64 w-[min(90vw,640px)] -translate-x-1/2 rounded-full bg-accent/20 blur-[100px]" />

      <motion.div style={{ x, y }} className="relative z-[1] mx-auto max-w-4xl text-center">
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-5 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-1.5 font-mono text-[11px] uppercase tracking-[0.2em] text-accent backdrop-blur"
        >
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
          Understand any website. Not just scrape it.
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.08 }}
          className="font-display text-4xl font-semibold leading-[1.05] tracking-tight text-slate-900 sm:text-5xl md:text-7xl"
        >
          Understand Any Website
          <span className="block bg-gradient-to-r from-slate-900 via-accent to-accent-blue bg-clip-text text-transparent">
            with AI
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.16 }}
          className="mx-auto mt-6 max-w-2xl text-base text-slate-600 md:text-xl md:leading-relaxed"
        >
          Extract structured data, discover hidden APIs, analyze website architecture, and generate
          AI-ready datasets in seconds.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.24 }}
          className="mt-9 flex flex-wrap items-center justify-center gap-3"
        >
          <Link
            href="#console"
            className="rounded-full bg-gradient-to-r from-accent to-accent-blue px-7 py-3.5 text-sm font-semibold text-white shadow-[0_8px_28px_rgba(13,148,136,0.28)] transition hover:brightness-110"
          >
            Start Free
          </Link>
          <a
            href="#demo"
            className="rounded-full border border-slate-200 bg-white px-7 py-3.5 text-sm font-medium text-slate-900 backdrop-blur transition hover:border-accent/40 hover:bg-slate-50"
          >
            View Live Demo
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.32 }}
          className="mx-auto mt-12 max-w-xl"
        >
          <div className="rounded-2xl border border-accent/25 bg-white p-2 shadow-[0_0_40px_rgba(56,225,210,0.12)] backdrop-blur-xl">
            <div className="flex items-center gap-2 rounded-xl bg-slate-50 px-4 py-3.5 font-mono text-sm">
              <span className="text-slate-700">https://</span>
              <span className="relative min-h-[1.25rem] flex-1 overflow-hidden text-left text-accent">
                <motion.span
                  key={idx}
                  initial={{ y: 12, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -12, opacity: 0 }}
                  className="absolute inset-x-0"
                >
                  {ROTATING[idx]}
                </motion.span>
              </span>
              <span className="hidden rounded-lg bg-accent/15 px-2 py-1 text-[10px] uppercase tracking-wider text-accent sm:inline">
                analyzing
              </span>
            </div>
          </div>
          <p className="mt-3 text-xs text-slate-700">
            Example domains for illustration — paste any public URL below to run a real extraction.
          </p>
        </motion.div>

        <div ref={statsRef} className="mt-14 grid grid-cols-2 gap-4 md:grid-cols-4 md:gap-6">
          {STATS.map((s, i) => (
            <motion.div
              key={s.label}
              initial={{ opacity: 0, y: 12 }}
              animate={inView ? { opacity: 1, y: 0 } : {}}
              transition={{ delay: 0.1 * i }}
              className="rounded-2xl border border-slate-200 bg-white px-3 py-4 backdrop-blur"
            >
              <p className="font-display text-2xl text-slate-900 md:text-3xl">
                <CountUp display={s.display} inView={inView} />
              </p>
              <p className="mt-1 text-xs text-slate-700">{s.label}</p>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </section>
  );
}
