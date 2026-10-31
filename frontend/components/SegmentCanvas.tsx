"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Upload,
  Scan,
  Sparkles,
  RefreshCw,
  ShoppingBag,
  MapPin,
  DollarSign,
  Phone,
  Store,
  Layers,
} from "lucide-react";
import {
  BoundingBox,
  SegmentCrop,
  SegmentResponse,
  MerchantContext,
  PipelineResponse,
  scanStore,
  scanStoreJson,
  segmentImage,
} from "@/lib/api";

interface SegmentCanvasProps {
  merchantContext: MerchantContext;
  onUpdateMerchantContext: (ctx: MerchantContext) => void;
  onPipelineComplete: (result: PipelineResponse) => void;
  onSelectBox: (box: BoundingBox) => void;
}

// High-fidelity physical storefront SVG (market shelf with produce, yams, palm oil, garri)
const MARKET_STALL_SVG = `data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">
  <rect width="1280" height="720" fill="%230b0f17"/>
  <!-- Canopy / Market Stall Awning -->
  <path d="M0,0 L1280,0 L1280,70 L0,70 Z" fill="%23064e3b"/>
  <path d="M0,70 Q640,110 1280,70 L1280,85 Q640,125 0,85 Z" fill="%2310b981"/>
  <text x="50" y="45" fill="%23ffffff" font-family="sans-serif" font-size="22" font-weight="bold">Mama Cass Market — Local Produce &amp; Dry Provisions</text>
  <text x="50" y="70" fill="%23a7f3d0" font-family="monospace" font-size="14">Akure Central Market, Ondo State, Nigeria • Physical Inventory Shelf Frame #042</text>

  <!-- Wooden Stall Shelves Background -->
  <rect x="40" y="110" width="1200" height="570" rx="12" fill="%2318181b" stroke="%2327272a" stroke-width="2"/>
  <rect x="40" y="380" width="1200" height="18" fill="%233f3f46"/>
  <rect x="40" y="660" width="1200" height="20" fill="%233f3f46"/>

  <!-- Shelf 1, Item 1: Large Local Yams -->
  <g id="yams">
    <rect x="70" y="140" width="340" height="230" rx="12" fill="%23271c19" stroke="%2378350f" stroke-width="2"/>
    <ellipse cx="180" cy="250" rx="90" ry="35" fill="%2392400e" transform="rotate(-15 180 250)"/>
    <ellipse cx="280" cy="240" rx="95" ry="38" fill="%2378350f" transform="rotate(10 280 240)"/>
    <ellipse cx="230" cy="280" rx="100" ry="40" fill="%23b45309"/>
    <text x="90" y="180" fill="%23fde68a" font-family="sans-serif" font-weight="bold" font-size="16">Organic Local Yams</text>
    <text x="90" y="202" fill="%23d97706" font-family="monospace" font-size="13">Qty: 4 Large Tubers • NGN 2,500/ea</text>
  </g>

  <!-- Shelf 1, Item 2: Fresh Tomatoes & Peppers Basket -->
  <g id="tomatoes">
    <rect x="440" y="140" width="360" height="230" rx="12" fill="%23261214" stroke="%23991b1b" stroke-width="2"/>
    <circle cx="530" cy="250" r="38" fill="%23dc2626"/>
    <circle cx="585" cy="240" r="36" fill="%23ef4444"/>
    <circle cx="650" cy="255" r="40" fill="%23b91c1c"/>
    <circle cx="560" cy="295" r="32" fill="%23f87171"/>
    <circle cx="620" cy="290" r="34" fill="%23dc2626"/>
    <!-- Peppers -->
    <path d="M700,260 Q730,220 740,270 Z" fill="%23ea580c"/>
    <path d="M730,280 Q760,250 750,300 Z" fill="%23f97316"/>
    <text x="460" y="180" fill="%23fecaca" font-family="sans-serif" font-weight="bold" font-size="16">Fresh Red Produce Basket</text>
    <text x="460" y="202" fill="%23ef4444" font-family="monospace" font-size="13">Qty: 6 Baskets • NGN 1,800/ea</text>
  </g>

  <!-- Shelf 1, Item 3: Cassava Flour / Garri Containers -->
  <g id="garri">
    <rect x="830" y="140" width="370" height="230" rx="12" fill="%231e293b" stroke="%233b82f6" stroke-width="2"/>
    <rect x="870" y="210" width="130" height="140" rx="10" fill="%23f8fafc" stroke="%23cbd5e1" stroke-width="3"/>
    <rect x="1030" y="210" width="130" height="140" rx="10" fill="%23f8fafc" stroke="%23cbd5e1" stroke-width="3"/>
    <text x="850" y="180" fill="%23bfdbfe" font-family="sans-serif" font-weight="bold" font-size="16">Ijebu Garri (5kg Tub)</text>
    <text x="850" y="202" fill="%2360a5fa" font-family="monospace" font-size="13">Qty: 8 Sealed • NGN 3,200/ea</text>
  </g>

  <!-- Shelf 2, Item 4: Pure Palm Oil 1L Bottles -->
  <g id="palmoil">
    <rect x="70" y="420" width="340" height="230" rx="12" fill="%232b1308" stroke="%23c2410c" stroke-width="2"/>
    <rect x="130" y="470" width="60" height="150" rx="8" fill="%23b91c1c" opacity="0.9"/>
    <rect x="210" y="470" width="60" height="150" rx="8" fill="%23c2410c" opacity="0.9"/>
    <rect x="290" y="470" width="60" height="150" rx="8" fill="%239a3412" opacity="0.9"/>
    <text x="90" y="455" fill="%23fed7aa" font-family="sans-serif" font-weight="bold" font-size="16">Pure Palm Oil (1L)</text>
    <text x="90" y="475" fill="%23fb923c" font-family="monospace" font-size="13">Qty: 10 Bottles • NGN 1,600/ea</text>
  </g>

  <!-- Shelf 2, Item 5: Ripe Cooking Plantains -->
  <g id="plantains">
    <rect x="440" y="420" width="360" height="230" rx="12" fill="%23202511" stroke="%2384cc16" stroke-width="2"/>
    <path d="M480,550 Q560,490 640,560 Q560,530 480,550 Z" fill="%23eab308"/>
    <path d="M510,580 Q590,520 670,590 Q590,560 510,580 Z" fill="%23ca8a04"/>
    <path d="M540,610 Q620,550 700,620 Q620,590 540,610 Z" fill="%23a16207"/>
    <text x="460" y="455" fill="%23fef08a" font-family="sans-serif" font-weight="bold" font-size="16">Ripe Plantains</text>
    <text x="460" y="475" fill="%23eab308" font-family="monospace" font-size="13">Qty: 5 Bunches • NGN 2,000/ea</text>
  </g>

  <!-- Shelf 2, Item 6: Assorted Seasoning Spices Tray -->
  <g id="spices">
    <rect x="830" y="420" width="370" height="230" rx="12" fill="%23231a0a" stroke="%23d97706" stroke-width="2"/>
    <rect x="860" y="500" width="90" height="110" rx="6" fill="%23b45309"/>
    <rect x="970" y="500" width="90" height="110" rx="6" fill="%23b91c1c"/>
    <rect x="1080" y="500" width="90" height="110" rx="6" fill="%23d97706"/>
    <text x="850" y="455" fill="%23fef3c7" font-family="sans-serif" font-weight="bold" font-size="16">Local Seasoning Packs</text>
    <text x="850" y="475" fill="%23f59e0b" font-family="monospace" font-size="13">Qty: 12 Packs • NGN 900/ea</text>
  </g>
</svg>`;

