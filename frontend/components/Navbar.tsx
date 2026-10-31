"use client";

import React from "react";
import {
  Store,
  Layers,
  Sparkles,
  Smartphone,
  Code2,
} from "lucide-react";

interface NavbarProps {
  backendConnected: boolean;
  activeTab: "demo" | "storefront" | "architecture";
  setActiveTab: (tab: "demo" | "storefront" | "architecture") => void;
  inventoryCount: number;
}

export const Navbar: React.FC<NavbarProps> = ({
  backendConnected,
  activeTab,
  setActiveTab,
  inventoryCount,
}) => {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#0c0f16]/95 backdrop-blur-md px-4 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Store className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-sm tracking-tight text-white">OmniStore AI</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/70 border border-emerald-800/50 text-emerald-300">
                Build for Your World
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Snap a stall photo → Get a WhatsApp online store in seconds
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-1.5 bg-[#141822] p-1 rounded-xl border border-white/10">
          <button
            onClick={() => setActiveTab("demo")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "demo"
                ? "bg-white text-black shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Interactive Studio</span>
          </button>

          <button
            onClick={() => setActiveTab("storefront")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "storefront"
                ? "bg-white text-black shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Smartphone className="w-3.5 h-3.5" />
            <span>Customer Storefront ({inventoryCount})</span>
          </button>

          <button
            onClick={() => setActiveTab("architecture")}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "architecture"
                ? "bg-white text-black shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Code2 className="w-3.5 h-3.5" />
            <span>Under The Hood</span>
          </button>
        </div>
      </div>
    </header>
  );
};
