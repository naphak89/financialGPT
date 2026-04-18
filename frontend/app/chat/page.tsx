"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  clearToken,
  educationAsk,
  getToken,
  marketData,
  me,
  newsData,
  sendFeedback,
} from "@/lib/api";
import { MarketChart } from "@/components/MarketChart";

type Mode = "market" | "news" | "education";

type Msg = {
  id: string;
  role: "user" | "assistant";
  mode: Mode;
  text: string;
  payload?: unknown;
};

export default function ChatPage() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);
  const [mode, setMode] = useState<Mode>("market");
  const [symbol, setSymbol] = useState("AAPL");
  const [days, setDays] = useState(30);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [loading, setLoading] = useState(false);
  const [feedbackChoice, setFeedbackChoice] = useState<Record<string, 1 | -1>>(
    {},
  );
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    me()
      .then((u) => setEmail(u.email))
      .catch(() => router.replace("/login"));
  }, [router]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const logout = () => {
    clearToken();
    router.replace("/login");
  };

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q && mode === "education") return;
    if (mode !== "education" && !symbol.trim()) return;

    const userText =
      mode === "education"
        ? q
        : mode === "market"
          ? `${symbol.toUpperCase()} · last ${days} trading days — ${q || "(fetch data)"}`
          : `${symbol.toUpperCase()} · last ${days}d — ${q || "(fetch news)"}`;

    const userMsg: Msg = {
      id: crypto.randomUUID(),
      role: "user",
      mode,
      text: userText,
    };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);

    try {
      let assistant: Msg;
      if (mode === "market") {
        const data = (await marketData({
          symbol: symbol.trim().toUpperCase(),
          resolution: "D",
          days,
          question: q,
        })) as MarketPayload;
        assistant = {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          text: data.answer?.trim() ?? "",
          payload: data,
        };
      } else if (mode === "news") {
        const data = (await newsData({
          symbol: symbol.trim().toUpperCase(),
          days,
          question: q,
        })) as NewsPayload;
        const n = data.articles?.length ?? 0;
        const srcLabel =
          data.source === "yahoo_rss"
            ? "Yahoo Finance RSS"
            : data.source === "yfinance"
              ? "yfinance"
              : (data.source ?? "feed");
        const summary = data.summary?.trim();
        const chatAns = data.answer?.trim();
        assistant = {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          text: chatAns
            ? chatAns
            : summary
              ? summary
              : `Headlines for ${symbol.trim().toUpperCase()} (${srcLabel}): ${n} article(s) below.`,
          payload: data,
        };
      } else {
        const data = await educationAsk(q);
        assistant = {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          text: data.answer as string,
          payload: data,
        };
      }
      setMessages((m) => [...m, assistant]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          mode,
          text: e instanceof Error ? e.message : "Request failed",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, mode, symbol, days]);

  async function onFeedback(messageId: string, rating: 1 | -1) {
    if (feedbackChoice[messageId] !== undefined) return;
    try {
      await sendFeedback({ message_id: messageId, rating });
      setFeedbackChoice((prev) => ({ ...prev, [messageId]: rating }));
    } catch {
      /* ignore */
    }
  }

  return (
    <div className="flex h-[100dvh] max-h-[100dvh] flex-col min-h-0 bg-background max-w-3xl mx-auto w-full">
      <header className="shrink-0 border-b border-borderline px-4 py-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-lg font-semibold tracking-tight">
            Financial GPT
          </h1>
          <p className="text-xs text-muted">{email ?? "…"}</p>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          {(["market", "news", "education"] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMode(m)}
              className={`rounded-full px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                mode === m
                  ? "bg-accent/15 text-accent border border-accent/30"
                  : "bg-surface border border-borderline text-muted hover:text-foreground"
              }`}
            >
              {m}
            </button>
          ))}
          <button
            type="button"
            onClick={logout}
            className="text-xs text-muted hover:text-foreground ml-2"
          >
            Log out
          </button>
        </div>
      </header>

      {(mode === "market" || mode === "news") && (
        <div className="shrink-0 px-4 py-3 border-b border-borderline flex flex-wrap gap-3 items-end bg-surface/40">
          <label className="flex flex-col gap-1 text-xs text-muted">
            Symbol
            <input
              value={symbol}
              onChange={(e) => setSymbol(e.target.value)}
              className="rounded-lg bg-surface border border-borderline px-3 py-2 text-sm text-foreground w-28"
            />
          </label>

          <label className="flex flex-col gap-1 text-xs text-muted">
            {mode === "market" ? "Chart span (days)" : "Days"}
            <input
              type="number"
              min={1}
              max={365}
              value={days}
              onChange={(e) => setDays(Number(e.target.value) || 30)}
              className="rounded-lg bg-surface border border-borderline px-3 py-2 text-sm text-foreground w-20"
            />
          </label>
        </div>
      )}

      <div className="flex-1 min-h-0 overflow-y-auto px-4 py-6 space-y-6">
        {messages.length === 0 && (
          <p className="text-sm text-muted text-center py-12">
            Choose a mode, adjust symbol or question, then send a message.
          </p>
        )}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === "user"
                  ? "bg-surface2 text-foreground border border-borderline"
                  : "bg-surface text-foreground/95 border border-borderline"
              }`}
            >
              <p className="text-[10px] uppercase tracking-wider text-muted mb-1">
                {msg.mode}
              </p>
              {msg.text ? (
                <p className="whitespace-pre-wrap">{msg.text}</p>
              ) : null}
              {msg.role === "assistant" &&
              msg.mode === "market" &&
              msg.payload ? (
                <MarketQuoteBlock data={msg.payload as MarketPayload} />
              ) : null}
              {msg.role === "assistant" &&
              msg.mode === "market" &&
              msg.payload ? (
                <MarketChart
                  candles={(msg.payload as MarketPayload).candles}
                  requestedDays={(msg.payload as MarketPayload).days}
                />
              ) : null}
              {msg.role === "assistant" &&
              msg.mode === "news" &&
              msg.payload ? (
                <NewsBlock data={msg.payload as NewsPayload} />
              ) : null}
              {msg.role === "assistant" &&
              msg.mode === "education" &&
              msg.payload ? (
                <EduBlock data={msg.payload as EduPayload} />
              ) : null}
              {msg.role === "assistant" && (
                <div className="mt-3 flex gap-2 border-t border-borderline pt-2">
                  <button
                    type="button"
                    disabled={feedbackChoice[msg.id] !== undefined}
                    onClick={() => onFeedback(msg.id, 1)}
                    className={`text-xs rounded-md px-2 py-1 transition-colors ${
                      feedbackChoice[msg.id] === 1
                        ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 cursor-default"
                        : feedbackChoice[msg.id] === -1
                          ? "text-muted/40 cursor-not-allowed opacity-50"
                          : "text-muted hover:text-emerald-300 border border-transparent hover:border-emerald-500/30"
                    }`}
                  >
                    Helpful
                  </button>
                  <button
                    type="button"
                    disabled={feedbackChoice[msg.id] !== undefined}
                    onClick={() => onFeedback(msg.id, -1)}
                    className={`text-xs rounded-md px-2 py-1 transition-colors ${
                      feedbackChoice[msg.id] === -1
                        ? "bg-rose-500/20 text-rose-300 border border-rose-500/40 cursor-default"
                        : feedbackChoice[msg.id] === 1
                          ? "text-muted/40 cursor-not-allowed opacity-50"
                          : "text-muted hover:text-rose-300 border border-transparent hover:border-rose-500/30"
                    }`}
                  >
                    Not helpful
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-xs text-muted text-center">Thinking…</p>}
        <div ref={bottomRef} />
      </div>

      <div className="shrink-0 border-t border-borderline bg-background p-4 pb-[max(1rem,env(safe-area-inset-bottom))] z-10">
        <div className="flex gap-2 max-w-3xl mx-auto w-full">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) =>
              e.key === "Enter" && !e.shiftKey && (e.preventDefault(), send())
            }
            placeholder={
              mode === "education"
                ? "Ask about the course materials…"
                : "Ask about this symbol or the data below (optional)…"
            }
            className="flex-1 min-w-0 rounded-xl bg-surface border border-borderline px-4 py-3 text-sm text-foreground placeholder:text-muted outline-none focus:border-accent/40"
            disabled={loading}
          />
          <button
            type="button"
            onClick={send}
            disabled={loading || (mode === "education" && !input.trim())}
            className="shrink-0 rounded-xl bg-accent/15 text-accent border border-accent/25 px-5 py-3 text-sm font-medium hover:bg-accent/20 disabled:opacity-40"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}

type MarketPayload = {
  symbol: string;
  days: number;
  resolution?: string;
  quote: Record<string, number | null>;
  candles: { s?: string; t?: number[]; c?: number[] };
  answer?: string | null;
};

function MarketQuoteBlock({ data }: { data: MarketPayload }) {
  const q = data.quote;
  const fmt = (v: number | null | undefined) =>
    v != null && Number.isFinite(v) ? v.toFixed(2) : "—";
  const candles = data.candles;
  const t = candles.t ?? [];
  const lastTs = t.length > 0 ? t[t.length - 1] : null;
  const asOf =
    lastTs != null
      ? new Date(lastTs * 1000).toLocaleDateString(undefined, {
          weekday: "short",
          year: "numeric",
          month: "short",
          day: "numeric",
        })
      : null;
  const barCount = t.length;

  return (
    <div className="mt-2 space-y-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <p className="text-xl font-semibold tracking-tight text-foreground">
            {data.symbol}
          </p>
          {asOf ? (
            <p className="text-xs text-muted mt-0.5">Last session · {asOf}</p>
          ) : (
            <p className="text-xs text-muted mt-0.5">No session date</p>
          )}
        </div>
        <p className="text-[10px] uppercase tracking-wider text-muted">
          Chart: last {barCount} bar{barCount === 1 ? "" : "s"}
          {data.days ? ` (≤${data.days} requested)` : ""}
        </p>
      </div>
      <dl className="grid grid-cols-2 gap-3 sm:grid-cols-4 text-sm rounded-xl border border-borderline bg-background/30 p-3">
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            Open
          </dt>
          <dd className="font-medium tabular-nums mt-0.5">{fmt(q.o)}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            High
          </dt>
          <dd className="font-medium tabular-nums mt-0.5">{fmt(q.h)}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            Low
          </dt>
          <dd className="font-medium tabular-nums mt-0.5">{fmt(q.l)}</dd>
        </div>
        <div>
          <dt className="text-[10px] uppercase tracking-wide text-muted">
            Close
          </dt>
          <dd className="font-medium tabular-nums text-accent mt-0.5">
            {fmt(q.c)}
          </dd>
        </div>
      </dl>
    </div>
  );
}

type NewsPayload = {
  articles: Array<Record<string, unknown>>;
  warning?: string | null;
  source?: string;
  summary?: string | null;
  answer?: string | null;
};

function NewsBlock({ data }: { data: NewsPayload }) {
  const articles = data.articles ?? [];
  return (
    <div className="mt-3 space-y-2 text-xs">
      {data.warning && (
        <p className="rounded-lg border border-amber-500/25 bg-amber-500/10 px-3 py-2 text-amber-200/90 leading-snug">
          {data.warning}
        </p>
      )}
      <p className="text-[10px] uppercase tracking-wider text-muted">
        Source:{" "}
        {data.source === "yahoo_rss"
          ? "Yahoo Finance RSS (no API key)"
          : data.source === "yfinance"
            ? "yfinance / Yahoo"
            : (data.source ?? "unknown")}
      </p>
      <ul className="space-y-2 max-h-48 overflow-y-auto">
        {articles.slice(0, 8).map((a, i) => (
          <li key={i} className="border-b border-borderline pb-2">
            <a
              href={String(a.url ?? "#")}
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              {String(a.headline ?? "Headline")}
            </a>
            <span className="text-muted ml-2">{String(a.source ?? "")}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

type EduPayload = {
  answer: string;
  sources: Array<{
    content_preview: string;
    score: number;
    metadata: Record<string, unknown>;
    file_name?: string;
    page?: number;
    highlight?: string;
  }>;
  low_confidence: boolean;
};

function educationReaderHref(s: EduPayload["sources"][0]): string {
  const params = new URLSearchParams();
  const file =
    s.file_name ||
    (typeof s.metadata?.source === "string"
      ? String(s.metadata.source).split(/[/\\]/).pop()
      : "") ||
    "Full.pdf";
  params.set("file", file);
  const page =
    typeof s.page === "number"
      ? s.page
      : typeof s.metadata?.page === "number"
        ? s.metadata.page
        : 1;
  params.set("page", String(page));
  const q = (s.highlight || "").trim();
  if (q) params.set("q", q);
  return `/textbook?${params.toString()}`;
}

function EduBlock({ data }: { data: EduPayload }) {
  if (!data.sources?.length) return null;
  return (
    <div className="mt-3 border-t border-borderline pt-2 space-y-2">
      <p className="text-[10px] uppercase text-muted">Sources</p>
      {data.low_confidence && (
        <p className="text-xs text-amber-200/80">Low confidence match.</p>
      )}
      <ul className="space-y-2 text-xs text-muted max-h-48 overflow-y-auto">
        {data.sources.map((s, i) => (
          <li key={i} className="rounded-lg bg-background/40 p-2">
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <span className="text-accent/80">
                score {s.score.toFixed(3)}
              </span>
              <Link
                href={educationReaderHref(s)}
                target="_blank"
                rel="noopener noreferrer"
                prefetch={false}
                className="text-xs font-medium text-accent hover:underline"
              >
                Open in textbook
                {s.page != null || s.metadata?.page != null
                  ? ` · p.${String(s.page ?? s.metadata?.page)}`
                  : ""}
              </Link>
            </div>
            {(() => {
              const pathLabel =
                s.file_name ||
                (typeof s.metadata?.source === "string"
                  ? s.metadata.source.split(/[/\\]/).pop()
                  : "");
              if (!pathLabel) return null;
              return (
                <p
                  className="mt-0.5 text-[10px] text-muted truncate"
                  title={s.file_name ?? pathLabel}
                >
                  {pathLabel}
                </p>
              );
            })()}
            <p className="mt-1 text-foreground/80">{s.content_preview}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