export const SegmentCanvas: React.FC<SegmentCanvasProps> = ({
  merchantContext,
  onUpdateMerchantContext,
  onPipelineComplete,
  onSelectBox,
}) => {
  const [imageSrc, setImageSrc] = useState<string>(MARKET_STALL_SVG);
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [segmentData, setSegmentData] = useState<SegmentResponse | null>(null);
  const [hoveredBoxId, setHoveredBoxId] = useState<string | null>(null);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Run initial scan on mount
  useEffect(() => {
    executeFullScan(MARKET_STALL_SVG);
  }, []);

  const executeFullScan = async (srcToUse: string) => {
    setIsScanning(true);
    setErrorMsg(null);
    try {
      const res = await scanStoreJson(srcToUse, merchantContext);
      setSegmentData({
        success: true,
        model_used: "sam-3.1",
        image_width: 1280,
        image_height: 720,
        bounding_boxes: res.bounding_boxes,
        crops: [],
        processing_time_ms: res.processing_time_ms,
        total_segments: res.segments_found,
      });
      onPipelineComplete(res);
    } catch (err: any) {
      console.error("Scan error:", err);
      setErrorMsg(err.message || "Failed to scan physical inventory");
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const dataUrl = event.target?.result as string;
      setImageSrc(dataUrl);
      executeFullScan(dataUrl);
    };
    reader.readAsDataURL(file);
  };

  // Render SAM 3.1 overlays on Canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !segmentData) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const w = canvas.width;
    const h = canvas.height;

    segmentData.bounding_boxes.forEach((box, idx) => {
      const [ymin, xmin, ymax, xmax] = box.bbox;
      const x = xmin * w;
      const y = ymin * h;
      const boxW = (xmax - xmin) * w;
      const boxH = (ymax - ymin) * h;

      const isHovered = hoveredBoxId === box.box_id;
      const isSelected = selectedBoxId === box.box_id;

      const colors = ["#10b981", "#00f0ff", "#a855f7", "#f59e0b", "#ec4899", "#38bdf8"];
      const baseColor = colors[idx % colors.length];

      ctx.lineWidth = isSelected ? 3.5 : isHovered ? 2.5 : 1.8;
      ctx.strokeStyle = isSelected ? "#ffffff" : baseColor;
      ctx.setLineDash(isHovered ? [5, 3] : []);
      ctx.strokeRect(x, y, boxW, boxH);

      ctx.fillStyle = isSelected
        ? "rgba(255, 255, 255, 0.15)"
        : isHovered
        ? `${baseColor}30`
        : `${baseColor}12`;
      ctx.fillRect(x, y, boxW, boxH);

      // Label Tag
      const tagText = `${box.label} [IOU: ${(box.confidence * 100).toFixed(0)}%]`;
      ctx.font = "bold 11px monospace";
      const textMetrics = ctx.measureText(tagText);
      const tagHeight = 20;
      const tagWidth = textMetrics.width + 14;

      ctx.fillStyle = isSelected ? "#ffffff" : baseColor;
      ctx.fillRect(x, Math.max(0, y - tagHeight), tagWidth, tagHeight);

      ctx.fillStyle = isSelected ? "#000000" : "#0b0f17";
      ctx.fillText(tagText, x + 7, Math.max(14, y - 5));
    });
  }, [segmentData, hoveredBoxId, selectedBoxId]);

  return (
    <div className="flex flex-col h-full bg-[#111726]/85 backdrop-blur-md rounded-2xl border border-slate-800 p-4 shadow-xl">
      {/* Merchant Context Setup Header */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5 pb-3 border-b border-slate-800/80">
        <div>
          <label className="text-[10px] text-slate-400 font-mono uppercase block mb-1">
            Store Name
          </label>
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <Store className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
            <input
              type="text"
              value={merchantContext.store_name}
              onChange={(e) =>
                onUpdateMerchantContext({ ...merchantContext, store_name: e.target.value })
              }
              className="bg-transparent text-xs text-slate-200 focus:outline-none w-full"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] text-slate-400 font-mono uppercase block mb-1">
            Location
          </label>
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <MapPin className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <input
              type="text"
              value={merchantContext.location}
              onChange={(e) =>
                onUpdateMerchantContext({ ...merchantContext, location: e.target.value })
              }
              className="bg-transparent text-xs text-slate-200 focus:outline-none w-full"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] text-slate-400 font-mono uppercase block mb-1">
            Currency
          </label>
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <DollarSign className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <select
              value={merchantContext.currency}
              onChange={(e) =>
                onUpdateMerchantContext({ ...merchantContext, currency: e.target.value })
              }
              className="bg-transparent text-xs text-slate-200 focus:outline-none w-full"
            >
              <option value="NGN">NGN (₦ Nigerian Naira)</option>
              <option value="USD">USD ($ US Dollar)</option>
              <option value="KES">KES (KSh Kenyan Shilling)</option>
              <option value="GHS">GHS (GH₵ Ghanaian Cedi)</option>
              <option value="ZAR">ZAR (R South African Rand)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="text-[10px] text-slate-400 font-mono uppercase block mb-1">
            WhatsApp Checkout
          </label>
          <div className="flex items-center space-x-1.5 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5">
            <Phone className="w-3.5 h-3.5 text-[#25D366] flex-shrink-0" />
            <input
              type="text"
              value={merchantContext.whatsapp_number || ""}
              onChange={(e) =>
                onUpdateMerchantContext({
                  ...merchantContext,
                  whatsapp_number: e.target.value,
                })
              }
              className="bg-transparent text-xs text-slate-200 focus:outline-none w-full font-mono"
            />
          </div>
        </div>
      </div>

      {/* Action / Trigger Bar */}
      <div className="flex items-center justify-between py-2.5">
        <div className="flex items-center space-x-2">
          <Scan className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold text-sm text-slate-100">
            SAM 3.1 Visual Perception (Physical Shelf Extraction)
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept="image/*"
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
          >
            <Upload className="w-3.5 h-3.5" />
            <span>Upload Store Photo</span>
          </button>

          <button
            onClick={() => executeFullScan(imageSrc)}
            disabled={isScanning}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isScanning ? "animate-spin" : ""}`} />
            <span>{isScanning ? "Digitizing Store..." : "1-Click Store Scan"}</span>
          </button>
        </div>
      </div>

      {/* Main Canvas Viewport */}
      <div className="relative flex-1 min-h-[300px] bg-slate-950 rounded-xl overflow-hidden border border-slate-800 flex items-center justify-center">
        <img
          src={imageSrc}
          alt="Storefront Shelf"
          className="w-full h-full object-contain pointer-events-none select-none"
        />

        <canvas
          ref={canvasRef}
          width={1280}
          height={720}
          className="absolute inset-0 w-full h-full object-contain cursor-pointer"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const clickX = (e.clientX - rect.left) / rect.width;
            const clickY = (e.clientY - rect.top) / rect.height;

            if (segmentData) {
              const clicked = segmentData.bounding_boxes.find((b) => {
                const [ymin, xmin, ymax, xmax] = b.bbox;
                return clickX >= xmin && clickX <= xmax && clickY >= ymin && clickY <= ymax;
              });
              if (clicked) {
                setSelectedBoxId(clicked.box_id);
                onSelectBox(clicked);
              }
            }
          }}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;

            if (segmentData) {
              const hovered = segmentData.bounding_boxes.find((b) => {
                const [ymin, xmin, ymax, xmax] = b.bbox;
                return x >= xmin && x <= xmax && y >= ymin && y <= ymax;
              });
              setHoveredBoxId(hovered ? hovered.box_id : null);
            }
          }}
        />

        {isScanning && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm flex flex-col items-center justify-center z-20">
            <div className="w-12 h-12 border-3 border-emerald-400 border-t-transparent rounded-full animate-spin" />
            <p className="mt-4 text-xs font-mono font-bold text-emerald-300">
              SAM 3.1 isolating inventory masks → Muse Spark pricing → Muse Code synthesizing...
            </p>
          </div>
        )}
      </div>

      {/* Detected Inventory Item Chips */}
      <div className="mt-3 pt-2.5 border-t border-slate-800 flex items-center justify-between">
        <span className="text-xs text-slate-400 font-mono">
          Extracted Products: {segmentData?.bounding_boxes.length || 0}
        </span>
        <div className="flex items-center space-x-1.5 overflow-x-auto max-w-[70%]">
          {segmentData?.bounding_boxes.map((b) => (
            <button
              key={b.box_id}
              onClick={() => {
                setSelectedBoxId(b.box_id);
                onSelectBox(b);
              }}
              className={`px-2.5 py-1 rounded-md text-[11px] font-mono whitespace-nowrap transition-all border ${
                selectedBoxId === b.box_id
                  ? "bg-emerald-500/20 text-emerald-300 border-emerald-400"
                  : "bg-slate-900 text-slate-300 border-slate-800 hover:border-slate-700"
              }`}
            >
              {b.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
