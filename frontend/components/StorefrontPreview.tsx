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
      `Hello ${storeSchema?.store_title || "Merchant"}! I want to order:\n${lines.join(
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
    <div className="flex flex-col h-full bg-[#111726]/85 backdrop-blur-md rounded-2xl border border-slate-800 p-5 shadow-xl">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
        <div className="flex items-center space-x-2">
          <Code className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold text-sm text-slate-100">
            Muse Code (Synthesized Mobile-First Storefront)
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 bg-slate-900 border border-slate-800 p-1 rounded-lg">
            <button
              onClick={() => setActiveTab("preview")}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                activeTab === "preview"
                  ? "bg-emerald-500/20 text-emerald-300 font-bold"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" />
              <span>Mobile Live View</span>
            </button>
            <button
              onClick={() => setActiveTab("code")}
              className={`flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                activeTab === "code"
                  ? "bg-purple-500/20 text-purple-300 font-bold"
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
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg text-xs font-bold bg-cyan-600 hover:bg-cyan-500 text-white transition-colors shadow-md"
            >
              <span>Instant Deploy</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 mt-4 overflow-hidden flex items-center justify-center">
        {activeTab === "preview" ? (
          /* Mobile Phone Frame Simulator */
          <div className="w-[360px] h-[640px] bg-slate-950 rounded-[36px] border-4 border-slate-700 shadow-2xl flex flex-col overflow-hidden relative">
            {/* Phone Notch */}
            <div className="h-5 bg-slate-900 flex justify-center items-center">
              <div className="w-20 h-3 bg-black rounded-b-xl" />
            </div>

            {/* Mobile Webview Header */}
            <div className="bg-slate-900 border-b border-slate-800 p-3 flex justify-between items-center">
              <div>
                <h3 className="font-bold text-xs text-emerald-400 truncate max-w-[190px]">
                  {storeSchema?.store_title || "Mama Cass Market"}
                </h3>
                <p className="text-[10px] text-slate-400 truncate">
                  {storeSchema?.location || "Akure, Nigeria"} • Open Now
                </p>
              </div>
              <div className="px-2 py-0.5 rounded-full bg-emerald-950 border border-emerald-800 text-[10px] font-mono text-emerald-300">
                Cart: {totalItems}
              </div>
            </div>

            {/* Mobile Product Feed */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2.5 pb-20">
              {inventory.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-slate-500 text-xs text-center">
                  Storefront empty. Complete Step 1 scan to synthesize products.
                </div>
              ) : (
                inventory.map((item) => (
                  <div
                    key={item.item_id}
                    className="p-2.5 bg-slate-900 border border-slate-800 rounded-xl space-y-1.5"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-semibold text-xs text-slate-100">
                          {item.name}
                        </h4>
                        <span className="text-xs font-mono font-bold text-emerald-400">
                          {item.suggested_price.toLocaleString()} {currency}
                        </span>
                      </div>
                      <button
                        onClick={() => addToCart(item.item_id)}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-[10px] font-bold shadow-sm"
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
              <div className="absolute bottom-2 left-2 right-2 p-2.5 bg-slate-900/95 backdrop-blur-md border border-slate-800 rounded-2xl flex justify-between items-center shadow-xl">
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
                  className="px-3.5 py-1.5 bg-[#25D366] hover:bg-[#20ba59] text-black font-bold rounded-xl text-xs flex items-center space-x-1 shadow-md"
                >
                  <PhoneCall className="w-3 h-3" />
                  <span>Order on WhatsApp</span>
                </button>
              </div>
            )}
          </div>
        ) : (
          /* Code Inspector View */
          <div className="w-full h-full flex flex-col bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
            {/* File Tabs */}
            <div className="flex items-center justify-between bg-slate-900 px-3 py-2 border-b border-slate-800">
              <div className="flex items-center space-x-1.5 overflow-x-auto">
                {Object.keys(files).map((filename) => (
                  <button
                    key={filename}
                    onClick={() => setSelectedFile(filename)}
                    className={`px-3 py-1 rounded-lg text-xs font-mono transition-colors ${
                      selectedFile === filename
                        ? "bg-slate-800 text-cyan-300 font-bold"
                        : "text-slate-400 hover:text-slate-200"
                    }`}
                  >
                    {filename}
                  </button>
                ))}
              </div>
              <button
                onClick={copyCode}
                className="flex items-center space-x-1 px-2.5 py-1 bg-slate-800 hover:bg-slate-700 rounded text-xs text-slate-300 font-mono transition-colors"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? "Copied" : "Copy"}</span>
              </button>
            </div>

            {/* Code Content */}
            <pre className="flex-1 p-4 text-xs font-mono text-slate-300 overflow-y-auto whitespace-pre-wrap leading-relaxed">
              {files[selectedFile] || "// Select a generated file tab above"}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};
