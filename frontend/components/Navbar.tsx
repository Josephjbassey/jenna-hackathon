"use client";

import React from "react";
import {
  Store,
  Layers,
  Sparkles,
  Code,
  Activity,
  ShoppingBag,
} from "lucide-react";

interface NavbarProps {
  backendConnected: boolean;
  activeTab: "pipeline" | "storefront" | "queue";
  setActiveTab: (tab: "pipeline" | "storefront" | "queue") => void;
  inventoryCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  backendConnected,
  activeTab,
  setActiveTab,
  inventoryCount,
}) => {
  return (
    <header className="sticky top-0 z-50 border-b border-slate-800 bg-[#0d131f]/95 backdrop-blur-md px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 via-cyan-500 to-indigo-600 p-[1px] shadow-lg shadow-emerald-500/20">
            <div className="w-full h-full bg-[#0b0f17] rounded-[11px] flex items-center justify-center">
              <Store className="w-5 h-5 text-emerald-400" />
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
                OmniStore <span className="text-emerald-400 font-light">AI</span>
              </h1>
              <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-800/60 text-emerald-300">
                Build for Your World
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Physical-to-Digital Micro-Commerce • SAM 3.1 + Muse Spark + Muse Code
            </p>
          </div>
        </div>

        {/* Pipeline Badges */}
        <div className="hidden md:flex items-center space-x-2 bg-slate-900/90 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <div className="flex items-center space-x-1.5 text-cyan-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            <span>Eyes: SAM 3.1</span>
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center space-x-1.5 text-purple-400">
            <span className="w-2 h-2 rounded-full bg-purple-400" />
            <span>Brain: Muse Spark</span>
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center space-x-1.5 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400" />
            <span>Hands: Muse Code</span>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              activeTab === "pipeline"
                ? "bg-slate-800 text-emerald-300 border-emerald-500/40 shadow-sm"
                : "text-slate-400 hover:text-slate-200 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
            <span>Pipeline Studio</span>
          </button>

          <button
            onClick={() => setActiveTab("storefront")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              activeTab === "storefront"
                ? "bg-slate-800 text-emerald-300 border-emerald-500/40 shadow-sm"
                : "text-slate-400 hover:text-slate-200 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <ShoppingBag className="w-3.5 h-3.5 text-cyan-400" />
            <span>Synthesized Store ({inventoryCount})</span>
          </button>

          <button
            onClick={() => setActiveTab("queue")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              activeTab === "queue"
                ? "bg-slate-800 text-emerald-300 border-emerald-500/40 shadow-sm"
                : "text-slate-400 hover:text-slate-200 border-slate-800 hover:bg-slate-850"
            }`}
          >
            <Activity className="w-3.5 h-3.5 text-indigo-400" />
            <span className="hidden sm:inline">Async Queue</span>
          </button>
        </div>
      </div>
    </header>
  );
};
