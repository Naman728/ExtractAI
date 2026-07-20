import Link from "next/link";

import { SiteFooter } from "@/components/saas/site-footer";
import { SiteNav } from "@/components/saas/site-nav";

const posts = [
  {
    slug: "selector-resilience",
    title: "Building resilient CSS selectors that survive layout changes",
    excerpt:
      "Practical patterns for fallback selectors, semantic anchors, and validation rules that keep extractions stable.",
    date: "Jun 12, 2026",
    category: "Engineering",
    readTime: "7 min",
  },
  {
    slug: "js-rendering-guide",
    title: "When to enable JavaScript rendering (and when not to)",
    excerpt:
      "Headless browsers cost more — learn how ExtractAI detects SPA shells and chooses the cheapest reliable strategy.",
    date: "May 28, 2026",
    category: "Guides",
    readTime: "5 min",
  },
  {
    slug: "proxy-rotation-101",
    title: "Proxy rotation 101 for ecommerce monitoring",
    excerpt:
      "Geo-targeting, session stickiness, and success-rate dashboards for price intelligence at scale.",
    date: "May 10, 2026",
    category: "Product",
    readTime: "6 min",
  },
  {
    slug: "ai-field-mapping",
    title: "AI-assisted field mapping: behind the scenes",
    excerpt:
      "How we combine DOM snapshots, LLM suggestions, and human-in-the-loop review for accurate schemas.",
    date: "Apr 22, 2026",
    category: "Engineering",
    readTime: "9 min",
  },
  {
    slug: "compliance-checklist",
    title: "A compliance checklist for web data collection",
    excerpt:
      "Robots.txt, rate limits, PII handling, and documentation practices for responsible extraction teams.",
    date: "Apr 3, 2026",
    category: "Compliance",
    readTime: "8 min",
  },
  {
    slug: "sheets-integration",
    title: "Syncing live data to Google Sheets without rate limit pain",
    excerpt:
      "Batching, deduplication, and incremental updates from scheduled ExtractAI runs.",
    date: "Mar 15, 2026",
    category: "Integrations",
    readTime: "4 min",
  },
];

export default function BlogPage() {
  return (
    <>
      <SiteNav />
      <main className="bg-white dark:bg-slate-950">
        <section className="border-b border-slate-200 px-4 py-16 dark:border-slate-800 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h1 className="font-display text-4xl font-semibold text-slate-900 dark:text-slate-100">Blog</h1>
            <p className="mt-4 text-slate-600 dark:text-slate-400">
              Guides, product updates, and engineering notes from the ExtractAI team.
            </p>
          </div>
        </section>

        <section className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
          <ul className="space-y-6">
            {posts.map((post) => (
              <li key={post.slug}>
                <article className="group rounded-2xl border border-slate-200 bg-white p-6 transition hover:border-teal-500/30 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-500">
                    <span className="rounded-full bg-teal-50 px-2.5 py-0.5 font-medium text-teal-700 dark:bg-teal-950/50 dark:text-teal-400">
                      {post.category}
                    </span>
                    <span>{post.date}</span>
                    <span aria-hidden>·</span>
                    <span>{post.readTime} read</span>
                  </div>
                  <h2 className="mt-3 text-xl font-semibold text-slate-900 group-hover:text-teal-600 dark:text-slate-100 dark:group-hover:text-teal-400">
                    <Link href={`/blog/${post.slug}`}>{post.title}</Link>
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{post.excerpt}</p>
                  <Link
                    href={`/blog/${post.slug}`}
                    className="mt-4 inline-block text-sm font-medium text-teal-600 dark:text-teal-400"
                  >
                    Read article →
                  </Link>
                </article>
              </li>
            ))}
          </ul>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
