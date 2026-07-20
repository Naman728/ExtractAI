"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { Github, Linkedin, Twitter } from "lucide-react";

const productLinks = [
  { href: "/#features", label: "Features" },
  { href: "/pricing", label: "Pricing" },
  { href: "/integrations", label: "Integrations" },
  { href: "/docs", label: "Documentation" },
];

const companyLinks = [
  { href: "/about", label: "About" },
  { href: "/blog", label: "Blog" },
  { href: "/contact", label: "Contact" },
  { href: "#", label: "Careers" },
];

const legalLinks = [
  { href: "#", label: "Privacy Policy" },
  { href: "#", label: "Terms of Service" },
];

export function SiteFooter() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  function handleNewsletter(e: FormEvent) {
    e.preventDefault();
    if (!email.trim()) return;
    setSubscribed(true);
    setEmail("");
  }

  return (
    <footer className="border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950">
      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-4">
          <div>
            <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900 dark:text-slate-100">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-sm font-bold text-white">
                E
              </span>
              ExtractAI
            </Link>
            <p className="mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
              Intelligent web data extraction for teams who need reliable, structured output from any site.
            </p>
            <a
              href="mailto:hello@extractai.app"
              className="mt-3 inline-block text-sm font-medium text-teal-600 hover:text-teal-700 dark:text-teal-400"
            >
              hello@extractai.app
            </a>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-900 dark:text-slate-100">
              Product
            </h3>
            <ul className="mt-4 space-y-2">
              {productLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-600 transition hover:text-teal-600 dark:text-slate-400 dark:hover:text-teal-400"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-900 dark:text-slate-100">
              Company
            </h3>
            <ul className="mt-4 space-y-2">
              {companyLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-600 transition hover:text-teal-600 dark:text-slate-400 dark:hover:text-teal-400"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
            <h3 className="mt-6 text-sm font-semibold uppercase tracking-wide text-slate-900 dark:text-slate-100">
              Legal
            </h3>
            <ul className="mt-4 space-y-2">
              {legalLinks.map((link) => (
                <li key={link.label}>
                  <Link
                    href={link.href}
                    className="text-sm text-slate-600 transition hover:text-teal-600 dark:text-slate-400 dark:hover:text-teal-400"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-900 dark:text-slate-100">
              Newsletter
            </h3>
            <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
              Product updates, scraping guides, and release notes — no spam.
            </p>
            <form onSubmit={handleNewsletter} className="mt-4 flex flex-col gap-2">
              <label htmlFor="footer-email" className="sr-only">
                Email address
              </label>
              <input
                id="footer-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-500 focus:border-teal-500 focus:outline-none focus:ring-2 focus:ring-teal-500/20 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
              />
              <button
                type="submit"
                aria-label="Subscribe to newsletter"
                className="rounded-lg bg-teal-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-teal-700"
              >
                Subscribe
              </button>
            </form>
            {subscribed ? (
              <p className="mt-2 text-sm text-teal-600 dark:text-teal-400" role="status">
                Thanks — you&apos;re on the list.
              </p>
            ) : null}
            <div className="mt-6 flex gap-3">
              {[
                { icon: Twitter, label: "Twitter" },
                { icon: Github, label: "GitHub" },
                { icon: Linkedin, label: "LinkedIn" },
              ].map(({ icon: Icon, label }) => (
                <a
                  key={label}
                  href="#"
                  aria-label={label}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition hover:border-teal-500/40 hover:text-teal-600 dark:border-slate-700 dark:text-slate-400"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-12 border-t border-slate-200 pt-8 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-500">
          © {new Date().getFullYear()} ExtractAI. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
