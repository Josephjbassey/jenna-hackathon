"use client";

import React, { useState } from "react";
import {
  Brain,
  Sparkles,
  ShoppingBag,
  Tag,
  DollarSign,
  Package,
  CheckCircle2,
  Code2,
  ChevronDown,
  ChevronRight,
  Send,
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
    <div className="flex flex-col h-full bg-[#111726]/85 backdrop-blur-md rounded-2xl border border-slate-800 p-4 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Brain className="w-4 h-4 text-purple-400" />
          <h2 className="font-semibold text-sm text-slate-100">
            Muse Spark 1.3 (Cognitive Reasoning & Localized Pricing)
          </h2>
        </div>
        <button
          onClick={onGenerateCode}
          disabled={isGeneratingCode || inventory.length === 0}
          className="flex items-center space-x-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-purple-600 hover:bg-purple-500 text-white shadow-md shadow-purple-600/20 transition-all disabled:opacity-50"
        >
          <Sparkles className={`w-3.5 h-3.5 ${isGeneratingCode ? "animate-spin" : ""}`} />
          <span>{isGeneratingCode ? "Synthesizing..." : "Synthesize Store (Muse Code)"}</span>
        </button>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-3 gap-2.5 my-3">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-center">
          <span className="text-[10px] uppercase font-mono text-slate-400 block">
            Cataloged Items
          </span>
          <span className="text-base font-bold text-cyan-400 font-mono">
            {inventory.length} SKUs
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-center">
          <span className="text-[10px] uppercase font-mono text-slate-400 block">
            Total Shelf Stock
          </span>
          <span className="text-base font-bold text-emerald-400 font-mono">
            {inventory.reduce((a, b) => a + b.estimated_quantity, 0)} units
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-center">
          <span className="text-[10px] uppercase font-mono text-slate-400 block">
            Est. Shelf Value
          </span>
          <span className="text-base font-bold text-amber-400 font-mono">
            {totalValue.toLocaleString()} {currency}
          </span>
        </div>
      </div>

      {/* Product Catalog List */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {inventory.length === 0 ? (
          <div className="h-40 flex flex-col items-center justify-center border border-dashed border-slate-800 rounded-xl text-slate-500 text-xs">
            No items cataloged yet. Run a physical store scan above.
          </div>
        ) : (
          inventory.map((item) => {
            const isHighlighted = selectedBox?.box_id === item.image_segment_id;
            return (
              <div
                key={item.item_id}
                className={`p-3 rounded-xl border transition-all ${
                  isHighlighted
                    ? "bg-purple-950/30 border-purple-400 shadow-md shadow-purple-500/10"
                    : "bg-slate-900/80 border-slate-800 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-emerald-400" />
                    <h3 className="font-semibold text-xs text-slate-200">
                      {item.name}
                    </h3>
                  </div>
                  <span className="font-mono text-xs font-bold text-emerald-400">
                    {item.suggested_price.toLocaleString()} {currency}
                  </span>
                </div>

                <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                  {item.description}
                </p>

                <div className="flex items-center justify-between mt-2 pt-1.5 border-t border-slate-800/60 text-[10px] font-mono text-slate-400">
                  <span className="px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-purple-300">
                    {item.category}
                  </span>
                  <span>Stock: {item.estimated_quantity} units</span>
                  <span className="text-cyan-400">ID: {item.image_segment_id}</span>
                </div>
              </div>
            );
          })
        )}

        {/* JSON Schema Accordion */}
        {storeSchema && (
          <div className="border border-slate-800 rounded-xl overflow-hidden mt-3">
            <button
              onClick={() => setShowJson(!showJson)}
              className="w-full flex items-center justify-between p-2.5 bg-slate-900 text-xs text-slate-400 font-mono transition-colors"
            >
              <div className="flex items-center space-x-1.5">
                <Code2 className="w-3.5 h-3.5 text-purple-400" />
                <span>StorefrontSchema (Muse Spark Output)</span>
              </div>
              {showJson ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
            </button>
            {showJson && (
              <pre className="p-3 bg-slate-950 text-[11px] font-mono text-purple-300 overflow-x-auto max-h-48">
                {JSON.stringify(storeSchema, null, 2)}
              </pre>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
