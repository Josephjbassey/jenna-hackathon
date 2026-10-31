"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Upload,
  Scan,
  Sparkles,
  MapPin,
  DollarSign,
  Phone,
  Store,
  Layers,
  Check,
} from "lucide-react";
import {
  BoundingBox,
  SegmentCrop,
  SegmentResponse,
  MerchantContext,
  PipelineResponse,
  scanStoreJson,
} from "@/lib/api";

interface SegmentCanvasProps {
  merchantContext: MerchantContext;
  onUpdateMerchantContext: (ctx: MerchantContext) => void;
  onPipelineComplete: (result: PipelineResponse) => void;
  onSelectBox: (box: BoundingBox) => void;
}

export const SegmentCanvas: React.FC<SegmentCanvasProps> = ({
  merchantContext,
  onUpdateMerchantContext,
  onPipelineComplete,
  onSelectBox,
}) => {
  const [isScanning, setIsScanning] = useState<boolean>(false);
  const [segmentData, setSegmentData] = useState<SegmentResponse | null>(null);
  const [hoveredBoxId, setHoveredBoxId] = useState<string | null>(null);
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>("seg_001");
  const [customImage, setCustomImage] = useState<string | null>(null);

  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initial scan on mount
  useEffect(() => {
    executeFullScan();
  }, []);

  const executeFullScan = async (uploadedBase64?: string) => {
    setIsScanning(true);
    try {
      const payloadImage =
        uploadedBase64 ||
        "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";

      const result = await scanStoreJson(
        payloadImage,
        merchantContext.store_name,
        merchantContext.currency,
        merchantContext.location,
        merchantContext.whatsapp_number
      );

      setSegmentData({
        success: true,
        model_used: "sam-3.1",
        image_width: 1280,
        image_height: 720,
        bounding_boxes: result.bounding_boxes,
        crops: [],
        processing_time_ms: result.processing_time_ms,
        total_segments: result.segments_found,
      });

      if (result.bounding_boxes.length > 0) {
        setSelectedBoxId(result.bounding_boxes[0].box_id);
        onSelectBox(result.bounding_boxes[0]);
      }

      onPipelineComplete(result);
    } catch (err) {
      console.error("Storefront scan error:", err);
    } finally {
      setIsScanning(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const b64 = event.target?.result as string;
      setCustomImage(b64);
      executeFullScan(b64);
    };
    reader.readAsDataURL(file);
  };

  // Draw SAM 3.1 Bounding Boxes over Shelf Viewport
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (!segmentData) return;

    segmentData.bounding_boxes.forEach((box) => {
      const [ymin, xmin, ymax, xmax] = box.bbox;
      const x = xmin * canvas.width;
      const y = ymin * canvas.height;
      const boxW = (xmax - xmin) * canvas.width;
      const boxH = (ymax - ymin) * canvas.height;

      const isSelected = box.box_id === selectedBoxId;
      const isHovered = box.box_id === hoveredBoxId;

      // Box outline
      ctx.lineWidth = isSelected ? 2.5 : isHovered ? 2 : 1.5;
      ctx.strokeStyle = isSelected
        ? "#ffffff"
        : isHovered
        ? "#38bdf8"
        : "rgba(56, 189, 248, 0.65)";
      ctx.strokeRect(x, y, boxW, boxH);

      // Box translucent fill
      ctx.fillStyle = isSelected
        ? "rgba(255, 255, 255, 0.14)"
        : isHovered
        ? "rgba(56, 189, 248, 0.22)"
        : "rgba(56, 189, 248, 0.08)";
      ctx.fillRect(x, y, boxW, boxH);

      // Monospace label tag
      const labelText = `${box.label} · ${(box.confidence * 100).toFixed(0)}%`;
      ctx.font = "bold 12px ui-monospace, SFMono-Regular, monospace";
      const metrics = ctx.measureText(labelText);
      const tagW = metrics.width + 12;
      const tagH = 20;
      const tagY = Math.max(0, y - tagH);

      ctx.fillStyle = isSelected ? "#ffffff" : isHovered ? "#38bdf8" : "#0d131f";
      ctx.fillRect(x, tagY, tagW, tagH);

      ctx.fillStyle = isSelected ? "#0a0d14" : isHovered ? "#080c14" : "#e2e8f0";
      ctx.fillText(labelText, x + 6, tagY + 14);
    });
  }, [segmentData, hoveredBoxId, selectedBoxId]);

  return (
    <div className="flex flex-col h-full bg-[#0d1117] rounded-2xl border border-white/10 p-4 shadow-2xl">
      {/* Merchant Context Header */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 pb-3 border-b border-white/10">
        <div>
          <label className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
            Store Name
          </label>
          <div className="flex items-center space-x-2 bg-[#161b22] border border-white/10 rounded-lg px-2.5 py-1.5 focus-within:border-emerald-500/60 transition-colors">
            <Store className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
            <input
              type="text"
              value={merchantContext.store_name}
              onChange={(e) =>
                onUpdateMerchantContext({ ...merchantContext, store_name: e.target.value })
              }
              className="bg-transparent text-xs text-slate-100 focus:outline-none w-full"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
            Physical Location
          </label>
          <div className="flex items-center space-x-2 bg-[#161b22] border border-white/10 rounded-lg px-2.5 py-1.5 focus-within:border-emerald-500/60 transition-colors">
            <MapPin className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
            <input
              type="text"
              value={merchantContext.location}
              onChange={(e) =>
                onUpdateMerchantContext({ ...merchantContext, location: e.target.value })
              }
              className="bg-transparent text-xs text-slate-100 focus:outline-none w-full"
            />
          </div>
        </div>

        <div>
          <label className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
            Currency
          </label>
          <div className="flex items-center space-x-2 bg-[#161b22] border border-white/10 rounded-lg px-2.5 py-1.5 focus-within:border-emerald-500/60 transition-colors">
            <DollarSign className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
            <select
              value={merchantContext.currency}
              onChange={(e) =>
                onUpdateMerchantContext({ ...merchantContext, currency: e.target.value })
              }
              className="bg-transparent text-xs text-slate-100 focus:outline-none w-full"
            >
              <option value="NGN" className="bg-[#161b22]">NGN (₦ Nigerian Naira)</option>
              <option value="USD" className="bg-[#161b22]">USD ($ US Dollar)</option>
              <option value="KES" className="bg-[#161b22]">KES (KSh Kenyan Shilling)</option>
              <option value="GHS" className="bg-[#161b22]">GHS (GH₵ Ghanaian Cedi)</option>
              <option value="ZAR" className="bg-[#161b22]">ZAR (R South African Rand)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
            WhatsApp Orders
          </label>
          <div className="flex items-center space-x-2 bg-[#161b22] border border-white/10 rounded-lg px-2.5 py-1.5 focus-within:border-emerald-500/60 transition-colors">
            <Phone className="w-3.5 h-3.5 text-[#25D366] flex-shrink-0" />
            <input
              type="text"
              value={merchantContext.whatsapp_number || ""}
              onChange={(e) =>
                onUpdateMerchantContext({ ...merchantContext, whatsapp_number: e.target.value })
              }
              className="bg-transparent text-xs text-slate-100 focus:outline-none w-full font-mono"
            />
          </div>
        </div>
      </div>

      {/* Action / Trigger Bar */}
      <div className="flex items-center justify-between py-3">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
          <h2 className="font-semibold text-xs text-slate-100 uppercase tracking-wider font-mono">
            SAM 3.1 Visual Perception · Spatial Extraction
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
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[#161b22] hover:bg-[#21262d] text-slate-200 border border-white/10 transition-colors"
          >
            <Upload className="w-3.5 h-3.5 text-slate-400" />
            <span>Upload Photo</span>
          </button>

          <button
            onClick={() => executeFullScan(customImage || undefined)}
            disabled={isScanning}
            className="flex items-center space-x-1.5 px-4 py-1.5 rounded-lg text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg shadow-emerald-500/20 active:translate-y-0.5 transition-all disabled:opacity-50"
          >
            <Sparkles className={`w-3.5 h-3.5 ${isScanning ? "animate-spin" : ""}`} />
            <span>{isScanning ? "Digitizing..." : "1-Click Store Scan"}</span>
          </button>
        </div>
      </div>

      {/* Main Vector Shelf & Interactive Canvas Viewport */}
      <div className="relative flex-1 min-h-[340px] bg-[#07090e] rounded-xl overflow-hidden border border-white/10 flex items-center justify-center">
        {/* Render Vector Stall Artwork Directly (Zero broken image dependencies) */}
        {!customImage ? (
          <svg
            viewBox="0 0 1280 720"
            className="w-full h-full object-contain select-none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <rect width="1280" height="720" fill="#080a0f" />

            {/* Market Awning / Stall Canopy */}
            <path d="M0,0 L1280,0 L1280,75 L0,75 Z" fill="#064e3b" />
            <path d="M0,75 Q640,115 1280,75 L1280,88 Q640,128 0,88 Z" fill="#10b981" />
            <text x="45" y="45" fill="#ffffff" fontFamily="sans-serif" fontSize="22" fontWeight="700">
              {merchantContext.store_name} — Provisions &amp; Fresh Harvest
            </text>
            <text x="45" y="68" fill="#a7f3d0" fontFamily="monospace" fontSize="13">
              {merchantContext.location} • Physical Inventory Shelf Frame #042
            </text>

            {/* Wooden Shelving Architecture */}
            <rect x="35" y="110" width="1210" height="575" rx="12" fill="#141820" stroke="#21262d" strokeWidth="2" />
            <rect x="35" y="380" width="1210" height="18" fill="#2d333b" />
            <rect x="35" y="665" width="1210" height="20" fill="#2d333b" />

            {/* Shelf 1, Slot 1: Large Organic Yams */}
            <g id="stall-yams">
              <rect x="65" y="135" width="350" height="235" rx="10" fill="#1c1410" stroke="#78350f" strokeWidth="1.5" />
              <ellipse cx="180" cy="250" rx="90" ry="34" fill="#92400e" transform="rotate(-15 180 250)" />
              <ellipse cx="280" cy="240" rx="95" ry="36" fill="#78350f" transform="rotate(10 280 240)" />
              <ellipse cx="230" cy="285" rx="100" ry="40" fill="#b45309" />
              <text x="85" y="175" fill="#fef3c7" fontFamily="sans-serif" fontWeight="700" fontSize="15">Organic Local Yams</text>
              <text x="85" y="196" fill="#f59e0b" fontFamily="monospace" fontSize="12">Qty: 4 Large Tubers • 2,500 {merchantContext.currency}/ea</text>
            </g>

            {/* Shelf 1, Slot 2: Tomatoes & Peppers Basket */}
            <g id="stall-tomatoes">
              <rect x="435" y="135" width="370" height="235" rx="10" fill="#1f1012" stroke="#991b1b" strokeWidth="1.5" />
              <circle cx="525" cy="250" r="38" fill="#dc2626" />
              <circle cx="585" cy="240" r="36" fill="#ef4444" />
              <circle cx="650" cy="255" r="40" fill="#b91c1c" />
              <circle cx="560" cy="295" r="32" fill="#f87171" />
              <circle cx="620" cy="290" r="34" fill="#dc2626" />
              <path d="M700,260 Q730,220 740,270 Z" fill="#ea580c" />
              <path d="M730,280 Q760,250 750,300 Z" fill="#f97316" />
              <text x="455" y="175" fill="#fee2e2" fontFamily="sans-serif" fontWeight="700" fontSize="15">Fresh Red Produce Basket</text>
              <text x="455" y="196" fill="#ef4444" fontFamily="monospace" fontSize="12">Qty: 6 Baskets • 1,800 {merchantContext.currency}/ea</text>
            </g>

            {/* Shelf 1, Slot 3: White Garri 5kg Tubs */}
            <g id="stall-garri">
              <rect x="825" y="135" width="395" height="235" rx="10" fill="#131b26" stroke="#2563eb" strokeWidth="1.5" />
              <rect x="870" y="210" width="135" height="140" rx="8" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="2.5" />
              <rect x="1035" y="210" width="135" height="140" rx="8" fill="#f8fafc" stroke="#cbd5e1" strokeWidth="2.5" />
              <text x="845" y="175" fill="#dbeafe" fontFamily="sans-serif" fontWeight="700" fontSize="15">Ijebu White Garri (5kg Seal)</text>
              <text x="845" y="196" fill="#60a5fa" fontFamily="monospace" fontSize="12">Qty: 8 Sealed • 3,200 {merchantContext.currency}/ea</text>
            </g>

            {/* Shelf 2, Slot 4: Pure Palm Oil 1L Bottles */}
            <g id="stall-palmoil">
              <rect x="65" y="415" width="350" height="235" rx="10" fill="#201108" stroke="#c2410c" strokeWidth="1.5" />
              <rect x="130" y="470" width="60" height="150" rx="8" fill="#b91c1c" opacity="0.9" />
              <rect x="210" y="470" width="60" height="150" rx="8" fill="#c2410c" opacity="0.9" />
              <rect x="290" y="470" width="60" height="150" rx="8" fill="#9a3412" opacity="0.9" />
              <text x="85" y="450" fill="#ffedd5" fontFamily="sans-serif" fontWeight="700" fontSize="15">Pure Palm Oil (1L Bottle)</text>
              <text x="85" y="472" fill="#fb923c" fontFamily="monospace" fontSize="12">Qty: 10 Bottles • 1,600 {merchantContext.currency}/ea</text>
            </g>

            {/* Shelf 2, Slot 5: Ripe Cooking Plantains */}
            <g id="stall-plantains">
              <rect x="435" y="415" width="370" height="235" rx="10" fill="#191d0d" stroke="#65a30d" strokeWidth="1.5" />
              <path d="M480,550 Q560,490 640,560 Q560,530 480,550 Z" fill="#eab308" />
              <path d="M510,580 Q590,520 670,590 Q590,560 510,580 Z" fill="#ca8a04" />
              <path d="M540,610 Q620,550 700,620 Q620,590 540,610 Z" fill="#a16207" />
              <text x="455" y="450" fill="#fef9c3" fontFamily="sans-serif" fontWeight="700" fontSize="15">Ripe Plantain Bunches</text>
              <text x="455" y="472" fill="#eab308" fontFamily="monospace" fontSize="12">Qty: 5 Bunches • 2,000 {merchantContext.currency}/ea</text>
            </g>

            {/* Shelf 2, Slot 6: Seasoning & Spice Packs */}
            <g id="stall-spices">
              <rect x="825" y="415" width="395" height="235" rx="10" fill="#1e180d" stroke="#d97706" strokeWidth="1.5" />
              <rect x="860" y="500" width="90" height="110" rx="6" fill="#b45309" />
              <rect x="970" y="500" width="90" height="110" rx="6" fill="#b91c1c" />
              <rect x="1080" y="500" width="90" height="110" rx="6" fill="#d97706" />
              <text x="845" y="450" fill="#fef3c7" fontFamily="sans-serif" fontWeight="700" fontSize="15">Assorted Market Spices</text>
              <text x="845" y="472" fill="#f59e0b" fontFamily="monospace" fontSize="12">Qty: 12 Packs • 900 {merchantContext.currency}/ea</text>
            </g>
          </svg>
        ) : (
          <img
            src={customImage}
            alt="Uploaded Physical Inventory"
            className="w-full h-full object-contain pointer-events-none select-none"
          />
        )}

        {/* Interactive SAM 3.1 Bounding Box Canvas */}
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
          onMouseLeave={() => setHoveredBoxId(null)}
        />
      </div>

      {/* Segment Selector Quick Strip */}
      {segmentData && segmentData.bounding_boxes.length > 0 && (
        <div className="pt-3 flex items-center justify-between">
          <span className="text-[11px] font-mono text-slate-400">
            Detected: {segmentData.bounding_boxes.length} SKUs
          </span>
          <div className="flex items-center space-x-1.5 overflow-x-auto py-0.5">
            {segmentData.bounding_boxes.map((box) => (
              <button
                key={box.box_id}
                onClick={() => {
                  setSelectedBoxId(box.box_id);
                  onSelectBox(box);
                }}
                className={`text-[11px] font-mono px-2.5 py-1 rounded-md border transition-all ${
                  box.box_id === selectedBoxId
                    ? "bg-white text-black font-semibold border-white"
                    : "bg-[#161b22] text-slate-300 border-white/10 hover:border-white/30"
                }`}
              >
                {box.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
