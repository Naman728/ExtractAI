"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

import { getAccessToken } from "@/lib/auth";

const LINKS = [
  { href: "#features", label: "Features" },
  { href: "#solutions", label: "Solutions" },
  { href: "#pricing", label: "Pricing" },
  { href: "#how", label: "Docs" },
  { href: "/intelligence", label: "API" },
];

export function MarketingNav() {
  const [scrolled, setScrolled] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setLoggedIn(Boolean(getAccessToken()));
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        scrolled
          ? "border-b border-slate-200 bg-white/80 shadow-lg shadow-slate-200/60 backdrop-blur-xl"
          : "bg-transparent"
      }`}
    >
      <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4 md:px-6">
        <Link href="/" className="font-display text-xl font-semibold tracking-tight text-slate-900 md:text-2xl">
          Extract<span className="text-accent">AI</span>
        </Link>

        <nav className="hidden items-center gap-7 text-sm text-slate-600 lg:flex">
          {LINKS.map((l) => (
            <a key={l.href} href={l.href} className="transition hover:text-slate-950">
              {l.label}
            </a>
          ))}
        </nav>

        <div className="hidden items-center gap-3 sm:flex">
          {loggedIn ? (
            <Link href="/dashboard" className="text-sm text-slate-600 transition hover:text-slate-950">
              Dashboard
            </Link>
          ) : (
            <Link href="/login" className="text-sm text-slate-600 transition hover:text-slate-950">
              Login
            </Link>
          )}
          <Link
            href="#console"
            className="rounded-full bg-gradient-to-r from-accent to-accent-blue px-4 py-2 text-sm font-semibold text-white shadow-[0_0_24px_rgba(56,225,210,0.35)] transition hover:brightness-110"
          >
            Start Free
          </Link>
        </div>

        <button
          type="button"
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-700 lg:hidden"
          onClick={() => setOpen((v) => !v)}
          aria-label="Menu"
        >
          {open ? "Close" : "Menu"}
        </button>
      </div>

      <AnimatePresence>
        {open ? (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden border-t border-slate-200 bg-white/95 backdrop-blur-xl lg:hidden"
          >
            <div className="flex flex-col gap-3 px-5 py-4 text-sm text-slate-700">
              {LINKS.map((l) => (
                <a key={l.href} href={l.href} onClick={() => setOpen(false)} className="py-1">
                  {l.label}
                </a>
              ))}
              <Link href={loggedIn ? "/dashboard" : "/login"} onClick={() => setOpen(false)}>
                {loggedIn ? "Dashboard" : "Login"}
              </Link>
              <Link
                href="#console"
                onClick={() => setOpen(false)}
                className="rounded-full bg-accent px-4 py-2 text-center font-semibold text-white"
              >
                Start Free
              </Link>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.header>
  );
}
