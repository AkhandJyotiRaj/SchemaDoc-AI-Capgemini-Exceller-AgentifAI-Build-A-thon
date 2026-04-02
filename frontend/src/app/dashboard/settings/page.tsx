"use client";

import { useState } from "react";
import { Settings, Save, Database, Key, Globe } from "lucide-react";
import { toast } from "sonner";

export default function SettingsPage() {
  const [backendUrl, setBackendUrl] = useState(
    process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  );

  const save = () => {
    toast.success("Settings saved (client-side only)");
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Settings</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Configure your SchemaDoc AI instance
        </p>
      </div>

      {/* Backend Connection */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="mb-4 flex items-center gap-2">
          <Globe className="h-4 w-4 text-blue-400" />
          <h2 className="text-sm font-semibold text-zinc-200">
            Backend Connection
          </h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs text-zinc-500">
              API Base URL
            </label>
            <input
              type="text"
              value={backendUrl}
              onChange={(e) => setBackendUrl(e.target.value)}
              className="w-full rounded-lg border border-zinc-700 bg-zinc-800 px-3 py-2 font-mono text-sm text-zinc-200 outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      {/* About */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="mb-4 flex items-center gap-2">
          <Database className="h-4 w-4 text-violet-400" />
          <h2 className="text-sm font-semibold text-zinc-200">About</h2>
        </div>

        <div className="space-y-2 text-xs text-zinc-500">
          <div className="flex justify-between">
            <span>Version</span>
            <span className="font-mono text-zinc-400">1.0.0-beta</span>
          </div>
          <div className="flex justify-between">
            <span>AI Model</span>
            <span className="font-mono text-zinc-400">Gemini 2.5 Flash</span>
          </div>
          <div className="flex justify-between">
            <span>Framework</span>
            <span className="font-mono text-zinc-400">
              Next.js + FastAPI + LangGraph
            </span>
          </div>
        </div>
      </div>

      <button
        onClick={save}
        className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-500"
      >
        <Save className="h-4 w-4" />
        Save Settings
      </button>
    </div>
  );
}
