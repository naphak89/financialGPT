"use client";

import type { CSSProperties } from "react";
import type { Plugin } from "@react-pdf-viewer/core";
import { SpecialZoomLevel, Viewer, Worker } from "@react-pdf-viewer/core";
import { defaultLayoutPlugin } from "@react-pdf-viewer/default-layout";
import { pageNavigationPlugin } from "@react-pdf-viewer/page-navigation";
import { searchPlugin } from "@react-pdf-viewer/search";
import Link from "next/link";
import { useSearchParams } from "next/navigation";

import "@react-pdf-viewer/core/lib/styles/index.css";
import "@react-pdf-viewer/default-layout/lib/styles/index.css";
import "@react-pdf-viewer/search/lib/styles/index.css";

const PDFJS_VERSION = "3.11.174";
const WORKER_URL = `https://unpkg.com/pdfjs-dist@${PDFJS_VERSION}/build/pdf.worker.min.js`;

function safePdfBasename(file: string | null): string | null {
  if (!file) return null;
  const base = file.split(/[/\\]/).pop() ?? "";
  if (!base || base.includes("..")) return null;
  if (!base.toLowerCase().endsWith(".pdf")) return null;
  return base;
}

/** Try several query strings — PDF text often differs slightly from indexed chunks. */
function highlightCandidates(full: string): Array<{ keyword: string; matchCase: boolean }> {
  const t = full.trim();
  if (t.length < 4) return [];
  const out: Array<{ keyword: string; matchCase: boolean }> = [];
  const seen = new Set<string>();
  const add = (s: string) => {
    const x = s.trim();
    if (x.length < 4 || seen.has(x)) return;
    seen.add(x);
    out.push({ keyword: x, matchCase: false });
  };

  add(t);
  const words = t.split(/\s+/).filter(Boolean);
  if (words.length > 12) {
    add(words.slice(0, 12).join(" "));
  }
  if (words.length > 6) {
    add(words.slice(0, 6).join(" "));
  }
  if (t.length > 80) {
    add(t.slice(0, 80).trim());
  }
  if (t.length > 45) {
    add(t.slice(0, 45).trim());
  }
  if (words.length >= 4) {
    add(words.slice(0, 4).join(" "));
  }
  return out;
}

export function TextbookReader() {
  const searchParams = useSearchParams();
  const rawFile = searchParams.get("file");
  const pageStr = searchParams.get("page");
  const q = searchParams.get("q") ?? "";

  const file = safePdfBasename(rawFile);
  const pageOneBased = Math.max(1, parseInt(pageStr || "1", 10) || 1);
  const pageIndex0 = pageOneBased - 1;
  const keyword = q.trim();

  // Plugin factories use React hooks internally — must run at top level, not inside useMemo.
  const pageNavigationPluginInstance = pageNavigationPlugin();
  const searchPluginInstance = searchPlugin({
    keyword: keyword || undefined,
  });
  const defaultLayoutPluginInstance = defaultLayoutPlugin();

  const jumpPlugin: Plugin = {
    onDocumentLoad: () => {
      searchPluginInstance.setTargetPages((tp) => tp.pageIndex === pageIndex0);
      pageNavigationPluginInstance.jumpToPage(pageIndex0);

      const runHighlight = async () => {
        if (!keyword) {
          searchPluginInstance.setTargetPages(() => true);
          return;
        }
        const candidates = highlightCandidates(keyword);
        for (const flag of candidates) {
          searchPluginInstance.setTargetPages((tp) => tp.pageIndex === pageIndex0);
          try {
            const matches = await searchPluginInstance.highlight(flag);
            if (matches.length > 0) {
              searchPluginInstance.jumpToMatch(0);
              searchPluginInstance.setTargetPages(() => true);
              return;
            }
          } catch {
            /* ignore and try shorter phrase */
          }
        }
        searchPluginInstance.setTargetPages(() => true);
      };

      // Wait for the page + text layer so search can find spans.
      window.setTimeout(() => {
        void runHighlight();
      }, 400);
    },
  };

  const plugins = [
    defaultLayoutPluginInstance,
    pageNavigationPluginInstance,
    searchPluginInstance,
    jumpPlugin,
  ];

  const fileUrl = file ? `/textbooks/${encodeURIComponent(file)}` : null;

  return (
    <div className="flex min-h-[100dvh] flex-col bg-background text-foreground">
      <header className="shrink-0 border-b border-borderline px-4 py-3 flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="text-[10px] uppercase tracking-wider text-muted">
            Textbook
          </p>
          <p className="text-sm font-medium truncate">
            {file ?? "No file selected"}
            {file ? ` · page ${pageOneBased}` : null}
          </p>
        </div>
        <Link
          href="/chat"
          className="text-xs text-accent hover:underline shrink-0"
        >
          Back to chat
        </Link>
      </header>

      {!fileUrl ? (
        <p className="p-6 text-sm text-muted">
          Open a source from Education mode in chat, or use{" "}
          <code className="rounded bg-surface px-1 py-0.5 text-xs">
            /textbook?file=Full.pdf&page=1&q=search+phrase
          </code>
          .
        </p>
      ) : (
        <div
          className="flex-1 min-h-[70vh] border-t border-borderline textbook-reader-pdf"
          style={
            {
              ["--rpv-search__highlight-background-color" as string]:
                "rgba(253, 224, 71, 0.55)",
              ["--rpv-search__highlight--current-background-color" as string]:
                "rgba(234, 179, 8, 0.65)",
            } as CSSProperties
          }
        >
          <Worker workerUrl={WORKER_URL}>
            <div className="h-[calc(100dvh-8rem)]">
              <Viewer
                key={`${file}-${pageOneBased}-${keyword}`}
                fileUrl={fileUrl}
                plugins={plugins}
                defaultScale={SpecialZoomLevel.PageWidth}
                initialPage={pageIndex0}
              />
            </div>
          </Worker>
        </div>
      )}
    </div>
  );
}
