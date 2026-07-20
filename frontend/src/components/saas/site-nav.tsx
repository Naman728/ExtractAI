"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";

import { api } from "@/lib/api";
import { clearTokens, getRefreshToken, isLoggedIn } from "@/lib/auth";
import { ThemeToggle } from "@/lib/theme";

const links = [
  { href: "/#features", label: "Features" },
  { href: "/#product-demos", label: "Product" },
  { href: "/pricing", label: "Pricing" },
  { href: "/docs", label: "Documentation" },
  { href: "/integrations", label: "Integrations" },
  { href: "/blog", label: "Blog" },
  { href: "/about", label: "About" },
  { href: "/contact", label: "Contact" },
];

export function SiteNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [loggedIn, setLoggedIn] = useState(false);

  useEffect(() => {
    setLoggedIn(isLoggedIn());
  }, [pathname]);

  async function signOut() {
    const refresh = getRefreshToken();
    try {
      if (refresh) {
        await api.post("/api/v1/auth/logout", { refresh_token: refresh });
      }
    } catch {
      // ignore
    }
    clearTokens();
    setLoggedIn(false);
    setOpen(false);
    router.push("/");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur-md dark:border-slate-800 dark:bg-slate-950/90">
      <nav
        className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6"
        aria-label="Main navigation"
      >
        <Link
          href="/"
          className="flex items-center gap-2 font-semibold tracking-tight text-slate-900 dark:text-slate-100"
        >
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-sm font-bold text-white">
            E
          </span>
          <span>
            Extract<span className="text-teal-600 dark:text-teal-400">AI</span>
          </span>
        </Link>

        <ul className="hidden items-center gap-1 lg:flex">
          {links.map((link) => {
            const active =
              pathname === link.href || (link.href !== "/#features" && pathname.startsWith(link.href));
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={`rounded-md px-3 py-2 text-sm font-medium transition ${
                    active
                      ? "text-teal-600 dark:text-teal-400"
                      : "text-slate-600 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
                  }`}
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
        </ul>

        <div className="hidden items-center gap-2 sm:flex">
          <ThemeToggle />
          {loggedIn ? (
            <>
              <Link
                href="/dashboard"
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
              >
                Dashboard
              </Link>
              <button
                type="button"
                onClick={() => void signOut()}
                className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:border-orange-300 hover:bg-orange-50 hover:text-orange-700 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-orange-950/40 dark:hover:text-orange-300"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:text-slate-900 dark:text-slate-300 dark:hover:text-white"
              >
                Login
              </Link>
              <Link
                href="/register"
                className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-700"
              >
                Sign Up
              </Link>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 sm:hidden">
          <ThemeToggle />
          <button
            type="button"
            className="rounded-lg p-2 text-slate-700 dark:text-slate-200"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {open ? (
        <div className="border-t border-slate-200 px-4 py-3 sm:hidden dark:border-slate-800">
          <ul className="space-y-1">
            {links.map((link) => (
              <li key={link.href}>
                <Link
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className="block rounded-md px-3 py-2 text-sm font-medium text-slate-700 dark:text-slate-200"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>
          <div className="mt-3 flex flex-col gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
            {loggedIn ? (
              <>
                <Link
                  href="/dashboard"
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-2 text-center text-sm font-medium text-slate-700 dark:text-slate-200"
                >
                  Dashboard
                </Link>
                <button
                  type="button"
                  onClick={() => void signOut()}
                  className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200"
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-2 text-center text-sm font-medium text-slate-700 dark:text-slate-200"
                >
                  Login
                </Link>
                <Link
                  href="/register"
                  onClick={() => setOpen(false)}
                  className="rounded-lg bg-teal-600 px-3 py-2 text-center text-sm font-semibold text-white"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      ) : null}
    </header>
  );
}
