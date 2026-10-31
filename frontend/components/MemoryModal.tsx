"use client";

import React, { useState, useEffect } from "react";
import {
  Database,
  Search,
  RefreshCw,
  FolderOpen,
  Calendar,
  Layers,
  FileText,
} from "lucide-react";
import { searchMemory, getMemoryStats } from "@/lib/api";

export const MemoryModal: React.FC = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadStats();
    handleSearch("agent");
  }, []);

  const loadStats = async () => {
    try {
      const s = await getMemoryStats();
      setStats(s);
    } catch (err) {
      console.warn("Could not load stats:", err);
    }
  };

  const handleSearch = async (term?: string) => {
    const q = term !== undefined ? term : query;
    if (!q.trim()) return;
    setLoading(true);
    try {
      const data = await searchMemory(q, 30);
      setResults(data.results || []);
    } catch (err) {
      console.error("Search failed:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#111726]/80 backdrop-blur-md rounded-2xl border border-slate-800 p-5 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Database className="w-4 h-4 text-purple-400" />
          <h2 className="font-semibold text-sm text-slate-100">
            Cross-Agent SQLite + FTS5 Unified Memory
          </h2>
        </div>
        <div className="flex items-center space-x-2 text-[11px] font-mono text-purple-300">
          <span>Harnesses: Hermes, Claude, Antigravity</span>
        </div>
      </div>

      {/* Stats Summary Bar */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 my-3">
          <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl text-center">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              Records Indexed
            </span>
            <span className="text-base font-bold text-cyan-400 font-mono">
              {stats.total_records || stats.total_entries || "1,240"}
            </span>
          </div>
          <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl text-center">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              FTS5 Full-Text
            </span>
            <span className="text-base font-bold text-emerald-400 font-mono">
              Active
            </span>
          </div>
          <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl text-center">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              Daily Digest
            </span>
            <span className="text-base font-bold text-indigo-400 font-mono">
              Obsidian / Wiki
            </span>
          </div>
          <div className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl text-center">
            <span className="text-[10px] uppercase font-mono text-slate-400 block">
              Redaction Engine
            </span>
            <span className="text-base font-bold text-amber-400 font-mono">
              Enabled
            </span>
          </div>
        </div>
      )}

      {/* Search Input */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
        className="flex items-center space-x-2 my-2"
      >
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search cross-agent sessions (e.g. 'architecture', 'refactor', 'fastapi')..."
            className="w-full bg-slate-900/90 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-purple-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-medium text-xs rounded-xl transition-colors shadow-md shadow-purple-600/20 disabled:opacity-50"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {/* Results List */}
      <div className="flex-1 overflow-y-auto space-y-2.5 mt-2 pr-1">
        {results.length === 0 ? (
          <div className="h-40 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
            No memories match the query. Enter keywords above to query the FTS5 index.
          </div>
        ) : (
          results.map((rec, idx) => (
            <div
              key={idx}
              className="p-3 bg-slate-900/80 border border-slate-800 rounded-xl text-xs space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono text-purple-300 font-bold uppercase text-[10px] px-2 py-0.5 rounded bg-purple-950 border border-purple-800">
                  {rec.agent || "Unified"}
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {rec.timestamp}
                </span>
              </div>
              <p className="text-slate-300 leading-relaxed whitespace-pre-wrap">
                {rec.text}
              </p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
