"use client";

import React from "react";
import {
  Store,
  Layers,
  Sparkles,
  ShoppingBag,
  Activity,
  ArrowRight,
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
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#090b0e]/95 backdrop-blur-md px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand & Identity */}
        <div className="flex items-center space-x-3.5">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-lg bg-[#161b22] border border-white/15 text-emerald-400 shadow-sm">
            <Store className="w-4 h-4" />
            <span
              className={`absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full border-2 border-[#090b0e] ${
                backendConnected ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
          </div>

          <div>
            <div className="flex items-center space-x-2">
              <h1 className="font-semibold text-slate-100 tracking-tight text-sm">
                OmniStore <span className="text-emerald-400 font-normal">AI</span>
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800/50 text-emerald-300">
                Build for Your World
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono">
              Physical-to-Digital Micro-Commerce · SAM 3.1 + Muse Spark + Muse Code
            </p>
          </div>
        </div>

        {/* 3-Model Pipeline Status Indicators */}
        <div className="hidden lg:flex items-center space-x-2 bg-[#12161f] px-3 py-1.5 rounded-lg border border-white/10 text-xs font-mono">
          <div className="flex items-center space-x-1.5 text-cyan-400">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
            <span>Eyes: SAM 3.1</span>
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center space-x-1.5 text-amber-400">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
            <span>Brain: Muse Spark</span>
          </div>
          <span className="text-slate-600">→</span>
          <div className="flex items-center space-x-1.5 text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <span>Hands: Muse Code</span>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center space-x-1.5 bg-[#12161f] p-1 rounded-xl border border-white/10">
          <button
            onClick={() => setActiveTab("pipeline")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "pipeline"
                ? "bg-white text-black font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Pipeline Studio</span>
          </button>

          <button
            onClick={() => setActiveTab("storefront")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "storefront"
                ? "bg-white text-black font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <ShoppingBag className="w-3.5 h-3.5" />
            <span>Storefront ({inventoryCount})</span>
          </button>

          <button
            onClick={() => setActiveTab("queue")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === "queue"
                ? "bg-white text-black font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Async Queue</span>
          </button>
        </div>
      </div>
    </header>
  );
};
