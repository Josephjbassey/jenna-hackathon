"use client";

import React, { useState } from "react";
import {
  Brain,
  Sparkles,
  ShoppingBag,
  Tag,
  DollarSign,
  Package,
  Code2,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import {
  StorefrontSchema,
  InventoryItem,
  BoundingBox,
  StructuredReasoningOutput,
} from "@/lib/api";

interface MultimodalReasoningPanelProps {
  storeSchema: StorefrontSchema | null;
  structuredOutput: StructuredReasoningOutput | null;
  selectedBox: BoundingBox | null;
  onGenerateCode: () => void;
  isGeneratingCode: boolean;
}

export const MultimodalReasoningPanel: React.FC<MultimodalReasoningPanelProps> = ({
  storeSchema,
  structuredOutput,
  selectedBox,
  onGenerateCode,
  isGeneratingCode,
}) => {
  const [showJson, setShowJson] = useState(false);

  const inventory = storeSchema?.inventory || [];
  const currency = storeSchema?.currency || "NGN";

  const totalValue = inventory.reduce(
    (sum, item) => sum + item.suggested_price * item.estimated_quantity,
    0
  );

  return (
    <div className="flex flex-col h-full bg-[#0d1117] rounded-2xl border border-white/10 p-4 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4 text-amber-400" />
          <h2 className="font-semibold text-xs text-slate-100 uppercase tracking-wider font-mono">
            Muse Spark 1.3 · Cognitive Market Reasoning
          </h2>
        </div>
        <button
          onClick={onGenerateCode}
          disabled={isGeneratingCode || inventory.length === 0}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-white hover:bg-slate-200 text-black active:translate-y-0.5 transition-all disabled:opacity-40"
        >
          <Code2 className={`w-3.5 h-3.5 ${isGeneratingCode ? "animate-spin" : ""}`} />
          <span>{isGeneratingCode ? "Synthesizing..." : "Synthesize Store (Muse Code)"}</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-2.5 my-3">
        <div className="bg-[#161b22] border border-white/10 rounded-xl p-2.5 text-center">
          <span className="text-[10px] uppercase font-mono text-slate-400 block mb-0.5">
            Cataloged Items
          </span>
          <span className="text-sm font-bold text-slate-100 font-mono">
            {inventory.length} SKUs
          </span>
        </div>

        <div className="bg-[#161b22] border border-white/10 rounded-xl p-2.5 text-center">
          <span className="text-[10px] uppercase font-mono text-slate-400 block mb-0.5">
            Shelf Stock
          </span>
          <span className="text-sm font-bold text-emerald-400 font-mono">
            {inventory.reduce((a, b) => a + b.estimated_quantity, 0)} units
          </span>
        </div>

        <div className="bg-[#161b22] border border-white/10 rounded-xl p-2.5 text-center">
          <span className="text-[10px] uppercase font-mono text-slate-400 block mb-0.5">
            Est. Shelf Value
          </span>
          <span className="text-sm font-bold text-amber-400 font-mono">
            {totalValue.toLocaleString()} {currency}
          </span>
        </div>
      </div>

      {/* Product Catalog List */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {inventory.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <ShoppingBag className="w-8 h-8 mb-2 opacity-40 text-slate-400" />
            <p className="text-xs">No physical items scanned yet.</p>
            <p className="text-[11px] text-slate-600 mt-1">
              Click &quot;1-Click Store Scan&quot; to run SAM 3.1 &amp; Muse Spark.
            </p>
          </div>
        ) : (
          inventory.map((item) => {
            const isTargeted = selectedBox?.box_id === item.image_segment_id;
            return (
              <div
                key={item.item_id}
                className={`p-3 rounded-xl border transition-all ${
                  isTargeted
                    ? "bg-[#1f242c] border-white/30 shadow-sm"
                    : "bg-[#161b22] border-white/5 hover:border-white/15"
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        isTargeted ? "bg-cyan-400 animate-ping" : "bg-emerald-400"
                      }`}
                    />
                    <h3 className="font-semibold text-xs text-slate-100">{item.name}</h3>
                  </div>
                  <span className="font-mono font-bold text-xs text-amber-400">
                    {item.suggested_price.toLocaleString()} {currency}
                  </span>
                </div>

                <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
                  {item.description}
                </p>

                <div className="flex items-center justify-between mt-2 pt-2 border-t border-white/5 text-[10px] font-mono text-slate-400">
                  <span className="px-2 py-0.5 rounded bg-[#0d1117] border border-white/5 text-slate-300">
                    {item.category}
                  </span>
                  <span>Stock: {item.estimated_quantity} units</span>
                  <span className="text-slate-500">ID: {item.image_segment_id}</span>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* JSON Schema Drawer Toggle */}
      <div className="pt-2.5 border-t border-white/10">
        <button
          onClick={() => setShowJson(!showJson)}
          className="flex items-center justify-between w-full text-slate-400 hover:text-slate-200 text-[11px] font-mono transition-colors"
        >
          <span>StorefrontSchema JSON Contract</span>
          {showJson ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
        </button>

        {showJson && storeSchema && (
          <pre className="mt-2 p-2.5 bg-[#090b0e] border border-white/10 rounded-lg text-[10px] font-mono text-emerald-400 overflow-x-auto max-h-36">
            {JSON.stringify(storeSchema, null, 2)}
          </pre>
        )}
      </div>
    </div>
  );
};
