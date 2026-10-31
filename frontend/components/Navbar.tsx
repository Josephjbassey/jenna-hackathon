"use client";

import React from "react";
import {
  Cpu,
  Activity,
  Layers,
  Database,
  Terminal,
  ShieldCheck,
  Radio,
} from "lucide-react";
import { SquadRoleInfo } from "@/lib/api";

interface NavbarProps {
  activeRole: string;
  onSelectRole: (role: string) => void;
  roles: SquadRoleInfo[];
  backendConnected: boolean;
  onOpenMemory: () => void;
  onOpenQueue: () => void;
  activeView: "dashboard" | "queue" | "memory";
  setActiveView: (view: "dashboard" | "queue" | "memory") => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeRole,
  onSelectRole,
  roles,
  backendConnected,
  activeView,
  setActiveView,
}) => {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-[#0d131f]/90 backdrop-blur-md px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand / Logo */}
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 p-[1px] shadow-lg shadow-cyan-500/20">
            <div className="w-full h-full bg-[#0b0f17] rounded-[11px] flex items-center justify-center">
              <span className="text-cyan-400 font-mono font-bold text-lg">J</span>
            </div>
            <span className="absolute -bottom-0.5 -right-0.5 flex h-2.5 w-2.5">
              <span
                className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                  backendConnected ? "bg-emerald-400" : "bg-amber-400"
                }`}
              />
              <span
                className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                  backendConnected ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
            </span>
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-bold text-slate-100 tracking-wide text-base">
                JENNA <span className="text-cyan-400 font-light">AI</span>
              </h1>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/60 text-cyan-300">
                v2.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Decoupled Next.js + FastAPI • SAM 3.1 & Muse Spark 1.3
            </p>
          </div>
        </div>

        {/* Squad Roles Quick Tabs */}
        <div className="hidden lg:flex items-center space-x-1.5 bg-slate-900/80 p-1 rounded-xl border border-slate-800">
          {roles.map((r) => {
            const isActive = activeRole === r.role;
            return (
              <button
                key={r.role}
                onClick={() => onSelectRole(r.role)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
                  isActive
                    ? "bg-cyan-500/15 border border-cyan-500/40 text-cyan-300 shadow-sm shadow-cyan-500/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 border border-transparent"
                }`}
              >
                <span>{r.name.replace("Jenna ", "")}</span>
                <span className="text-[10px] font-mono opacity-60">
                  [{r.model.replace("muse-", "").replace("-1.3", "").replace("-1.0", "")}]
                </span>
              </button>
            );
          })}
        </div>

        {/* Actions / Telemetry Nav */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveView("dashboard")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              activeView === "dashboard"
                ? "bg-slate-800 text-cyan-300 border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Workspace</span>
          </button>

          <button
            onClick={() => setActiveView("queue")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              activeView === "queue"
                ? "bg-slate-800 text-cyan-300 border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Inference Queue</span>
          </button>

          <button
            onClick={() => setActiveView("memory")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
              activeView === "memory"
                ? "bg-slate-800 text-cyan-300 border-cyan-500/30"
                : "text-slate-400 hover:text-slate-200 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <Database className="w-3.5 h-3.5 text-purple-400" />
            <span className="hidden sm:inline">Cross Memory</span>
          </button>
        </div>
      </div>
    </header>
  );
};
