"use client";

import React, { useState } from "react";
import {
  Code,
  Smartphone,
  ExternalLink,
  ShoppingBag,
  Check,
  Copy,
  Layers,
  Sparkles,
  PhoneCall,
  Terminal,
} from "lucide-react";
import { StorefrontSchema, CodeGenerateResponse } from "@/lib/api";

interface StorefrontPreviewProps {
  storeSchema: StorefrontSchema | null;
  codeResponse: CodeGenerateResponse | null;
}

export const StorefrontPreview: React.FC<StorefrontPreviewProps> = ({
  storeSchema,
  codeResponse,
}) => {
  const [activeTab, setActiveTab] = useState<"preview" | "code">("preview");
  const [selectedFile, setSelectedFile] = useState<string>("app/page.tsx");
  const [cart, setCart] = useState<{ [id: string]: number }>({});
  const [copied, setCopied] = useState(false);

  const inventory = storeSchema?.inventory || [];
  const currency = storeSchema?.currency || "NGN";
  const files = codeResponse?.repository_files || {};

  const addToCart = (id: string) => {
    setCart((prev) => ({ ...prev, [id]: (prev[id] || 0) + 1 }));
  };

  const totalItems = Object.values(cart).reduce((a, b) => a + b, 0);
  const totalPrice = inventory.reduce(
    (sum, item) => sum + (cart[item.item_id] || 0) * item.suggested_price,
    0
  );

  const handleWhatsAppOrder = () => {
    const lines = inventory
      .filter((p) => cart[p.item_id])
      .map(
        (p) =>
          `- ${p.name} x${cart[p.item_id]} (${(p.suggested_price * cart[p.item_id]).toLocaleString()} ${currency})`
      );
    const msg = encodeURIComponent(
      `Hello ${storeSchema?.store_title || "Merchant"}! I would like to order:\n${lines.join(
        "\n"
      )}\n\nTotal: ${totalPrice.toLocaleString()} ${currency}`
    );
    const phone = storeSchema?.whatsapp_number?.replace("+", "") || "2348012345678";
    window.open(`https://wa.me/${phone}?text=${msg}`, "_blank");
  };

  const copyCode = () => {
    if (files[selectedFile]) {
      navigator.clipboard.writeText(files[selectedFile]);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d1117] rounded-2xl border border-white/10 p-5 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-white/10">
        <div className="flex items-center space-x-2">
          <Code className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold text-xs text-slate-100 uppercase tracking-wider font-mono">
            Muse Code · Synthesized Mobile-First Storefront
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 bg-[#161b22] border border-white/10 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("preview")}
              className={`flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-medium transition-all ${
                activeTab === "preview"
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span>Mobile Live View</span>
            </button>
            <button
              onClick={() => setActiveTab("code")}
              className={`flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-medium transition-all ${
                activeTab === "code"
                  ? "bg-white text-black font-semibold shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Generated Code ({Object.keys(files).length || 4})</span>
            </button>
          </div>

          {codeResponse?.preview_url && (
            <a
              href={codeResponse.preview_url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#161b22] hover:bg-[#21262d] text-slate-200 border border-white/10 transition-colors"
            >
              <span>Instant Deploy</span>
              <ExternalLink className="w-3 h-3 text-slate-400" />
            </a>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 mt-4 overflow-hidden flex items-center justify-center min-h-[640px]">
        {activeTab === "preview" ? (
          /* Mobile Phone Frame Simulator */
          <div className="w-[370px] h-[660px] bg-[#07090e] rounded-[40px] border-4 border-slate-700 shadow-2xl flex flex-col overflow-hidden relative">
            {/* Phone Notch */}
            <div className="h-6 bg-[#0d1117] flex justify-center items-center">
              <div className="w-24 h-3.5 bg-black rounded-b-xl" />
            </div>

            {/* Mobile Webview Header */}
            <div className="bg-[#111620] border-b border-white/10 p-3.5 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-xs text-slate-100 truncate max-w-[190px]">
                  {storeSchema?.store_title || "Mama Cass Market"}
                </h3>
                <p className="text-[10px] text-slate-400 truncate">
                  {storeSchema?.location || "Akure Central Market, Nigeria"} • Open Now
                </p>
              </div>
              <div className="px-2.5 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800 text-[10px] font-mono font-bold text-emerald-300">
                Cart: {totalItems}
              </div>
            </div>

            {/* Mobile Product Feed */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2.5 pb-24">
              {inventory.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-slate-500 text-xs text-center">
                  Storefront empty. Complete Step 1 scan to synthesize products.
                </div>
              ) : (
                inventory.map((item) => (
                  <div
                    key={item.item_id}
                    className="p-3 bg-[#111620] border border-white/5 rounded-xl space-y-1.5"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-semibold text-xs text-slate-100">
                          {item.name}
                        </h4>
                        <span className="text-xs font-mono font-bold text-amber-400">
                          {item.suggested_price.toLocaleString()} {currency}
                        </span>
                      </div>
                      <button
                        onClick={() => addToCart(item.item_id)}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 active:translate-y-0.5 text-white rounded-lg text-[10px] font-bold shadow-sm transition-all"
                      >
                        + Add {cart[item.item_id] ? `(${cart[item.item_id]})` : ""}
                      </button>
                    </div>
                    <p className="text-[10px] text-slate-400 leading-tight">
                      {item.description}
                    </p>
                  </div>
                ))
              )}
            </div>

            {/* Sticky WhatsApp Checkout Bar */}
            {totalItems > 0 && (
              <div className="absolute bottom-3 left-3 right-3 p-3 bg-[#111620]/95 backdrop-blur-md border border-white/10 rounded-2xl flex justify-between items-center shadow-2xl">
                <div>
                  <span className="text-[9px] text-slate-400 uppercase font-mono block">
                    Total Due
                  </span>
                  <span className="text-xs font-bold font-mono text-emerald-400">
                    {totalPrice.toLocaleString()} {currency}
                  </span>
                </div>
                <button
                  onClick={handleWhatsAppOrder}
                  className="px-4 py-2 bg-[#25D366] hover:bg-[#20ba59] active:translate-y-0.5 text-black font-bold rounded-xl text-xs flex items-center space-x-1.5 shadow-lg shadow-emerald-950 transition-all"
                >
                  <PhoneCall className="w-3.5 h-3.5" />
                  <span>Order on WhatsApp</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Code Inspector View */
          <div className="w-full h-full flex flex-col bg-[#07090e] rounded-xl border border-white/10 overflow-hidden">
            {/* File Tab Strip */}
            <div className="flex items-center justify-between bg-[#111620] px-3 py-2 border-b border-white/10">
              <div className="flex items-center space-x-1 overflow-x-auto">
                {Object.keys(files).map((fileName) => (
                  <button
                    key={fileName}
                    onClick={() => setSelectedFile(fileName)}
                    className={`px-3 py-1 rounded text-xs font-mono transition-colors ${
                      selectedFile === fileName
                        ? "bg-white text-black font-semibold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {fileName}
                  </button>
                ))}
              </div>

              <button
                onClick={copyCode}
                className="flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-mono text-slate-300 hover:text-white bg-[#161b22] border border-white/10"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>

            {/* Code Body */}
            <div className="flex-1 p-4 overflow-y-auto font-mono text-xs text-slate-300 leading-relaxed bg-[#07090e]">
              <pre>{files[selectedFile] || "// Synthesizing repository files with Muse Code..."}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
