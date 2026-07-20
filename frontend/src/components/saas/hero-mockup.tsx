"use client";

import { useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";

import { BrowserChrome } from "./illustrations";

type TreeNode = {
  id: string;
  label: string;
  depth: number;
  dataKey?: string;
};

const treeNodes: TreeNode[] = [
  { id: "html", label: "<html>", depth: 0 },
  { id: "body", label: "<body>", depth: 1 },
  { id: "main", label: "<main class=\"catalog\">", depth: 2 },
  { id: "article-1", label: "<article data-id=\"p-101\">", depth: 3, dataKey: "product" },
  { id: "h2-1", label: "<h2 class=\"title\">", depth: 4, dataKey: "title" },
  { id: "span-price", label: "<span class=\"price\">", depth: 4, dataKey: "price" },
  { id: "article-2", label: "<article data-id=\"p-102\">", depth: 3 },
  { id: "nav", label: "<nav class=\"pagination\">", depth: 3, dataKey: "pagination" },
];

const tabContent: Record<string, { url: string; highlight: string }> = {
  Select: { url: "https://shop.example.com/catalog", highlight: "Point-and-click selectors" },
  Dynamic: { url: "https://shop.example.com/catalog?page=2", highlight: "Infinite scroll detected" },
  Pagination: { url: "https://shop.example.com/catalog?page=3", highlight: "Auto-follow next links" },
  "JS Render": { url: "https://spa.example.com/app#/listings", highlight: "Headless browser active" },
};

const previewByKey: Record<string, object> = {
  product: { id: "p-101", sku: "WDG-4421", category: "Hardware" },
  title: { text: "Precision Torque Wrench Set", selector: "article h2.title" },
  price: { amount: 89.99, currency: "USD", formatted: "$89.99" },
  pagination: { current: 2, total: 14, next: "/catalog?page=3" },
};

const defaultPreview = {
  run_id: "run_8f3k2m",
  status: "ready",
  items_extracted: 24,
  hint: "Select a node to inspect mapped fields",
};

const tabs = ["Select", "Dynamic", "Pagination", "JS Render"] as const;

export function HeroMockup() {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>("Select");
  const [selectedId, setSelectedId] = useState("h2-1");

  const preview = useMemo(() => {
    const node = treeNodes.find((n) => n.id === selectedId);
    if (node?.dataKey && previewByKey[node.dataKey]) {
      return previewByKey[node.dataKey];
    }
    return defaultPreview;
  }, [selectedId]);

  const tabMeta = tabContent[activeTab];

  return (
    <div className="w-full max-w-4xl">
      <BrowserChrome url={tabMeta.url} className="shadow-lg dark:shadow-teal-900/10">
        <div className="flex flex-wrap items-center gap-1 border-b border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-800/50">
          {tabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              aria-label={`Switch to ${tab} mode`}
              aria-pressed={activeTab === tab}
              className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                activeTab === tab
                  ? "bg-teal-600 text-white"
                  : "text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-700"
              }`}
            >
              {tab}
            </button>
          ))}
          <span className="ml-auto hidden text-[10px] text-teal-600 dark:text-teal-400 sm:inline">
            {tabMeta.highlight}
          </span>
        </div>

        <div className="grid min-h-[280px] grid-cols-1 md:grid-cols-2">
          <div className="border-b border-slate-200 p-3 font-mono text-[11px] leading-relaxed dark:border-slate-700 md:border-b-0 md:border-r">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">DOM Tree</p>
            <ul className="space-y-0.5">
              {treeNodes.map((node) => {
                const selected = selectedId === node.id;
                return (
                  <li key={node.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(node.id)}
                      aria-label={`Select ${node.label}`}
                      aria-pressed={selected}
                      style={{ paddingLeft: `${node.depth * 12 + 4}px` }}
                      className={`block w-full truncate rounded px-1 py-0.5 text-left transition ${
                        selected
                          ? "bg-teal-600/15 text-teal-700 ring-1 ring-teal-500/40 dark:text-teal-300"
                          : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
                      }`}
                    >
                      {node.label}
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>

          <div className="bg-slate-950 p-3 font-mono text-[11px] text-emerald-400">
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-slate-500">JSON Preview</p>
            <AnimatePresence mode="wait">
              <motion.pre
                key={selectedId + activeTab}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                transition={{ duration: 0.2 }}
                className="overflow-x-auto whitespace-pre-wrap break-words"
              >
                {JSON.stringify({ mode: activeTab, ...preview }, null, 2)}
              </motion.pre>
            </AnimatePresence>
          </div>
        </div>
      </BrowserChrome>
    </div>
  );
}
