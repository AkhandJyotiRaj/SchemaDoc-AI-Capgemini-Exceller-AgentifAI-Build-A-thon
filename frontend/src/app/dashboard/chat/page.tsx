"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { PipelineRun } from "@/lib/api";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  Bot,
  User,
  Loader2,
  Sparkles,
  MessageSquare,
  Copy,
  Check,
  AlertCircle,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sql?: string;
  timestamp: Date;
}

function CodeBlock({ code }: { code: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-2 overflow-hidden rounded-lg border border-zinc-700">
      <div className="flex items-center justify-between bg-zinc-800 px-3 py-1.5">
        <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">
          SQL
        </span>
        <button
          onClick={copy}
          className="text-zinc-500 hover:text-zinc-300 transition-colors"
        >
          {copied ? (
            <Check className="h-3.5 w-3.5 text-emerald-400" />
          ) : (
            <Copy className="h-3.5 w-3.5" />
          )}
        </button>
      </div>
      <pre className="overflow-x-auto bg-zinc-900 p-3 font-mono text-xs text-blue-300">
        {code}
      </pre>
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    if (typeof window !== "undefined") {
      try {
        const saved = localStorage.getItem("schemadoc-chat");
        return saved ? JSON.parse(saved) : [];
      } catch {
        return [];
      }
    }
    return [];
  });
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Get the latest pipeline run for context
  const { data: runs = [] } = useQuery<PipelineRun[]>({
    queryKey: ["runs"],
    queryFn: api.listRuns,
  });

  const latestRun = runs.find((r) => r.status === "completed") || null;

  // Persist messages to localStorage
  useEffect(() => {
    if (typeof window !== "undefined") {
      localStorage.setItem("schemadoc-chat", JSON.stringify(messages));
    }
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const mutation = useMutation({
    mutationFn: (question: string) =>
      api.sendChatMessage({ question, run_id: latestRun?.run_id || "" }),
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.response,
          sql: data.sql_query ?? undefined,
          timestamp: new Date(),
        },
      ]);
    },
    onError: (err: Error) => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err.message}. Make sure you've run the pipeline first.`,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const send = () => {
    const q = input.trim();
    if (!q || mutation.isPending) return;

    setMessages((prev) => [
      ...prev,
      { role: "user", content: q, timestamp: new Date() },
    ]);
    setInput("");
    mutation.mutate(q);
  };

  const clearChat = useCallback(() => {
    setMessages([]);
    localStorage.removeItem("schemadoc-chat");
  }, []);

  const suggestions = [
    "Show me all tables with foreign key relationships",
    "Which tables have the most columns?",
    "Find all columns that store dates or timestamps",
    "What are the primary keys across all tables?",
  ];

  return (
    <div className="mx-auto flex h-[calc(100vh-140px)] max-w-4xl flex-col">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">AI Chat</h1>
          <p className="mt-1 text-sm text-zinc-500">
            {latestRun
              ? `Connected to run ${latestRun.run_id} — Ask about your schema`
              : "Run the pipeline first to enable chat"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!latestRun && (
            <span className="flex items-center gap-1.5 rounded-lg bg-amber-500/10 px-3 py-1.5 text-xs text-amber-400">
              <AlertCircle className="h-3.5 w-3.5" /> No pipeline run
            </span>
          )}
          {messages.length > 0 && (
            <button
              onClick={clearChat}
              className="rounded-lg border border-zinc-700 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800"
            >
              Clear Chat
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-blue-500/10">
              <Sparkles className="h-8 w-8 text-blue-400" />
            </div>
            <h2 className="mb-2 text-lg font-semibold text-zinc-200">
              Ask anything about your schema
            </h2>
            <p className="mb-8 text-sm text-zinc-500">
              I can help you understand your database structure, find
              relationships, and generate SQL queries.
            </p>

            {/* Suggestions */}
            <div className="grid max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900/50 px-3 py-2 text-left text-xs text-zinc-400 transition-colors hover:border-zinc-700 hover:text-zinc-300"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <AnimatePresence>
              {messages.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "flex gap-3",
                    msg.role === "user" ? "justify-end" : "justify-start",
                  )}
                >
                  {msg.role === "assistant" && (
                    <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-blue-500/10">
                      <Bot className="h-4 w-4 text-blue-400" />
                    </div>
                  )}

                  <div
                    className={cn(
                      "max-w-[80%] rounded-xl px-4 py-3",
                      msg.role === "user"
                        ? "bg-blue-600 text-white"
                        : "bg-zinc-800 text-zinc-200",
                    )}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose-sm text-sm text-zinc-200 [&_p]:my-1 [&_ul]:my-1.5 [&_ol]:my-1.5 [&_li]:my-0.5 [&_ul]:list-disc [&_ul]:pl-4 [&_ol]:list-decimal [&_ol]:pl-4 [&_strong]:text-zinc-100 [&_strong]:font-semibold [&_code]:rounded [&_code]:bg-zinc-700 [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-blue-300 [&_code]:text-xs [&_pre]:my-2 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-zinc-900 [&_pre]:p-3 [&_pre_code]:bg-transparent [&_pre_code]:p-0 [&_h1]:text-base [&_h1]:font-bold [&_h1]:text-zinc-100 [&_h2]:text-sm [&_h2]:font-bold [&_h2]:text-zinc-100 [&_h3]:text-sm [&_h3]:font-semibold [&_h3]:text-zinc-200 [&_a]:text-blue-400 [&_a]:underline [&_blockquote]:border-l-2 [&_blockquote]:border-zinc-600 [&_blockquote]:pl-3 [&_blockquote]:text-zinc-400 [&_hr]:border-zinc-700">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {msg.content}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">
                        {msg.content}
                      </p>
                    )}
                    {msg.sql && <CodeBlock code={msg.sql} />}
                  </div>

                  {msg.role === "user" && (
                    <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-zinc-700">
                      <User className="h-4 w-4 text-zinc-300" />
                    </div>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {mutation.isPending && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-500/10">
                  <Bot className="h-4 w-4 text-blue-400" />
                </div>
                <div className="rounded-xl bg-zinc-800 px-4 py-3">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-400" />
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="mt-3 flex items-center gap-2">
        <div className="relative flex-1">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && send()}
            placeholder="Ask about your database schema..."
            className="w-full rounded-xl border border-zinc-700 bg-zinc-900 py-3 pl-4 pr-12 text-sm text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-blue-500/50"
          />
          <button
            onClick={send}
            disabled={!input.trim() || mutation.isPending}
            className={cn(
              "absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-2 transition-all",
              input.trim() && !mutation.isPending
                ? "bg-blue-600 text-white hover:bg-blue-500"
                : "text-zinc-600",
            )}
          >
            <Send className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
